from typing import Any, List, TypeVar, Generic
from django.db.models import QuerySet
from ninja.pagination import PaginationBase
from pydantic import Field
from _sdk.response import api_success
from _sdk.schemas import BaseSchema

T = TypeVar("T")

class TrackerPagination(PaginationBase):
    class Input(BaseSchema):
        page: int = Field(1, ge=1)
        per_page: int = Field(20, ge=1, le=100)

    def paginate_queryset(self, queryset: QuerySet, pagination: Input, request=None, **params) -> Any:
        offset = (pagination.page - 1) * pagination.per_page
        items = list(queryset[offset : offset + pagination.per_page])
        total_count = queryset.count()
        total_pages = (total_count + pagination.per_page - 1) // pagination.per_page if pagination.per_page > 0 else 0
        
        pagination_meta = {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": pagination.page < total_pages,
            "has_previous": pagination.page > 1,
        }
        
        return api_success(data=items, request=request, pagination=pagination_meta)
