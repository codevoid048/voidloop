from datetime import date, datetime, time
from typing import List, Optional

from ninja import Schema
from pydantic import Field


class TaskCreateSchema(Schema):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="", max_length=5000)
    status: str = Field(default="todo")
    priority: str = Field(default="none")
    due_date: Optional[date] = None
    due_time: Optional[time] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    sort_order: int = Field(default=0, ge=0)
    undated: bool = False


class TaskUpdateSchema(Schema):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[date] = None
    due_time: Optional[time] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    sort_order: Optional[int] = Field(default=None, ge=0)


class TaskReorderSchema(Schema):
    ordered_ids: List[int] = Field(..., min_length=1)


class TaskResponseSchema(Schema):
    id: int
    title: str
    description: str
    status: str
    priority: str
    due_date: Optional[date] = None
    due_time: Optional[time] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    sort_order: int
    is_done: bool
    created_at: datetime
    updated_at: datetime
