from django.conf import settings
from django.db import models

from _sdk.managers import SoftDeleteManager
from _sdk.models import TimestampedModel


class NoteFolder(TimestampedModel):
    """
    Optional grouping for notes.

    `parent` is reserved for nested folders later; v1 can stay flat.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="note_folders",
    )
    name = models.CharField(max_length=120)
    color = models.CharField(max_length=7, blank=True, default="#7c3aed")
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )
    sort_order = models.PositiveIntegerField(default=0)

    objects = SoftDeleteManager()

    class Meta:
        db_table = "notes_notefolder"
        ordering = ["sort_order", "id"]
        indexes = [
            models.Index(fields=["user", "sort_order"], name="note_folder_user_sort_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.user_id})"


class Note(TimestampedModel):
    """
    Markdown note owned by a user.

    Future-friendly fields:
    - folder for organization
    - is_pinned / is_archived for workflows
    - content as plain Markdown (Monaco / code blocks later are FE-only)
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notes",
    )
    folder = models.ForeignKey(
        NoteFolder,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="notes",
    )
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True, default="")
    is_pinned = models.BooleanField(default=False, db_index=True)
    is_archived = models.BooleanField(default=False, db_index=True)
    sort_order = models.PositiveIntegerField(default=0)

    objects = SoftDeleteManager()

    class Meta:
        db_table = "notes_note"
        ordering = ["-is_pinned", "sort_order", "-updated_at", "id"]
        indexes = [
            models.Index(
                fields=["user", "is_archived", "is_pinned"],
                name="note_user_arch_pin_idx",
            ),
            models.Index(fields=["user", "folder"], name="note_user_folder_idx"),
            models.Index(fields=["user", "updated_at"], name="note_user_updated_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.user_id})"
