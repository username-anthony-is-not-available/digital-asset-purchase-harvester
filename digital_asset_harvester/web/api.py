import os
import logging
import shutil
import uuid
import csv
import json
import tempfile
import threading
import asyncio
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, Depends, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect
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
from ..utils.fx_rates import fx_service
from ..telemetry import MetricsTracker, StructuredLoggerFactory
from ..cli import process_emails, configure_logging
from ..utils.data_utils import normalize_for_frontend, denormalize_from_frontend
from ..exporters.koinly import KoinlyReportGenerator
from ..exporters.cryptotaxcalculator import CryptoTaxCalculatorReportGenerator
from ..exporters.cointracker import CoinTrackerReportGenerator
from ..exporters.cra import CRAReportGenerator, write_purchase_data_to_cra_pdf

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory store for task status and results
TASKS_DB = "tasks_db.json"
tasks = {}
tasks_lock = threading.Lock()


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, task_id: str, websocket: WebSocket):
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = []
        self.active_connections[task_id].append(websocket)

    def disconnect(self, task_id: str, websocket: WebSocket):
        if task_id in self.active_connections:
            if websocket in self.active_connections[task_id]:
                self.active_connections[task_id].remove(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]

    async def broadcast(self, task_id: str, message: dict):
        if task_id in self.active_connections:
            for connection in list(self.active_connections[task_id]):
                try:
                    await connection.send_json(message)
                except Exception:
                    if connection in self.active_connections[task_id]:
                        self.active_connections[task_id].remove(connection)


manager = ConnectionManager()
main_loop: Optional[asyncio.AbstractEventLoop] = None


def broadcast_sync(task_id: str, message: dict):
    """Thread-safe way to broadcast from synchronous background tasks."""
    global main_loop
    if main_loop is None:
        try:
            main_loop = asyncio.get_event_loop()
        except RuntimeError:
            return

    if main_loop and main_loop.is_running():
        main_loop.call_soon_threadsafe(lambda: asyncio.create_task(manager.broadcast(task_id, message)))


def _save_tasks():
    """Save tasks to a JSON file atomically."""
    with tasks_lock:
        try:
            # Use a temporary file for atomic write
            fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(TASKS_DB)) or ".", suffix=".tmp")
            try:
                with os.fdopen(fd, "w") as f:
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
    "email_subject",
    "vendor",
    "currency",
    "amount",
    "purchase_date",
    "transaction_id",
    "crypto_currency",
    "crypto_amount",
    "fiat_amount_base",
    "confidence_score",
]


def get_logger_factory():
    settings = get_settings()
    return configure_logging(settings)


def _create_progress_callback(task_id: str):
    def progress_callback(current: int, total: int):
        with tasks_lock:
            if task_id in tasks:
                tasks[task_id]["progress"] = {
                    "current": current,
                    "total": total,
                    "percentage": round((current / total) * 100, 2) if total > 0 else 0,
                }
                broadcast_sync(task_id, {"type": "progress", "data": tasks[task_id]["progress"]})

    return progress_callback


def _create_log_callback(task_id: str):
    def log_callback(message: str):
        with tasks_lock:
            if task_id in tasks:
                if "logs" not in tasks[task_id]:
                    tasks[task_id]["logs"] = []

                log_entry = {"timestamp": datetime.now().isoformat(), "message": message}
                tasks[task_id]["logs"].append(log_entry)

                # Keep only last 100 logs
                if len(tasks[task_id]["logs"]) > 100:
                    tasks[task_id]["logs"].pop(0)

                broadcast_sync(task_id, {"type": "log", "data": log_entry})

    return log_callback


def process_eml_files(task_id: str, temp_dir: str, logger_factory: StructuredLoggerFactory):
    """Processes a directory of eml files and stores the result."""
    with tasks_lock:
        tasks[task_id] = {
            "status": "processing",
            "result": None,
            "progress": {"current": 0, "total": 0, "percentage": 0},
            "logs": [],
            "created_at": datetime.now().isoformat(),
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

        purchases, _ = process_emails(
            emails,
            extractor,
            logger_factory,
            show_progress=False,
            progress_callback=_create_progress_callback(task_id),
            loading_callback=_create_progress_callback(task_id),
            log_callback=_create_log_callback(task_id),
        )

        # Initialize review status and map fields for frontend
        normalized_purchases = [normalize_for_frontend(p) for p in purchases]

        tasks[task_id]["status"] = "complete"
        tasks[task_id]["result"] = normalized_purchases
        tasks[task_id]["metrics"] = extractor.metrics.snapshot()
        broadcast_sync(task_id, {"type": "status", "data": "complete"})
        _save_tasks()
    except Exception as e:
        import traceback

        tasks[task_id].update({"status": "error", "error": str(e), "traceback": traceback.format_exc()})
        broadcast_sync(task_id, {"type": "status", "data": "error", "error": str(e)})
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
            "progress": {"current": 0, "total": 0, "percentage": 0},
            "logs": [],
            "created_at": datetime.now().isoformat(),
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

        purchases, _ = process_emails(
            emails,
            extractor,
            logger_factory,
            show_progress=False,
            progress_callback=_create_progress_callback(task_id),
            loading_callback=_create_progress_callback(task_id),
            log_callback=_create_log_callback(task_id),
        )

        # Initialize review status and map fields for frontend
        normalized_purchases = [normalize_for_frontend(p) for p in purchases]

        tasks[task_id]["status"] = "complete"
        tasks[task_id]["result"] = normalized_purchases
        tasks[task_id]["metrics"] = extractor.metrics.snapshot()
        broadcast_sync(task_id, {"type": "status", "data": "complete"})
        _save_tasks()
    except Exception as e:
        import traceback

        tasks[task_id].update({"status": "error", "error": str(e), "traceback": traceback.format_exc()})
        broadcast_sync(task_id, {"type": "status", "data": "error", "error": str(e)})
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
            "progress": {"current": 0, "total": 0, "percentage": 0},
            "logs": [],
            "created_at": datetime.now().isoformat(),
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
                broadcast_sync(task_id, {"type": "status", "data": "complete"})
                _save_tasks()
                return

            emails = list(
                imap_client.fetch_emails_by_uids(uids, settings.imap_folder, raw=settings.enable_multiprocessing)
            )
            purchases, _ = process_emails(
                emails,
                extractor,
                logger_factory,
                show_progress=False,
                progress_callback=_create_progress_callback(task_id),
                loading_callback=_create_progress_callback(task_id),
                log_callback=_create_log_callback(task_id),
            )

            if emails:
                max_uid = max(int(email["uid"]) for email in emails)
                sync_state.set_last_uid(settings.imap_server, settings.imap_user, settings.imap_folder, max_uid)

            normalized_purchases = [normalize_for_frontend(p) for p in purchases]
            tasks[task_id]["status"] = "complete"
            tasks[task_id]["result"] = normalized_purchases
            tasks[task_id]["metrics"] = extractor.metrics.snapshot()
            broadcast_sync(task_id, {"type": "status", "data": "complete"})
            _save_tasks()

    except Exception as e:
        import traceback

        tasks[task_id].update({"status": "error", "error": str(e), "traceback": traceback.format_exc()})
        broadcast_sync(task_id, {"type": "status", "data": "error", "error": str(e)})
        _save_tasks()


def process_gmail_sync(task_id: str, logger_factory: StructuredLoggerFactory):
    """Synchronizes emails from Gmail API and stores the result."""
    with tasks_lock:
        tasks[task_id] = {
            "status": "processing",
            "result": None,
            "progress": {"current": 0, "total": 0, "percentage": 0},
            "logs": [],
            "created_at": datetime.now().isoformat(),
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
        purchases, _ = process_emails(
            emails,
            extractor,
            logger_factory,
            show_progress=False,
            progress_callback=_create_progress_callback(task_id),
            loading_callback=_create_progress_callback(task_id),
            log_callback=_create_log_callback(task_id),
        )

        normalized_purchases = [normalize_for_frontend(p) for p in purchases]
        tasks[task_id]["status"] = "complete"
        tasks[task_id]["result"] = normalized_purchases
        tasks[task_id]["metrics"] = extractor.metrics.snapshot()
        broadcast_sync(task_id, {"type": "status", "data": "complete"})
        _save_tasks()
    except Exception as e:
        import traceback

        tasks[task_id].update({"status": "error", "error": str(e), "traceback": traceback.format_exc()})
        broadcast_sync(task_id, {"type": "status", "data": "error", "error": str(e)})
        _save_tasks()


def process_outlook_sync(task_id: str, client_id: str, authority: str, logger_factory: StructuredLoggerFactory):
    """Synchronizes emails from Outlook API and stores the result."""
    with tasks_lock:
        tasks[task_id] = {
            "status": "processing",
            "result": None,
            "progress": {"current": 0, "total": 0, "percentage": 0},
            "logs": [],
            "created_at": datetime.now().isoformat(),
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
        purchases, _ = process_emails(
            emails,
            extractor,
            logger_factory,
            show_progress=False,
            progress_callback=_create_progress_callback(task_id),
            loading_callback=_create_progress_callback(task_id),
            log_callback=_create_log_callback(task_id),
        )

        normalized_purchases = [normalize_for_frontend(p) for p in purchases]
        tasks[task_id]["status"] = "complete"
        tasks[task_id]["result"] = normalized_purchases
        tasks[task_id]["metrics"] = extractor.metrics.snapshot()
        broadcast_sync(task_id, {"type": "status", "data": "complete"})
        _save_tasks()
    except Exception as e:
        import traceback

        tasks[task_id].update({"status": "error", "error": str(e), "traceback": traceback.format_exc()})
        broadcast_sync(task_id, {"type": "status", "data": "error", "error": str(e)})
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


@router.get("/export/cointracker/{task_id}")
async def export_cointracker(task_id: str):
    task = tasks.get(task_id)
    if not task or task["status"] != "complete":
        raise HTTPException(status_code=404, detail="Task not found or not complete")

    results = task.get("result", [])
    denormalized_results = [denormalize_from_frontend(p) for p in results]

    generator = CoinTrackerReportGenerator()
    rows = generator.generate_csv_rows(denormalized_results)

    output = StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    else:
        headers = [
            "Date",
            "Received Quantity",
            "Received Currency",
            "Sent Quantity",
            "Sent Currency",
            "Fee Quantity",
            "Fee Currency",
            "Tag",
        ]
        writer = csv.writer(output)
        writer.writerow(headers)

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=cointracker_{task_id}.csv"},
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

    settings = get_settings()
    results = task.get("result", [])
    denormalized_results = [denormalize_from_frontend(p) for p in results]

    generator = CRAReportGenerator(base_fiat_currency=settings.base_fiat_currency)
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
            f"Sent Quantity ({settings.base_fiat_currency})",
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

    settings = get_settings()
    results = task.get("result", [])
    denormalized_results = [denormalize_from_frontend(p) for p in results]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        write_purchase_data_to_cra_pdf(denormalized_results, tmp.name, base_fiat_currency=settings.base_fiat_currency)
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
    logger_factory: StructuredLoggerFactory = Depends(get_logger_factory),
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
    background_tasks: BackgroundTasks, logger_factory: StructuredLoggerFactory = Depends(get_logger_factory)
):
    settings = get_settings()
    if not settings.enable_imap:
        raise HTTPException(status_code=400, detail="IMAP is not enabled in settings")

    task_id = str(uuid.uuid4())
    background_tasks.add_task(process_imap_sync, task_id, logger_factory)

    return RedirectResponse(url=f"/status/{task_id}", status_code=303)


@router.post("/sync/gmail")
async def sync_gmail(
    background_tasks: BackgroundTasks, logger_factory: StructuredLoggerFactory = Depends(get_logger_factory)
):
    task_id = str(uuid.uuid4())
    background_tasks.add_task(process_gmail_sync, task_id, logger_factory)

    return RedirectResponse(url=f"/status/{task_id}", status_code=303)


@router.post("/sync/outlook")
async def sync_outlook(
    background_tasks: BackgroundTasks, logger_factory: StructuredLoggerFactory = Depends(get_logger_factory)
):
    settings = get_settings()
    # Support both new and legacy setting names
    client_id = settings.outlook_client_id or settings.imap_client_id
    authority = settings.outlook_authority or settings.imap_authority

    if not client_id or not authority:
        raise HTTPException(
            status_code=400, detail="Outlook API requires outlook_client_id and outlook_authority in settings"
        )

    task_id = str(uuid.uuid4())
    background_tasks.add_task(process_outlook_sync, task_id, client_id, authority, logger_factory)

    return RedirectResponse(url=f"/status/{task_id}", status_code=303)


@router.get("/status/{task_id}")
async def get_status(task_id: str):
    return tasks.get(task_id, {"status": "not_found"})


@router.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await manager.connect(task_id, websocket)
    try:
        # Send initial state
        with tasks_lock:
            if task_id in tasks:
                await websocket.send_json(
                    {
                        "type": "init",
                        "data": {
                            "progress": tasks[task_id].get("progress"),
                            "logs": tasks[task_id].get("logs", []),
                            "status": tasks[task_id].get("status"),
                        },
                    }
                )

        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(task_id, websocket)
    except Exception:
        manager.disconnect(task_id, websocket)


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

    settings = get_settings()
    # Check if crypto_currency changed and we need to update asset_id
    from ..utils.asset_mapping import mapper

    old_currency = results[index].get("crypto_currency")
    new_currency = updated_record.get("crypto_currency")

    # Fields that might trigger a fiat recalculation
    old_total_spent = results[index].get("total_spent")
    new_total_spent = updated_record.get("total_spent")
    old_fiat_currency = results[index].get("currency")
    new_fiat_currency = updated_record.get("currency")
    old_date = results[index].get("purchase_date")
    new_date = updated_record.get("purchase_date")

    results[index].update(updated_record)

    # 1. Update Asset ID if crypto currency changed
    if new_currency and new_currency != old_currency:
        # Only auto-update asset_id if it wasn't explicitly provided/changed to something non-empty
        if not updated_record.get("asset_id"):
            asset_id = mapper.get_asset_id(new_currency)
            if asset_id:
                results[index]["asset_id"] = asset_id

    # 2. Recalculate base fiat if enabled and relevant fields changed
    if settings.enable_currency_conversion:
        # Check if any field involved in the calculation changed
        # We use 'in' check for updated_record to see if it was part of the update
        fiat_changed = (
            "total_spent" in updated_record or "currency" in updated_record or "purchase_date" in updated_record
        )

        # Only recalculate if it wasn't manually overridden in this update
        if fiat_changed and "fiat_amount_base" not in updated_record:
            try:
                from_curr = results[index].get("currency")
                to_curr = settings.base_fiat_currency
                p_date = results[index].get("purchase_date", "")
                spent = results[index].get("total_spent")

                if spent is not None:
                    rate = fx_service.get_rate(p_date, from_curr, to_curr)
                    if rate:
                        from decimal import Decimal

                        base_amount = Decimal(str(spent)) * rate
                        results[index]["fiat_amount_base"] = float(base_amount)
            except Exception as e:
                logger.warning(f"Failed to auto-recalculate fiat_amount_base: {e}")

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
        "review_status": "pending",
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


@router.get("/system-info")
async def get_system_info():
    """Return sanitized application settings."""
    settings = get_settings()
    from dataclasses import asdict

    settings_dict = asdict(settings)

    # Sanitize sensitive fields
    sensitive_keywords = ["key", "password", "secret", "token", "auth"]
    sanitized = {}
    for k, v in settings_dict.items():
        if any(kw in k.lower() for kw in sensitive_keywords):
            sanitized[k] = "********" if v else ""
        else:
            sanitized[k] = v

    return {"status": "success", "settings": sanitized}


@router.get("/metrics")
async def get_metrics():
    """Aggregate metrics from all completed tasks."""
    combined_metrics = MetricsTracker()
    total_confidence = 0.0
    confidence_count = 0

    for task_id, task in tasks.items():
        if task.get("status") == "complete":
            # 1. Aggregate counters
            if "metrics" in task:
                task_metrics = task["metrics"]
                for key, value in task_metrics.items():
                    if isinstance(value, (int, float)) and not key.endswith("_latency"):
                        combined_metrics.increment(key, int(value))

            # 2. Aggregate confidence from records
            for record in task.get("result", []):
                conf = record.get("confidence")
                if conf is not None and record.get("review_status") != "rejected":
                    total_confidence += float(conf)
                    confidence_count += 1

    # Calculate average confidence across all valid records
    if confidence_count > 0:
        combined_metrics.set_metadata("avg_confidence", total_confidence / confidence_count)

    # Add task summary metrics
    combined_metrics.set_metadata("total_tasks", len(tasks))
    combined_metrics.increment("completed_tasks", sum(1 for t in tasks.values() if t.get("status") == "complete"))
    combined_metrics.increment("error_tasks", sum(1 for t in tasks.values() if t.get("status") == "error"))

    return {"status": "success", "metrics": combined_metrics.snapshot()}
