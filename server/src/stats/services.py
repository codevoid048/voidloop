from datetime import date, timedelta
from typing import Optional

from django.db.models import Q
from django.utils import timezone

from _sdk.exceptions import ValidationException
from habits.models import HabitCheckIn
from habits.services import HabitService, compute_streak
from tasks.models import Task, TaskStatus

MAX_RANGE_DAYS = 90


def _today() -> date:
    return timezone.localdate()


def _daterange(since: date, until: date) -> list[date]:
    days: list[date] = []
    cursor = since
    while cursor <= until:
        days.append(cursor)
        cursor += timedelta(days=1)
    return days


class StatsService:
    @staticmethod
    def resolve_range(
        *,
        since: Optional[date] = None,
        until: Optional[date] = None,
    ) -> tuple[date, date]:
        until_date = until or _today()
        since_date = since or (until_date - timedelta(days=29))

        if since_date > until_date:
            raise ValidationException(message="since must be on or before until")

        span = (until_date - since_date).days + 1
        if span > MAX_RANGE_DAYS:
            raise ValidationException(
                message=f"Date range cannot exceed {MAX_RANGE_DAYS} days"
            )

        return since_date, until_date

    @staticmethod
    def get_dashboard(user, *, since: Optional[date] = None, until: Optional[date] = None) -> dict:
        since_date, until_date = StatsService.resolve_range(since=since, until=until)
        today = _today()
        days = _daterange(since_date, until_date)

        habits = HabitService.list_habits(user, archived="active")
        habit_ids = [h.id for h in habits]
        total_habits = len(habits)

        # Check-ins for chart range + streak lookback
        streak_since = today - timedelta(days=400)
        dates_by_habit = HabitService.check_in_dates_for_habits(
            habits,
            since=min(since_date, streak_since),
            until=until_date,
        )

        check_ins_in_range = HabitCheckIn.objects.filter(
            habit_id__in=habit_ids,
            date__gte=since_date,
            date__lte=until_date,
        ).values_list("date", flat=True)

        completed_by_day: dict[date, int] = {d: 0 for d in days}
        for check_date in check_ins_in_range:
            if check_date in completed_by_day:
                completed_by_day[check_date] += 1

        habits_by_day = [
            {
                "date": d,
                "completed": completed_by_day[d],
                "total": total_habits,
            }
            for d in days
        ]

        possible = total_habits * len(days)
        actual = sum(completed_by_day.values())
        habit_completion_rate = (
            round((actual / possible) * 100, 1) if possible > 0 else 0.0
        )

        habit_streaks = []
        streaks_total = 0
        best_streak = 0
        for habit in habits:
            streak = compute_streak(dates_by_habit.get(habit.id, set()), today=today)
            streaks_total += streak
            best_streak = max(best_streak, streak)
            habit_streaks.append(
                {
                    "id": habit.id,
                    "name": habit.name,
                    "color": habit.color,
                    "current_streak": streak,
                }
            )
        habit_streaks.sort(key=lambda row: (-row["current_streak"], row["name"]))

        # Tasks in range by due_date / completed_at date
        tasks = Task.objects.filter(user=user).filter(
            Q(due_date__gte=since_date, due_date__lte=until_date)
            | Q(
                completed_at__date__gte=since_date,
                completed_at__date__lte=until_date,
            )
        )

        done_by_day: dict[date, int] = {d: 0 for d in days}
        open_by_day: dict[date, int] = {d: 0 for d in days}
        tasks_done = 0
        tasks_open = 0
        tasks_overdue = 0

        for task in tasks:
            if task.status == TaskStatus.CANCELLED:
                continue

            if task.status == TaskStatus.DONE:
                tasks_done += 1
                done_day = None
                if task.completed_at:
                    done_day = timezone.localtime(task.completed_at).date()
                elif task.due_date:
                    done_day = task.due_date
                if done_day and done_day in done_by_day:
                    done_by_day[done_day] += 1
            elif task.status == TaskStatus.TODO:
                tasks_open += 1
                if task.due_date and task.due_date in open_by_day:
                    open_by_day[task.due_date] += 1
                if task.due_date and task.due_date < today:
                    tasks_overdue += 1

        tasks_by_day = [
            {"date": d, "done": done_by_day[d], "open": open_by_day[d]} for d in days
        ]

        return {
            "range": {"since": since_date, "until": until_date},
            "summary": {
                "active_habits": total_habits,
                "habit_completion_rate": habit_completion_rate,
                "current_streaks_total": streaks_total,
                "best_streak": best_streak,
                "tasks_done": tasks_done,
                "tasks_open": tasks_open,
                "tasks_overdue": tasks_overdue,
            },
            "habits_by_day": habits_by_day,
            "habit_streaks": habit_streaks,
            "tasks_by_day": tasks_by_day,
        }
