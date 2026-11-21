"""Discord runtime adapted from Yuki's lifecycle and command-handler split."""

import asyncio
import contextlib

from app.actions.service import ActionService
from app.incidents.alerts import AlertBridge, AlertEvent
from app.incidents.service import IncidentService
from app.shared.contracts import (
    ActionRequest,
    ActionResult,
    ActorRole,
    Incident,
    IncidentCreate,
    IncidentSeverity,
    RunbookAction,
)
from app.shared.magic_link import make_console_link

LEAD_ROLE_NAMES = {"sre-lead", "lead", "oncall-lead"}
RESPONDER_ROLE_NAMES = {"sre", "devops", "developer", "dev", "responder"}

DISCORD_FIELD_LIMIT = 1000


def actor_role_for(role_names: list[str]) -> ActorRole:
    """Map Discord role names to PocketSRE actor roles."""
    lowered = {name.lower() for name in role_names}
    if lowered & LEAD_ROLE_NAMES:
        return ActorRole.LEAD
    if lowered & RESPONDER_ROLE_NAMES:
        return ActorRole.RESPONDER
    return ActorRole.VIEWER


def member_role_names(member: object) -> list[str]:
    """Roles of an interaction user; empty outside guilds (DMs get VIEWER)."""
    roles = getattr(member, "roles", None) or []
    return [getattr(role, "name", "") for role in roles]


def truncate(text: str, limit: int = DISCORD_FIELD_LIMIT) -> str:
    return text if len(text) <= limit else text[: limit - 3] + "..."


def alert_embed(incident: Incident, console_url: str | None):
    """Card proposing the allowed next steps for a proactive/reactive alert."""
    import discord

    embed = discord.Embed(
        title=f"🚨 {incident.severity.value} — {incident.service}",
        description=truncate(incident.summary, 500),
        color=discord.Color.red(),
    )
    embed.add_field(name="Incident", value=f"`{incident.id}`", inline=True)
    embed.add_field(name="Source", value=incident.source, inline=True)
    embed.add_field(
        name="Allowed next steps",
        value="`Fetch logs` / `Inspect` run free · `Restart` needs a lead",
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


def make_bot(
    incidents: IncidentService,
    actions: ActionService,
    alert_channel_id: int | None = None,
    alerts: AlertBridge | None = None,
    public_base_url: str = "",
    magic_link_secret: str = "",
    autonomy_mode: str = "strict_confirmation",
):
    """Create the Discord adapter lazily so HTTP-only development needs no bot token."""
    import discord
    from discord import app_commands
    from discord.ext import commands

    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="/", intents=intents)

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
        except PermissionError as exc:
            await channel.send(f"⛔ `{action.value}` denied: {exc}")
            return None
        except Exception as exc:
            await channel.send(f"⚠️ `{action.value}` failed to run: {exc}")
            return None
        await channel.send(embed=report_embed(result))
        return result

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
            role = actor_role_for(member_role_names(interaction.user))
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
                    embed=alert_embed(incident, console_url(incident, "lead")),
                    view=IncidentApprovalView(incident),
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

    @bot.event
    async def on_ready() -> None:
        await bot.tree.sync()
        if alerts is not None:
            bot.loop.create_task(alert_consumer(), name="pocketsre-alert-consumer")

    @bot.event
    async def on_message(message: discord.Message) -> None:
        if message.author == bot.user:
            return

        is_alert_channel = alert_channel_id is not None and message.channel.id == alert_channel_id
        is_webhook = message.webhook_id is not None
        if is_alert_channel or is_webhook:
            content = message.content or ""
            for embed in message.embeds:
                if embed.title:
                    content += f" {embed.title}"
                if embed.description:
                    content += f" {embed.description}"

            detected_container = "yuki-core-api"
            for container in (
                "yuki-core-api",
                "yuki-discord-bot",
                "yuki-telegram-bot",
                "yuki-horiz-client",
                "yuki-redis",
            ):
                if container in content or container.replace("yuki-", "") in content:
                    detected_container = container
                    break

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

    @bot.tree.command(name="status", description="Show PocketSRE control-plane status")
    async def status(interaction: discord.Interaction) -> None:
        await interaction.response.send_message("PocketSRE control plane is online.", ephemeral=True)

    @bot.tree.command(name="triage", description="Create an incident for a monitored service")
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
) -> None:
    bot = make_bot(
        incidents,
        actions,
        alert_channel_id=alert_channel_id,
        alerts=alerts,
        public_base_url=public_base_url,
        magic_link_secret=magic_link_secret,
        autonomy_mode=autonomy_mode,
    )
    await bot.start(token)


async def stop_task(task: asyncio.Task[object] | None) -> None:
    if task is None:
        return
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task
