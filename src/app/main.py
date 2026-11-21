from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.actions.service import ActionService
from app.actions.ssh_executor import SshExecutor, SshNotConfiguredError
from app.api.routes import router
from app.config import get_settings
from app.incidents.alerts import AlertBridge
from app.incidents.poller import PresencePoller
from app.incidents.presence import PresenceProbe
from app.incidents.service import IncidentService
from app.shared.audit import AuditLog
from app.bot.discord_runtime import run_discord_bot, stop_task


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.audit_log = AuditLog()
    app.state.incidents = IncidentService()
    settings = get_settings()
    try:
        executor = SshExecutor.from_settings(settings)
    except SshNotConfiguredError:
        executor = None
    app.state.actions = ActionService(
        app.state.audit_log,
        executor,
        PresenceProbe(settings.presence_base_url),
    )

    # Presence Poller for Proactive Target Health
    endpoints = [ep.strip() for ep in settings.presence_endpoints.split(",") if ep.strip()]
    app.state.alerts = AlertBridge()
    app.state.poller = PresencePoller(
        base_url=settings.presence_base_url,
        endpoints=endpoints,
        incidents=app.state.incidents,
        interval_seconds=15.0,
        alerts=app.state.alerts,
    )
    app.state.poller_task = asyncio.create_task(app.state.poller.run(), name="pocketsre-presence-poller")

    # Discord Gateway Bot Task
    app.state.discord_task = None
    if settings.discord_token:
        app.state.discord_task = asyncio.create_task(
            run_discord_bot(
                settings.discord_token,
                app.state.incidents,
                app.state.actions,
                alert_channel_id=settings.discord_alert_channel_id,
                alerts=app.state.alerts,
                public_base_url=settings.public_base_url,
                magic_link_secret=settings.magic_link_secret,
                autonomy_mode=settings.autonomy_mode,
                devin_api_key=settings.devin_api_key,
            ),
            name="pocketsre-discord",
        )
    try:
        yield
    finally:
        if hasattr(app.state, "poller") and app.state.poller:
            app.state.poller.stop()
        await stop_task(app.state.poller_task)
        await stop_task(app.state.discord_task)



app = FastAPI(title="PocketSRE", version="0.1.0", lifespan=lifespan)
app.include_router(router)

web_dist = get_settings().web_dist_path
if web_dist.is_dir():
    app.mount("/console", StaticFiles(directory=web_dist, html=True), name="console")


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "pocketsre", "console": "/console"}
