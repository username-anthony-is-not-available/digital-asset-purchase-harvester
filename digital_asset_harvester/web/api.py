import os
import logging
import shutil
import uuid
import csv
import json
import tempfile
import threading
from datetime import datetime
from typing import List
from fastapi import APIRouter, File, UploadFile, Depends, BackgroundTasks, HTTPException
from fastapi.responses import RedirectResponse, StreamingResponse
from io import StringIO
from .. import (
    EmailPurchaseExtractor,
    MboxDataExtractor,
    EmlDataExtractor,
    get_llm_client,
    get_settings,
)
from ..ingest import ImapClient, GmailClient, OutlookClient
from ..utils.sync_state import SyncState
from ..telemetry import StructuredLoggerFactory
from ..cli import process_emails, configure_logging
from ..utils.data_utils import normalize_for_frontend, denormalize_from_frontend
from ..exporters.koinly import KoinlyReportGenerator
from ..exporters.cryptotaxcalculator import CryptoTaxCalculatorReportGenerator
from ..exporters.cra import CRAReportGenerator, write_purchase_data_to_cra_pdf

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory store for task status and results
TASKS_DB = "tasks_db.json"
tasks = {}
tasks_lock = threading.Lock()

def _save_tasks():
    """Save tasks to a JSON file atomically."""
    with tasks_lock:
        try:
            # Use a temporary file for atomic write
            fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(TASKS_DB)) or ".", suffix=".tmp")
            try:
                with os.fdopen(fd, 'w') as f:
                    json.dump(tasks, f, indent=2)
                # Atomic replacement
                os.replace(temp_path, TASKS_DB)
            except Exception:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise
        except Exception as e:
            logger.error(f"Failed to save tasks: {e}")

def _load_tasks():
    """Load tasks from a JSON file."""
    global tasks
    with tasks_lock:
        if os.path.exists(TASKS_DB):
            try:
                with open(TASKS_DB, "r") as f:
                    tasks = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load tasks: {e}")
                tasks = {}

_load_tasks()

DEFAULT_CSV_HEADERS = [
    "email_subject", "vendor", "currency", "amount", "purchase_date",
    "transaction_id", "crypto_currency", "crypto_amount", "confidence_score"
]


def get_logger_factory():
    settings = get_settings()
    return configure_logging(settings)

def process_eml_files(task_id: str, temp_dir: str, logger_factory: StructuredLoggerFactory):
    """Processes a directory of eml files and stores the result."""
    with tasks_lock:
        tasks[task_id] = {
            "status": "processing",
            "result": None,
            "created_at": datetime.now().isoformat()
        }
    _save_tasks()

    settings = get_settings()
    llm_client = get_llm_client()
    extractor = EmailPurchaseExtractor(
        settings=settings,
        llm_client=llm_client,
        logger_factory=logger_factory,
    )

    try:
        eml_reader = EmlDataExtractor(temp_dir)
        emails = eml_reader.extract_emails(raw=settings.enable_multiprocessing)

        purchases, _ = process_emails(emails, extractor, logger_factory, show_progress=False)

        # Initialize review status and map fields for frontend
        normalized_purchases = [normalize_for_frontend(p) for p in purchases]

        tasks[task_id]["status"] = "complete"
        tasks[task_id]["result"] = normalized_purchases
        tasks[task_id]["metrics"] = extractor.metrics.snapshot()
        _save_tasks()
    except Exception as e:
        import traceback
        tasks[task_id].update({"status": "error", "error": str(e), "traceback": traceback.format_exc()})
        _save_tasks()
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def process_mbox_file(task_id: str, temp_path: str, logger_factory: StructuredLoggerFactory):
    """Processes the mbox file and stores the result."""
    with tasks_lock:
        tasks[task_id] = {
            "status": "processing",
            "result": None,
            "created_at": datetime.now().isoformat()
        }
    _save_tasks()

    settings = get_settings()
    llm_client = get_llm_client()
    extractor = EmailPurchaseExtractor(
        settings=settings,
        llm_client=llm_client,
        logger_factory=logger_factory,
    )

    try:
        mbox_reader = MboxDataExtractor(temp_path)
        emails = mbox_reader.extract_emails(raw=settings.enable_multiprocessing)

        purchases, _ = process_emails(emails, extractor, logger_factory, show_progress=False)

        # Initialize review status and map fields for frontend
        normalized_purchases = [normalize_for_frontend(p) for p in purchases]

        tasks[task_id]["status"] = "complete"
        tasks[task_id]["result"] = normalized_purchases
        tasks[task_id]["metrics"] = extractor.metrics.snapshot()
        _save_tasks()
    except Exception as e:
        import traceback
        tasks[task_id].update({"status": "error", "error": str(e), "traceback": traceback.format_exc()})
        _save_tasks()
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def process_imap_sync(task_id: str, logger_factory: StructuredLoggerFactory):
    """Synchronizes emails from IMAP and stores the result."""
    with tasks_lock:
        tasks[task_id] = {
            "status": "processing",
            "result": None,
            "created_at": datetime.now().isoformat()
        }
    _save_tasks()
    settings = get_settings()

    if not settings.enable_imap:
        tasks[task_id].update({"status": "error", "error": "IMAP is not enabled in settings"})
        _save_tasks()
        return

    llm_client = get_llm_client()
    extractor = EmailPurchaseExtractor(
        settings=settings,
        llm_client=llm_client,
        logger_factory=logger_factory,
    )

    try:
        with ImapClient(
            settings.imap_server,
            settings.imap_user,
            settings.imap_password,
            settings.imap_auth_type,
            settings.imap_client_id,
            settings.imap_authority,
        ) as imap_client:
            sync_state = SyncState()
            last_uid = sync_state.get_last_uid(settings.imap_server, settings.imap_user, settings.imap_folder)

            if last_uid > 0:
                full_query = f"UID {last_uid + 1}:* {settings.imap_query}"
            else:
                full_query = settings.imap_query

            uids = imap_client.uid_search(full_query, settings.imap_folder)

            if not uids:
                tasks[task_id].update({"status": "complete", "result": []})
                _save_tasks()
                return

            emails = list(imap_client.fetch_emails_by_uids(uids, settings.imap_folder, raw=settings.enable_multiprocessing))
            purchases, _ = process_emails(emails, extractor, logger_factory, show_progress=False)

            if emails:
                max_uid = max(int(email["uid"]) for email in emails)
                sync_state.set_last_uid(settings.imap_server, settings.imap_user, settings.imap_folder, max_uid)

            normalized_purchases = [normalize_for_frontend(p) for p in purchases]
            tasks[task_id]["status"] = "complete"
            tasks[task_id]["result"] = normalized_purchases
            tasks[task_id]["metrics"] = extractor.metrics.snapshot()
            _save_tasks()

    except Exception as e:
        import traceback
        tasks[task_id].update({"status": "error", "error": str(e), "traceback": traceback.format_exc()})
        _save_tasks()

def process_gmail_sync(task_id: str, logger_factory: StructuredLoggerFactory):
    """Synchronizes emails from Gmail API and stores the result."""
    with tasks_lock:
        tasks[task_id] = {
            "status": "processing",
            "result": None,
            "created_at": datetime.now().isoformat()
        }
    _save_tasks()
    settings = get_settings()

    llm_client = get_llm_client()
    extractor = EmailPurchaseExtractor(
        settings=settings,
        llm_client=llm_client,
        logger_factory=logger_factory,
    )

    try:
        gmail_client = GmailClient()
        query = settings.gmail_query
        emails = gmail_client.search_emails(query, raw=settings.enable_multiprocessing)
        purchases, _ = process_emails(emails, extractor, logger_factory, show_progress=False)

        normalized_purchases = [normalize_for_frontend(p) for p in purchases]
        tasks[task_id]["status"] = "complete"
        tasks[task_id]["result"] = normalized_purchases
        tasks[task_id]["metrics"] = extractor.metrics.snapshot()
        _save_tasks()
    except Exception as e:
        import traceback
        tasks[task_id].update({"status": "error", "error": str(e), "traceback": traceback.format_exc()})
        _save_tasks()

def process_outlook_sync(task_id: str, client_id: str, authority: str, logger_factory: StructuredLoggerFactory):
    """Synchronizes emails from Outlook API and stores the result."""
    with tasks_lock:
        tasks[task_id] = {
            "status": "processing",
            "result": None,
            "created_at": datetime.now().isoformat()
        }
    _save_tasks()
    settings = get_settings()

    llm_client = get_llm_client()
    extractor = EmailPurchaseExtractor(
        settings=settings,
        llm_client=llm_client,
        logger_factory=logger_factory,
    )

    try:
        outlook_client = OutlookClient(client_id, authority)
        query = settings.outlook_query
        emails = outlook_client.search_emails(query, raw=settings.enable_multiprocessing)
        purchases, _ = process_emails(emails, extractor, logger_factory, show_progress=False)

        normalized_purchases = [normalize_for_frontend(p) for p in purchases]
        tasks[task_id]["status"] = "complete"
        tasks[task_id]["result"] = normalized_purchases
        tasks[task_id]["metrics"] = extractor.metrics.snapshot()
        _save_tasks()
    except Exception as e:
        import traceback
        tasks[task_id].update({"status": "error", "error": str(e), "traceback": traceback.format_exc()})
        _save_tasks()

@router.get("/export/koinly/{task_id}")
async def export_koinly(task_id: str):
    task = tasks.get(task_id)
    if not task or task["status"] != "complete":
        raise HTTPException(status_code=404, detail="Task not found or not complete")

    results = task.get("result", [])
    # Denormalize records for exporter
    denormalized_results = [denormalize_from_frontend(p) for p in results]

    generator = KoinlyReportGenerator()
    rows = generator.generate_csv_rows(denormalized_results)

    output = StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    else:
        # Standard Koinly headers if no data
        headers = [
            "Date", "Sent Amount", "Sent Currency", "Received Amount", "Received Currency",
            "Fee Amount", "Fee Currency", "Net Worth Amount", "Net Worth Currency",
            "Label", "Description", "TxHash"
        ]
        writer = csv.writer(output)
        writer.writerow(headers)

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=koinly_{task_id}.csv"}
    )

@router.get("/export/ctc/{task_id}")
async def export_ctc(task_id: str):
    task = tasks.get(task_id)
    if not task or task["status"] != "complete":
        raise HTTPException(status_code=404, detail="Task not found or not complete")

    results = task.get("result", [])
    denormalized_results = [denormalize_from_frontend(p) for p in results]

    generator = CryptoTaxCalculatorReportGenerator()
    rows = generator.generate_csv_rows(denormalized_results)

    output = StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    else:
        headers = [
            "Timestamp (UTC)", "Type", "Base Currency", "Base Amount", "Quote Currency",
            "Quote Amount", "Fee Currency", "Fee Amount", "From", "To", "ID", "Description"
        ]
        writer = csv.writer(output)
        writer.writerow(headers)

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=ctc_{task_id}.csv"}
    )

@router.get("/export/cra/{task_id}")
async def export_cra(task_id: str):
    task = tasks.get(task_id)
    if not task or task["status"] != "complete":
        raise HTTPException(status_code=404, detail="Task not found or not complete")

    results = task.get("result", [])
    denormalized_results = [denormalize_from_frontend(p) for p in results]

    generator = CRAReportGenerator()
    rows = generator.generate_csv_rows(denormalized_results)

    output = StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    else:
        headers = [
            "Date", "Type", "Received Quantity", "Received Currency", "Sent Quantity",
            "Sent Currency", "Fee Quantity", "Fee Currency", "Description"
        ]
        writer = csv.writer(output)
        writer.writerow(headers)

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=cra_{task_id}.csv"}
    )


@router.get("/export/cra-pdf/{task_id}")
async def export_cra_pdf(task_id: str):
    task = tasks.get(task_id)
    if not task or task["status"] != "complete":
        raise HTTPException(status_code=404, detail="Task not found or not complete")

    results = task.get("result", [])
    denormalized_results = [denormalize_from_frontend(p) for p in results]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        write_purchase_data_to_cra_pdf(denormalized_results, tmp.name)
        tmp_path = tmp.name

    def iterfile():
        with open(tmp_path, mode="rb") as f:
            yield from f
        os.remove(tmp_path)

    return StreamingResponse(
        iterfile(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=cra_report_{task_id}.pdf"},
    )

@router.post("/upload")
async def upload_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    logger_factory: StructuredLoggerFactory = Depends(get_logger_factory)
):
    task_id = str(uuid.uuid4())

    # Check if we have a single mbox file
    if len(files) == 1 and files[0].filename.endswith(".mbox"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mbox") as temp_file:
            shutil.copyfileobj(files[0].file, temp_file)
            temp_path = temp_file.name
        background_tasks.add_task(process_mbox_file, task_id, temp_path, logger_factory)
    else:
        # Otherwise, assume they are .eml files (or a mix, we will filter in background)
        temp_dir = tempfile.mkdtemp()
        for file in files:
            # Sanitize filename to prevent directory traversal
            filename = os.path.basename(file.filename)
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
        background_tasks.add_task(process_eml_files, task_id, temp_dir, logger_factory)

    return RedirectResponse(url=f"/status/{task_id}", status_code=303)

@router.post("/sync/imap")
async def sync_imap(
    background_tasks: BackgroundTasks,
    logger_factory: StructuredLoggerFactory = Depends(get_logger_factory)
):
    settings = get_settings()
    if not settings.enable_imap:
        raise HTTPException(status_code=400, detail="IMAP is not enabled in settings")

    task_id = str(uuid.uuid4())
    background_tasks.add_task(process_imap_sync, task_id, logger_factory)

    return RedirectResponse(url=f"/status/{task_id}", status_code=303)

@router.post("/sync/gmail")
async def sync_gmail(
    background_tasks: BackgroundTasks,
    logger_factory: StructuredLoggerFactory = Depends(get_logger_factory)
):
    task_id = str(uuid.uuid4())
    background_tasks.add_task(process_gmail_sync, task_id, logger_factory)

    return RedirectResponse(url=f"/status/{task_id}", status_code=303)

@router.post("/sync/outlook")
async def sync_outlook(
    background_tasks: BackgroundTasks,
    logger_factory: StructuredLoggerFactory = Depends(get_logger_factory)
):
    settings = get_settings()
    # Support both new and legacy setting names
    client_id = settings.outlook_client_id or settings.imap_client_id
    authority = settings.outlook_authority or settings.imap_authority

    if not client_id or not authority:
        raise HTTPException(status_code=400, detail="Outlook API requires outlook_client_id and outlook_authority in settings")

    task_id = str(uuid.uuid4())
    background_tasks.add_task(process_outlook_sync, task_id, client_id, authority, logger_factory)

    return RedirectResponse(url=f"/status/{task_id}", status_code=303)

@router.get("/status/{task_id}")
async def get_status(task_id: str):
    return tasks.get(task_id, {"status": "not_found"})

@router.get("/export/csv/{task_id}")
async def export_csv(task_id: str):
    task = tasks.get(task_id)
    if not task or task["status"] != "complete":
        return {"error": "Task not found or not complete"}

    output = StringIO()
    results = task.get("result", [])

    if not results:
        writer = csv.writer(output)
        writer.writerow(DEFAULT_CSV_HEADERS)
    else:
        writer = csv.DictWriter(output, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    output.seek(0)

    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=purchases_{task_id}.csv"})

@router.get("/export/json/{task_id}")
async def export_json(task_id: str):
    task = tasks.get(task_id)
    if not task or task["status"] != "complete":
        return {"error": "Task not found or not complete"}

    results = task.get("result", [])
    return StreamingResponse(
        iter([json.dumps(results, indent=2)]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=purchases_{task_id}.json"},
    )

@router.put("/task/{task_id}/records/{index}")
async def update_record(task_id: str, index: int, updated_record: dict):
    task = tasks.get(task_id)
    if not task or task["status"] != "complete":
        raise HTTPException(status_code=404, detail="Task not found or not complete")

    results = task.get("result", [])
    if index < 0 or index >= len(results):
        raise HTTPException(status_code=404, detail="Record index out of bounds")

    # Check if crypto_currency changed and we need to update asset_id
    from ..utils.asset_mapping import mapper
    old_currency = results[index].get("crypto_currency")
    new_currency = updated_record.get("crypto_currency")

    results[index].update(updated_record)

    if new_currency and new_currency != old_currency:
        # Only auto-update asset_id if it wasn't explicitly provided/changed to something non-empty
        if not updated_record.get("asset_id"):
            asset_id = mapper.get_asset_id(new_currency)
            if asset_id:
                results[index]["asset_id"] = asset_id

    # Reset review status on manual edit
    results[index]["review_status"] = "pending"
    _save_tasks()
    return {"status": "success", "updated_record": results[index]}


@router.put("/task/{task_id}/records/{index}/approve")
async def approve_record(task_id: str, index: int):
    task = tasks.get(task_id)
    if not task or task["status"] != "complete":
        raise HTTPException(status_code=404, detail="Task not found or not complete")

    results = task.get("result", [])
    if index < 0 or index >= len(results):
        raise HTTPException(status_code=404, detail="Record index out of bounds")

    results[index]["review_status"] = "approved"
    _save_tasks()
    return {"status": "success", "record": results[index]}


@router.put("/task/{task_id}/records/{index}/reject")
async def reject_record(task_id: str, index: int):
    task = tasks.get(task_id)
    if not task or task["status"] != "complete":
        raise HTTPException(status_code=404, detail="Task not found or not complete")

    results = task.get("result", [])
    if index < 0 or index >= len(results):
        raise HTTPException(status_code=404, detail="Record index out of bounds")

    results[index]["review_status"] = "rejected"
    _save_tasks()
    return {"status": "success", "record": results[index]}


@router.post("/task/{task_id}/approve-batch")
async def approve_batch(task_id: str, indices: list[int]):
    task = tasks.get(task_id)
    if not task or task["status"] != "complete":
        raise HTTPException(status_code=404, detail="Task not found or not complete")

    results = task.get("result", [])
    updated_indices = []
    for index in indices:
        if 0 <= index < len(results):
            results[index]["review_status"] = "approved"
            updated_indices.append(index)

    _save_tasks()
    return {"status": "success", "approved_indices": updated_indices}


@router.post("/task/{task_id}/reject-batch")
async def reject_batch(task_id: str, indices: list[int]):
    task = tasks.get(task_id)
    if not task or task["status"] != "complete":
        raise HTTPException(status_code=404, detail="Task not found or not complete")

    results = task.get("result", [])
    updated_indices = []
    for index in indices:
        if 0 <= index < len(results):
            results[index]["review_status"] = "rejected"
            updated_indices.append(index)

    _save_tasks()
    return {"status": "success", "rejected_indices": updated_indices}


@router.post("/task/{task_id}/records")
async def add_record(task_id: str):
    task = tasks.get(task_id)
    if not task or task["status"] != "complete":
        raise HTTPException(status_code=404, detail="Task not found or not complete")

    results = task.get("result", [])
    new_record = {
        "email_subject": "Manual Entry",
        "vendor": "Manual",
        "currency": "USD",
        "amount": 0.0,
        "purchase_date": "",
        "transaction_id": "",
        "crypto_currency": "",
        "crypto_amount": 0.0,
        "fee_amount": 0.0,
        "fee_currency": "",
        "asset_id": "",
        "confidence_score": 1.0,
        "review_status": "pending"
    }
    results.append(new_record)
    _save_tasks()
    return {"status": "success", "index": len(results) - 1, "record": new_record}


@router.delete("/task/{task_id}/records/{index}")
async def delete_record(task_id: str, index: int):
    task = tasks.get(task_id)
    if not task or task["status"] != "complete":
        raise HTTPException(status_code=404, detail="Task not found or not complete")

    results = task.get("result", [])
    if index < 0 or index >= len(results):
        raise HTTPException(status_code=404, detail="Record index out of bounds")

    deleted_record = results.pop(index)
    _save_tasks()
    return {"status": "success", "deleted_record": deleted_record}


@router.delete("/tasks")
async def clear_tasks():
    global tasks
    with tasks_lock:
        tasks = {}
    _save_tasks()
    return {"status": "success", "message": "All tasks cleared"}


@router.get("/metrics")
async def get_metrics():
    """Aggregate metrics from all completed tasks."""
    from ..telemetry import MetricsTracker

    combined_metrics = MetricsTracker()

    for task_id, task in tasks.items():
        if task.get("status") == "complete" and "metrics" in task:
            task_metrics = task["metrics"]
            for key, value in task_metrics.items():
                if isinstance(value, (int, float)) and not key.endswith("_latency"):
                    combined_metrics.increment(key, int(value))

    # Since we are not currently storing MetricsTracker objects in tasks (we store normalized dicts)
    # let's at least return the number of tasks as a metric
    combined_metrics.set_metadata("total_tasks", len(tasks))
    combined_metrics.increment("completed_tasks", sum(1 for t in tasks.values() if t.get("status") == "complete"))
    combined_metrics.increment("error_tasks", sum(1 for t in tasks.values() if t.get("status") == "error"))

    return {"status": "success", "metrics": combined_metrics.snapshot()}
