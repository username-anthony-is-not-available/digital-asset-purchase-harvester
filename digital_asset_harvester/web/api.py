import os
import shutil
import uuid
import csv
import json
import tempfile
from fastapi import APIRouter, File, UploadFile, Depends, BackgroundTasks, HTTPException
from fastapi.responses import RedirectResponse, StreamingResponse
from io import StringIO
from .. import (
    EmailPurchaseExtractor,
    MboxDataExtractor,
    get_llm_client,
    get_settings,
)
from ..ingest.imap_client import ImapClient
from ..utils.sync_state import SyncState
from ..telemetry import StructuredLoggerFactory
from ..cli import process_emails, configure_logging
from ..utils.data_utils import normalize_for_frontend, denormalize_from_frontend
from ..exporters.koinly import KoinlyReportGenerator
from ..exporters.cryptotaxcalculator import CryptoTaxCalculatorReportGenerator
from ..exporters.cra import CRAReportGenerator, write_purchase_data_to_cra_pdf

router = APIRouter()

# In-memory store for task status and results
tasks = {}

DEFAULT_CSV_HEADERS = [
    "email_subject",
    "vendor",
    "currency",
    "amount",
    "purchase_date",
    "transaction_id",
    "crypto_currency",
    "crypto_amount",
    "confidence_score",
]


def get_logger_factory():
    settings = get_settings()
    return configure_logging(settings)


def process_mbox_file(task_id: str, temp_path: str, logger_factory: StructuredLoggerFactory):
    """Processes the mbox file and stores the result."""
    tasks[task_id] = {"status": "processing", "result": None}

    settings = get_settings()
    llm_client = get_llm_client()
    extractor = EmailPurchaseExtractor(
        settings=settings,
        llm_client=llm_client,
        logger_factory=logger_factory,
    )

    mbox_reader = MboxDataExtractor(temp_path)
    emails = mbox_reader.extract_emails()

    purchases, _ = process_emails(emails, extractor, logger_factory, show_progress=False)

    # Initialize review status and map fields for frontend
    normalized_purchases = [normalize_for_frontend(p) for p in purchases]

    tasks[task_id]["status"] = "complete"
    tasks[task_id]["result"] = normalized_purchases


def process_imap_sync(task_id: str, logger_factory: StructuredLoggerFactory):
    """Synchronizes emails from IMAP and stores the result."""
    tasks[task_id] = {"status": "processing", "result": None}
    settings = get_settings()

    if not settings.enable_imap:
        tasks[task_id] = {"status": "error", "error": "IMAP is not enabled in settings"}
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
                tasks[task_id] = {"status": "complete", "result": []}
                return

            emails = list(imap_client.fetch_emails_by_uids(uids, settings.imap_folder))
            purchases, _ = process_emails(emails, extractor, logger_factory, show_progress=False)

            if emails:
                max_uid = max(int(email["uid"]) for email in emails)
                sync_state.set_last_uid(settings.imap_server, settings.imap_user, settings.imap_folder, max_uid)

            normalized_purchases = [normalize_for_frontend(p) for p in purchases]
            tasks[task_id]["status"] = "complete"
            tasks[task_id]["result"] = normalized_purchases

    except Exception as e:
        tasks[task_id] = {"status": "error", "error": str(e)}


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
            "Date",
            "Sent Amount",
            "Sent Currency",
            "Received Amount",
            "Received Currency",
            "Fee Amount",
            "Fee Currency",
            "Net Worth Amount",
            "Net Worth Currency",
            "Label",
            "Description",
            "TxHash",
        ]
        writer = csv.writer(output)
        writer.writerow(headers)

    output.seek(0)
    return StreamingResponse(
        output, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=koinly_{task_id}.csv"}
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
            "Timestamp (UTC)",
            "Type",
            "Base Currency",
            "Base Amount",
            "Quote Currency",
            "Quote Amount",
            "Fee Currency",
            "Fee Amount",
            "From",
            "To",
            "ID",
            "Description",
        ]
        writer = csv.writer(output)
        writer.writerow(headers)

    output.seek(0)
    return StreamingResponse(
        output, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=ctc_{task_id}.csv"}
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
            "Date",
            "Type",
            "Received Quantity",
            "Received Currency",
            "Sent Quantity",
            "Sent Currency",
            "Fee Quantity",
            "Fee Currency",
            "Description",
        ]
        writer = csv.writer(output)
        writer.writerow(headers)

    output.seek(0)
    return StreamingResponse(
        output, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=cra_{task_id}.csv"}
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
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    logger_factory: StructuredLoggerFactory = Depends(get_logger_factory),
):
    task_id = str(uuid.uuid4())

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mbox") as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_path = temp_file.name

    background_tasks.add_task(process_mbox_file, task_id, temp_path, logger_factory)

    return RedirectResponse(url=f"/status/{task_id}", status_code=303)


@router.post("/sync/imap")
async def sync_imap(
    background_tasks: BackgroundTasks, logger_factory: StructuredLoggerFactory = Depends(get_logger_factory)
):
    settings = get_settings()
    if not settings.enable_imap:
        raise HTTPException(status_code=400, detail="IMAP is not enabled in settings")

    task_id = str(uuid.uuid4())
    background_tasks.add_task(process_imap_sync, task_id, logger_factory)

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

    return StreamingResponse(
        output, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=purchases_{task_id}.csv"}
    )


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

    results[index].update(updated_record)
    # Reset review status on manual edit
    results[index]["review_status"] = "pending"
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

    return {"status": "success", "approved_indices": updated_indices}
