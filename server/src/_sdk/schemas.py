"""
Pydantic Schemas for Tracker Backend

Base schemas for request/response validation, common patterns, and API contracts.
Provides standardized structure for all API endpoints.
"""

from typing import Any, Dict, List, Optional, Generic, TypeVar, Union
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, validator, model_validator
from pydantic.functional_validators import field_validator

# Type variable for generic schemas
T = TypeVar('T')


class BaseSchema(BaseModel):
    """
    Base schema with common configuration.
    All other schemas should inherit from this.
    """
    model_config = ConfigDict(
        # Allow access via attribute notation (schema.field)
        from_attributes=True,
        # Use enum values instead of enum objects
        use_enum_values=True,
        # Exclude None values from serialization by default
        exclude_none=False,
        # Validate assignment when setting values
        validate_assignment=True,
        # Allow extra fields but don't validate them
        extra='ignore',
    )


class TimestampMixin(BaseModel):
    """Mixin for models with timestamps."""
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class SoftDeleteMixin(BaseModel):
    """Mixin for models with soft delete."""
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp (null if active)")


class AuditMixin(BaseModel):
    """Mixin for models with audit fields."""
    created_by: Optional[int] = Field(None, description="ID of user who created this record")
    updated_by: Optional[int] = Field(None, description="ID of user who last updated this record")


class BaseResourceSchema(BaseSchema, TimestampMixin):
    """
    Base schema for resources with ID and timestamps.
    Most domain models should inherit from this.
    """
    id: int = Field(description="Unique identifier")


class BaseResourceWithAuditSchema(BaseResourceSchema, AuditMixin):
    """Base schema for resources with full audit trail."""
    pass


class BaseResourceWithSoftDeleteSchema(BaseResourceSchema, SoftDeleteMixin):
    """Base schema for resources with soft delete support."""
    pass


class BaseFullAuditSchema(BaseResourceSchema, AuditMixin, SoftDeleteMixin):
    """Base schema for resources with complete audit and soft delete."""
    pass


# ============================================================================
# Response Envelope Schemas
# ============================================================================

class PaginationMeta(BaseSchema):
    """Pagination metadata."""
    page: int = Field(ge=1, description="Current page number")
    per_page: int = Field(ge=1, le=100, description="Items per page")
    total_count: int = Field(ge=0, description="Total number of items")
    total_pages: int = Field(ge=0, description="Total number of pages")
    has_next: bool = Field(description="Whether there are more pages")
    has_previous: bool = Field(description="Whether there are previous pages")


class ResponseMeta(BaseSchema):
    """Response metadata."""
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")
    pagination: Optional[PaginationMeta] = Field(None, description="Pagination info")


class ErrorDetail(BaseSchema):
    """Individual error detail."""
    code: str = Field(description="Error code")
    message: str = Field(description="Human-readable error message")
    field: Optional[str] = Field(None, description="Field that caused the error")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class APIResponse(BaseSchema, Generic[T]):
    """
    Standard API response envelope.
    All API endpoints should return this structure.
    """
    success: bool = Field(description="Whether the request was successful")
    data: Optional[T] = Field(None, description="Response data")
    error: Optional[ErrorDetail] = Field(None, description="Error information if success=false")
    meta: ResponseMeta = Field(default_factory=ResponseMeta, description="Response metadata")


class PaginatedResponse(BaseSchema, Generic[T]):
    """Response for paginated endpoints."""
    success: bool = Field(True, description="Whether the request was successful")
    data: List[T] = Field(description="List of items")
    meta: ResponseMeta = Field(description="Response metadata with pagination")


class ValidationErrorResponse(BaseSchema):
    """Response for validation errors."""
    success: bool = Field(False, description="Always false for error responses")
    error: ErrorDetail = Field(description="Validation error details")
    validation_errors: List[ErrorDetail] = Field(description="Field-level validation errors")
    meta: ResponseMeta = Field(default_factory=ResponseMeta, description="Response metadata")


# ============================================================================
# Authentication Schemas
# ============================================================================

class TokenPair(BaseSchema):
    """JWT token pair response."""
    access: str = Field(description="JWT access token")
    refresh: str = Field(description="JWT refresh token")
    expires_in: int = Field(description="Access token expiry in seconds")


class LoginRequest(BaseSchema):
    """Login request payload."""
    email: Optional[str] = Field(None, description="User email")
    mobile: Optional[str] = Field(None, description="User mobile number")
    password: str = Field(min_length=1, description="User password")

    @field_validator('email', 'mobile')
    @classmethod
    def validate_identifier(cls, v: Optional[str]) -> Optional[str]:
        """Individual field validation for email and mobile."""
        return v

    @model_validator(mode='after')
    def check_identifier_provided(self):
        """Model-level validation to ensure either email or mobile is provided."""
        if not self.email and not self.mobile:
            raise ValueError('Either email or mobile must be provided')
        return self


class LoginResponse(BaseSchema):
    """Login response."""
    user: Dict[str, Any] = Field(description="User information")
    tokens: TokenPair = Field(description="JWT tokens")


class RefreshTokenRequest(BaseSchema):
    """Token refresh request."""
    refresh: str = Field(description="JWT refresh token")


class RefreshTokenResponse(BaseSchema):
    """Token refresh response."""
    tokens: TokenPair = Field(description="New JWT tokens")


class OTPRequest(BaseSchema):
    """OTP request payload."""
    mobile: str = Field(min_length=10, max_length=15, description="Mobile number for OTP")
    purpose: str = Field(description="Purpose of OTP (registration, login, phone_verification)")


class OTPVerification(BaseSchema):
    """OTP verification payload."""
    mobile: str = Field(min_length=10, max_length=15, description="Mobile number")
    otp: str = Field(min_length=6, max_length=6, description="6-digit OTP code")
    purpose: str = Field(description="Purpose of OTP verification")


class ChangePasswordRequest(BaseSchema):
    """Change password request."""
    current_password: str = Field(min_length=1, description="Current password")
    new_password: str = Field(min_length=8, description="New password (minimum 8 characters)")
    confirm_password: str = Field(min_length=8, description="Password confirmation")

    @field_validator('confirm_password')
    @classmethod
    def validate_confirm_password(cls, v: str) -> str:
        """Basic validation for confirm password field."""
        return v

    @model_validator(mode='after')
    def passwords_match(self):
        """Model-level validation to ensure passwords match."""
        if (self.new_password and
            self.confirm_password and
            self.new_password != self.confirm_password):
            raise ValueError('Passwords do not match')
        return self


# ============================================================================
# Common Request Schemas
# ============================================================================

class IDListRequest(BaseSchema):
    """Request with list of IDs."""
    ids: List[int] = Field(min_length=1, description="List of resource IDs")


class BulkActionRequest(BaseSchema):
    """Bulk action request."""
    ids: List[int] = Field(min_length=1, description="List of resource IDs")
    action: str = Field(description="Action to perform")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Action parameters")


class SearchRequest(BaseSchema):
    """Search request parameters."""
    q: str = Field(min_length=1, max_length=100, description="Search query")
    fields: Optional[List[str]] = Field(None, description="Fields to search in")
    limit: int = Field(10, ge=1, le=100, description="Maximum results to return")


class FilterRequest(BaseSchema):
    """Generic filter request."""
    filters: Dict[str, Any] = Field(description="Filter criteria")
    sort_by: Optional[str] = Field(None, description="Sort field")
    sort_order: str = Field("asc", pattern="^(asc|desc)$", description="Sort order")


class PaginationRequest(BaseSchema):
    """Pagination request parameters."""
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")


# ============================================================================
# Status and Action Schemas
# ============================================================================

class StatusUpdate(BaseSchema):
    """Generic status update."""
    status: str = Field(description="New status")
    reason: Optional[str] = Field(None, description="Reason for status change")


class ApprovalAction(BaseSchema):
    """Approval/rejection action."""
    action: str = Field(pattern="^(approve|reject)$", description="Action to take")
    reason: Optional[str] = Field(None, description="Reason for action")


# ============================================================================
# File Upload Schemas
# ============================================================================

class FileUploadResponse(BaseSchema):
    """File upload response."""
    url: str = Field(description="File URL")
    filename: str = Field(description="Original filename")
    size: int = Field(description="File size in bytes")
    content_type: str = Field(description="MIME content type")


class ImageUploadResponse(FileUploadResponse):
    """Image upload response with additional metadata."""
    width: int = Field(description="Image width in pixels")
    height: int = Field(description="Image height in pixels")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL if generated")


# ============================================================================
# Utility Schemas
# ============================================================================

class HealthCheckResponse(BaseSchema):
    """Health check response."""
    status: str = Field("healthy", description="Service status")
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = Field(description="API version")
    services: Dict[str, str] = Field(description="Dependent service statuses")


class MessageResponse(BaseSchema):
    """Simple message response."""
    message: str = Field(description="Response message")


class CountResponse(BaseSchema):
    """Count response."""
    count: int = Field(ge=0, description="Total count")


# ============================================================================
# Address Schemas
# ============================================================================

class AddressSchema(BaseResourceSchema):
    """Address schema."""
    type: str = Field(description="Address type (home, work, etc.)")
    line1: str = Field(max_length=100, description="Address line 1")
    line2: Optional[str] = Field(None, max_length=100, description="Address line 2")
    city: str = Field(max_length=50, description="City")
    state: str = Field(max_length=50, description="State")
    pincode: str = Field(max_length=6, description="PIN code")
    country: str = Field(default="IN", description="Country code")
    is_default: bool = Field(False, description="Whether this is the default address")


class AddressCreateRequest(BaseSchema):
    """Address creation request."""
    type: str = Field(description="Address type")
    line1: str = Field(max_length=100, description="Address line 1")
    line2: Optional[str] = Field(None, max_length=100, description="Address line 2")
    city: str = Field(max_length=50, description="City")
    state: str = Field(max_length=50, description="State")
    pincode: str = Field(max_length=6, pattern=r"^\d{6}$", description="6-digit PIN code")
    is_default: bool = Field(False, description="Set as default address")


# ============================================================================
# Exports for convenient importing
# ============================================================================

__all__ = [
    # Base schemas
    "BaseSchema",
    "TimestampMixin",
    "SoftDeleteMixin",
    "AuditMixin",
    "BaseResourceSchema",
    "BaseResourceWithAuditSchema",
    "BaseResourceWithSoftDeleteSchema",
    "BaseFullAuditSchema",

    # Response schemas
    "PaginationMeta",
    "ResponseMeta",
    "ErrorDetail",
    "APIResponse",
    "PaginatedResponse",
    "ValidationErrorResponse",

    # Auth schemas
    "TokenPair",
    "LoginRequest",
    "LoginResponse",
    "RefreshTokenRequest",
    "RefreshTokenResponse",
    "OTPRequest",
    "OTPVerification",
    "ChangePasswordRequest",

    # Common request schemas
    "IDListRequest",
    "BulkActionRequest",
    "SearchRequest",
    "FilterRequest",
    "PaginationRequest",

    # Action schemas
    "StatusUpdate",
    "ApprovalAction",

    # File schemas
    "FileUploadResponse",
    "ImageUploadResponse",

    # Utility schemas
    "HealthCheckResponse",
    "MessageResponse",
    "CountResponse",

    # Address schemas
    "AddressSchema",
    "AddressCreateRequest",
]