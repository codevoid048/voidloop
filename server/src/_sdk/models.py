"""
_sdk/models.py - Reusable base models for industrial-level e-commerce backend

This module provides:
- TimestampedModel: Auto-managed created_at, updated_at, deleted_at timestamps
- AuditableModel: Extended with user tracking (created_by, updated_by)
- AuditLog: Field-level change tracking for compliance & investigation
"""

from django.db import models
from django.conf import settings

from _sdk.constants import AuditAction


class TimestampedModel(models.Model):
    """
    Abstract base model for all entities requiring soft-delete & timestamp tracking.

    Fields:
    - created_at: Immutable creation timestamp (auto_now_add=True)
    - updated_at: Auto-updated on every save
    - deleted_at: Soft-delete marker (null until soft-deleted)

    Usage:
        class Product(TimestampedModel):
            name = models.CharField(max_length=255)
            objects = SoftDeleteManager()
    """

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Immutable timestamp when record was created",
    )
    updated_at = models.DateTimeField(
        auto_now=True, db_index=True, help_text="Auto-updated timestamp on every save"
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Soft-delete marker (null = active)",
    )

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["deleted_at"]),
        ]


class AuditableModel(TimestampedModel):
    """
    Extended TimestampedModel with user tracking for audit compliance.

    Fields:
    - created_by: User who created the record (null = system/migration)
    - updated_by: User who last updated the record

    Note: These are read-only and must be set programmatically from middleware/views.
    They track WHO made changes, while AuditLog tracks WHAT changed.

    Usage in views:
        product._audit_user = request.user
        product.save()
    """

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",  # No reverse lookup (internal only)
        editable=False,
        help_text="User who created this record",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        editable=False,
        help_text="User who last updated this record",
    )

    class Meta:
        abstract = True


class AuditLog(TimestampedModel):
    """
    Field-level change tracking for all domain models.

    Tracks WHAT changed (model, fields, before/after values) and WHO changed it (user, IP).
    Automatically populated by signal handlers on model save.

    Fields:
    - action: 'create', 'update', or 'delete'
    - changes: JSON dict of field changes: {"field_name": {"old": ..., "new": ...}}
    - user: Which user triggered the change (null = system)
    - ip_address: Request IP address for forensics

    Example change log:
    {
        "price": {"old": 100.0, "new": 150.0},
        "stock": {"old": 50, "new": 45},
        "is_active": {"old": true, "new": false}
    }

    Queries:
    - AuditLog.objects.filter(action='update').filter(content_type=ContentType.objects.get_for_model(Product))
    - AuditLog.objects.filter(user=admin_user).filter(action='delete')
    """

    # What model changed
    content_type = models.ForeignKey(
        "contenttypes.ContentType",  # Lazy reference to avoid circular import
        on_delete=models.DO_NOTHING,  # CRITICAL: Never delete audit history
        help_text="Which model was changed (e.g., Product, Order)",
    )
    object_id = models.BigIntegerField(help_text="Primary key of the changed object")
    action = models.CharField(
        max_length=10,
        choices=AuditAction.CHOICES,
        db_index=True,
        help_text="What action was performed",
    )

    # Who changed it
    user = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="User who triggered this change (null = system)",
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the request that triggered this change",
    )

    # What changed (JSON for flexibility across different model fields)
    changes = models.JSONField(
        default=dict, blank=True, help_text="JSON dict of field-level changes"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            # Query: Find all changes to a specific object
            models.Index(
                fields=["content_type", "object_id", "-created_at"],
                name="audit_log_object_idx",
            ),
            # Query: Find all changes by a specific user
            models.Index(fields=["user", "-created_at"], name="audit_log_user_idx"),
            # Query: Find all deletions in a time period
            models.Index(fields=["action", "-created_at"], name="audit_log_action_idx"),
        ]

    def __str__(self):
        return f"{self.get_action_display()} {self.content_type} #{self.object_id} at {self.created_at}"

    @property
    def object_url(self):
        """Generate admin URL to view the changed object"""
        return f"/admin/{self.content_type.app_label}/{self.content_type.model}/{self.object_id}/change/"
