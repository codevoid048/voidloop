from datetime import date, timedelta
from typing import List, Optional

from django.utils import timezone
from ninja import Router

from _sdk.decorators import require_auth
from habits.schemas import (
    HabitCheckInRequestSchema,
    HabitCheckInResponseSchema,
    HabitCreateSchema,
    HabitReorderSchema,
    HabitResponseSchema,
    HabitUpdateSchema,
)
from habits.services import HabitService

habits_router = Router(tags=["Habits"])


@habits_router.get("", response={200: List[HabitResponseSchema]})
@require_auth
def list_habits(
    request,
    on_date: Optional[date] = None,
    archived: str = "active",
):
    """
    List habits with check-in status for a day (defaults to today).

    Query params:
    - on_date: YYYY-MM-DD
    - archived: active | archived | all
    """
    habits = HabitService.list_habits(request.auth_user, archived=archived)
    target = on_date or timezone.localdate()
    since = target - timedelta(days=400)
    dates_by_habit = HabitService.check_in_dates_for_habits(habits, since=since)

    return [
        HabitService.serialize_habit(
            habit,
            check_in_dates=dates_by_habit.get(habit.id, set()),
            on_date=target,
        )
        for habit in habits
    ]


@habits_router.post("", response={200: HabitResponseSchema})
@require_auth
def create_habit(request, payload: HabitCreateSchema):
    habit = HabitService.create_habit(
        request.auth_user,
        name=payload.name,
        description=payload.description,
        color=payload.color,
        sort_order=payload.sort_order,
    )
    return HabitService.serialize_habit(habit, check_in_dates=set())


@habits_router.post("/reorder", response={200: List[HabitResponseSchema]})
@require_auth
def reorder_habits(request, payload: HabitReorderSchema):
    habits = HabitService.reorder_habits(request.auth_user, payload.ordered_ids)
    today = timezone.localdate()
    since = today - timedelta(days=400)
    dates_by_habit = HabitService.check_in_dates_for_habits(habits, since=since)
    return [
        HabitService.serialize_habit(
            habit,
            check_in_dates=dates_by_habit.get(habit.id, set()),
            on_date=today,
        )
        for habit in habits
    ]


@habits_router.get("/{habit_id}", response={200: HabitResponseSchema})
@require_auth
def get_habit(request, habit_id: int, on_date: Optional[date] = None):
    habit = HabitService.get_habit(request.auth_user, habit_id)
    return HabitService.serialize_habit(habit, on_date=on_date)


@habits_router.patch("/{habit_id}", response={200: HabitResponseSchema})
@require_auth
def update_habit(request, habit_id: int, payload: HabitUpdateSchema):
    habit = HabitService.update_habit(
        request.auth_user,
        habit_id,
        **payload.model_dump(exclude_unset=True),
    )
    return HabitService.serialize_habit(habit)


@habits_router.delete("/{habit_id}", response={200: dict})
@require_auth
def delete_habit(request, habit_id: int):
    HabitService.delete_habit(request.auth_user, habit_id)
    return {"message": "Habit deleted"}


@habits_router.post("/{habit_id}/archive", response={200: HabitResponseSchema})
@require_auth
def archive_habit(request, habit_id: int):
    habit = HabitService.archive_habit(request.auth_user, habit_id)
    return HabitService.serialize_habit(habit)


@habits_router.post("/{habit_id}/unarchive", response={200: HabitResponseSchema})
@require_auth
def unarchive_habit(request, habit_id: int):
    habit = HabitService.unarchive_habit(request.auth_user, habit_id)
    return HabitService.serialize_habit(habit)


@habits_router.get(
    "/{habit_id}/check-ins",
    response={200: List[HabitCheckInResponseSchema]},
)
@require_auth
def list_check_ins(
    request,
    habit_id: int,
    since: Optional[date] = None,
    until: Optional[date] = None,
    limit: int = 60,
):
    check_ins = HabitService.list_check_ins(
        request.auth_user,
        habit_id,
        since=since,
        until=until,
        limit=limit,
    )
    return [HabitService.serialize_check_in(item) for item in check_ins]


@habits_router.post(
    "/{habit_id}/check-ins",
    response={200: HabitCheckInResponseSchema},
)
@require_auth
def create_check_in(request, habit_id: int, payload: HabitCheckInRequestSchema):
    check_in = HabitService.check_in(
        request.auth_user,
        habit_id,
        on_date=payload.on_date,
        note=payload.note,
    )
    return HabitService.serialize_check_in(check_in)


@habits_router.delete("/{habit_id}/check-ins", response={200: dict})
@require_auth
def undo_check_in(request, habit_id: int, on_date: Optional[date] = None):
    """Undo check-in for a date (defaults to today)."""
    HabitService.undo_check_in(request.auth_user, habit_id, on_date=on_date)
    return {"message": "Check-in removed"}
