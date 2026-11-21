"""Incident event bridge: poller/webhook producers → Discord consumer."""

import asyncio
from dataclasses import dataclass
from typing import Literal

from app.shared.contracts import Incident


@dataclass(frozen=True)
class AlertEvent:
    kind: Literal["opened", "resolved"]
    incident: Incident


class AlertBridge:
    """In-process queue wiring detection events into the Discord runtime."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[AlertEvent] = asyncio.Queue()

    def emit(self, kind: Literal["opened", "resolved"], incident: Incident) -> None:
        self._queue.put_nowait(AlertEvent(kind=kind, incident=incident))

    async def next(self) -> AlertEvent:
        return await self._queue.get()
