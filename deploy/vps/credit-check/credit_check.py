#!/usr/bin/env python3
"""Chequeo diario del crédito de Azure que le queda al VPS (ADR 0010).

Consulta el saldo estimado del perfil de facturación con la identidad
administrada de la VM, lo registra en el journal y deja un reporte JSON en
`$LIFEOS_CREDIT_STATE` (por defecto /var/lib/lifeos/credit.json). Ese reporte
es lo que en el futuro van a leer las apps para avisar el saldo restante.

Por debajo de `LIFEOS_CREDIT_THRESHOLD` (USD 10 por defecto) se loguea con
prioridad warning. Solo usa la biblioteca estándar: corre con el python3 del
sistema, fuera del contenedor.

Configuración (variables de entorno):
    LIFEOS_BILLING_SCOPE      /providers/Microsoft.Billing/billingAccounts/<id>
                              /billingProfiles/<id>   (obligatoria)
    LIFEOS_CREDIT_THRESHOLD   umbral en la moneda del crédito (default 10)
    LIFEOS_CREDIT_STATE       ruta del reporte JSON
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ARM = "https://management.azure.com"
API_VERSION = "2023-05-01"
IMDS_TOKEN_URL = (
    "http://169.254.169.254/metadata/identity/oauth2/token"
    "?api-version=2018-02-01&resource=" + urllib.parse.quote(ARM + "/", safe="")
)
DEFAULT_STATE = "/var/lib/lifeos/credit.json"

# Prefijos de prioridad que journald interpreta en stdout/stderr (sd-daemon).
INFO, WARNING, ERROR = "<6>", "<4>", "<3>"


class CreditCheckError(Exception):
    """Falla consultando Azure o interpretando su respuesta."""


def balance_url(scope: str) -> str:
    return (
        f"{ARM}{scope}/providers/Microsoft.Consumption/credits/balanceSummary"
        f"?api-version={API_VERSION}"
    )


def parse_balance(payload: dict[str, Any]) -> tuple[float, str]:
    """Saldo estimado: incluye cargos todavía no facturados."""
    try:
        estimated = payload["properties"]["balanceSummary"]["estimatedBalance"]
        return float(estimated["value"]), str(estimated["currency"])
    except (KeyError, TypeError, ValueError) as exc:
        raise CreditCheckError(f"respuesta inesperada de Azure: {exc!r}") from exc


def build_report(
    balance: float, currency: str, *, threshold: float, now: datetime
) -> dict[str, Any]:
    return {
        "balance": balance,
        "currency": currency,
        "threshold": threshold,
        "low": balance < threshold,
        "checked_at": now.isoformat(),
    }


def _get_json(url: str, headers: dict[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:300]
        raise CreditCheckError(
            f"HTTP {exc.code} en {url.split('?')[0]}: {detail}"
        ) from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise CreditCheckError(
            f"no se pudo consultar {url.split('?')[0]}: {exc}"
        ) from exc


def azure_fetch(url: str) -> dict[str, Any]:
    """GET a ARM autenticado con la identidad administrada de la VM."""
    token = _get_json(IMDS_TOKEN_URL, {"Metadata": "true"}).get("access_token")
    if not token:
        raise CreditCheckError("IMDS no devolvió token: ¿la VM tiene identidad?")
    return _get_json(url, {"Authorization": f"Bearer {token}"})


def _write_atomically(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    tmp.replace(path)


def run(
    *,
    scope: str,
    threshold: float,
    state_path: Path,
    fetch: Callable[[str], dict[str, Any]],
    now: datetime,
) -> int:
    if not scope:
        print(f"{ERROR}falta LIFEOS_BILLING_SCOPE", file=sys.stderr)
        return 1
    try:
        balance, currency = parse_balance(fetch(balance_url(scope)))
    except CreditCheckError as exc:
        print(f"{ERROR}{exc}", file=sys.stderr)
        return 1

    report = build_report(balance, currency, threshold=threshold, now=now)
    _write_atomically(state_path, report)
    if report["low"]:
        print(
            f"{WARNING}quedan {currency} {balance:.2f} de crédito, "
            f"menos de {threshold:.2f}: hay que pensar alternativas al VPS",
            file=sys.stderr,
        )
    else:
        print(f"{INFO}crédito restante: {currency} {balance:.2f}")
    return 0


def main() -> int:
    return run(
        scope=os.environ.get("LIFEOS_BILLING_SCOPE", "").rstrip("/"),
        threshold=float(os.environ.get("LIFEOS_CREDIT_THRESHOLD", "10")),
        state_path=Path(os.environ.get("LIFEOS_CREDIT_STATE", DEFAULT_STATE)),
        fetch=azure_fetch,
        now=datetime.now(UTC),
    )


if __name__ == "__main__":
    sys.exit(main())
