from datetime import datetime
from typing import Optional

from ninja import Schema
from pydantic import Field


class FolderCreateSchema(Schema):
    name: str = Field(..., min_length=1, max_length=120)
    color: str = Field(default="#7c3aed", max_length=7)
    parent_id: Optional[int] = None
    sort_order: int = Field(default=0, ge=0)


class FolderUpdateSchema(Schema):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    color: Optional[str] = Field(default=None, max_length=7)
    parent_id: Optional[int] = None
    sort_order: Optional[int] = Field(default=None, ge=0)


class FolderResponseSchema(Schema):
    id: int
    name: str
    color: str
    parent_id: Optional[int] = None
    sort_order: int
    created_at: datetime
    updated_at: datetime


class NoteCreateSchema(Schema):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(default="")
    folder_id: Optional[int] = None
    is_pinned: bool = False
    sort_order: int = Field(default=0, ge=0)


class NoteUpdateSchema(Schema):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    content: Optional[str] = None
    folder_id: Optional[int] = None
    is_pinned: Optional[bool] = None
    is_archived: Optional[bool] = None
    sort_order: Optional[int] = Field(default=None, ge=0)


class NoteListItemSchema(Schema):
    id: int
    title: str
    folder_id: Optional[int] = None
    is_pinned: bool
    is_archived: bool
    sort_order: int
    preview: str = ""
    created_at: datetime
    updated_at: datetime


class NoteResponseSchema(Schema):
    id: int
    title: str
    content: str
    folder_id: Optional[int] = None
    is_pinned: bool
    is_archived: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime
