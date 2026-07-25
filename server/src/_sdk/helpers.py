"""
Business-Specific Utilities for Tracker Backend

Contains business-specific helper functions that complement Django's built-in utilities.
For common Django operations, use Django's built-in functions instead.
"""

from typing import Optional, Dict, Any, Union
from decimal import Decimal
from datetime import datetime
from django.utils.text import slugify as django_slugify
from django.utils import timezone
from django.core.cache import cache
import re


# ============================================================================
# Business-Specific Formatting
# ============================================================================


def format_currency(amount: Union[Decimal, int, float], symbol: str = "₹") -> str:
    """
    Format currency amount for Indian market display.

    Args:
        amount: Amount to format
        symbol: Currency symbol (default: ₹)

    Returns:
        Formatted currency string (e.g., "₹1,234.56")
    """
    if amount is None:
        return f"{symbol}0.00"

    decimal_amount = Decimal(str(amount))
    return f"{symbol}{decimal_amount:,.2f}"


def format_phone_display(phone: str, country: str = "IN") -> str:
    """
    Format phone number for Indian market display.

    Args:
        phone: Phone number to format
        country: Country code for formatting (default: IN)

    Returns:
        Formatted phone number (e.g., "+91 98765 43210")
    """
    if not phone:
        return ""

    # Remove any existing formatting
    clean_phone = re.sub(r"[\s\-\(\)]", "", phone)

    if country == "IN":
        # Handle Indian numbers
        if clean_phone.startswith("+91"):
            number = clean_phone[3:]
            return f"+91 {number[:5]} {number[5:]}"
        elif clean_phone.startswith("91") and len(clean_phone) == 12:
            number = clean_phone[2:]
            return f"+91 {number[:5]} {number[5:]}"
        elif len(clean_phone) == 10:
            return f"+91 {clean_phone[:5]} {clean_phone[5:]}"

    return phone  # Return original if can't format


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in bytes to human readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Human readable size (e.g., "1.5 MB", "256 KB")
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    size_bytes = float(size_bytes)
    i = 0

    while size_bytes >= 1024.0 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    if i == 0:
        return f"{int(size_bytes)} {size_names[i]}"
    else:
        return f"{size_bytes:.1f} {size_names[i]}"


# ============================================================================
# Security & Data Protection
# ============================================================================


def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """
    Mask sensitive data for logging/display.

    Args:
        data: Sensitive data to mask
        mask_char: Character to use for masking
        visible_chars: Number of characters to leave visible at end

    Returns:
        Masked data string
    """
    if not data or len(data) <= visible_chars:
        return mask_char * len(data) if data else ""

    mask_length = len(data) - visible_chars
    masked_part = mask_char * mask_length
    visible_part = data[-visible_chars:]

    return f"{masked_part}{visible_part}"


def normalize_search_query(query: str) -> str:
    """
    Normalize search query for consistent searching across the platform.

    Args:
        query: Raw search query

    Returns:
        Normalized search query
    """
    if not query:
        return ""

    # Remove extra whitespace and convert to lowercase
    normalized = " ".join(query.strip().lower().split())

    # Remove special characters except spaces and basic punctuation
    normalized = re.sub(r"[^\w\s\-\.]", "", normalized)

    return normalized


# ============================================================================
# Business Logic Utilities
# ============================================================================


def generate_unique_slug(
    text: str, model_class: Any, field: str = "slug", max_length: int = 50
) -> str:
    """
    Generate unique slug for model field using Django's slugify.

    Args:
        text: Text to slugify
        model_class: Django model class
        field: Field name to check for uniqueness
        max_length: Maximum slug length

    Returns:
        Unique slug string
    """
    base_slug = django_slugify(text)[:max_length]
    slug = base_slug
    counter = 1

    # Check if slug exists using Django ORM
    while model_class.objects.filter(**{field: slug}).exists():
        # Append counter to make unique
        suffix = f"-{counter}"
        available_length = max_length - len(suffix)
        slug = f"{base_slug[:available_length]}{suffix}"
        counter += 1

        # Safety check to prevent infinite loop
        if counter > 1000:
            # Add timestamp as fallback
            import time
            timestamp = str(int(time.time()))[-4:]
            slug = f"{base_slug[:max_length-5]}-{timestamp}"
            break

    return slug


def get_domain_from_email(email: str) -> Optional[str]:
    """Extract domain from email address for business logic."""
    if "@" in email:
        return email.split("@")[1].lower()
    return None


# ============================================================================
# Simple Cache Helpers (Use Django's cache framework directly for complex cases)
# ============================================================================


def cache_key_for_user(prefix: str, user_id: int, *args: Any) -> str:
    """Generate cache key for user-specific data."""
    parts = [prefix, f"user_{user_id}"]
    parts.extend(str(arg) for arg in args)
    return ":".join(parts)


def cache_key_for_model(prefix: str, instance: Any) -> str:
    """Generate cache key for model instance."""
    return f"{prefix}:{instance.__class__.__name__}_{instance.pk}"


# Example usage patterns:
"""
# ✅ RECOMMENDED - Use Django built-ins where available

# Instead of custom get_client_ip()
def get_client_ip(request):
    return request.META.get('HTTP_X_FORWARDED_FOR',
                           request.META.get('REMOTE_ADDR'))

# Instead of custom pagination parsing
@router.get("/users/", response=List[UserSchema])
@paginate(PageNumberPagination)  # Django Ninja handles this
def list_users(request):
    return User.objects.all()

# Instead of custom timestamp formatting
from django.utils.timesince import timesince
relative_time = timesince(some_datetime)

# Instead of custom HTML cleaning
from bleach import clean
clean_html = clean(html, tags=['p', 'br'], strip=True)

# Use Django's built-in caching
from django.core.cache import cache
from django.views.decorators.cache import cache_page

# Simple cache usage
result = cache.get_or_set('key', lambda: expensive_operation(), 300)
"""
