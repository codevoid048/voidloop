"""
Permission Decorators for Tracker Backend

Provides authentication and authorization decorators for Django Ninja endpoints.
Handles JWT authentication, permission checking, and user state validation.
"""

from functools import wraps
from typing import Callable, Any, Optional, List, Union
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.http import HttpRequest
from django.views.decorators.csrf import csrf_exempt

from .jwt import JWTService, JWTAuthBackend
from .exceptions import (
    AuthenticationRequiredException,
    TokenInvalidException,
    TokenExpiredException,
    PermissionDeniedException,
    AccountNotVerifiedException,
    AccountSuspendedException,
)

User = get_user_model()


def extract_token_from_request(request: HttpRequest) -> Optional[str]:
    """
    Extract JWT token from request Authorization header.

    Args:
        request: Django HttpRequest object

    Returns:
        Token string if found, None otherwise
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None

    try:
        scheme, token = auth_header.split()
        if scheme.lower() == 'bearer':
            return token
    except ValueError:
        pass

    return None


def get_authenticated_user(request: HttpRequest) -> User:
    """
    Get authenticated user from request token.

    Args:
        request: Django HttpRequest object

    Returns:
        User instance if authenticated

    Raises:
        AuthenticationRequiredException: If authentication fails
    """
    token = extract_token_from_request(request)
    if not token:
        raise AuthenticationRequiredException(message="Authentication token required")

    try:
        user = JWTService.get_user_from_token(token)
        if not user:
            raise AuthenticationRequiredException(message="Invalid authentication token")

        # Store user in request for later use
        request.auth_user = user
        return user

    except (TokenInvalidException, TokenExpiredException) as e:
        raise AuthenticationRequiredException(message=str(e))


def require_auth(func: Callable) -> Callable:
    """
    Decorator to require user authentication.

    Usage:
        @api.post("/protected-endpoint")
        @require_auth
        def protected_view(request):
            user = request.auth_user  # Available after decorator
            return {"message": f"Hello {user.email}"}

    Raises:
        AuthenticationRequiredException: If user is not authenticated
    """
    @wraps(func)
    def wrapper(request: HttpRequest, *args, **kwargs) -> Any:
        user = get_authenticated_user(request)

        if not user.is_active:
            raise AccountSuspendedException(message="Account is disabled")

        return func(request, *args, **kwargs)

    return wrapper


def require_staff(func: Callable) -> Callable:
    """
    Decorator to require staff/admin permissions.

    Usage:
        @api.post("/admin-endpoint")
        @require_staff
        def admin_view(request):
            return {"message": "Admin access granted"}

    Raises:
        AuthenticationRequiredException: If user is not authenticated
        PermissionDeniedException: If user is not staff
    """
    @wraps(func)
    def wrapper(request: HttpRequest, *args, **kwargs) -> Any:
        user = get_authenticated_user(request)

        if not user.is_staff:
            raise PermissionDeniedException(message="Staff access required")

        return func(request, *args, **kwargs)

    return wrapper


def require_superuser(func: Callable) -> Callable:
    """
    Decorator to require superuser permissions.

    Usage:
        @api.post("/superuser-endpoint")
        @require_superuser
        def superuser_view(request):
            return {"message": "Superuser access granted"}

    Raises:
        AuthenticationRequiredException: If user is not authenticated
        PermissionDeniedException: If user is not superuser
    """
    @wraps(func)
    def wrapper(request: HttpRequest, *args, **kwargs) -> Any:
        user = get_authenticated_user(request)

        if not user.is_superuser:
            raise PermissionDeniedException(message="Superuser access required")

        return func(request, *args, **kwargs)

    return wrapper


def require_verified(func: Callable) -> Callable:
    """
    Decorator to require verified email or mobile.

    Usage:
        @api.post("/verified-endpoint")
        @require_verified
        def verified_view(request):
            return {"message": "Verified user access granted"}

    Raises:
        AuthenticationRequiredException: If user is not authenticated
        AccountNotVerifiedException: If user is not verified
    """
    @wraps(func)
    def wrapper(request: HttpRequest, *args, **kwargs) -> Any:
        user = get_authenticated_user(request)

        # Active users are considered verified
        is_verified = user.is_active

        if not is_verified:
            raise AccountNotVerifiedException(
                message="Account verification required"
            )

        return func(request, *args, **kwargs)

    return wrapper


def require_permissions(permissions: Union[str, List[str]], all_required: bool = True) -> Callable:
    """
    Decorator to require specific Django permissions.

    Args:
        permissions: Permission string or list of permission strings
        all_required: If True, user must have ALL permissions. If False, ANY permission.

    Usage:
        @api.post("/manage-users")
        @require_permissions('auth.change_user')
        def manage_users(request):
            return {"message": "User management access granted"}

        @api.post("/admin-panel")
        @require_permissions(['auth.add_user', 'auth.delete_user'], all_required=False)
        def admin_panel(request):
            return {"message": "Admin panel access granted"}

    Raises:
        AuthenticationRequiredException: If user is not authenticated
        PermissionDeniedException: If user lacks required permissions
    """
    if isinstance(permissions, str):
        permissions = [permissions]

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(request: HttpRequest, *args, **kwargs) -> Any:
            user = get_authenticated_user(request)

            # Superuser has all permissions
            if user.is_superuser:
                return func(request, *args, **kwargs)

            user_permissions = set(user.get_all_permissions())

            if all_required:
                # User must have ALL permissions
                missing_perms = set(permissions) - user_permissions
                if missing_perms:
                    raise PermissionDeniedException(
                        message=f"Missing required permissions: {', '.join(missing_perms)}"
                    )
            else:
                # User must have at least ONE permission
                if not any(perm in user_permissions for perm in permissions):
                    raise PermissionDeniedException(
                        message=f"One of these permissions required: {', '.join(permissions)}"
                    )

            return func(request, *args, **kwargs)

        return wrapper
    return decorator


def require_owner_or_staff(owner_field: str = 'user', owner_lookup: str = 'pk') -> Callable:
    """
    Decorator to require ownership of resource or staff access.

    Args:
        owner_field: Field name on the model that contains the owner
        owner_lookup: URL parameter name for resource lookup

    Usage:
        @api.get("/orders/{order_id}")
        @require_owner_or_staff(owner_field='user', owner_lookup='order_id')
        def get_order(request, order_id: int):
            # Only order owner or staff can access
            return {"order_id": order_id}

    Raises:
        AuthenticationRequiredException: If user is not authenticated
        PermissionDeniedException: If user is not owner and not staff
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(request: HttpRequest, *args, **kwargs) -> Any:
            user = get_authenticated_user(request)

            # Staff can access anything
            if user.is_staff:
                return func(request, *args, **kwargs)

            # Get the resource ID from URL parameters
            resource_id = kwargs.get(owner_lookup)
            if not resource_id:
                raise PermissionDeniedException(message=f"Resource ID ({owner_lookup}) not found")

            # This is a basic check - in real implementation, you'd need to:
            # 1. Get the model from the view context
            # 2. Fetch the resource and check ownership
            # For now, we'll defer to the view to implement ownership checks

            return func(request, *args, **kwargs)

        return wrapper
    return decorator


def optional_auth(func: Callable) -> Callable:
    """
    Decorator for optional authentication.
    Sets request.auth_user if token is provided, otherwise None.

    Usage:
        @api.get("/public-endpoint")
        @optional_auth
        def public_view(request):
            if request.auth_user:
                return {"message": f"Hello {request.auth_user.email}"}
            return {"message": "Hello anonymous user"}
    """
    @wraps(func)
    def wrapper(request: HttpRequest, *args, **kwargs) -> Any:
        try:
            get_authenticated_user(request)
        except AuthenticationRequiredException:
            # Set to None if authentication fails
            request.auth_user = None

        return func(request, *args, **kwargs)

    return wrapper


def rate_limit(requests_per_minute: int = 60) -> Callable:
    """
    Basic rate limiting decorator (placeholder for future implementation).

    Args:
        requests_per_minute: Maximum requests per minute per user

    Usage:
        @api.post("/send-otp")
        @rate_limit(requests_per_minute=5)
        def send_otp(request):
            return {"message": "OTP sent"}

    Note: This is a placeholder. In production, use Redis-based rate limiting.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(request: HttpRequest, *args, **kwargs) -> Any:
            # TODO: Implement Redis-based rate limiting
            # For now, just pass through
            return func(request, *args, **kwargs)

        return wrapper
    return decorator


# Convenience combinations
def require_authenticated_staff(func: Callable) -> Callable:
    """Convenience decorator combining @require_auth and @require_staff."""
    return csrf_exempt(require_staff(require_auth(func)))


def require_authenticated_verified(func: Callable) -> Callable:
    """Convenience decorator combining @require_auth and @require_verified."""
    return require_verified(require_auth(func))


# Django Ninja authentication class for automatic auth
class TrackerJWTAuth(JWTAuthBackend):
    """
    Django Ninja authentication class using Tracker JWT backend.

    Usage in Django Ninja:
        from _sdk.decorators import TrackerJWTAuth

        api = NinjaAPI(auth=TrackerJWTAuth())

        @api.get("/protected")
        def protected_endpoint(request):
            return {"user_id": request.auth.id}
    """
    pass