from uuid import uuid4

import pytest

from app.config import get_settings
from app.shared.budget import BudgetExhaustedError, BudgetGovernor


def _governor(**overrides) -> BudgetGovernor:
    settings = get_settings()
    # cached singleton — reset every cap so tests never leak into each other
    settings.budget_devin_usd = None
    settings.budget_llm_usd = None
    settings.budget_sarvam_usd = None
    settings.budget_smallest_usd = None
    settings.budget_per_incident_usd = 5.0
    for k, v in overrides.items():
        setattr(settings, k, v)
    return BudgetGovernor(db=None, settings=settings)


def test_provider_cap_blocks_call() -> None:
    gov = _governor(budget_devin_usd=1.0)
    gov.record("devin", 1.0, uuid4())
    with pytest.raises(BudgetExhaustedError):
        gov.check("devin")


def test_per_incident_cap_blocks() -> None:
    gov = _governor(budget_per_incident_usd=5.0)
    inc = uuid4()
    gov.record("devin", 4.9, inc)
    gov.record("llm", 0.2, inc)
    with pytest.raises(BudgetExhaustedError) as exc:
        gov.check("devin", inc)
    assert "per-incident" in str(exc.value)


def test_below_caps_passes() -> None:
    gov = _governor(budget_devin_usd=5.0, budget_per_incident_usd=5.0)
    inc = uuid4()
    gov.record("devin", 1.0, inc)
    gov.check("devin", inc)  # no raise


def test_uncapped_provider_passes() -> None:
    gov = _governor(budget_llm_usd=None)
    gov.record("llm", 0.0)
    gov.check("llm")


def test_provider_totals() -> None:
    gov = _governor()
    inc = uuid4()
    gov.record("devin", 1.0, inc)
    gov.record("llm", 0.01, inc)
    totals = gov.provider_totals()
    assert totals["devin"] == pytest.approx(1.0)
    assert totals["llm"] == pytest.approx(0.01)
    assert gov.incident_spend(inc) == pytest.approx(1.01)
