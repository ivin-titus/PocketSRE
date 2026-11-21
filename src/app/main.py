from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.actions.service import ActionService
from app.actions.ssh_executor import SshExecutor, SshNotConfiguredError
from app.ai.factory import build_llm_router
from app.ai.knowledge import load_infra_context
from app.api.console import router as console_router
from app.api.routes import router
from app.config import get_settings
from app.incidents.alerts import AlertBridge
from app.incidents.poller import PresencePoller
from app.incidents.presence import PresenceProbe
from app.incidents.service import IncidentService
from app.shared.audit import AuditLog
from app.shared.budget import BudgetGovernor
from app.shared.rbac import parse_role_permissions
from app.storage.db import Database
from app.swe.tracker import IssueTracker
from app.bot.discord_runtime import run_discord_bot, stop_task


async def db_keepalive(db: Database) -> None:
    """Neon suspends idle computes; ping periodically to keep it warm."""
    while True:
        await asyncio.sleep(240)
        try:
            await asyncio.to_thread(db.keepalive)
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    db: Database | None = None
    if settings.neon_database_url:
        try:
            db = await asyncio.to_thread(Database, settings.neon_database_url)
        except Exception:
            db = None  # DB optional: in-memory fallback keeps the app alive
    app.state.db = db
    app.state.budget = BudgetGovernor(db, settings)
    app.state.audit_log = AuditLog(db=db)
    app.state.incidents = IncidentService(db=db)
    app.state.keepalive_task = (
        asyncio.create_task(db_keepalive(db), name="pocketsre-db-keepalive")
        if db is not None
        else None
    )
    try:
        executor = SshExecutor.from_settings(settings)
    except SshNotConfiguredError:
        executor = None
    app.state.llm = build_llm_router(settings)
    app.state.probe = PresenceProbe(settings.presence_base_url)
    app.state.actions = ActionService(
        app.state.audit_log,
        executor,
        app.state.probe,
        max_trials=settings.max_trials_per_incident,
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
                role_permissions=parse_role_permissions(settings.role_permissions),
                llm_router=app.state.llm,
                context_provider=lambda: load_infra_context(db=app.state.db),
                budget=app.state.budget,
                devin_session_cost_usd=settings.devin_session_cost_estimate_usd,
                llm_call_cost_usd=settings.llm_call_cost_estimate_usd,
                tracker=IssueTracker(
                    settings.linear_api_key,
                    settings.linear_team_id,
                    settings.github_pat,
                    settings.github_repo,
                ),
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
        await stop_task(app.state.keepalive_task)



app = FastAPI(title="PocketSRE", version="0.1.0", lifespan=lifespan)
app.include_router(router)
app.include_router(console_router)

web_dist = get_settings().web_dist_path
if web_dist.is_dir():
    app.mount("/console", StaticFiles(directory=web_dist, html=True), name="console")


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "pocketsre", "console": "/console"}
