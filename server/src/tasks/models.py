from django.conf import settings
from django.db import models

from _sdk.managers import SoftDeleteManager
from _sdk.models import TimestampedModel


class TaskStatus(models.TextChoices):
    TODO = "todo", "To do"
    DONE = "done", "Done"
    CANCELLED = "cancelled", "Cancelled"


class TaskPriority(models.TextChoices):
    NONE = "none", "None"
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"


class Task(TimestampedModel):
    """
    User-owned task / schedule item.

    Designed to grow:
    - due_date / due_time → daily todo list
    - starts_at / ends_at → timed schedule blocks / calendar slots
    - external_source / external_id → Google Calendar (or other) sync later
    - status / priority → workflow without schema churn
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")

    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.TODO,
        db_index=True,
    )
    priority = models.CharField(
        max_length=20,
        choices=TaskPriority.choices,
        default=TaskPriority.NONE,
    )

    # Day-bound todos (primary UX for v1)
    due_date = models.DateField(null=True, blank=True, db_index=True)
    due_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Optional time-of-day ordering within due_date",
    )

    # Timed schedule blocks (future calendar / hourly slots)
    starts_at = models.DateTimeField(null=True, blank=True, db_index=True)
    ends_at = models.DateTimeField(null=True, blank=True)

    completed_at = models.DateTimeField(null=True, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    # External calendar sync hooks (unused for now)
    external_source = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text='Provider key, e.g. "google"',
    )
    external_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Remote event/task id for sync",
    )

    objects = SoftDeleteManager()

    class Meta:
        db_table = "tasks_task"
        ordering = ["sort_order", "due_time", "id"]
        indexes = [
            models.Index(fields=["user", "due_date", "status"], name="task_user_due_status_idx"),
            models.Index(fields=["user", "status"], name="task_user_status_idx"),
            models.Index(fields=["user", "starts_at"], name="task_user_starts_idx"),
            models.Index(
                fields=["user", "external_source", "external_id"],
                name="task_user_external_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.user_id})"

    @property
    def is_done(self) -> bool:
        return self.status == TaskStatus.DONE
