# Error Code Mapping Documentation

This document defines how Django exceptions are mapped to standardized API error codes in the Tracker Backend system.

## Overview

The Tracker API uses a standardized error response format:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "field": "email",
    "details": {
      "invalid_format": "Email address format is invalid"
    }
  },
  "meta": {
    "timestamp": "2024-01-01T12:00:00Z",
    "request_id": "req_12345"
  }
}
```

## Error Code Categories

### 1. Authentication Errors (AUTH\_\*)

| Django Exception                  | Error Code                  | HTTP Status | Message                          |
| --------------------------------- | --------------------------- | ----------- | -------------------------------- |
| `AuthenticationRequiredException` | `AUTH_REQUIRED`             | 401         | Authentication required          |
| `TokenInvalidException`           | `AUTH_INVALID_TOKEN`        | 401         | Invalid authentication token     |
| `TokenExpiredException`           | `AUTH_TOKEN_EXPIRED`        | 401         | Authentication token has expired |
| `AccountNotVerifiedException`     | `AUTH_ACCOUNT_NOT_VERIFIED` | 403         | Account verification required    |
| `AccountSuspendedException`       | `AUTH_ACCOUNT_SUSPENDED`    | 403         | Account has been suspended       |

### 2. Permission Errors (PERM\_\*)

| Django Exception                          | Error Code                | HTTP Status | Message                    |
| ----------------------------------------- | ------------------------- | ----------- | -------------------------- |
| `PermissionDeniedException`               | `PERM_DENIED`             | 403         | Permission denied          |
| `django.core.exceptions.PermissionDenied` | `PERM_INSUFFICIENT`       | 403         | Insufficient permissions   |
| `InsufficientPrivilegesException`         | `PERM_PRIVILEGE_REQUIRED` | 403         | Higher privileges required |

### 3. Validation Errors (VAL\_\*)

| Django Exception                         | Error Code             | HTTP Status | Message                 |
| ---------------------------------------- | ---------------------- | ----------- | ----------------------- |
| `ValidationException`                    | `VAL_VALIDATION_ERROR` | 400         | Validation failed       |
| `InvalidFormatException`                 | `VAL_INVALID_FORMAT`   | 400         | Invalid data format     |
| `django.core.exceptions.ValidationError` | `VAL_FIELD_ERROR`      | 400         | Field validation error  |
| `pydantic.ValidationError`               | `VAL_SCHEMA_ERROR`     | 400         | Schema validation error |
| `RequiredFieldException`                 | `VAL_REQUIRED_FIELD`   | 400         | Required field missing  |

### 4. Resource Errors (RES\_\*)

| Django Exception             | Error Code      | HTTP Status | Message                      |
| ---------------------------- | --------------- | ----------- | ---------------------------- |
| `ResourceNotFoundException`  | `RES_NOT_FOUND` | 404         | Resource not found           |
| `django.http.Http404`        | `RES_NOT_FOUND` | 404         | Resource not found           |
| `DuplicateResourceException` | `RES_DUPLICATE` | 409         | Resource already exists      |
| `ResourceConflictException`  | `RES_CONFLICT`  | 409         | Resource conflict            |
| `ResourceGoneException`      | `RES_GONE`      | 410         | Resource no longer available |

### 5. Business Logic Errors (BIZ\_\*)

| Django Exception                | Error Code                 | HTTP Status | Message                      |
| ------------------------------- | -------------------------- | ----------- | ---------------------------- |
| `InsufficientStockException`    | `BIZ_INSUFFICIENT_STOCK`   | 400         | Insufficient stock available |
| `OrderProcessingException`      | `BIZ_ORDER_PROCESSING`     | 400         | Order processing failed      |
| `PaymentProcessingException`    | `BIZ_PAYMENT_FAILED`       | 400         | Payment processing failed    |
| `ShippingNotAvailableException` | `BIZ_SHIPPING_UNAVAILABLE` | 400         | Shipping not available       |
| `CouponInvalidException`        | `BIZ_INVALID_COUPON`       | 400         | Coupon is invalid or expired |
| `ReturnWindowExpiredException`  | `BIZ_RETURN_EXPIRED`       | 400         | Return window has expired    |

### 6. Rate Limiting Errors (RATE\_\*)

| Django Exception             | Error Code               | HTTP Status | Message             |
| ---------------------------- | ------------------------ | ----------- | ------------------- |
| `RateLimitExceededException` | `RATE_LIMIT_EXCEEDED`    | 429         | Rate limit exceeded |
| `TooManyRequestsException`   | `RATE_TOO_MANY_REQUESTS` | 429         | Too many requests   |
| `QuotaExceededException`     | `RATE_QUOTA_EXCEEDED`    | 429         | API quota exceeded  |

### 7. External Service Errors (EXT\_\*)

| Django Exception           | Error Code             | HTTP Status | Message                   |
| -------------------------- | ---------------------- | ----------- | ------------------------- |
| `PaymentGatewayException`  | `EXT_PAYMENT_GATEWAY`  | 502         | Payment gateway error     |
| `SMSServiceException`      | `EXT_SMS_SERVICE`      | 502         | SMS service unavailable   |
| `EmailServiceException`    | `EXT_EMAIL_SERVICE`    | 502         | Email service unavailable |
| `ShippingServiceException` | `EXT_SHIPPING_SERVICE` | 502         | Shipping service error    |
| `ExternalAPIException`     | `EXT_API_ERROR`        | 502         | External API error        |

### 8. System Errors (SYS\_\*)

| Django Exception          | Error Code           | HTTP Status | Message                    |
| ------------------------- | -------------------- | ----------- | -------------------------- |
| `DatabaseException`       | `SYS_DATABASE_ERROR` | 500         | Database error             |
| `django.db.DatabaseError` | `SYS_DATABASE_ERROR` | 500         | Database error             |
| `CacheException`          | `SYS_CACHE_ERROR`    | 500         | Cache system error         |
| `FileStorageException`    | `SYS_STORAGE_ERROR`  | 500         | File storage error         |
| `ConfigurationException`  | `SYS_CONFIG_ERROR`   | 500         | System configuration error |

### 9. Generic HTTP Errors

| Django Exception                | Error Code                | HTTP Status | Message                  |
| ------------------------------- | ------------------------- | ----------- | ------------------------ |
| `BadRequestException`           | `HTTP_BAD_REQUEST`        | 400         | Bad request              |
| `MethodNotAllowedException`     | `HTTP_METHOD_NOT_ALLOWED` | 405         | Method not allowed       |
| `UnsupportedMediaTypeException` | `HTTP_UNSUPPORTED_MEDIA`  | 415         | Unsupported media type   |
| `RequestTooLargeException`      | `HTTP_REQUEST_TOO_LARGE`  | 413         | Request entity too large |

## Implementation Guidelines

### 1. Exception Handler Priority

The Django Ninja exception handler processes exceptions in this order:

1. **Custom Tracker Exceptions** - Defined in `_sdk/exceptions.py`
2. **Django Core Exceptions** - Built-in Django exceptions
3. **Pydantic Validation Errors** - Schema validation errors
4. **Generic Python Exceptions** - Fallback to generic error

### 2. Error Code Format

- **Prefix**: Category identifier (AUTH, VAL, RES, etc.)
- **Descriptor**: Specific error type
- **Format**: `{PREFIX}_{DESCRIPTOR}` (uppercase, underscore-separated)

Examples:

- `AUTH_REQUIRED` - Authentication required
- `VAL_INVALID_FORMAT` - Validation format error
- `BIZ_INSUFFICIENT_STOCK` - Business logic stock error

### 3. HTTP Status Code Mapping

| Status Code | Category            | Usage                                          |
| ----------- | ------------------- | ---------------------------------------------- |
| 400         | Client Error        | Validation, business logic, malformed requests |
| 401         | Unauthorized        | Authentication required or failed              |
| 403         | Forbidden           | Permission denied, account issues              |
| 404         | Not Found           | Resource does not exist                        |
| 409         | Conflict            | Resource conflict, duplicate creation          |
| 410         | Gone                | Resource permanently removed                   |
| 413         | Payload Too Large   | Request body too large                         |
| 415         | Unsupported Media   | Invalid content type                           |
| 429         | Too Many Requests   | Rate limiting                                  |
| 500         | Internal Error      | System, database, configuration errors         |
| 502         | Bad Gateway         | External service errors                        |
| 503         | Service Unavailable | Service temporarily down                       |

### 4. Error Response Structure

```python
# Standard error response structure
{
    "success": False,
    "error": {
        "code": str,          # Error code from mapping table
        "message": str,       # Human-readable error message
        "field": str,         # Optional: field name for validation errors
        "details": dict       # Optional: additional error context
    },
    "meta": {
        "timestamp": str,     # ISO timestamp
        "request_id": str     # Unique request identifier
    }
}
```

### 5. Field-Level Validation Errors

For validation errors with multiple field issues:

```json
{
  "success": false,
  "error": {
    "code": "VAL_VALIDATION_ERROR",
    "message": "Multiple validation errors"
  },
  "validation_errors": [
    {
      "code": "VAL_REQUIRED_FIELD",
      "message": "Email is required",
      "field": "email"
    },
    {
      "code": "VAL_INVALID_FORMAT",
      "message": "Mobile number format is invalid",
      "field": "mobile"
    }
  ],
  "meta": {
    "timestamp": "2024-01-01T12:00:00Z",
    "request_id": "req_12345"
  }
}
```

## Custom Exception Development

### 1. Creating New Exceptions

When creating new exceptions in `_sdk/exceptions.py`:

```python
class InsufficientStockException(BusinessLogicException):
    """Raised when requested quantity exceeds available stock."""

    default_code = "BIZ_INSUFFICIENT_STOCK"
    default_message = "Insufficient stock available"
    http_status = 400
```

### 2. Exception Handler Registration

Register new exceptions in `_sdk/ninja_handlers.py`:

```python
@api.exception_handler(InsufficientStockException)
def handle_insufficient_stock(request, exc):
    return error_response(
        code=exc.code,
        message=str(exc),
        status_code=exc.http_status,
        details={
            'requested_qty': exc.requested_quantity,
            'available_qty': exc.available_quantity
        }
    )
```

### 3. Testing Error Responses

Use test utilities from `_sdk/testing.py`:

```python
def test_insufficient_stock_error(self):
    response = self.client.post('/api/orders/', data={
        'items': [{'product_id': 1, 'quantity': 999}]
    })

    assert_response_error(
        response,
        expected_code='BIZ_INSUFFICIENT_STOCK',
        status_code=400
    )
```

## Monitoring and Alerting

### 1. Error Tracking

- **5xx Errors**: Immediate alerts (system issues)
- **4xx Errors**: Track patterns (client issues, potential attacks)
- **Rate Limit Errors**: Monitor for abuse patterns
- **Authentication Errors**: Track failed login attempts

### 2. Error Metrics

Key metrics to monitor:

- Error rate by endpoint
- Error distribution by code
- Response time for error responses
- Retry patterns for recoverable errors

### 3. Logging Standards

```python
# Error logging format
logger.error(
    "API Error: %s",
    error_code,
    extra={
        'error_code': error_code,
        'user_id': getattr(request, 'user', {}).get('id'),
        'request_id': request_id,
        'endpoint': request.path,
        'method': request.method,
        'exception_type': type(exc).__name__
    }
)
```

## Version History

| Version | Date       | Changes                             |
| ------- | ---------- | ----------------------------------- |
| 1.0     | 2024-03-25 | Initial error mapping documentation |

## Related Documentation

- [API Response Format](../docs/api-response-format.md)
- [Exception Handling Guide](../docs/exception-handling.md)
- [Testing Error Scenarios](../docs/testing-guide.md)
- [Monitoring and Alerting](../docs/monitoring.md)
