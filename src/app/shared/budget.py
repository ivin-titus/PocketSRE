"""Budget governor: pre-call cap enforcement for metered providers.

Ledger rows live in NeonDB (`budget_ledger`); when the DB is unavailable an
in-memory ledger keeps the caps enforced for the session.
"""

from datetime import UTC, datetime
from uuid import UUID

from app.config import Settings
from app.storage.db import Database


class BudgetExhaustedError(Exception):
    """Raised before a paid call when a cap is already exhausted."""


class BudgetGovernor:
    def __init__(self, db: Database | None, settings: Settings) -> None:
        self._db = db
        self._local: list[tuple[str | None, str, float, str]] = []  # (incident_id, provider, amount, day)
        self._caps = {
            "devin": settings.budget_devin_usd,
            "llm": settings.budget_llm_usd,
            "sarvam": settings.budget_sarvam_usd,
            "smallest": settings.budget_smallest_usd,
        }
        self._daily_caps = {
            "devin": settings.budget_devin_daily_usd,
            "llm": settings.budget_llm_daily_usd,
            "sarvam": settings.budget_sarvam_daily_usd,
            "smallest": settings.budget_smallest_daily_usd,
        }
        self.per_incident_cap = settings.budget_per_incident_usd

    def provider_spend(self, provider: str) -> float:
        if self._db is not None:
            return self._db.provider_spend(provider)
        return sum(a for _, p, a, _ in self._local if p == provider)

    def incident_spend(self, incident_id: UUID) -> float:
        if self._db is not None:
            return self._db.incident_spend(incident_id)
        return sum(a for i, _, a, _ in self._local if i == str(incident_id))

    def provider_totals(self) -> dict[str, float]:
        if self._db is not None:
            return self._db.provider_totals()
        totals: dict[str, float] = {}
        for _, p, a, _ in self._local:
            totals[p] = totals.get(p, 0.0) + a
        return totals

    def provider_spend_today(self, provider: str) -> float:
        if self._db is not None:
            return self._db.provider_spend_today(provider)
        today = datetime.now(UTC).date().isoformat()
        return sum(
            a
            for (_, p, a, day) in self._local
            if p == provider and day == today
        )

    def check(self, provider: str, incident_id: UUID | None = None) -> None:
        """Raise BudgetExhaustedError when any cap (flat, daily, per-incident) is hit."""
        cap = self._caps.get(provider)
        if cap is not None and self.provider_spend(provider) >= cap:
            raise BudgetExhaustedError(
                f"{provider} budget exhausted ({self.provider_spend(provider):.4f} >= {cap:.2f} USD cap)"
            )
        daily_cap = self._daily_caps.get(provider)
        if daily_cap is not None and self.provider_spend_today(provider) >= daily_cap:
            raise BudgetExhaustedError(
                f"{provider} daily budget exhausted ({self.provider_spend_today(provider):.4f} >= {daily_cap:.2f} USD/day)"
            )
        if incident_id is not None and self.incident_spend(incident_id) >= self.per_incident_cap:
            raise BudgetExhaustedError(
                f"incident {incident_id} hit the ${self.per_incident_cap:.2f} per-incident cap"
            )

    def record(self, provider: str, amount: float, incident_id: UUID | None = None) -> None:
        """Append to the ledger; negative/zero amounts still record traceability."""
        if self._db is not None:
            self._db.record_spend(incident_id, provider, amount)
        else:
            self._local.append(
                (
                    str(incident_id) if incident_id else None,
                    provider,
                    amount,
                    datetime.now(UTC).date().isoformat(),
                )
            )
