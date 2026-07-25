from datetime import date, datetime
from typing import List, Optional

from ninja import Schema
from pydantic import Field


class HabitCreateSchema(Schema):
    name: str = Field(..., min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)
    color: str = Field(default="#7c3aed", max_length=7)
    sort_order: int = Field(default=0, ge=0)


class HabitUpdateSchema(Schema):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2000)
    color: Optional[str] = Field(default=None, max_length=7)
    is_archived: Optional[bool] = None
    sort_order: Optional[int] = Field(default=None, ge=0)


class HabitCheckInRequestSchema(Schema):
    on_date: Optional[date] = None
    note: str = Field(default="", max_length=255)


class HabitReorderSchema(Schema):
    ordered_ids: List[int] = Field(..., min_length=1)


class HabitResponseSchema(Schema):
    id: int
    name: str
    description: str
    color: str
    is_archived: bool
    sort_order: int
    checked_in: bool
    checked_in_today: bool
    current_streak: int
    created_at: datetime
    updated_at: datetime


class HabitCheckInResponseSchema(Schema):
    id: int
    habit_id: int
    date: date
    note: str
    created_at: datetime
