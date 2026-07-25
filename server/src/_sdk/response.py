"""
Response Utilities for Tracker Backend

Django Ninja handles most response formatting automatically using response schemas.
This module provides utilities for cases where manual response formatting is needed.

IMPORTANT: Prefer Django Ninja's automatic response handling over manual formatting.

Django Ninja Automatic Response Handling:
```python
# ✅ PREFERRED - Django Ninja automatically formats responses
@api.get("/users/{user_id}", response=UserResponseSchema)
def get_user(request, user_id: int):
    user = get_object_or_404(User, id=user_id)
    return user  # Automatically serialized to UserResponseSchema

# ✅ PREFERRED - Django Ninja handles pagination
@api.get("/users/", response=List[UserListSchema])
@paginate(PageNumberPagination)
def list_users(request):
    return User.objects.all()  # Automatically paginated and serialized
```

Manual Response Utilities (use sparingly):
- Middleware-level responses
- Custom error responses (though ninja_handlers.py handles most cases)
- Migration from legacy APIs
"""

from typing import Any, Dict, Optional
from django.http import JsonResponse
from django.utils import timezone

from _sdk.constants import ErrorCode, HTTPStatus


def manual_error_response(
    message: str,
    error_code: str = 'error',
    details: Optional[Dict[str, Any]] = None,
    request=None,
    status: int = 400,
) -> JsonResponse:
    """
    Build a manual error response for cases where Django Ninja exception handlers
    are not sufficient (e.g., middleware-level errors).

    IMPORTANT: Prefer using Django Ninja exception handlers in ninja_handlers.py
    for API endpoint errors.

    Args:
        message: Human-readable error message
        error_code: Machine-readable error code
        details: Optional field-level error details
        request: Django request object (for request_id)
        status: HTTP status code

    Returns:
        JsonResponse with standardized error format

    Usage:
        # In middleware or non-API contexts
        return manual_error_response(
            message="Authentication required",
            error_code="auth_required",
            status=401
        )
    """
    error_body = {
        'code': error_code,
        'message': message,
    }

    if details:
        error_body['details'] = details

    response_body = {
        'success': False,
        'error': error_body,
        'meta': {
            'timestamp': timezone.now().isoformat(),
            'request_id': getattr(request, 'request_id', 'unknown'),
        }
    }

    return JsonResponse(response_body, status=status, safe=False)


def manual_success_response(
    data: Any = None,
    request=None,
    status: int = 200,
    **extra_meta
) -> JsonResponse:
    """Returns a JsonResponse (direct response bypass)."""
    return JsonResponse(
        api_success(data, request, **extra_meta),
        status=status,
        safe=False
    )


def api_success(
    data: Any = None,
    request=None,
    **extra_meta
) -> Dict[str, Any]:
    """
    Build a success response dictionary for Django Ninja endpoints.
    
    Args:
        data: Response payload
        request: Django request object
        **extra_meta: Additional meta fields
        
    Returns:
        Standardized success response dictionary
    """
    return {
        'success': True,
        'data': data,
        'meta': {
            'timestamp': timezone.now().isoformat(),
            'request_id': getattr(request, 'request_id', 'unknown'),
            **extra_meta
        }
    }


def api_error(
    message: str,
    error_code: str = 'error',
    details: Optional[Dict[str, Any]] = None,
    request=None,
) -> Dict[str, Any]:
    """
    Build an error response dictionary for Django Ninja endpoints.
    """
    error_body = {
        'code': error_code,
        'message': message,
    }
    if details:
        error_body['details'] = details

    return {
        'success': False,
        'error': error_body,
        'meta': {
            'timestamp': timezone.now().isoformat(),
            'request_id': getattr(request, 'request_id', 'unknown'),
        }
    }


# Re-export for backwards compatibility with existing code
# DEPRECATED: Use manual_error_response instead
def error_response(*args, **kwargs):
    """DEPRECATED: Use manual_error_response or Django Ninja exception handlers."""
    return manual_error_response(*args, **kwargs)


# DEPRECATED: Use manual_success_response instead
def success_response(*args, **kwargs):
    """DEPRECATED: Use manual_success_response or Django Ninja automatic responses."""
    return manual_success_response(*args, **kwargs)


# Re-export constants for convenience
__all__ = [
    'manual_error_response',
    'manual_success_response',
    'error_response',  # deprecated
    'success_response',  # deprecated
    'ErrorCode',
    'HTTPStatus'
]

# Migration Guide:
"""
# ❌ OLD WAY - Manual response formatting
@api.get("/users/{user_id}")
def get_user(request, user_id: int):
    try:
        user = User.objects.get(id=user_id)
        return success_response(
            data=user.to_dict(),
            request=request
        )
    except User.DoesNotExist:
        return error_response(
            message="User not found",
            error_code="not_found",
            status=404
        )

# ✅ NEW WAY - Django Ninja automatic handling
@api.get("/users/{user_id}", response=UserResponseSchema)
def get_user(request, user_id: int):
    user = get_object_or_404(User, id=user_id)
    return user  # Django Ninja handles serialization and error formatting

# Errors are handled by ninja_handlers.py automatically
"""
