"""Discord runtime adapted from Yuki's lifecycle and command-handler split."""

import asyncio
import contextlib

from app.actions.service import ActionService
from app.incidents.service import IncidentService
from app.shared.contracts import IncidentCreate, IncidentSeverity


def make_bot(incidents: IncidentService, actions: ActionService):
    """Create the Discord adapter lazily so HTTP-only development needs no bot token."""
    import discord
    from discord import app_commands
    from discord.ext import commands

    intents = discord.Intents.default()
    bot = commands.Bot(command_prefix="/", intents=intents)

    @bot.event
    async def on_ready() -> None:
        await bot.tree.sync()

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
    token: str, incidents: IncidentService, actions: ActionService
) -> None:
    bot = make_bot(incidents, actions)
    await bot.start(token)


async def stop_task(task: asyncio.Task[object] | None) -> None:
    if task is None:
        return
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task
