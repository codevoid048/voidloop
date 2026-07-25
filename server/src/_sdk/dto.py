"""
Data Transfer Objects (DTOs) for Tracker Backend

Internal data structures for service layer communication. These are NOT exposed
to the API and are used for type-safe data exchange between services.

DTOs are lightweight (dataclasses) and focused on internal operations,
while Pydantic schemas handle external API contracts.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum


# ============================================================================
# Order & Commerce DTOs
# ============================================================================


@dataclass
class OrderCalculationDTO:
    """
    Result of order total calculation.

    Used by OrderService.calculate_totals() to return
    comprehensive pricing breakdown.
    """

    subtotal: Decimal
    discount: Decimal
    shipping: Decimal
    tax: Decimal
    total: Decimal
    coupon_code: Optional[str] = None
    coupon_discount: Decimal = Decimal("0.00")
    loyalty_discount: Decimal = Decimal("0.00")

    @property
    def total_discount(self) -> Decimal:
        """Total discount applied (including coupon and loyalty)."""
        return self.discount + self.coupon_discount + self.loyalty_discount

    @property
    def effective_total(self) -> Decimal:
        """Final payable amount after all calculations."""
        return max(Decimal("0.00"), self.total)


@dataclass
class OrderItemCalculationDTO:
    """Individual order item calculation details."""

    product_id: int
    variant_id: Optional[int]
    quantity: int
    unit_price: Decimal
    discount_per_unit: Decimal
    subtotal: Decimal  # (unit_price - discount_per_unit) * quantity
    tax_amount: Decimal
    total: Decimal  # subtotal + tax_amount


@dataclass
class InventoryCheckDTO:
    """
    Inventory availability check result.

    Used by InventoryService to return stock availability
    and reservation details for products.
    """

    product_id: int
    variant_id: Optional[int]
    available_qty: int
    reserved_qty: int
    requested_qty: int
    is_available: bool
    backorder_allowed: bool = False
    expected_restock_date: Optional[datetime] = None

    @property
    def shortfall(self) -> int:
        """Quantity short if not enough stock."""
        return max(0, self.requested_qty - self.available_qty)


@dataclass
class CartCalculationDTO:
    """Shopping cart calculation summary."""

    items: List[OrderItemCalculationDTO] = field(default_factory=list)
    subtotal: Decimal = Decimal("0.00")
    total_discount: Decimal = Decimal("0.00")
    shipping_estimate: Decimal = Decimal("0.00")
    tax_estimate: Decimal = Decimal("0.00")
    estimated_total: Decimal = Decimal("0.00")
    items_count: int = 0

    @property
    def total_weight(self) -> Decimal:
        """Total weight of items in cart (for shipping calculation)."""
        # Would need product weight data to calculate
        return Decimal("0.00")


# ============================================================================
# Payment DTOs
# ============================================================================


class PaymentStatus(Enum):
    """Payment status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


@dataclass
class PaymentIntentDTO:
    """
    Payment intent creation data.

    Used to communicate payment setup between
    OrderService and PaymentService.
    """

    amount: Decimal
    currency: str
    order_id: int
    user_id: int
    payment_method: str  # 'razorpay', 'stripe', 'upi', etc.
    metadata: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None
    callback_url: Optional[str] = None

    @property
    def amount_in_paise(self) -> int:
        """Amount in smallest currency unit (paise for INR)."""
        return int(self.amount * 100)


@dataclass
class PaymentResponseDTO:
    """
    Payment gateway response data.

    Standardized response from different payment gateways
    processed by PaymentService.
    """

    payment_id: str
    gateway_payment_id: str
    status: PaymentStatus
    amount: Decimal
    currency: str
    gateway_response: Dict[str, Any] = field(default_factory=dict)
    failure_reason: Optional[str] = None
    processed_at: Optional[datetime] = None


@dataclass
class RefundRequestDTO:
    """
    Refund request data.

    Used by RefundService to process refund requests
    across different payment gateways.
    """

    payment_id: int
    amount: Decimal
    reason: str
    requested_by: int
    order_id: Optional[int] = None
    is_partial: bool = False
    notes: Optional[str] = None


@dataclass
class RefundResponseDTO:
    """Refund processing response."""

    refund_id: str
    gateway_refund_id: str
    status: str
    amount: Decimal
    processed_at: Optional[datetime] = None
    gateway_response: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Shipping & Logistics DTOs
# ============================================================================


class ShipmentStatus(Enum):
    """Shipment status enumeration."""

    CREATED = "created"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED_DELIVERY = "failed_delivery"
    RETURNED = "returned"
    CANCELLED = "cancelled"


@dataclass
class ShipmentTrackingDTO:
    """
    Shipment tracking update.

    Used by ShippingService to standardize tracking
    data from different logistics partners.
    """

    status: ShipmentStatus
    location: Optional[str]
    timestamp: datetime
    message: str
    tracking_url: Optional[str] = None
    estimated_delivery: Optional[datetime] = None

    @property
    def is_delivered(self) -> bool:
        """Check if shipment is delivered."""
        return self.status == ShipmentStatus.DELIVERED


@dataclass
class ShippingCalculationDTO:
    """
    Shipping cost calculation result.

    Used by ShippingService to return shipping options
    and costs for different carriers.
    """

    carrier: str
    service_type: str  # 'standard', 'express', 'overnight'
    cost: Decimal
    estimated_days: int
    tracking_available: bool = True
    insurance_available: bool = False
    cod_available: bool = False

    @property
    def estimated_delivery_range(self) -> str:
        """Human-readable delivery estimate."""
        if self.estimated_days == 1:
            return "Next day"
        elif self.estimated_days <= 3:
            return f"{self.estimated_days} days"
        else:
            return f"{self.estimated_days-1}-{self.estimated_days+1} days"


@dataclass
class AddressValidationDTO:
    """Address validation result."""

    is_valid: bool
    normalized_address: Dict[str, str] = field(default_factory=dict)
    confidence_score: float = 0.0
    serviceable: bool = True
    cod_available: bool = False
    estimated_delivery_days: int = 7
    validation_errors: List[str] = field(default_factory=list)


# ============================================================================
# Notification DTOs
# ============================================================================


class NotificationType(Enum):
    """Notification type enumeration."""

    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WHATSAPP = "whatsapp"


class NotificationPriority(Enum):
    """Notification priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class NotificationDTO:
    """
    Notification dispatch data.

    Used by NotificationService to send notifications
    across different channels.
    """

    recipient: str  # email, phone, user_id
    type: NotificationType
    template: str
    context: Dict[str, Any] = field(default_factory=dict)
    priority: NotificationPriority = NotificationPriority.NORMAL
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    @property
    def is_immediate(self) -> bool:
        """Check if notification should be sent immediately."""
        return self.scheduled_at is None or self.scheduled_at <= datetime.now()


@dataclass
class NotificationResponseDTO:
    """Notification delivery response."""

    notification_id: str
    status: str  # 'sent', 'failed', 'queued'
    provider: str  # 'sendgrid', 'twilio', 'fcm'
    provider_message_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    failure_reason: Optional[str] = None


# ============================================================================
# Analytics & Reporting DTOs
# ============================================================================


@dataclass
class SalesAnalyticsDTO:
    """Sales analytics data for reporting."""

    period_start: datetime
    period_end: datetime
    total_orders: int
    total_revenue: Decimal
    average_order_value: Decimal
    unique_customers: int
    top_products: List[Dict[str, Any]] = field(default_factory=list)
    revenue_by_category: Dict[str, Decimal] = field(default_factory=dict)

    @property
    def conversion_rate(self) -> float:
        """Calculate conversion rate if we have visitor data."""
        # Would need visitor/session data to calculate
        return 0.0


@dataclass
class ProductPerformanceDTO:
    """Individual product performance metrics."""

    product_id: int
    total_orders: int
    total_quantity: int
    total_revenue: Decimal
    average_rating: float
    return_rate: float
    inventory_turnover: float

    @property
    def revenue_per_unit(self) -> Decimal:
        """Revenue per unit sold."""
        if self.total_quantity > 0:
            return self.total_revenue / self.total_quantity
        return Decimal("0.00")


# ============================================================================
# User & Authentication DTOs
# ============================================================================


@dataclass
class UserRegistrationDTO:
    """User registration data from OAuth/social providers."""

    email: str
    mobile: Optional[str]
    first_name: str
    last_name: str
    provider: str  # 'google', 'facebook', 'apple'
    provider_id: str
    avatar_url: Optional[str] = None
    email_verified: bool = False
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserProfileUpdateDTO:
    """User profile update data."""

    user_id: int
    updated_by: int
    update_reason: str
    updates: Dict[str, Any] = field(default_factory=dict)
    requires_verification: bool = False

    @property
    def has_sensitive_changes(self) -> bool:
        """Check if update contains sensitive fields."""
        sensitive_fields = {"email", "mobile", "password"}
        return any(field in self.updates for field in sensitive_fields)


# ============================================================================
# Search & Catalog DTOs
# ============================================================================


@dataclass
class SearchResultDTO:
    """Search results with metadata."""

    query: str
    total_results: int
    products: List[Dict[str, Any]] = field(default_factory=list)
    categories: List[Dict[str, Any]] = field(default_factory=list)
    filters_applied: Dict[str, Any] = field(default_factory=dict)
    search_time_ms: float = 0.0
    suggestions: List[str] = field(default_factory=list)

    @property
    def has_results(self) -> bool:
        """Check if search returned any results."""
        return self.total_results > 0


@dataclass
class ProductRecommendationDTO:
    """Product recommendation data."""

    user_id: Optional[int]
    product_ids: List[int]
    recommendation_type: str  # 'similar', 'complementary', 'trending'
    confidence_scores: List[float] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)

    @property
    def top_recommendation(self) -> Optional[int]:
        """Get the top recommended product ID."""
        if self.product_ids:
            return self.product_ids[0]
        return None


# ============================================================================
# Utility Functions for DTOs
# ============================================================================


def dto_to_dict(dto_instance: Any, exclude_none: bool = True) -> Dict[str, Any]:
    """
    Convert dataclass DTO to dictionary.

    Args:
        dto_instance: Any dataclass instance
        exclude_none: Whether to exclude None values

    Returns:
        Dictionary representation of the DTO
    """
    from dataclasses import asdict

    result = asdict(dto_instance)

    if exclude_none:
        result = {k: v for k, v in result.items() if v is not None}

    return result


def dict_to_dto(data: Dict[str, Any], dto_class: type) -> Any:
    """
    Create DTO instance from dictionary.

    Args:
        data: Dictionary with DTO data
        dto_class: DTO class to instantiate

    Returns:
        DTO instance
    """
    # Filter data to only include fields that exist in the DTO
    from dataclasses import fields

    field_names = {f.name for f in fields(dto_class)}
    filtered_data = {k: v for k, v in data.items() if k in field_names}

    return dto_class(**filtered_data)


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Order & Commerce
    "OrderCalculationDTO",
    "OrderItemCalculationDTO",
    "InventoryCheckDTO",
    "CartCalculationDTO",
    # Payments
    "PaymentStatus",
    "PaymentIntentDTO",
    "PaymentResponseDTO",
    "RefundRequestDTO",
    "RefundResponseDTO",
    # Shipping
    "ShipmentStatus",
    "ShipmentTrackingDTO",
    "ShippingCalculationDTO",
    "AddressValidationDTO",
    # Notifications
    "NotificationType",
    "NotificationPriority",
    "NotificationDTO",
    "NotificationResponseDTO",
    # Analytics
    "SalesAnalyticsDTO",
    "ProductPerformanceDTO",
    # Users
    "UserRegistrationDTO",
    "UserProfileUpdateDTO",
    # Search & Catalog
    "SearchResultDTO",
    "ProductRecommendationDTO",
    # Utilities
    "dto_to_dict",
    "dict_to_dto",
]
