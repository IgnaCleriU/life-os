"""Tests del chequeo diario de crédito del VPS (credit_check.py).

Corren con el entorno del backend, sin red:

    cd backend && uv run pytest ../deploy/vps/credit-check
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import credit_check
import pytest

BALANCE_RESPONSE = {
    "properties": {
        "balanceSummary": {
            "estimatedBalance": {"currency": "USD", "value": 42.5},
            "currentBalance": {"currency": "USD", "value": 50.0},
        }
    }
}
NOW = datetime(2026, 10, 16, 15, 0, tzinfo=UTC)
SCOPE = "/providers/Microsoft.Billing/billingAccounts/acc/billingProfiles/prof"


def test_parse_balance_uses_the_estimated_balance() -> None:
    """El estimado incluye cargos aún no facturados: es el saldo real disponible."""
    assert credit_check.parse_balance(BALANCE_RESPONSE) == (42.5, "USD")


def test_parse_balance_rejects_an_unexpected_payload() -> None:
    with pytest.raises(credit_check.CreditCheckError):
        credit_check.parse_balance({"properties": {}})


def test_balance_url_targets_the_billing_profile() -> None:
    url = credit_check.balance_url(SCOPE)

    assert url.startswith(f"https://management.azure.com{SCOPE}/providers/")
    assert "credits/balanceSummary" in url


@pytest.mark.parametrize(
    ("balance", "low"), [(9.99, True), (10.0, False), (75.0, False), (0.0, True)]
)
def test_low_means_strictly_below_the_threshold(balance: float, low: bool) -> None:
    report = credit_check.build_report(balance, "USD", threshold=10.0, now=NOW)

    assert report["low"] is low


def test_report_carries_what_a_client_needs() -> None:
    report = credit_check.build_report(42.5, "USD", threshold=10.0, now=NOW)

    assert report == {
        "balance": 42.5,
        "currency": "USD",
        "threshold": 10.0,
        "low": False,
        "checked_at": "2026-10-16T15:00:00+00:00",
    }


def test_run_writes_the_report_and_returns_zero(tmp_path) -> None:
    state = tmp_path / "credit.json"

    code = credit_check.run(
        scope=SCOPE,
        threshold=10.0,
        state_path=state,
        fetch=lambda url: BALANCE_RESPONSE,
        now=NOW,
    )

    assert code == 0
    assert json.loads(state.read_text())["balance"] == 42.5


def test_run_warns_when_low(tmp_path, capsys) -> None:
    low = {
        "properties": {
            "balanceSummary": {"estimatedBalance": {"currency": "USD", "value": 7.0}}
        }
    }

    code = credit_check.run(
        scope=SCOPE,
        threshold=10.0,
        state_path=tmp_path / "credit.json",
        fetch=lambda url: low,
        now=NOW,
    )

    assert code == 0
    assert "<4>" in capsys.readouterr().err  # prioridad warning en journald


def test_run_fails_without_touching_the_state_when_azure_errors(tmp_path) -> None:
    state = tmp_path / "credit.json"
    state.write_text('{"balance": 50.0}')

    def broken(url: str) -> dict:
        raise credit_check.CreditCheckError("403 AuthorizationFailed")

    code = credit_check.run(
        scope=SCOPE, threshold=10.0, state_path=state, fetch=broken, now=NOW
    )

    assert code == 1
    assert json.loads(state.read_text()) == {"balance": 50.0}


def test_run_requires_a_scope(tmp_path) -> None:
    code = credit_check.run(
        scope="",
        threshold=10.0,
        state_path=tmp_path / "credit.json",
        fetch=lambda url: BALANCE_RESPONSE,
        now=NOW,
    )

    assert code == 1
