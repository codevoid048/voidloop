from django.conf import settings
from django.db import models

from _sdk.managers import SoftDeleteManager
from _sdk.models import TimestampedModel


class Habit(TimestampedModel):
    """A recurring habit owned by a user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="habits",
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, default="")
    color = models.CharField(
        max_length=7,
        blank=True,
        default="#7c3aed",
        help_text="Hex color for UI accents",
    )
    is_archived = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    objects = SoftDeleteManager()

    class Meta:
        db_table = "habits_habit"
        ordering = ["sort_order", "id"]
        indexes = [
            models.Index(fields=["user", "is_archived"], name="habit_user_arch_idx"),
            models.Index(fields=["user", "sort_order"], name="habit_user_sort_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.user_id})"


class HabitCheckIn(TimestampedModel):
    """One check-in for a habit on a calendar date."""

    habit = models.ForeignKey(
        Habit,
        on_delete=models.CASCADE,
        related_name="check_ins",
    )
    date = models.DateField()
    note = models.CharField(max_length=255, blank=True, default="")

    objects = SoftDeleteManager()

    class Meta:
        db_table = "habits_habitcheckin"
        ordering = ["-date", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["habit", "date"],
                condition=models.Q(deleted_at__isnull=True),
                name="habit_checkin_unique_active",
            ),
        ]
        indexes = [
            models.Index(fields=["habit", "date"], name="habit_checkin_date_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.habit_id} @ {self.date}"
