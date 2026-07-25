"""Non-blocking business audit event helpers.

This module is intentionally fail-safe: audit emission never raises to callers.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional


audit_logger = logging.getLogger("audit_logger")


def mask_phone(phone_number: Optional[str]) -> str:
    """Return a masked phone representation safe for logs."""
    if not phone_number:
        return "unknown"
    value = phone_number.strip()
    if len(value) <= 4:
        return "****"
    return f"{'*' * (len(value) - 4)}{value[-4:]}"


def _request_context(request: Any) -> Dict[str, Any]:
    if request is None:
        return {}

    ip_address = request.META.get("HTTP_X_FORWARDED_FOR") or request.META.get("REMOTE_ADDR")
    if isinstance(ip_address, str) and "," in ip_address:
        ip_address = ip_address.split(",")[0].strip()

    user_id = None
    user = getattr(request, "auth_user", None) or getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        user_id = getattr(user, "id", None)

    return {
        "request_id": getattr(request, "request_id", None),
        "method": getattr(request, "method", None),
        "path": getattr(request, "path", None),
        "ip": ip_address,
        "user_id": user_id,
    }


def emit_audit_event(
    event: str,
    *,
    request: Any | None = None,
    level: str = "info",
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Emit business audit event without ever breaking request flow."""
    try:
        payload: Dict[str, Any] = {
            "event": event,
            **_request_context(request),
        }
        if details:
            payload.update(details)

        if level == "error":
            audit_logger.error("Audit event", extra=payload)
        elif level == "warning":
            audit_logger.warning("Audit event", extra=payload)
        else:
            audit_logger.info("Audit event", extra=payload)
    except Exception:
        # Non-blocking by design: never interrupt business flow for observability.
        return
