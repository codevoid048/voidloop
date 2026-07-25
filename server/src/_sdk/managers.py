"""
_sdk/managers.py - Custom QuerySet and Manager for soft-delete support

Provides SoftDeleteManager and SoftDeleteQuerySet to handle soft-delete operations
across all models that inherit from TimestampedModel.

Usage:
    class Product(TimestampedModel):
        objects = SoftDeleteManager()  # Default: returns only active (non-deleted) records
        all_objects = SoftDeleteManager.from_queryset(SoftDeleteQuerySet)()

    # Queries:
    Product.objects.all()                    # Only active (deleted_at IS NULL)
    Product.objects.deleted()                # Only soft-deleted
    Product.all_objects.all_with_deleted()  # All records including deleted
    Product.objects.filter(name='xyz')       # Active only (filters automatically)
"""

from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    """
    Custom QuerySet that enables soft-delete operations.

    Methods:
    - delete(): Soft-delete (updates deleted_at) instead of hard-delete
    - active(): Filter to only active records (deleted_at IS NULL)
    - deleted(): Filter to only soft-deleted records (deleted_at IS NOT NULL)
    """

    def delete(self):
        """
        Soft-delete all records in this queryset.
        Updates deleted_at timestamp instead of removing from database.

        Returns:
            tuple: (number_of_rows_updated, {})

        Examples:
            Product.objects.filter(name='old').delete()  # Soft-delete
            order.delete()  # Soft-deletes via model's delete() override
        """
        return self.update(deleted_at=timezone.now())

    def active(self):
        """
        Filter to only active (non-soft-deleted) records.

        Returns:
            QuerySet: Filtered to deleted_at IS NULL

        Examples:
            Product.objects.active()  # Automatically applied by SoftDeleteManager
            Product.all_objects.active()  # Explicit filter on unrestricted manager
        """
        return self.filter(deleted_at__isnull=True)

    def deleted(self):
        """
        Filter to only soft-deleted records (for recovery or inspection).

        Returns:
            QuerySet: Filtered to deleted_at IS NOT NULL

        Examples:
            Product.objects.deleted()  # Soft-deleted products
            Product.all_objects.filter(created_at__gte=...).deleted()  # Chain filters
        """
        return self.exclude(deleted_at__isnull=True)


class SoftDeleteManager(models.Manager):
    """
    Custom Manager that enforces soft-delete by default.

    The default manager (objects) returns only ACTIVE records.
    Use all_objects manager to access deleted records.

    Usage:
        class Product(TimestampedModel):
            objects = SoftDeleteManager()  # Default: active only
            all_objects = SoftDeleteManager.from_queryset(SoftDeleteQuerySet)()

    Key behaviors:
    - Product.objects.all() → only non-deleted products
    - Product.objects.deleted() → only soft-deleted products
    - Product.all_objects.all() → all products (including deleted)
    """

    def get_queryset(self):
        """
        Override default queryset to filter active records.
        This ensures every query through the default manager excludes deleted items.
        """
        return SoftDeleteQuerySet(self.model, using=self._db).active()

    def deleted(self):
        """
        Shortcut to get soft-deleted records.

        Returns:
            QuerySet: Only deleted_at IS NOT NULL

        Examples:
            Product.objects.deleted()
            User.objects.deleted().filter(created_at__year=2024)
        """
        return self.get_queryset().deleted()

    def all_with_deleted(self):
        """
        Access the unrestricted queryset (including deleted).

        Equivalent to:
            Product.all_objects.all()

        Returns:
            QuerySet: All records regardless of deleted_at

        Examples:
            Product.objects.all_with_deleted()  # Access via default manager
            Product.all_objects.all()  # Via explicit all_objects manager
        """
        return SoftDeleteQuerySet(self.model, using=self._db)

    @classmethod
    def from_queryset(cls, queryset_class, class_name=None):
        """
        Factory method to create a manager from a custom queryset class.

        This is used to create the all_objects manager with full queryset functionality.

        Usage:
            all_objects = SoftDeleteManager.from_queryset(SoftDeleteQuerySet)

        Returns:
            Manager class (not an instance) that can be used on a model
        """
        # Call parent implementation to handle class creation
        # This returns a new manager CLASS that combines our manager with the queryset
        return super().from_queryset(queryset_class)
