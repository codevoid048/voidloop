from django.contrib import admin

from notes.models import Note, NoteFolder


@admin.register(NoteFolder)
class NoteFolderAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "parent", "sort_order", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "user__email", "user__username")
    readonly_fields = ("created_at", "updated_at", "deleted_at")


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "folder",
        "is_pinned",
        "is_archived",
        "updated_at",
    )
    list_filter = ("is_pinned", "is_archived", "updated_at")
    search_fields = ("title", "content", "user__email", "user__username")
    readonly_fields = ("created_at", "updated_at", "deleted_at")
