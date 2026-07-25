"""AWS Lambda entrypoint for the Django ASGI application."""
import os

from mangum import Mangum

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.base")

from core.asgi import application  # noqa: E402


def _normalize_base_path(value: str | None) -> str:
    """Normalize API Gateway base path into the format expected by Mangum."""
    if not value:
        return "/"

    base_path = value.strip()
    if not base_path:
        return "/"

    if not base_path.startswith("/"):
        base_path = f"/{base_path}"

    return base_path.rstrip("/") or "/"


handler = Mangum(
    application,
    lifespan="off",
    api_gateway_base_path=_normalize_base_path(os.environ.get("API_GATEWAY_BASE_PATH")),
)
