from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .api import router as api_router, tasks, _save_tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Cleanup stale and old tasks on startup."""
    import asyncio
    from . import api

    api.main_loop = asyncio.get_running_loop()

    modified = False
    now = datetime.now()
    cutoff = now - timedelta(hours=24)

    tasks_to_delete = []

    for task_id, task in tasks.items():
        # 1. Handle stale processing tasks
        if task.get("status") == "processing":
            task["status"] = "failed"
            task["error"] = "Task interrupted by server restart"
            modified = True

        # 2. Identify old tasks for pruning
        created_at_str = task.get("created_at")
        if created_at_str:
            try:
                created_at = datetime.fromisoformat(created_at_str)
                if created_at < cutoff:
                    tasks_to_delete.append(task_id)
            except (ValueError, TypeError):
                # If timestamp is invalid, we could either keep it or prune it.
                # Pruning invalid timestamps is safer for maintenance.
                tasks_to_delete.append(task_id)

    # 3. Perform pruning
    for task_id in tasks_to_delete:
        del tasks[task_id]
        modified = True

    if modified:
        _save_tasks()
    yield


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="digital_asset_harvester/web/static"), name="static")
templates = Jinja2Templates(directory="digital_asset_harvester/web/templates")

app.include_router(api_router, prefix="/api")


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/status/{task_id}")
async def status_page(request: Request, task_id: str):
    return templates.TemplateResponse(request, "status.html", {"task_id": task_id})


@app.get("/metrics")
async def metrics_page(request: Request):
    return templates.TemplateResponse(request, "metrics.html")


def run():
    """Run the Web UI server."""
    import uvicorn

    uvicorn.run("digital_asset_harvester.web.main:app", host="0.0.0.0", port=8000, reload=True)
