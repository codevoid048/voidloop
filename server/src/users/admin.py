from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


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
