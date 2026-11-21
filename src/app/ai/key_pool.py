"""A dependency-free adaptation of Yuki's fair API-key distributor.

PocketSRE currently needs one process, so this intentionally excludes Yuki's
Redis/database synchronization. The useful invariants remain: serialized key
reservation, rate-limit windows, health-aware selection, and cooldowns.
"""

import asyncio
import random
import time
from dataclasses import dataclass


class KeyPoolRateLimitError(Exception):
    def __init__(self, retry_after: float) -> None:
        self.retry_after = retry_after
        super().__init__(f"No API key is available for {retry_after:.1f}s")


@dataclass
class KeyState:
    key: str
    rpm_limit: int
    daily_limit: int
    requests_this_minute: int = 0
    requests_today: int = 0
    minute_window: int = 0
    day_window: int = 0
    health: float = 0.8
    consecutive_failures: int = 0
    cooldown_until: float = 0.0


class KeyPool:
    """Select a healthy key proportionally to its remaining capacity."""

    def __init__(self, keys: list[str], *, rpm_limit: int = 15, daily_limit: int = 1_000) -> None:
        if not keys:
            raise ValueError("At least one API key is required")
        now = time.time()
        self._states = [
            KeyState(key=key, rpm_limit=rpm_limit, daily_limit=daily_limit, minute_window=int(now // 60), day_window=int(now // 86_400))
            for key in keys
        ]
        self._lock = asyncio.Lock()

    async def acquire(self) -> str:
        async with self._lock:
            now = time.time()
            self._refresh_windows(now)
            available = [state for state in self._states if self._eligible(state, now)]
            if not available:
                waits = [max(0.1, state.cooldown_until - now) for state in self._states]
                raise KeyPoolRateLimitError(min(waits, default=60.0))
            weights = [self._weight(state) for state in available]
            selected = random.choices(available, weights=weights, k=1)[0]
            selected.requests_this_minute += 1
            selected.requests_today += 1
            return selected.key

    async def record_success(self, key: str) -> None:
        async with self._lock:
            state = self._state(key)
            state.consecutive_failures = 0
            state.health = min(1.0, state.health + 0.05)

    async def record_failure(self, key: str, *, retry_after: float | None = None) -> None:
        async with self._lock:
            state = self._state(key)
            state.consecutive_failures += 1
            state.health = max(0.1, state.health - 0.2)
            cooldown = retry_after if retry_after is not None else min(60.0, 2 ** state.consecutive_failures)
            state.cooldown_until = time.time() + cooldown

    def stats(self) -> list[dict[str, float | int]]:
        return [
            {
                "requests_this_minute": state.requests_this_minute,
                "requests_today": state.requests_today,
                "health": round(state.health, 2),
                "cooldown_seconds": max(0.0, round(state.cooldown_until - time.time(), 1)),
            }
            for state in self._states
        ]

    def _refresh_windows(self, now: float) -> None:
        minute, day = int(now // 60), int(now // 86_400)
        for state in self._states:
            if state.minute_window != minute:
                state.minute_window, state.requests_this_minute = minute, 0
            if state.day_window != day:
                state.day_window, state.requests_today = day, 0

    @staticmethod
    def _eligible(state: KeyState, now: float) -> bool:
        return (
            state.cooldown_until <= now
            and state.requests_this_minute < state.rpm_limit
            and state.requests_today < state.daily_limit
        )

    @staticmethod
    def _weight(state: KeyState) -> float:
        minute_headroom = (state.rpm_limit - state.requests_this_minute) / state.rpm_limit
        day_headroom = (state.daily_limit - state.requests_today) / state.daily_limit
        return max(0.001, minute_headroom * day_headroom * state.health)

    def _state(self, key: str) -> KeyState:
        for state in self._states:
            if state.key == key:
                return state
        raise ValueError("Unknown API key")
