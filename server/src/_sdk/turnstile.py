"""Cloudflare Turnstile siteverify helper."""

from __future__ import annotations

from typing import Optional

import requests
from django.http import HttpRequest

from _sdk.exceptions import ValidationException
from config import config

TURNSTILE_SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def get_client_ip(request: HttpRequest) -> str:
    """Extract real client IP (first X-Forwarded-For hop, else REMOTE_ADDR)."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "") or ""


def verify_turnstile_token(
    token: Optional[str],
    remote_ip: Optional[str] = None,
) -> None:
    """
    Verify a Turnstile token with Cloudflare.

    No-op when Turnstile is disabled. Raises ValidationException on failure.
    """
    if not config.turnstile.is_enabled:
        return

    secret = config.turnstile.secret_key.strip()
    if not secret:
        raise ValidationException(
            message="Turnstile is enabled but CLOUDFLARE_TURNSTILE_SECRET_KEY is not set."
        )

    value = (token or "").strip()
    if not value:
        raise ValidationException(message="Security check failed. Please try again.")

    data = {
        "secret": secret,
        "response": value,
    }
    if remote_ip:
        data["remoteip"] = remote_ip

    try:
        response = requests.post(
            TURNSTILE_SITEVERIFY_URL,
            data=data,
            timeout=5,
        )
        response.raise_for_status()
        result = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise ValidationException(
            message="Security check unavailable. Please try again."
        ) from exc

    if not result.get("success"):
        raise ValidationException(
            message="Security check failed. Please complete the challenge again."
        )


def require_turnstile(request: HttpRequest, token: Optional[str]) -> None:
    """Verify Turnstile using the request client IP."""
    verify_turnstile_token(token, remote_ip=get_client_ip(request))
