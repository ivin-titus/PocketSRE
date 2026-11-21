"""Discord runtime adapted from Yuki's lifecycle and command-handler split."""

import asyncio
import contextlib
import time
from collections.abc import Callable

from app.actions.service import ActionService, EscalationRequiredError
from app.incidents.alerts import AlertBridge, AlertEvent
from app.incidents.presence import ROUTE_CONTAINER_DEFAULTS
from app.incidents.service import IncidentService
from app.swe.dispatch import DevinDispatcher
from app.swe.tracker import IssueTracker
from app.shared.contracts import (
    ActionRequest,
    ActionResult,
    ActorRole,
    Incident,
    IncidentCreate,
    IncidentSeverity,
    RunbookAction,
)
from app.ai.router import LLMRouter
from app.ai.triage import classify_message
from app.shared.budget import BudgetExhaustedError, BudgetGovernor
from app.shared.magic_link import make_console_link
from app.shared.rbac import actor_role_for

DISCORD_FIELD_LIMIT = 1000


def member_role_names(member: object) -> list[str]:
    """Roles of an interaction user; empty outside guilds (DMs get VIEWER)."""
    roles = getattr(member, "roles", None) or []
    return [getattr(role, "name", "") for role in roles]


def truncate(text: str, limit: int = DISCORD_FIELD_LIMIT) -> str:
    return text if len(text) <= limit else text[: limit - 3] + "..."


def alert_embed(incident: Incident, console_url: str | None, autonomy_mode: str = "strict_confirmation"):
    """Card proposing the allowed next steps for a proactive/reactive alert."""
    import discord

    embed = discord.Embed(
        title=f"🚨 {incident.severity.value} — {incident.service}",
        description=truncate(incident.summary, 500),
        color=discord.Color.red(),
    )
    embed.add_field(name="Incident", value=f"`{incident.id}`", inline=True)
    embed.add_field(name="Source", value=incident.source, inline=True)
    embed.add_field(name="Mode", value=f"`{autonomy_mode}`", inline=True)
    embed.add_field(
        name="Allowed next steps",
        value="`Fetch logs` / `Inspect` run free · `Restart` needs a lead · `Dispatch Devin` for code fixes",
        inline=False,
    )
    if console_url:
        embed.add_field(name="Console", value=console_url, inline=False)
    return embed


def report_embed(result: ActionResult):
    """Concise post-execution report."""
    import discord

    ok = result.status in ("succeeded", "verified")
    embed = discord.Embed(
        title=f"{result.action.value} → {result.service}",
        description=f"**Status:** `{result.status}`",
        color=discord.Color.green() if ok else discord.Color.orange(),
    )
    if result.output.strip():
        embed.add_field(name="Output", value=f"```{truncate(result.output, 900)}```", inline=False)
    return embed


def resolution_embed(incident: Incident):
    import discord

    embed = discord.Embed(
        title=f"✅ Resolved — {incident.service}",
        description=truncate(incident.summary, 500),
        color=discord.Color.green(),
    )
    embed.add_field(name="Incident", value=f"`{incident.id}`", inline=True)
    return embed


def dossier_embed(dossier: dict, reason: str):
    """Break-glass escalation: what happened / tried / halted / next steps."""
    import discord

    tried = "\n".join(
        f"- `{t['action']}` → {t['status']}" for t in dossier.get("what_was_tried", [])
    ) or "none"
    embed = discord.Embed(
        title="🛑 Escalation — PocketSRE out of depth",
        description=f"**{truncate(reason, 300)}**",
        color=discord.Color.dark_red(),
    )
    embed.add_field(
        name="What happened", value=truncate(str(dossier.get("what_happened", "")), 400), inline=False
    )
    embed.add_field(name="What was tried", value=truncate(tried, 600), inline=False)
    embed.add_field(
        name="Current health",
        value=truncate("; ".join(dossier.get("current_health", [])), 400),
        inline=False,
    )
    embed.add_field(
        name="Recommended next steps",
        value=truncate("\n".join(f"- {s}" for s in dossier.get("next_steps", [])), 700),
        inline=False,
    )
    embed.add_field(
        name="Autonomy budget",
        value=f"`{dossier.get('trials_used')}/{dossier.get('max_trials')}` mutating trials used",
        inline=True,
    )
    return embed


def make_bot(
    incidents: IncidentService,
    actions: ActionService,
    alert_channel_id: int | None = None,
    alerts: AlertBridge | None = None,
    public_base_url: str = "",
    magic_link_secret: str = "",
    autonomy_mode: str = "strict_confirmation",
    devin_api_key: str | None = None,
    role_permissions: dict[str, ActorRole] | None = None,
    llm_router: LLMRouter | None = None,
    context_provider: Callable[[], str] | None = None,
    budget: BudgetGovernor | None = None,
    devin_session_cost_usd: float = 1.00,
    llm_call_cost_usd: float = 0.00,
    tracker: IssueTracker | None = None,
    pr_watch_interval_seconds: float = 300.0,
    pr_watch_timeout_minutes: float = 720.0,
):
    """Create the Discord adapter lazily so HTTP-only development needs no bot token."""
    import discord
    from discord import app_commands
    from discord.ext import commands

    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="/", intents=intents)

    dispatcher = DevinDispatcher(devin_api_key)
    pr_watches: list[dict] = []  # {incident, session_id, channel, pr_url, dispatched_at, reminded}

    def console_url(incident: Incident, actor_id: str) -> str | None:
        if not (public_base_url and magic_link_secret):
            return None
        return make_console_link(public_base_url, incident.id, actor_id, magic_link_secret)

    async def run_action(
        channel: discord.abc.Messageable,
        incident: Incident,
        action: RunbookAction,
        actor_id: str,
        role: ActorRole,
        approved: bool,
    ) -> ActionResult | None:
        request = ActionRequest(
            incident_id=incident.id,
            action=action,
            service=incident.service,
            actor_id=actor_id,
            actor_role=role,
            approved=approved,
        )
        try:
            result = await asyncio.to_thread(actions.execute, request)
        except EscalationRequiredError as exc:
            await channel.send(embed=dossier_embed(exc.dossier, str(exc)))
            return None
        except PermissionError as exc:
            await channel.send(f"⛔ `{action.value}` denied: {exc}")
            return None
        except Exception as exc:
            await channel.send(f"⚠️ `{action.value}` failed to run: {exc}")
            return None
        await channel.send(embed=report_embed(result))
        return result


    async def status_embed():
        """Live presence snapshot + open incidents + spend placeholder."""
        lines: list[str] = []
        if actions.presence is not None:
            for route, container in ROUTE_CONTAINER_DEFAULTS.items():
                reasons = await asyncio.to_thread(actions.presence.health_reasons, container)
                if reasons is None:
                    mark = "❔ no coverage"
                elif reasons:
                    mark = "⚠️ " + "; ".join(reasons)
                else:
                    mark = "✅"
                lines.append(f"**{route}** ({container}): {mark}")
        open_incidents = [
            i for i in incidents.list_all() if i.status.value in ("open", "triaged")
        ]
        embed = discord.Embed(
            title="PocketSRE — live presence",
            description="\n".join(lines) or "Presence probe not configured.",
            color=discord.Color.blue(),
        )
        embed.add_field(name="Open incidents", value=str(len(open_incidents)), inline=True)
        embed.add_field(name="Mode", value=f"`{autonomy_mode}`", inline=True)
        return embed

    async def _approve_text_path(message: discord.Message) -> None:
        """`@PocketSRE approve <incident-id>` — text approval for the restart runbook."""
        words = message.content.split()
        candidates = [
            i
            for i in incidents.list_all()
            if i.status.value in ("open", "triaged")
            and (len(words) < 3 or str(i.id).startswith(words[-1]))
        ]
        if len(candidates) > 1:
            await message.channel.send(
                f"⚠️ {len(candidates)} active incidents — pass an incident id prefix: "
                + ", ".join(f"`{str(i.id)[:8]}` ({i.service})" for i in candidates)
            )
            return
        incident = candidates[0] if candidates else None
        if incident is None:
            await message.channel.send("No active incident matched — pass an incident id prefix.")
            return
        role = actor_role_for(member_role_names(message.author), role_permissions)
        await run_action(
            message.channel,
            incident,
            RunbookAction.RESTART_SERVICE,
            str(message.author.id),
            role,
            approved=True,
        )

    class IncidentApprovalView(discord.ui.View):
        def __init__(self, incident: Incident) -> None:
            super().__init__(timeout=600)
            self.incident = incident

        async def _dispatch(
            self,
            interaction: discord.Interaction,
            action: RunbookAction,
            approved: bool,
        ) -> None:
            role = actor_role_for(member_role_names(interaction.user), role_permissions)
            await interaction.response.defer()
            await run_action(
                interaction.channel, self.incident, action, str(interaction.user.id), role, approved
            )

        @discord.ui.button(label="Fetch logs", style=discord.ButtonStyle.secondary)
        async def fetch_logs(self, interaction: discord.Interaction, _button) -> None:
            await self._dispatch(interaction, RunbookAction.FETCH_SERVICE_LOGS, approved=True)

        @discord.ui.button(label="Inspect", style=discord.ButtonStyle.secondary)
        async def inspect(self, interaction: discord.Interaction, _button) -> None:
            await self._dispatch(interaction, RunbookAction.INSPECT_SERVICE, approved=True)

        @discord.ui.button(label="Approve & Restart", style=discord.ButtonStyle.danger)
        async def restart(self, interaction: discord.Interaction, _button) -> None:
            await self._dispatch(interaction, RunbookAction.RESTART_SERVICE, approved=True)

        @discord.ui.button(label="Dispatch Devin fix", style=discord.ButtonStyle.primary)
        async def dispatch_devin(self, interaction: discord.Interaction, _button) -> None:
            role = actor_role_for(member_role_names(interaction.user), role_permissions)
            if role is not ActorRole.LEAD:
                await interaction.response.send_message(
                    "⛔ Dispatching Devin requires a lead role.", ephemeral=True
                )
                return
            await interaction.response.defer()
            if any(w["incident"].id == self.incident.id for w in pr_watches):
                await interaction.channel.send(
                    f"🤖 Devin already dispatched for `{self.incident.id}` — watching its PR."
                )
                return
            if budget is not None:
                try:
                    budget.check("devin", self.incident.id)
                except BudgetExhaustedError as exc:
                    await interaction.channel.send(f"💸 Devin dispatch blocked: {exc}")
                    return
            note = await asyncio.to_thread(dispatcher.dispatch, self.incident)
            await interaction.channel.send(note)
            if budget is not None:
                budget.record("devin", devin_session_cost_usd, self.incident.id)
            if dispatcher._last_session_id:
                pr_watches.append(
                    {
                        "incident": self.incident,
                        "session_id": dispatcher._last_session_id,
                        "channel": interaction.channel,
                        "pr_url": None,
                        "dispatched_at": time.monotonic(),
                        "reminded": False,
                    }
                )
                dispatcher._last_session_id = None
            if tracker is not None:
                refs = await asyncio.to_thread(
                    tracker.create_issue,
                    self.incident,
                    self.incident.summary + "\n\n" + note,
                    True,  # Devin dispatch implies a code-level incident
                )
                links = [
                    f"Linear: {refs['linear_url']}" if refs.get("linear_url") else None,
                    f"GitHub: {refs['github_url']}" if refs.get("github_url") else None,
                ]
                errors = [
                    f"Linear failed: {refs['linear_error']}" if refs.get("linear_error") else None,
                    f"GitHub failed: {refs['github_error']}" if refs.get("github_error") else None,
                ]
                body = "\n".join([p for p in links + errors if p]) or "No trackers configured"
                await interaction.channel.send(f"📋 Tracked — {body}")

        @discord.ui.button(label="Deny", style=discord.ButtonStyle.secondary)
        async def deny(self, interaction: discord.Interaction, button) -> None:
            await interaction.response.send_message("Denied — no action taken.", ephemeral=True)
            button.disabled = True

    async def alert_consumer() -> None:
        """Proactive loop: detection event → card → optional auto-run → report → summary."""
        await bot.wait_until_ready()
        channel = bot.get_channel(alert_channel_id) if alert_channel_id else None
        if channel is None:
            return
        while True:
            event: AlertEvent = await alerts.next()
            incident = event.incident
            if event.kind == "opened":
                await channel.send(
                    embed=alert_embed(incident, console_url(incident, "lead"), autonomy_mode),
                    view=IncidentApprovalView(incident),
                )
                if autonomy_mode in ("read_auto", "full_autonomy"):
                    # READ_AUTO: diagnostics run without asking, announce post-facto.
                    await channel.send(
                        "🔍 Read-auto mode: running diagnostics (logs + inspect) now."
                    )
                    for diag in (RunbookAction.FETCH_SERVICE_LOGS, RunbookAction.INSPECT_SERVICE):
                        await run_action(
                            channel,
                            incident,
                            diag,
                            actor_id="pocketsre-autonomy",
                            role=ActorRole.LEAD,
                            approved=True,
                        )
                if autonomy_mode == "full_autonomy":
                    await channel.send("🤖 Full-autonomy mode: executing restart now.")
                    await run_action(
                        channel,
                        incident,
                        RunbookAction.RESTART_SERVICE,
                        actor_id="pocketsre-autonomy",
                        role=ActorRole.LEAD,
                        approved=True,
                    )
            elif event.kind == "resolved":
                await channel.send(embed=resolution_embed(incident))

    async def pr_watch_consumer() -> None:
        """Follow-up loop: poll Devin session → PR appears → poll GitHub merge state →
        post transparency updates; re-ping lead on stale PRs; resolve incident on merge."""
        await bot.wait_until_ready()

        while True:
            await asyncio.sleep(pr_watch_interval_seconds)
            for watch in list(pr_watches):
                channel = watch["channel"]
                incident = watch["incident"]
                try:
                    if watch["pr_url"] is None:
                        prs = await asyncio.to_thread(
                            dispatcher.session_pull_requests, watch["session_id"]
                        )
                        if prs:
                            watch["pr_url"] = prs[0]
                            if tracker is not None:
                                await asyncio.to_thread(
                                    tracker.link_pr, incident, watch["pr_url"]
                                )
                            await channel.send(
                                f"🔧 Devin opened a fix PR for `{incident.id}`: {watch['pr_url']}\n"
                                "Watching for merge — a human SWE reviews + merges it."
                            )
                        continue
                    if tracker is None:
                        continue  # can announce the PR but cannot poll merge state
                    status = await asyncio.to_thread(tracker.pr_status, watch["pr_url"])
                    if status is None:
                        continue
                    if status.get("merged"):
                        by = status.get("merged_by") or "a SWE"
                        await channel.send(
                            f"✅ PR merged by **{by}** for `{incident.id}` — re-checking service health."
                        )
                        reasons = None
                        if actions.presence is not None:
                            reasons = await asyncio.to_thread(
                                actions.presence.health_reasons, incident.service
                            )
                        if reasons:
                            await channel.send(
                                f"⚠️ Still unhealthy after merge: {'; '.join(reasons)} — incident stays open."
                            )
                        else:
                            incidents.resolve(incident.id)
                            await channel.send(embed=resolution_embed(incident))
                        pr_watches.remove(watch)
                    elif status.get("state") == "closed":
                        await channel.send(
                            f"❌ PR {watch['pr_url']} closed without merge for `{incident.id}` — "
                            "escalate or re-dispatch."
                        )
                        pr_watches.remove(watch)
                    else:
                        age_min = (time.monotonic() - watch["dispatched_at"]) / 60
                        if age_min > pr_watch_timeout_minutes and not watch["reminded"]:
                            watch["reminded"] = True
                            await channel.send(
                                f"⏰ PR {watch['pr_url']} for `{incident.id}` still unmerged after "
                                f"{int(age_min)} min — a lead should review it."
                            )
                except Exception:
                    continue  # transient API/Discord failures never kill the watcher

    @bot.event
    async def on_ready() -> None:
        await bot.tree.sync()
        if alerts is not None:
            bot.loop.create_task(alert_consumer(), name="pocketsre-alert-consumer")
        bot.loop.create_task(pr_watch_consumer(), name="pocketsre-pr-watch")

    @bot.event
    async def on_message(message: discord.Message) -> None:
        if message.author == bot.user:
            return

        if getattr(message.author, "bot", False):
            return  # other bots are never humans

        is_webhook = message.webhook_id is not None
        if is_webhook:
            content = message.content or ""
            for embed in message.embeds:
                if embed.title:
                    content += f" {embed.title}"
                if embed.description:
                    content += f" {embed.description}"

            lowered_content = content.lower()
            # Gate ingestion: only real alert payloads (a Yuki container name or
            # alert keywords + a known service) may open an incident — CI posts,
            # git webhook noise and arbitrary messages are ignored.
            named_containers = [
                c
                for c in (
                    "yuki-core-api",
                    "yuki-discord-bot",
                    "yuki-telegram-bot",
                    "yuki-horiz-client",
                    "yuki-redis",
                )
                if c in lowered_content or c.replace("yuki-", "") in lowered_content
            ]
            alert_keywords = ("crash", "down", "error", "alert", "incident", "oom", "500", "unhealthy", "restart")
            if not named_containers or not any(k in lowered_content for k in alert_keywords):
                await bot.process_commands(message)
                return

            detected_container = named_containers[0]

            active = incidents.get_active_for_service(detected_container)
            if not active:
                incident = incidents.create(
                    IncidentCreate(
                        source="discord_webhook",
                        service=detected_container,
                        summary=content[:500] or "Alert detected from Discord webhook",
                        severity=(
                            IncidentSeverity.P1
                            if "crash" in content.lower() or "oom" in content.lower()
                            else IncidentSeverity.P2
                        ),
                    )
                )
                if alerts:
                    alerts.emit("opened", incident)
                else:
                    await message.channel.send(
                        f"🚨 **PocketSRE Alert Ingested**: Incident `{incident.id}` opened for `{incident.service}`. Initiating triage..."
                    )
            await bot.process_commands(message)
            return

        # Reactive path: a human pings the bot or reports an issue. Guilds only —
        # DMs have no roles, so anything mutating would map to VIEWER anyway.
        if message.guild is None:
            return
        if bot.user in message.mentions:
            lowered = message.content.lower()
            if "approve" in lowered:
                await _approve_text_path(message)
                return

            # LLM classification first; keywords are the deterministic fallback.
            infra_ctx = context_provider() if context_provider else ""
            if budget is not None and llm_router is not None:
                try:
                    budget.check("llm")
                except BudgetExhaustedError as exc:
                    await message.channel.send(f"💸 LLM budget exhausted: {exc}")
                    return
            classified = await classify_message(
                llm_router, message.content, infra_context=infra_ctx
            )
            if classified is not None and budget is not None and llm_call_cost_usd > 0:
                budget.record("llm", llm_call_cost_usd)
            if classified is not None:
                if classified["intent"] == "status":
                    await message.channel.send(embed=await status_embed())
                    return
                if classified["intent"] == "incident":
                    severity = IncidentSeverity(classified.get("severity_hint", "P2"))
                    service = classified.get("service") or "yuki-core-api"
                    if service == "unknown":
                        service = "yuki-core-api"
                    incident = incidents.create(
                        IncidentCreate(
                            source="discord_reactive",
                            service=service,
                            summary=classified.get("summary") or message.content[:500],
                            severity=severity,
                        )
                    )
                    await message.channel.send(
                        embed=alert_embed(incident, console_url(incident, str(message.author.id)), autonomy_mode),
                        view=IncidentApprovalView(incident),
                    )
                    return
                return  # "other": not our business

            if any(k in lowered for k in ("fine", "status", "healthy", "everything ok")):
                await message.channel.send(embed=await status_embed())
                return
            if any(k in lowered for k in ("down", "crash", "error", "broken", "not working", "issue")):
                incident = incidents.create(
                    IncidentCreate(
                        source="discord_reactive",
                        service="yuki-core-api",
                        summary=message.content[:500],
                        severity=IncidentSeverity.P2,
                    )
                )
                await message.channel.send(
                    embed=alert_embed(incident, console_url(incident, str(message.author.id)), autonomy_mode),
                    view=IncidentApprovalView(incident),
                )
                return

        await bot.process_commands(message)

    @bot.tree.command(name="status", description="Show live presence + open incidents")
    @app_commands.guild_only()
    async def status(interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        await interaction.followup.send(embed=await status_embed())

    @bot.tree.command(name="approve", description="Approve and run the restart runbook for an incident")
    @app_commands.guild_only()
    @app_commands.describe(incident_id="Incident id (or its prefix)")
    async def approve(interaction: discord.Interaction, incident_id: str) -> None:
        incident = next(
            (
                i
                for i in incidents.list_all()
                if i.status.value in ("open", "triaged") and str(i.id).startswith(incident_id)
            ),
            None,
        )
        if incident is None:
            await interaction.response.send_message("No active incident matched.", ephemeral=True)
            return
        role = actor_role_for(member_role_names(interaction.user), role_permissions)
        await interaction.response.defer()
        await run_action(
            interaction.channel,
            incident,
            RunbookAction.RESTART_SERVICE,
            str(interaction.user.id),
            role,
            approved=True,
        )

    @bot.tree.command(name="triage", description="Create an incident for a monitored service")
    @app_commands.guild_only()
    @app_commands.describe(service="Allowed target service", summary="What is failing")
    async def triage(interaction: discord.Interaction, service: str, summary: str) -> None:
        incident = incidents.create(
            IncidentCreate(source="discord", service=service, summary=summary, severity=IncidentSeverity.P2)
        )
        await interaction.response.send_message(
            f"Incident `{incident.id}` created for `{incident.service}`. Status: `{incident.status.value}`."
        )

    return bot


async def run_discord_bot(
    token: str,
    incidents: IncidentService,
    actions: ActionService,
    alert_channel_id: int | None = None,
    alerts: AlertBridge | None = None,
    public_base_url: str = "",
    magic_link_secret: str = "",
    autonomy_mode: str = "strict_confirmation",
    devin_api_key: str | None = None,
    role_permissions: dict[str, ActorRole] | None = None,
    llm_router: LLMRouter | None = None,
    context_provider: Callable[[], str] | None = None,
    budget: BudgetGovernor | None = None,
    devin_session_cost_usd: float = 1.00,
    llm_call_cost_usd: float = 0.00,
    tracker: IssueTracker | None = None,
    pr_watch_interval_seconds: float = 300.0,
    pr_watch_timeout_minutes: float = 720.0,
) -> None:
    bot = make_bot(
        incidents,
        actions,
        alert_channel_id=alert_channel_id,
        alerts=alerts,
        public_base_url=public_base_url,
        magic_link_secret=magic_link_secret,
        autonomy_mode=autonomy_mode,
        devin_api_key=devin_api_key,
        role_permissions=role_permissions,
        context_provider=context_provider,
        llm_router=llm_router,
        budget=budget,
        devin_session_cost_usd=devin_session_cost_usd,
        llm_call_cost_usd=llm_call_cost_usd,
        tracker=tracker,
        pr_watch_interval_seconds=pr_watch_interval_seconds,
        pr_watch_timeout_minutes=pr_watch_timeout_minutes,
    )
    await bot.start(token)


async def stop_task(task: asyncio.Task[object] | None) -> None:
    if task is None:
        return
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task
