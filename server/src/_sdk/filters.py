"""
Simplified Filter Utilities for Tracker Backend

Provides common filtering patterns that complement Django ORM.
For complex filtering, use django-filter package instead of custom implementations.
"""

from typing import Any, Dict, Optional
from django.db.models import QuerySet, Q
from django.http import HttpRequest


def apply_text_search(queryset: QuerySet, search_fields: list[str], query: str) -> QuerySet:
    """
    Apply text search across multiple fields using Django ORM.

    Args:
        queryset: Django QuerySet to filter
        search_fields: List of field names to search in
        query: Search query string

    Returns:
        Filtered QuerySet

    Example:
        # Instead of complex custom filtering
        filtered_users = apply_text_search(
            User.objects.all(),
            ['email', 'first_name', 'last_name'],
            'john'
        )
    """
    if not query or not search_fields:
        return queryset

    q_objects = Q()
    for field in search_fields:
        q_objects |= Q(**{f"{field}__icontains": query.strip()})

    return queryset.filter(q_objects)


def parse_boolean(value: Any) -> Optional[bool]:
    """
    Parse boolean value from request parameter.

    Args:
        value: Value to parse

    Returns:
        Boolean value or None if invalid

    Example:
        is_active = parse_boolean(request.GET.get('is_active'))
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)
    """
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.lower() in ['true', '1', 'yes', 'on']

    return None


def parse_comma_separated(value: str) -> list[str]:
    """
    Parse comma-separated string into list.

    Args:
        value: Comma-separated string

    Returns:
        List of trimmed strings

    Example:
        statuses = parse_comma_separated(request.GET.get('status'))
        queryset = queryset.filter(status__in=statuses)
    """
    if not value:
        return []

    return [item.strip() for item in value.split(',') if item.strip()]


class CommonFilters:
    """
    Common filtering patterns using Django ORM.
    Prefer these simple patterns over custom filtering systems.
    """

    @staticmethod
    def apply_status_filter(queryset: QuerySet, status: Optional[str]) -> QuerySet:
        """Apply status filter using Django ORM."""
        if status:
            if ',' in status:
                # Multiple statuses
                statuses = parse_comma_separated(status)
                return queryset.filter(status__in=statuses)
            else:
                return queryset.filter(status=status)
        return queryset

    @staticmethod
    def apply_active_filter(queryset: QuerySet, is_active: Optional[str]) -> QuerySet:
        """Apply active/inactive filter using Django ORM."""
        active_value = parse_boolean(is_active)
        if active_value is not None:
            return queryset.filter(is_active=active_value)
        return queryset

    @staticmethod
    def apply_date_range_filter(
        queryset: QuerySet,
        field_name: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> QuerySet:
        """Apply date range filter using Django ORM."""
        if date_from:
            queryset = queryset.filter(**{f"{field_name}__gte": date_from})
        if date_to:
            queryset = queryset.filter(**{f"{field_name}__lte": date_to})
        return queryset


# Example usage patterns:
"""
# ✅ RECOMMENDED - Use Django ORM directly
@router.get("/users/", response=List[UserListSchema])
def list_users(
    request,
    search: Optional[str] = None,
    is_active: Optional[str] = None,
    status: Optional[str] = None
):
    queryset = User.objects.select_related('profile')

    # Text search
    if search:
        queryset = apply_text_search(queryset, ['email', 'first_name'], search)

    # Status filter
    if status:
        queryset = CommonFilters.apply_status_filter(queryset, status)

    # Active filter
    if is_active:
        queryset = CommonFilters.apply_active_filter(queryset, is_active)

    return queryset

# ✅ EVEN BETTER - Use django-filter for complex cases
from django_filters import rest_framework as filters

class UserFilter(filters.FilterSet):
    search = filters.CharFilter(method='filter_search')
    status = filters.ChoiceFilter(choices=USER_STATUS_CHOICES)
    created_after = filters.DateFilter(field_name='created_at', lookup_expr='gte')

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(email__icontains=value) |
            Q(first_name__icontains=value)
        )

    class Meta:
        model = User
        fields = ['is_active', 'is_staff']
"""
