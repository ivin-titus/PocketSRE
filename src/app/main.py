from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.actions.service import ActionService
from app.api.routes import router
from app.config import get_settings
from app.incidents.service import IncidentService
from app.shared.audit import AuditLog
from app.bot.discord_runtime import run_discord_bot, stop_task


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.audit_log = AuditLog()
    app.state.incidents = IncidentService()
    app.state.actions = ActionService(app.state.audit_log)
    settings = get_settings()
    app.state.discord_task = None
    if settings.discord_token:
        app.state.discord_task = asyncio.create_task(
            run_discord_bot(settings.discord_token, app.state.incidents, app.state.actions),
            name="pocketsre-discord",
        )
    try:
        yield
    finally:
        await stop_task(app.state.discord_task)


app = FastAPI(title="PocketSRE", version="0.1.0", lifespan=lifespan)
app.include_router(router)

web_dist = get_settings().web_dist_path
if web_dist.is_dir():
    app.mount("/console", StaticFiles(directory=web_dist, html=True), name="console")


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "pocketsre", "console": "/console"}
