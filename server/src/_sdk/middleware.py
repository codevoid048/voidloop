"""
Essential Middleware for Tracker Backend

Contains only business-specific middleware that Django/Django Ninja doesn't provide.
For standard middleware (security headers, CORS, etc.), use Django's built-in middleware.

IMPORTANT: Django Ninja handles most API concerns automatically:
- Response formatting (use response schemas)
- Exception handling (use ninja_handlers.py)
- Authentication (use Django Ninja auth decorators)

Removed redundant middleware:
- StandardAPIResponseMiddleware (Django Ninja handles response formatting)
- SecurityHeadersMiddleware (use django.middleware.security.SecurityMiddleware)
- RateLimitMiddleware (use django-ratelimit package)
- APIExceptionMiddleware (use ninja_handlers.py for Django Ninja APIs)
"""

import logging
import time
import uuid
from django.utils.deprecation import MiddlewareMixin

from _sdk.signals import clear_audit_context

logger = logging.getLogger('django')
audit_logger = logging.getLogger('audit_logger')


class RequestContextMiddleware(MiddlewareMixin):
    """
    Generate unique request ID and set audit context for business logic.

    Features:
    - Generates UUID for each request (for tracing across logs)
    - Sets audit context (user, IP) for AuditLog signal handlers
    - Adds timing information for performance monitoring
    - Adds request_id to response headers (X-Request-ID)

    This is business-specific functionality not provided by Django.
    Should be placed early in middleware stack.
    """

    def process_request(self, request):
        """Generate request ID and timing for audit/tracing purposes"""
        request.request_id = str(uuid.uuid4())
        request.start_time = time.time()

        # Log request start for audit trail
        audit_logger.info(
            f"Request started: {request.method} {request.path}",
            extra={
                'request_id': request.request_id,
                'method': request.method,
                'path': request.path,
                'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
                'ip': self._get_client_ip(request),
            }
        )

    def process_response(self, request, response):
        """Add request ID to response and set audit context"""
        if hasattr(request, 'request_id'):
            response['X-Request-ID'] = request.request_id

            # Log request completion with timing
            duration_ms = 0
            if hasattr(request, 'start_time'):
                duration_ms = round((time.time() - request.start_time) * 1000, 2)

            audit_logger.info(
                f"Request completed: {request.method} {request.path} - {response.status_code}",
                extra={
                    'request_id': request.request_id,
                    'status_code': response.status_code,
                    'duration_ms': duration_ms,
                }
            )

        # Set audit context for signal handlers (business-specific requirement)
        if hasattr(request, 'user') and request.user.is_authenticated:
            from _sdk.signals import set_audit_context
            ip_address = self._get_client_ip(request)
            set_audit_context(request.user, ip_address)

        # Prevent thread-local context leaks between requests.
        clear_audit_context()

        return response

    def process_exception(self, request, exception):
        """Audit unhandled request exceptions with request tracing context."""
        request_id = getattr(request, 'request_id', None)
        audit_logger.exception(
            f"Unhandled exception during request: {request.method} {request.path}",
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.path,
                'ip': self._get_client_ip(request),
            },
        )

        # Return None so Django continues normal exception handling.
        return None

    def _get_client_ip(self, request) -> str:
        """Extract real client IP address (behind proxies/load balancers)"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')


# Migration guide for removed middleware:
"""
# ❌ REMOVED - Use Django's built-in SecurityMiddleware instead
# MIDDLEWARE = [
#     'django.middleware.security.SecurityMiddleware',  # ✅ Use this
#     # ... other middleware
# ]

# ❌ REMOVED - Use Django Ninja response schemas instead
# Django Ninja automatically formats responses when you define response schemas:

@api.get("/users/{user_id}", response=UserResponseSchema)
def get_user(request, user_id: int):
    user = get_object_or_404(User, id=user_id)
    return user  # Automatically formatted by Django Ninja

# ❌ REMOVED - Use ninja_handlers.py for API exception handling
# Django Ninja uses the exception handlers defined in ninja_handlers.py

# ❌ REMOVED - Use django-ratelimit for rate limiting
# pip install django-ratelimit
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='100/h', method='GET')
@api.get("/public-endpoint")
def public_endpoint(request):
    return {"message": "Hello"}

# ❌ REMOVED - JWT Authentication placeholder
# Use Django Ninja's built-in authentication:
from ninja.security import APIKeyHeader

class AuthBearer(APIKeyHeader):
    param_name = "Authorization"

    def authenticate(self, request, key):
        # Implement JWT validation here
        pass

@api.get("/protected", auth=AuthBearer())
def protected_endpoint(request):
    return {"user": request.auth}
"""
