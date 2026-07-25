from datetime import date
from typing import List

from ninja import Schema


class StatsRangeSchema(Schema):
    since: date
    until: date


class StatsSummarySchema(Schema):
    active_habits: int
    habit_completion_rate: float
    current_streaks_total: int
    best_streak: int
    tasks_done: int
    tasks_open: int
    tasks_overdue: int


class HabitDayStatSchema(Schema):
    date: date
    completed: int
    total: int


class HabitStreakSchema(Schema):
    id: int
    name: str
    color: str
    current_streak: int


class TaskDayStatSchema(Schema):
    date: date
    done: int
    open: int


class StatsResponseSchema(Schema):
    range: StatsRangeSchema
    summary: StatsSummarySchema
    habits_by_day: List[HabitDayStatSchema]
    habit_streaks: List[HabitStreakSchema]
    tasks_by_day: List[TaskDayStatSchema]
