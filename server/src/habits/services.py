from datetime import date, timedelta
from typing import Iterable, List, Optional, Set

from django.db import IntegrityError, transaction
from django.utils import timezone

from _sdk.exceptions import ResourceNotFoundException, ValidationException
from habits.models import Habit, HabitCheckIn


def _today() -> date:
    return timezone.localdate()


def _soft_delete(instance) -> None:
    instance.deleted_at = timezone.now()
    instance.save(update_fields=["deleted_at", "updated_at"])


def compute_streak(check_in_dates: Set[date], today: Optional[date] = None) -> int:
    """
    Consecutive days ending on `today` (or yesterday if that day is not checked).
    """
    if not check_in_dates:
        return 0

    today = today or _today()
    cursor = today if today in check_in_dates else today - timedelta(days=1)
    if cursor not in check_in_dates:
        return 0

    streak = 0
    while cursor in check_in_dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


class HabitService:
    @staticmethod
    def list_habits(
        user,
        *,
        archived: str = "active",
    ) -> list[Habit]:
        """
        archived: active | archived | all
        """
        qs = Habit.objects.filter(user=user)
        if archived == "active":
            qs = qs.filter(is_archived=False)
        elif archived == "archived":
            qs = qs.filter(is_archived=True)
        elif archived != "all":
            raise ValidationException(
                message="archived must be one of: active, archived, all"
            )
        return list(qs.order_by("sort_order", "id"))

    @staticmethod
    def get_habit(user, habit_id: int) -> Habit:
        habit = Habit.objects.filter(user=user, id=habit_id).first()
        if not habit:
            raise ResourceNotFoundException(message="Habit not found")
        return habit

    @staticmethod
    def create_habit(
        user,
        *,
        name: str,
        description: str = "",
        color: str = "#7c3aed",
        sort_order: int = 0,
    ) -> Habit:
        name = name.strip()
        if not name:
            raise ValidationException(message="Habit name is required")

        return Habit.objects.create(
            user=user,
            name=name,
            description=description.strip(),
            color=color or "#7c3aed",
            sort_order=sort_order,
        )

    @staticmethod
    def update_habit(user, habit_id: int, **fields) -> Habit:
        habit = HabitService.get_habit(user, habit_id)

        if "name" in fields and fields["name"] is not None:
            name = fields["name"].strip()
            if not name:
                raise ValidationException(message="Habit name is required")
            habit.name = name

        if "description" in fields and fields["description"] is not None:
            habit.description = fields["description"].strip()

        if "color" in fields and fields["color"] is not None:
            habit.color = fields["color"] or "#7c3aed"

        if "is_archived" in fields and fields["is_archived"] is not None:
            habit.is_archived = fields["is_archived"]

        if "sort_order" in fields and fields["sort_order"] is not None:
            habit.sort_order = fields["sort_order"]

        habit.save()
        return habit

    @staticmethod
    def archive_habit(user, habit_id: int) -> Habit:
        return HabitService.update_habit(user, habit_id, is_archived=True)

    @staticmethod
    def unarchive_habit(user, habit_id: int) -> Habit:
        return HabitService.update_habit(user, habit_id, is_archived=False)

    @staticmethod
    def delete_habit(user, habit_id: int) -> None:
        habit = HabitService.get_habit(user, habit_id)
        _soft_delete(habit)

    @staticmethod
    def reorder_habits(user, ordered_ids: list[int]) -> list[Habit]:
        if not ordered_ids:
            return []

        habits = {
            habit.id: habit
            for habit in Habit.objects.filter(user=user, id__in=ordered_ids)
        }
        missing = [habit_id for habit_id in ordered_ids if habit_id not in habits]
        if missing:
            raise ResourceNotFoundException(
                message=f"Habit not found: {missing[0]}"
            )

        updated: list[Habit] = []
        for index, habit_id in enumerate(ordered_ids):
            habit = habits[habit_id]
            if habit.sort_order != index:
                habit.sort_order = index
                habit.save(update_fields=["sort_order", "updated_at"])
            updated.append(habit)
        return updated

    @staticmethod
    def check_in_dates_for_habits(
        habits: Iterable[Habit],
        *,
        since: date,
        until: Optional[date] = None,
    ) -> dict[int, Set[date]]:
        habit_ids = [h.id for h in habits]
        if not habit_ids:
            return {}

        qs = HabitCheckIn.objects.filter(
            habit_id__in=habit_ids,
            date__gte=since,
        )
        if until:
            qs = qs.filter(date__lte=until)

        rows = qs.values_list("habit_id", "date")
        by_habit: dict[int, Set[date]] = {hid: set() for hid in habit_ids}
        for habit_id, check_date in rows:
            by_habit[habit_id].add(check_date)
        return by_habit

    @staticmethod
    def list_check_ins(
        user,
        habit_id: int,
        *,
        since: Optional[date] = None,
        until: Optional[date] = None,
        limit: int = 60,
    ) -> list[HabitCheckIn]:
        habit = HabitService.get_habit(user, habit_id)
        qs = HabitCheckIn.objects.filter(habit=habit)
        if since:
            qs = qs.filter(date__gte=since)
        if until:
            qs = qs.filter(date__lte=until)
        return list(qs.order_by("-date", "-id")[: max(1, min(limit, 365))])

    @staticmethod
    def serialize_habit(
        habit: Habit,
        *,
        check_in_dates: Optional[Set[date]] = None,
        on_date: Optional[date] = None,
    ) -> dict:
        on_date = on_date or _today()
        dates = check_in_dates or set()
        if check_in_dates is None:
            since = on_date - timedelta(days=400)
            dates = {
                d
                for d in HabitCheckIn.objects.filter(
                    habit=habit, date__gte=since
                ).values_list("date", flat=True)
            }

        checked_in = on_date in dates
        return {
            "id": habit.id,
            "name": habit.name,
            "description": habit.description,
            "color": habit.color,
            "is_archived": habit.is_archived,
            "sort_order": habit.sort_order,
            "checked_in": checked_in,
            "checked_in_today": checked_in if on_date == _today() else (_today() in dates),
            "current_streak": compute_streak(dates, today=on_date),
            "created_at": habit.created_at,
            "updated_at": habit.updated_at,
        }

    @staticmethod
    def serialize_check_in(check_in: HabitCheckIn) -> dict:
        return {
            "id": check_in.id,
            "habit_id": check_in.habit_id,
            "date": check_in.date,
            "note": check_in.note,
            "created_at": check_in.created_at,
        }

    @staticmethod
    @transaction.atomic
    def check_in(
        user,
        habit_id: int,
        *,
        on_date: Optional[date] = None,
        note: str = "",
    ) -> HabitCheckIn:
        habit = HabitService.get_habit(user, habit_id)
        if habit.is_archived:
            raise ValidationException(message="Cannot check in an archived habit")

        target = on_date or _today()
        existing = HabitCheckIn.objects.filter(habit=habit, date=target).first()
        if existing:
            if note:
                existing.note = note.strip()
                existing.save(update_fields=["note", "updated_at"])
            return existing

        try:
            return HabitCheckIn.objects.create(
                habit=habit,
                date=target,
                note=note.strip(),
            )
        except IntegrityError:
            existing = HabitCheckIn.objects.filter(habit=habit, date=target).first()
            if existing:
                return existing
            raise

    @staticmethod
    def undo_check_in(
        user,
        habit_id: int,
        *,
        on_date: Optional[date] = None,
    ) -> None:
        habit = HabitService.get_habit(user, habit_id)
        target = on_date or _today()
        check_in = HabitCheckIn.objects.filter(habit=habit, date=target).first()
        if not check_in:
            raise ResourceNotFoundException(
                message="Check-in not found for that date"
            )
        _soft_delete(check_in)
