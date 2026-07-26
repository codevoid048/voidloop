from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Invite, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    """

    list_display = [
        "email",
        "username",
        "name",
        "is_active",
        "is_staff",
        "created_at",
    ]

    list_filter = [
        "is_active",
        "is_staff",
        "is_superuser",
        "created_at",
    ]

    search_fields = [
        "email",
        "username",
        "name",
    ]

    ordering = ["-created_at"]

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("name", "email")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
        (
            "Audit Trail",
            {
                "fields": ("created_at", "updated_at", "deleted_at"),
                "classes": ("collapse",),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "name", "password1", "password2"),
            },
        ),
    )

    readonly_fields = [
        "created_at",
        "updated_at",
        "deleted_at",
        "date_joined",
        "last_login",
    ]


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "email",
        "created_by",
        "expires_at",
        "uses_count",
        "max_uses",
        "revoked_at",
        "created_at",
    ]
    list_filter = ["revoked_at", "expires_at", "created_at"]
    search_fields = ["email", "token"]
    readonly_fields = ["token", "uses_count", "accepted_by", "created_at", "updated_at"]
    raw_id_fields = ["created_by", "accepted_by"]
