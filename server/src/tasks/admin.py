from django.contrib import admin

from tasks.models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "status",
        "priority",
        "due_date",
        "starts_at",
        "created_at",
    )
    list_filter = ("status", "priority", "due_date", "external_source")
    search_fields = ("title", "description", "user__email", "user__username", "external_id")
    readonly_fields = ("created_at", "updated_at", "deleted_at", "completed_at")
    ordering = ("-created_at",)
