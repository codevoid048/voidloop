"""
_sdk/ninja_handlers.py - Django Ninja exception handlers and renderers

Integrates with Django Ninja's exception handling system to provide
consistent error responses across all API endpoints.

Usage in api.py:
    from ninja import NinjaAPI
    from _sdk.ninja_handlers import (
        validation_error_handler,
        http_error_handler,
        generic_error_handler
    )

    api = NinjaAPI()

    # Register exception handlers
    api.add_exception_handler(ValidationError, validation_error_handler)
    api.add_exception_handler(Http404, http_error_handler)
    api.add_exception_handler(Exception, generic_error_handler)
"""

import logging
from typing import Any, Dict

from django.conf import settings
from django.core.exceptions import ValidationError, PermissionDenied, ObjectDoesNotExist
from django.http import Http404
from django.utils import timezone
from ninja.responses import Response as NinjaResponse

from _sdk.constants import ErrorCode
from _sdk.exceptions import TrackerException

logger = logging.getLogger("django")


def tracker_exception_handler(request, exc: TrackerException):
    """
    Handle custom TrackerException with standardized response.
    """
    return NinjaResponse(
        {
            "success": False,
            "error": exc.to_dict(),
            "meta": {
                "timestamp": timezone.now().isoformat(),
                "request_id": getattr(request, "request_id", "unknown"),
            },
        },
        status=exc.status_code,
    )


def validation_error_handler(request, exc: ValidationError):
    """
    Handle Django ValidationError with field-level details.

    Response:
    {
        "success": false,
        "error": {
            "code": "validation_error",
            "message": "Validation failed",
            "details": {"field_name": ["error message"]}
        },
        "meta": {...}
    }
    """
    details = {}
    if hasattr(exc, "message_dict"):
        details = exc.message_dict
    elif hasattr(exc, "messages"):
        details = {"non_field_errors": list(exc.messages)}

    return NinjaResponse(
        {
            "success": False,
            "error": {
                "code": ErrorCode.VALIDATION_ERROR,
                "message": "Validation failed. Please check your input.",
                "details": details,
            },
            "meta": {
                "timestamp": timezone.now().isoformat(),
                "request_id": getattr(request, "request_id", "unknown"),
            },
        },
        status=400,
    )


def http_error_handler(request, exc: Http404):
    """
    Handle 404 Not Found errors.

    Response:
    {
        "success": false,
        "error": {
            "code": "not_found",
            "message": "Resource not found"
        },
        "meta": {...}
    }
    """
    return NinjaResponse(
        {
            "success": False,
            "error": {
                "code": ErrorCode.NOT_FOUND,
                "message": "The requested resource was not found.",
            },
            "meta": {
                "timestamp": timezone.now().isoformat(),
                "request_id": getattr(request, "request_id", "unknown"),
            },
        },
        status=404,
    )


def permission_denied_handler(request, exc: PermissionDenied):
    """
    Handle 403 Permission Denied errors.

    Response:
    {
        "success": false,
        "error": {
            "code": "permission_denied",
            "message": "Permission denied"
        },
        "meta": {...}
    }
    """
    return NinjaResponse(
        {
            "success": False,
            "error": {
                "code": ErrorCode.PERMISSION_DENIED,
                "message": "You do not have permission to perform this action.",
            },
            "meta": {
                "timestamp": timezone.now().isoformat(),
                "request_id": getattr(request, "request_id", "unknown"),
            },
        },
        status=403,
    )


def generic_error_handler(request, exc: Exception):
    """
    Catch-all exception handler for unhandled errors.

    Logs full exception details internally.
    Returns sanitized error message to client (detailed in DEBUG mode).

    Response:
    {
        "success": false,
        "error": {
            "code": "internal_error",
            "message": "An internal error occurred"
        },
        "meta": {...}
    }
    """
    # Log full exception with context
    logger.error(
        f"Unhandled exception in {request.path}: {exc}",
        exc_info=True,
        extra={
            "request_id": getattr(request, "request_id", "unknown"),
            "user": (
                getattr(request.user, "username", "Anonymous")
                if hasattr(request, "user")
                else "Anonymous"
            ),
            "method": request.method,
            "path": request.path,
        },
    )

    # Hide error details in production
    if settings.DEBUG:
        error_message = str(exc)
        error_details = {"exception_type": exc.__class__.__name__}
    else:
        error_message = "An internal error occurred. Please try again later."
        error_details = None

    error_body = {
        "code": ErrorCode.INTERNAL_ERROR,
        "message": error_message,
    }

    if error_details:
        error_body["details"] = error_details

    return NinjaResponse(
        {
            "success": False,
            "error": error_body,
            "meta": {
                "timestamp": timezone.now().isoformat(),
                "request_id": getattr(request, "request_id", "unknown"),
            },
        },
        status=500,
    )


def object_not_found_handler(request, exc: ObjectDoesNotExist):
    """
    Handle Django ObjectDoesNotExist (from .get() queries).

    Response: Same as 404 handler
    """
    return NinjaResponse(
        {
            "success": False,
            "error": {
                "code": ErrorCode.NOT_FOUND,
                "message": "The requested item was not found.",
            },
            "meta": {
                "timestamp": timezone.now().isoformat(),
                "request_id": getattr(request, "request_id", "unknown"),
            },
        },
        status=404,
    )
