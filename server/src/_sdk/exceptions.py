from typing import Any, Dict, Optional


class TrackerException(Exception):
    """
    Base exception for all custom Tracker exceptions.

    Attributes:
        error_code: Machine-readable error code (e.g., 'validation_error')
        status_code: HTTP status code (e.g., 400, 404, 500)
        default_message: Human-readable error message
        details: Optional field-level error details
    """

    error_code: str = 'internal_error'
    status_code: int = 500
    default_message: str = 'An error occurred'

    def __init__(self, message: Optional[str] = None, details: Optional[Dict[str, Any]] = None, **kwargs):
        self.message = message or self.default_message
        self.details = details or {}

        if kwargs:
            try:
                self.message = self.message.format(**kwargs)
            except KeyError:
                pass

        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to API error response format"""
        error_dict = {
            'code': self.error_code,
            'message': self.message,
        }

        if self.details:
            error_dict['details'] = self.details

        return error_dict


# ==========================================
# Authentication & Authorization Exceptions
# ==========================================

class AuthenticationRequiredException(TrackerException):
    error_code = 'authentication_required'
    status_code = 401
    default_message = 'Authentication is required to access this resource.'


class InvalidCredentialsException(TrackerException):
    error_code = 'invalid_credentials'
    status_code = 401
    default_message = 'Invalid credentials provided.'


class TokenExpiredException(TrackerException):
    error_code = 'token_expired'
    status_code = 401
    default_message = 'Your session has expired. Please log in again.'


class TokenInvalidException(TrackerException):
    error_code = 'token_invalid'
    status_code = 401
    default_message = 'Invalid authentication token.'


class PermissionDeniedException(TrackerException):
    error_code = 'permission_denied'
    status_code = 403
    default_message = 'You do not have permission to perform this action.'


class AccountNotVerifiedException(TrackerException):
    error_code = 'account_not_verified'
    status_code = 403
    default_message = 'Please verify your account to continue.'


class AccountSuspendedException(TrackerException):
    error_code = 'account_suspended'
    status_code = 403
    default_message = 'Your account has been suspended. Contact support for assistance.'


# ==========================================
# Validation Exceptions
# ==========================================

class ValidationException(TrackerException):
    error_code = 'validation_error'
    status_code = 400
    default_message = 'Validation failed. Please check your input.'


class MissingFieldException(ValidationException):
    error_code = 'missing_field'
    default_message = 'Required field is missing: {field_name}'


class InvalidFormatException(ValidationException):
    error_code = 'invalid_format'
    default_message = 'Invalid format for field: {field_name}'


class DuplicateEntryException(ValidationException):
    error_code = 'duplicate_entry'
    status_code = 409
    default_message = 'A record with this {field_name} already exists.'


# ==========================================
# Resource Exceptions
# ==========================================

class ResourceNotFoundException(TrackerException):
    error_code = 'not_found'
    status_code = 404
    default_message = 'The requested {resource_type} was not found.'


class ResourceAlreadyExistsException(TrackerException):
    error_code = 'already_exists'
    status_code = 409
    default_message = 'The {resource_type} already exists.'


class ResourceConflictException(TrackerException):
    error_code = 'conflict'
    status_code = 409
    default_message = 'This operation conflicts with the current state of {resource_type}.'


class RateLimitExceededException(TrackerException):
    error_code = 'rate_limit_exceeded'
    status_code = 429
    default_message = 'Too many requests. Please try again later.'


class ExternalServiceException(TrackerException):
    error_code = 'external_service_error'
    status_code = 502
    default_message = 'An external service is currently unavailable. Please try again later.'


class MediaUploadException(TrackerException):
    error_code = 'media_upload_failed'
    status_code = 500
    default_message = 'Failed to upload media file.'
