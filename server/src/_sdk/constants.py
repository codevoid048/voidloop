"""
_sdk/constants.py - Global constants for Tracker Backend

Centralized location for all constants used across the application:
- HTTP status codes
- Error codes
- Order statuses
- Payment statuses
- Action types
- Business constants

Import and use throughout the codebase for consistency.

Usage:
    from _sdk.constants import HTTPStatus, ErrorCode, OrderStatus

    if order.status == OrderStatus.PENDING:
        # ...

    return error_response(
        error_code=ErrorCode.OUT_OF_STOCK,
        status=HTTPStatus.BAD_REQUEST
    )
"""

from typing import Final


# ==========================================
# HTTP Status Codes
# ==========================================

class HTTPStatus:
    """Standard HTTP status codes"""

    # Success 2xx
    OK: Final[int] = 200
    CREATED: Final[int] = 201
    ACCEPTED: Final[int] = 202
    NO_CONTENT: Final[int] = 204

    # Client Errors 4xx
    BAD_REQUEST: Final[int] = 400
    UNAUTHORIZED: Final[int] = 401
    FORBIDDEN: Final[int] = 403
    NOT_FOUND: Final[int] = 404
    METHOD_NOT_ALLOWED: Final[int] = 405
    CONFLICT: Final[int] = 409
    UNPROCESSABLE_ENTITY: Final[int] = 422
    TOO_MANY_REQUESTS: Final[int] = 429

    # Server Errors 5xx
    INTERNAL_SERVER_ERROR: Final[int] = 500
    NOT_IMPLEMENTED: Final[int] = 501
    BAD_GATEWAY: Final[int] = 502
    SERVICE_UNAVAILABLE: Final[int] = 503
    GATEWAY_TIMEOUT: Final[int] = 504


# ==========================================
# API Error Codes (for client response)
# ==========================================

class ErrorCode:
    """
    Machine-readable error codes for API responses.

    Used in error response: {"error": {"code": "out_of_stock", ...}}
    """

    # Authentication & Authorization (4xx)
    AUTHENTICATION_REQUIRED: Final[str] = 'authentication_required'
    INVALID_CREDENTIALS: Final[str] = 'invalid_credentials'
    TOKEN_EXPIRED: Final[str] = 'token_expired'
    TOKEN_INVALID: Final[str] = 'token_invalid'
    PERMISSION_DENIED: Final[str] = 'permission_denied'
    ACCOUNT_NOT_VERIFIED: Final[str] = 'account_not_verified'
    ACCOUNT_SUSPENDED: Final[str] = 'account_suspended'

    # Validation (4xx)
    VALIDATION_ERROR: Final[str] = 'validation_error'
    MISSING_FIELD: Final[str] = 'missing_field'
    INVALID_FORMAT: Final[str] = 'invalid_format'
    DUPLICATE_ENTRY: Final[str] = 'duplicate_entry'

    # Resources (4xx)
    NOT_FOUND: Final[str] = 'not_found'
    ALREADY_EXISTS: Final[str] = 'already_exists'
    CONFLICT: Final[str] = 'conflict'

    # Catalog/Product (4xx)
    OUT_OF_STOCK: Final[str] = 'out_of_stock'
    INSUFFICIENT_STOCK: Final[str] = 'insufficient_stock'
    PRODUCT_NOT_ACTIVE: Final[str] = 'product_not_active'
    INVALID_VARIANT: Final[str] = 'invalid_variant'

    # Orders (4xx)
    ORDER_NOT_FOUND: Final[str] = 'order_not_found'
    ORDER_CANNOT_BE_CANCELLED: Final[str] = 'order_cannot_be_cancelled'
    ORDER_CANNOT_BE_MODIFIED: Final[str] = 'order_cannot_be_modified'
    ORDER_ALREADY_COMPLETED: Final[str] = 'order_already_completed'
    EMPTY_CART: Final[str] = 'empty_cart'

    # Payments (4xx, 5xx)
    PAYMENT_FAILED: Final[str] = 'payment_failed'
    PAYMENT_GATEWAY_ERROR: Final[str] = 'payment_gateway_error'
    INVALID_PAYMENT_METHOD: Final[str] = 'invalid_payment_method'
    PAYMENT_AMOUNT_MISMATCH: Final[str] = 'payment_amount_mismatch'

    # Coupons/Offers (4xx)
    INVALID_COUPON: Final[str] = 'invalid_coupon'
    COUPON_EXPIRED: Final[str] = 'coupon_expired'
    COUPON_NOT_APPLICABLE: Final[str] = 'coupon_not_applicable'
    COUPON_USAGE_LIMIT: Final[str] = 'coupon_usage_limit'
    MINIMUM_ORDER_VALUE: Final[str] = 'minimum_order_value'

    # Address (4xx)
    ADDRESS_NOT_FOUND: Final[str] = 'address_not_found'
    INVALID_PINCODE: Final[str] = 'invalid_pincode'

    # Rate Limiting (4xx)
    RATE_LIMIT_EXCEEDED: Final[str] = 'rate_limit_exceeded'

    # Server Errors (5xx)
    INTERNAL_ERROR: Final[str] = 'internal_error'
    SERVICE_UNAVAILABLE: Final[str] = 'service_unavailable'
    EXTERNAL_SERVICE_ERROR: Final[str] = 'external_service_error'
    MEDIA_UPLOAD_FAILED: Final[str] = 'media_upload_failed'


# ==========================================
# Order Status
# ==========================================

class OrderStatus:
    """Order lifecycle statuses"""

    PENDING: Final[str] = 'pending'                    # Order created, payment pending
    CONFIRMED: Final[str] = 'confirmed'                # Payment received, awaiting processing
    PROCESSING: Final[str] = 'processing'              # Order being prepared
    SHIPPED: Final[str] = 'shipped'                    # Order dispatched
    OUT_FOR_DELIVERY: Final[str] = 'out_for_delivery'  # With delivery agent
    DELIVERED: Final[str] = 'delivered'                # Successfully delivered
    CANCELLED: Final[str] = 'cancelled'                # Cancelled by user/admin
    REFUNDED: Final[str] = 'refunded'                  # Payment refunded
    FAILED: Final[str] = 'failed'                      # Payment/processing failed

    # All choices for Django model
    CHOICES = [
        (PENDING, 'Pending'),
        (CONFIRMED, 'Confirmed'),
        (PROCESSING, 'Processing'),
        (SHIPPED, 'Shipped'),
        (OUT_FOR_DELIVERY, 'Out for Delivery'),
        (DELIVERED, 'Delivered'),
        (CANCELLED, 'Cancelled'),
        (REFUNDED, 'Refunded'),
        (FAILED, 'Failed'),
    ]

    # Statuses that allow cancellation
    CANCELLABLE = {PENDING, CONFIRMED, PROCESSING}

    # Statuses that are final/terminal
    TERMINAL = {DELIVERED, CANCELLED, REFUNDED, FAILED}


# ==========================================
# Payment Status
# ==========================================

class PaymentStatus:
    """Payment transaction statuses"""

    PENDING: Final[str] = 'pending'          # Payment initiated
    PROCESSING: Final[str] = 'processing'    # Processing with gateway
    COMPLETED: Final[str] = 'completed'      # Payment successful
    FAILED: Final[str] = 'failed'            # Payment failed
    REFUNDED: Final[str] = 'refunded'        # Full refund issued
    PARTIALLY_REFUNDED: Final[str] = 'partially_refunded'  # Partial refund
    CANCELLED: Final[str] = 'cancelled'      # Payment cancelled

    CHOICES = [
        (PENDING, 'Pending'),
        (PROCESSING, 'Processing'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
        (REFUNDED, 'Refunded'),
        (PARTIALLY_REFUNDED, 'Partially Refunded'),
        (CANCELLED, 'Cancelled'),
    ]

    # Successful payment statuses
    SUCCESS = {COMPLETED}

    # Terminal statuses (cannot be changed)
    TERMINAL = {COMPLETED, FAILED, REFUNDED, CANCELLED}


# ==========================================
# Payment Method
# ==========================================

class PaymentMethod:
    """Supported payment methods"""

    RAZORPAY: Final[str] = 'razorpay'          # Razorpay gateway
    COD: Final[str] = 'cod'                    # Cash on Delivery
    UPI: Final[str] = 'upi'                    # UPI payment
    CARD: Final[str] = 'card'                  # Credit/Debit card
    NET_BANKING: Final[str] = 'net_banking'    # Net banking
    WALLET: Final[str] = 'wallet'              # Digital wallet

    CHOICES = [
        (RAZORPAY, 'Razorpay'),
        (COD, 'Cash on Delivery'),
        (UPI, 'UPI'),
        (CARD, 'Card'),
        (NET_BANKING, 'Net Banking'),
        (WALLET, 'Wallet'),
    ]

    # Methods that require online payment gateway
    ONLINE_METHODS = {RAZORPAY, UPI, CARD, NET_BANKING, WALLET}


# ==========================================
# Coupon Type
# ==========================================

class CouponType:
    """Types of discount coupons"""

    PERCENTAGE: Final[str] = 'percentage'      # Percentage discount (e.g., 10% off)
    FIXED_AMOUNT: Final[str] = 'fixed_amount'  # Fixed amount off (e.g., ₹100 off)
    FREE_SHIPPING: Final[str] = 'free_shipping'  # Free shipping
    BUY_X_GET_Y: Final[str] = 'buy_x_get_y'    # Buy X get Y free

    CHOICES = [
        (PERCENTAGE, 'Percentage Discount'),
        (FIXED_AMOUNT, 'Fixed Amount'),
        (FREE_SHIPPING, 'Free Shipping'),
        (BUY_X_GET_Y, 'Buy X Get Y'),
    ]


# ==========================================
# Address Type
# ==========================================

class AddressType:
    """Types of addresses"""

    SHIPPING: Final[str] = 'shipping'    # Delivery address
    BILLING: Final[str] = 'billing'      # Billing address

    CHOICES = [
        (SHIPPING, 'Shipping Address'),
        (BILLING, 'Billing Address'),
    ]


# ==========================================
# Audit Log Actions
# ==========================================

class AuditAction:
    """Actions recorded in audit logs"""

    CREATE: Final[str] = 'create'
    UPDATE: Final[str] = 'update'
    DELETE: Final[str] = 'delete'
    VIEW: Final[str] = 'view'          # For sensitive operations
    LOGIN: Final[str] = 'login'
    LOGOUT: Final[str] = 'logout'
    EXPORT: Final[str] = 'export'      # Data export operations

    CHOICES = [
        (CREATE, 'Create'),
        (UPDATE, 'Update'),
        (DELETE, 'Delete'),
        (VIEW, 'View'),
        (LOGIN, 'Login'),
        (LOGOUT, 'Logout'),
        (EXPORT, 'Export'),
    ]


# ==========================================
# Product Attribute Types
# ==========================================

class AttributeType:
    """Product attribute data types"""

    TEXT: Final[str] = 'text'          # Short text (e.g., "Color: Red")
    NUMBER: Final[str] = 'number'      # Numeric value (e.g., "Weight: 500")
    BOOLEAN: Final[str] = 'boolean'    # True/False (e.g., "Handmade: Yes")
    SELECT: Final[str] = 'select'      # Single choice (e.g., "Size: M")
    MULTISELECT: Final[str] = 'multiselect'  # Multiple choices

    CHOICES = [
        (TEXT, 'Text'),
        (NUMBER, 'Number'),
        (BOOLEAN, 'Boolean'),
        (SELECT, 'Single Select'),
        (MULTISELECT, 'Multi Select'),
    ]


# ==========================================
# Business Constants
# ==========================================

class BusinessConstants:
    """Business logic constants"""

    # Inventory
    LOW_STOCK_THRESHOLD: Final[int] = 10           # Alert when stock below this
    OUT_OF_STOCK_THRESHOLD: Final[int] = 0         # Disable purchases at 0

    # OTP & Security
    OTP_MAX_ATTEMPTS: Final[int] = 3               # Limit failed verification tries
    OTP_LOCKOUT_MINUTES: Final[int] = 30           # Lockout duration after max failures

    # Pricing
    MIN_PRODUCT_PRICE: Final[float] = 1.00         # Minimum product price (₹)
    MAX_PRODUCT_PRICE: Final[float] = 100000.00    # Maximum product price (₹)

    # Orders
    ORDER_CANCELLATION_WINDOW_HOURS: Final[int] = 24  # Cancel within 24h
    MIN_ORDER_VALUE: Final[float] = 100.00         # Minimum order value (₹)
    MAX_ORDER_ITEMS: Final[int] = 50               # Max items per order

    # Coupons
    MAX_DISCOUNT_PERCENTAGE: Final[int] = 90       # Max 90% discount
    MIN_COUPON_CODE_LENGTH: Final[int] = 4         # Min coupon code length
    MAX_COUPON_CODE_LENGTH: Final[int] = 20        # Max coupon code length

    # Pagination
    DEFAULT_PAGE_SIZE: Final[int] = 20             # Default items per page
    MAX_PAGE_SIZE: Final[int] = 100                # Maximum items per page

    # Rate Limiting
    ANONYMOUS_RATE_LIMIT: Final[str] = '100/h'     # 100 requests/hour
    AUTHENTICATED_RATE_LIMIT: Final[str] = '1000/h'  # 1000 requests/hour

    # Media
    MAX_IMAGE_SIZE_MB: Final[int] = 5              # Max image upload size
    MAX_IMAGES_PER_PRODUCT: Final[int] = 10        # Max product images

    # Currency
    CURRENCY_CODE: Final[str] = 'INR'
    CURRENCY_SYMBOL: Final[str] = '₹'
    
    # Shipping
    DEFAULT_SHIPPING_COST: Final[float] = 50.00    # ₹50 flat shipping
    FREE_SHIPPING_THRESHOLD: Final[float] = 500.00  # Free shipping above ₹500

    # Tax
    GST_RATE: Final[float] = 0.18                  # 18% GST

# ==========================================
# Indian State Codes (for Address)
# ==========================================

class IndianStates:
    """Indian state codes and names"""

    STATES = [
        ('AN', 'Andaman and Nicobar Islands'),
        ('AP', 'Andhra Pradesh'),
        ('AR', 'Arunachal Pradesh'),
        ('AS', 'Assam'),
        ('BR', 'Bihar'),
        ('CH', 'Chandigarh'),
        ('CG', 'Chhattisgarh'),
        ('DN', 'Dadra and Nagar Haveli'),
        ('DD', 'Daman and Diu'),
        ('DL', 'Delhi'),
        ('GA', 'Goa'),
        ('GJ', 'Gujarat'),
        ('HR', 'Haryana'),
        ('HP', 'Himachal Pradesh'),
        ('JK', 'Jammu and Kashmir'),
        ('JH', 'Jharkhand'),
        ('KA', 'Karnataka'),
        ('KL', 'Kerala'),
        ('LA', 'Ladakh'),
        ('LD', 'Lakshadweep'),
        ('MP', 'Madhya Pradesh'),
        ('MH', 'Maharashtra'),
        ('MN', 'Manipur'),
        ('ML', 'Meghalaya'),
        ('MZ', 'Mizoram'),
        ('NL', 'Nagaland'),
        ('OR', 'Odisha'),
        ('PY', 'Puducherry'),
        ('PB', 'Punjab'),
        ('RJ', 'Rajasthan'),
        ('SK', 'Sikkim'),
        ('TN', 'Tamil Nadu'),
        ('TS', 'Telangana'),
        ('TR', 'Tripura'),
        ('UP', 'Uttar Pradesh'),
        ('UK', 'Uttarakhand'),
        ('WB', 'West Bengal'),
    ]


# ==========================================
# Collection Type (for Product Collections)
# ==========================================

class CollectionType:
    """Product collection types"""

    FEATURED: Final[str] = 'featured'              # Featured products
    NEW_ARRIVALS: Final[str] = 'new_arrivals'      # New arrivals
    BEST_SELLERS: Final[str] = 'best_sellers'      # Best selling products
    SALE: Final[str] = 'sale'                      # On sale
    SEASONAL: Final[str] = 'seasonal'              # Seasonal collections
    ETHNIC_WEAR: Final[str] = 'ethnic_wear'        # Ethnic wear category
    CUSTOM: Final[str] = 'custom'                  # Custom collections

    CHOICES = [
        (FEATURED, 'Featured'),
        (NEW_ARRIVALS, 'New Arrivals'),
        (BEST_SELLERS, 'Best Sellers'),
        (SALE, 'Sale'),
        (SEASONAL, 'Seasonal'),
        (ETHNIC_WEAR, 'Ethnic Wear'),
        (CUSTOM, 'Custom'),
    ]


# ==========================================
# User Roles/Permissions
# ==========================================

class UserRole:
    """User role identifiers (for permission checks)"""

    CUSTOMER: Final[str] = 'customer'      # Regular customer
    STAFF: Final[str] = 'staff'            # Staff member
    ADMIN: Final[str] = 'admin'            # Administrator
    SUPER_ADMIN: Final[str] = 'super_admin'  # Super admin


# ==========================================
# API Version
# ==========================================

class APIVersion:
    """API version constants"""

    V1: Final[str] = 'v1'
    CURRENT: Final[str] = V1


# ==========================================
# Cache Keys (for Redis/caching)
# ==========================================

class CacheKey:
    """Redis cache key prefixes"""

    # Products
    PRODUCT_DETAIL: Final[str] = 'product:detail:{product_id}'
    PRODUCT_LIST: Final[str] = 'product:list:{page}:{filters_hash}'
    CATEGORY_TREE: Final[str] = 'category:tree'

    # User
    USER_PROFILE: Final[str] = 'user:profile:{user_id}'
    USER_CART: Final[str] = 'user:cart:{user_id}'

    # Cart TTL (seconds)
    CART_TTL: Final[int] = 86400  # 24 hours


# ==========================================
# Default Values
# ==========================================

class Defaults:
    """Default values used across models"""

    # Product
    DEFAULT_PRODUCT_IMAGE: Final[str] = '/static/placeholder-product.png'
    DEFAULT_CATEGORY_IMAGE: Final[str] = '/static/placeholder-category.png'

    # Shipping
    DEFAULT_SHIPPING_COST: Final[float] = 50.00    # ₹50 flat shipping
    FREE_SHIPPING_THRESHOLD: Final[float] = 500.00  # Free shipping above ₹500

    # Tax
    GST_RATE: Final[float] = 0.18                  # 18% GST


# ==========================================
# Email Events (for Notifications)
# ==========================================

class EmailEvent:
    """Email notification event types"""

    ORDER_CONFIRMATION: Final[str] = 'order_confirmation'
    ORDER_SHIPPED: Final[str] = 'order_shipped'
    ORDER_DELIVERED: Final[str] = 'order_delivered'
    RETURN_APPROVED: Final[str] = 'return_approved'
    REFUND_INITIATED: Final[str] = 'refund_initiated'
    PASSWORD_RESET: Final[str] = 'password_reset'
    WELCOME_EMAIL: Final[str] = 'welcome_email'
    ORDER_CANCELLED: Final[str] = 'order_cancelled'

    CHOICES = [
        (ORDER_CONFIRMATION, 'Order Confirmation'),
        (ORDER_SHIPPED, 'Order Shipped'),
        (ORDER_DELIVERED, 'Order Delivered'),
        (RETURN_APPROVED, 'Return Approved'),
        (REFUND_INITIATED, 'Refund Initiated'),
        (PASSWORD_RESET, 'Password Reset'),
        (WELCOME_EMAIL, 'Welcome Email'),
        (ORDER_CANCELLED, 'Order Cancelled'),
    ]


# ==========================================
# Return Status & Reasons
# ==========================================

class ReturnReason:
    """Reasons for product returns"""

    WRONG_SIZE: Final[str] = 'wrong_size'
    WRONG_ITEM: Final[str] = 'wrong_item'
    DAMAGED: Final[str] = 'damaged'
    NOT_AS_DESCRIBED: Final[str] = 'not_as_described'
    CHANGED_MIND: Final[str] = 'changed_mind'

    CHOICES = [
        (WRONG_SIZE, 'Wrong Size'),
        (WRONG_ITEM, 'Wrong Item Received'),
        (DAMAGED, 'Damaged/Defective'),
        (NOT_AS_DESCRIBED, 'Not As Described'),
        (CHANGED_MIND, 'Changed My Mind'),
    ]


class ReturnStatus:
    """Return request lifecycle statuses"""

    REQUESTED: Final[str] = 'requested'
    APPROVED: Final[str] = 'approved'
    REJECTED: Final[str] = 'rejected'
    PICKUP_SCHEDULED: Final[str] = 'pickup_scheduled'
    RECEIVED: Final[str] = 'received'
    COMPLETED: Final[str] = 'completed'
    CANCELLED: Final[str] = 'cancelled'

    CHOICES = [
        (REQUESTED, 'Return Requested'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
        (PICKUP_SCHEDULED, 'Pickup Scheduled'),
        (RECEIVED, 'Received'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled'),
    ]


# ==========================================
# Shipment Status
# ==========================================

class ShipmentStatus:
    """Shipment/delivery tracking statuses"""

    CREATED: Final[str] = 'created'
    READY_TO_SHIP: Final[str] = 'ready_to_ship'
    PICKED_UP: Final[str] = 'picked_up'
    IN_TRANSIT: Final[str] = 'in_transit'
    OUT_FOR_DELIVERY: Final[str] = 'out_for_delivery'
    DELIVERED: Final[str] = 'delivered'
    RTO_INITIATED: Final[str] = 'rto_initiated'
    RETURNED: Final[str] = 'returned'
    DELIVERY_FAILED: Final[str] = 'delivery_failed'
    CANCELLED: Final[str] = 'cancelled'

    CHOICES = [
        (CREATED, 'Created'),
        (READY_TO_SHIP, 'Ready to Ship'),
        (PICKED_UP, 'Picked Up'),
        (IN_TRANSIT, 'In Transit'),
        (OUT_FOR_DELIVERY, 'Out for Delivery'),
        (DELIVERED, 'Delivered'),
        (RTO_INITIATED, 'RTO Initiated'),
        (RETURNED, 'Returned'),
        (DELIVERY_FAILED, 'Delivery Failed'),
        (CANCELLED, 'Cancelled'),
    ]


# ==========================================
# OTP & Notifications
# ==========================================

class OTPPurpose:
    """Purpose types for OTP verification"""

    REGISTRATION: Final[str] = 'registration'
    LOGIN: Final[str] = 'login'
    PHONE_VERIFICATION: Final[str] = 'phone_verification'

    CHOICES = [
        (REGISTRATION, 'Registration'),
        (LOGIN, 'Login'),
        (PHONE_VERIFICATION, 'Phone Verification'),
    ]


class NotificationType:
    """In-app notification types"""

    ORDER_UPDATE: Final[str] = 'order_update'
    RETURN_UPDATE: Final[str] = 'return_update'
    PAYMENT_UPDATE: Final[str] = 'payment_update'
    GENERAL: Final[str] = 'general'

    CHOICES = [
        (ORDER_UPDATE, 'Order Update'),
        (RETURN_UPDATE, 'Return Update'),
        (PAYMENT_UPDATE, 'Payment Update'),
        (GENERAL, 'General'),
    ]


# ==========================================
# Regex Patterns
# ==========================================

class ValidationPattern:
    """Regex patterns for validation"""

    # International E.164 phone number (+ and up to 15 digits)
    MOBILE_NUMBER: Final[str] = r'^\+[1-9]\d{7,14}$'

    # Indian pincode (6 digits)
    PINCODE: Final[str] = r'^\d{6}$'

    # SKU format (alphanumeric with dash/underscore)
    SKU: Final[str] = r'^[A-Z0-9\-_]{4,20}$'

    # Coupon code (alphanumeric, uppercase, 4-20 chars)
    COUPON_CODE: Final[str] = r'^[A-Z0-9]{4,20}$'

    # Slug (lowercase alphanumeric with dash)
    SLUG: Final[str] = r'^[a-z0-9\-]+$'
