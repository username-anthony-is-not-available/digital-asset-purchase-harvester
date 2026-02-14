from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .api import router as api_router
from .api import tasks

app = FastAPI()

app.mount("/static", StaticFiles(directory="digital_asset_harvester/web/static"), name="static")
templates = Jinja2Templates(directory="digital_asset_harvester/web/templates")

app.include_router(api_router, prefix="/api")


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/status/{task_id}")
async def status_page(request: Request, task_id: str):
    return templates.TemplateResponse(request, "status.html", {"task_id": task_id})


def run():
    """Run the Web UI server."""
    import uvicorn

    uvicorn.run("digital_asset_harvester.web.main:app", host="0.0.0.0", port=8000, reload=True)
