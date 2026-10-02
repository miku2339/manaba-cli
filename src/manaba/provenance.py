from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

ALLOWED_SOURCES = {"manaba_html", "unverified"}
SITE = "nagasaki-gaigo"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def envelope(
    *,
    command: str,
    source: str,
    ok: bool,
    status: str,
    **payload: Any,
) -> dict[str, Any]:
    if source not in ALLOWED_SOURCES:
        source = "unverified"
    body: dict[str, Any] = {
        "ok": ok,
        "status": status,
        "command": command,
        "captured_at": utc_now(),
        "site": SITE,
        "source": source,
    }
    body.update(payload)
    return body
