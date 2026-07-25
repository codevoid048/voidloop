"""
_sdk/signals.py - Automatic audit logging via Django signals

This module registers signal handlers that automatically create AuditLog entries
whenever a model instance is saved or deleted.

The signal handlers track:
- WHAT changed: model name, object ID, action (create/update/delete)
- WHO changed it: user ID, IP address (via request context)
- HOW it changed: JSON dict of field-level changes

Request context (user, IP) is stored in thread-local storage via middleware
and retrieved when a signal fires.

Usage:
    # In _sdk/signals.py
    from _sdk.signals import set_audit_context

    # In middleware:
    set_audit_context(request.user if request.user.is_authenticated else None, get_ip(request))

    # Then any model save() will automatically log to AuditLog
"""

from threading import local
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from _sdk.constants import AuditAction


# Thread-local storage for request context (user, IP)
_thread_locals = local()


def set_audit_context(user, ip_address):
    """
    Store request context for audit logging.

    Called by middleware on every request to capture the authenticated user
    and request IP address. This context is later used by signal handlers
    to populate AuditLog records.

    Args:
        user: Django User instance (or None if guest)
        ip_address: Client IP address string (e.g., '192.168.1.1')

    Usage (in middleware):
        set_audit_context(
            request.user if request.user.is_authenticated else None,
            get_client_ip(request)
        )
    """
    _thread_locals.user = user
    _thread_locals.ip_address = ip_address


def get_audit_context():
    """
    Retrieve current request context for audit logging.

    Returns:
        dict: {'user': User or None, 'ip_address': str or None}

    Called by signal handlers on model save to populate AuditLog.
    """
    return {
        "user": getattr(_thread_locals, "user", None),
        "ip_address": getattr(_thread_locals, "ip_address", None),
    }


def clear_audit_context():
    """
    Clear audit context from thread-local storage.

    Called at end of request cycle to prevent context leakage between requests.
    Usually not needed (Django manages thread lifecycle), but useful in tests.

    Usage (in tests):
        from _sdk.signals import clear_audit_context

        def tearDown(self):
            clear_audit_context()
    """
    if hasattr(_thread_locals, 'user'):
        delattr(_thread_locals, 'user')
    if hasattr(_thread_locals, 'ip_address'):
        delattr(_thread_locals, 'ip_address')


@receiver(post_save)
def audit_log_on_save(sender, instance, created, **kwargs):
    """
    Signal handler: automatically log model saves to AuditLog.

    Triggers on every model.save() and creates an AuditLog entry with:
    - action: 'create' or 'update'
    - user: from request context (or None if system operation)
    - ip_address: from request context
    - changes: field-level changes (from instance._audit_changes if set)

    Exceptions:
    - Skips internal models: AuditLog, Session, ContentType
    - Skips if instance._skip_audit = True (for bulk operations or tests)

    Args:
        sender: Model class that was saved
        instance: Instance that was saved
        created: bool, True if new record, False if updated
        **kwargs: Other signal args (pre_save, raw, using, update_fields, etc.)

    Usage (automatic):
        user = User.objects.create(email='test@example.com')  # AuditLog auto-created
        product.name = 'New Name'
        product.save()  # AuditLog auto-created

    Usage (skip audit):
        user._skip_audit = True
        user.save()  # No AuditLog entry
    """
    # Skip fixture/raw saves and Django internal migration bookkeeping.
    # During `migrate`, the recorder model is saved very early and should never be audited.
    if kwargs.get("raw", False):
        return
    if sender.__module__.startswith("django.db.migrations"):
        return
    if getattr(getattr(sender, "_meta", None), "app_label", "") == "migrations":
        return

    # Skip internal Django models and avoid recursion
    SKIP_MODELS = {"AuditLog", "Session", "ContentType", "LogEntry"}
    if sender.__name__ in SKIP_MODELS:
        return

    # Allow opt-out: instance._skip_audit = True
    if getattr(instance, "_skip_audit", False):
        return

    # Late imports to avoid circular imports and AppRegistryNotReady errors
    from django.contrib.contenttypes.models import ContentType
    from _sdk.models import AuditLog

    ctx = get_audit_context()

    # Get field-level changes (set by views/serializers if needed)
    changes = getattr(instance, "_audit_changes", {})

    # Create audit log entry
    AuditLog.objects.create(
        content_type=ContentType.objects.get_for_model(sender),
        object_id=instance.pk,
        action=AuditAction.CREATE if created else AuditAction.UPDATE,
        changes=changes,
        user=ctx["user"],
        ip_address=ctx["ip_address"],
    )


# Note: We don't use pre_delete/post_delete signals because our soft-delete
# strategy updates deleted_at on the model (not a real delete). This means
# soft deletes are actually UPDATE operations, not DELETE operations,
# and they're captured by the post_save signal above.
#
# Example flow:
#   Product.objects.all().delete()
#       → Calls SoftDeleteQuerySet.delete()
#       → Updates deleted_at field
#       → Triggers post_save signal (for each affected model? No - bulk update doesn't trigger signal)
#       → Should be manually logged or handled differently
#
# For production, consider:
# 1. Using pre_delete to log before soft-delete update
# 2. Or explicitly calling AuditLog.objects.create() in views handling deletes
# 3. Or using a custom delete() method on models that logs explicitly


@receiver(post_delete)
def audit_log_on_delete(sender, instance, **kwargs):
    """Signal handler: log hard deletes to AuditLog.

    Soft deletes should remain UPDATE actions via deleted_at changes.
    This handler catches true DELETE operations that remove rows.
    """
    if kwargs.get("raw", False):
        return
    if sender.__module__.startswith("django.db.migrations"):
        return
    if getattr(getattr(sender, "_meta", None), "app_label", "") == "migrations":
        return

    skip_models = {"AuditLog", "Session", "ContentType", "LogEntry"}
    if sender.__name__ in skip_models:
        return
    if getattr(instance, "_skip_audit", False):
        return

    from django.contrib.contenttypes.models import ContentType
    from _sdk.models import AuditLog

    ctx = get_audit_context()

    AuditLog.objects.create(
        content_type=ContentType.objects.get_for_model(sender),
        object_id=instance.pk,
        action=AuditAction.DELETE,
        changes=getattr(instance, "_audit_changes", {}),
        user=ctx["user"],
        ip_address=ctx["ip_address"],
    )
