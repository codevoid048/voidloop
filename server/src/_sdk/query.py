"""
Query Optimization Patterns for Tracker Backend

IMPORTANT: Django ORM is already very powerful for most use cases.
Use Django ORM directly instead of custom utilities where possible.

This module provides only essential patterns that complement Django ORM,
not replace it. For complex queries, use Django's Q objects, select_related,
prefetch_related, and other built-in features directly.
"""

from typing import List
from django.db import models
from django.db.models import QuerySet
from django.core.exceptions import FieldError
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Simple Optimization Mixin (Optional Pattern)
# ============================================================================


class OptimizationHintsMixin:
    """
    Optional mixin for Django models to document common optimization patterns.

    This is just a documentation pattern - you can still use Django ORM directly:

    # ✅ DIRECT DJANGO ORM (Recommended)
    products = Product.objects.select_related('category').prefetch_related('images')

    # ✅ USING MIXIN (Optional)
    products = Product.get_optimized_queryset()

    Usage:
        class Product(TimestampedModel, OptimizationHintsMixin):
            _select_related = ['category', 'brand']
            _prefetch_related = ['images', 'variants']
    """

    _select_related: List[str] = []
    _prefetch_related: List[str] = []

    @classmethod
    def get_optimized_queryset(cls, queryset: QuerySet = None) -> QuerySet:
        """
        Get queryset with documented optimization hints applied.

        Note: This is just a convenience method. You can achieve the same with:
        queryset.select_related(*fields).prefetch_related(*fields)
        """
        if queryset is None:
            queryset = cls.objects.all()

        # Apply select_related hints if defined
        if hasattr(cls, "_select_related") and cls._select_related:
            try:
                queryset = queryset.select_related(*cls._select_related)
            except FieldError as e:
                logger.warning(f"Invalid select_related for {cls.__name__}: {e}")

        # Apply prefetch_related hints if defined
        if hasattr(cls, "_prefetch_related") and cls._prefetch_related:
            try:
                queryset = queryset.prefetch_related(*cls._prefetch_related)
            except FieldError as e:
                logger.warning(f"Invalid prefetch_related for {cls.__name__}: {e}")

        return queryset


# ============================================================================
# Testing Utility (Useful for N+1 Detection)
# ============================================================================


class QueryCountContext:
    """
    Context manager for tracking query count during testing.

    Useful for ensuring your optimizations work correctly.

    Usage:
        def test_no_n_plus_one():
            with QueryCountContext(max_queries=2):
                products = Product.objects.select_related('category')[:10]
                for product in products:
                    print(product.category.name)  # Should not trigger extra queries
    """

    def __init__(self, max_queries: int = None):
        self.max_queries = max_queries
        self.initial_count = 0
        self.query_count = 0

    def __enter__(self):
        from django.db import connection
        self.initial_count = len(connection.queries)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        from django.db import connection
        self.query_count = len(connection.queries) - self.initial_count

        if self.max_queries is not None and self.query_count > self.max_queries:
            raise AssertionError(
                f"Too many queries: {self.query_count} (max: {self.max_queries})"
            )


# Migration guide - Use Django ORM directly:
"""
# ❌ REMOVED - Use Django ORM directly instead

# Instead of custom apply_filters():
queryset = queryset.filter(**filter_dict)

# Instead of custom apply_search():
from django.db.models import Q
queryset = queryset.filter(
    Q(name__icontains=query) | Q(description__icontains=query)
)

# Instead of custom apply_ordering():
queryset = queryset.order_by('-created_at')

# Instead of custom build_range_filter():
from django.db.models import Q
queryset = queryset.filter(Q(price__gte=min_price) & Q(price__lte=max_price))

# Instead of custom build_choice_filter():
queryset = queryset.filter(category__in=categories)

# Instead of custom build_date_range_filter():
queryset = queryset.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)

# ✅ PREFERRED - Django ORM Patterns

# Prevent N+1 queries with select_related (ForeignKey, OneToOne)
users_with_profiles = User.objects.select_related('profile')

# Prevent N+1 queries with prefetch_related (ManyToMany, reverse FK)
users_with_orders = User.objects.prefetch_related('orders')

# Combine both for complex relationships
products = Product.objects.select_related('category').prefetch_related('images', 'reviews__user')

# Use only() to fetch specific fields
products = Product.objects.only('name', 'price', 'category__name').select_related('category')

# Use defer() to exclude heavy fields
products = Product.objects.defer('description', 'long_text_field')

# Complex filtering with Q objects
from django.db.models import Q
products = Product.objects.filter(
    Q(name__icontains='phone') | Q(category__name='Electronics'),
    price__gte=100,
    is_active=True
)

# Aggregation and annotation
from django.db.models import Count, Avg
categories = Category.objects.annotate(
    product_count=Count('products'),
    avg_price=Avg('products__price')
)

# ✅ PAGINATION - Use Django Ninja built-in pagination
from ninja.pagination import paginate, PageNumberPagination

@api.get("/products/", response=List[ProductSchema])
@paginate(PageNumberPagination)
def list_products(request):
    return Product.objects.select_related('category')

# ✅ TESTING N+1 - Use Django's assertNumQueries
from django.test import TestCase
from django.test.utils import override_settings

class QueryOptimizationTest(TestCase):
    def test_no_n_plus_one(self):
        with self.assertNumQueries(2):  # Django's built-in assertion
            products = Product.objects.select_related('category')[:10]
            categories = [p.category.name for p in products]
"""


__all__ = [
    "OptimizationHintsMixin",
    "QueryCountContext"
]
