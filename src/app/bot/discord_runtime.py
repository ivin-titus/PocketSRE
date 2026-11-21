"""Discord runtime adapted from Yuki's lifecycle and command-handler split."""

import asyncio
import contextlib

from app.actions.service import ActionService
from app.incidents.service import IncidentService
from app.shared.contracts import IncidentCreate, IncidentSeverity


def make_bot(
    incidents: IncidentService, actions: ActionService, alert_channel_id: int | None = None
):
    """Create the Discord adapter lazily so HTTP-only development needs no bot token."""
    import discord
    from discord import app_commands
    from discord.ext import commands

    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="/", intents=intents)

    @bot.event
    async def on_ready() -> None:
        await bot.tree.sync()

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
) -> None:
    bot = make_bot(incidents, actions, alert_channel_id=alert_channel_id)
    await bot.start(token)



async def stop_task(task: asyncio.Task[object] | None) -> None:
    if task is None:
        return
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task
