from datetime import date
from typing import List, Optional

from ninja import Router

from _sdk.decorators import require_auth
from tasks.schemas import (
    TaskCreateSchema,
    TaskReorderSchema,
    TaskResponseSchema,
    TaskUpdateSchema,
)
from tasks.services import TaskService

tasks_router = Router(tags=["Tasks"])


@tasks_router.get("", response={200: List[TaskResponseSchema]})
@require_auth
def list_tasks(
    request,
    on_date: Optional[date] = None,
    status: Optional[str] = None,
    include_undated: bool = False,
    inbox_only: bool = False,
    include_cancelled: bool = False,
):
    """
    List tasks for a day (defaults to today), or inbox-only undated tasks.

    Query params:
    - on_date: YYYY-MM-DD
    - status: todo | done | cancelled
    - include_undated: merge inbox items into day view
    - inbox_only: only undated tasks
    - include_cancelled: show cancelled when status is not set
    """
    tasks = TaskService.list_tasks(
        request.auth_user,
        on_date=on_date,
        status=status,
        include_undated=include_undated,
        inbox_only=inbox_only,
        include_cancelled=include_cancelled,
    )
    return [TaskService.serialize(task) for task in tasks]


@tasks_router.post("", response={200: TaskResponseSchema})
@require_auth
def create_task(request, payload: TaskCreateSchema):
    task = TaskService.create_task(
        request.auth_user,
        **payload.model_dump(),
    )
    return TaskService.serialize(task)


@tasks_router.post("/reorder", response={200: List[TaskResponseSchema]})
@require_auth
def reorder_tasks(request, payload: TaskReorderSchema):
    tasks = TaskService.reorder_tasks(request.auth_user, payload.ordered_ids)
    return [TaskService.serialize(task) for task in tasks]


@tasks_router.get("/{task_id}", response={200: TaskResponseSchema})
@require_auth
def get_task(request, task_id: int):
    task = TaskService.get_task(request.auth_user, task_id)
    return TaskService.serialize(task)


@tasks_router.patch("/{task_id}", response={200: TaskResponseSchema})
@require_auth
def update_task(request, task_id: int, payload: TaskUpdateSchema):
    task = TaskService.update_task(
        request.auth_user,
        task_id,
        **payload.model_dump(exclude_unset=True),
    )
    return TaskService.serialize(task)


@tasks_router.delete("/{task_id}", response={200: dict})
@require_auth
def delete_task(request, task_id: int):
    TaskService.delete_task(request.auth_user, task_id)
    return {"message": "Task deleted"}


@tasks_router.post("/{task_id}/complete", response={200: TaskResponseSchema})
@require_auth
def complete_task(request, task_id: int):
    task = TaskService.complete_task(request.auth_user, task_id)
    return TaskService.serialize(task)


@tasks_router.post("/{task_id}/reopen", response={200: TaskResponseSchema})
@require_auth
def reopen_task(request, task_id: int):
    task = TaskService.reopen_task(request.auth_user, task_id)
    return TaskService.serialize(task)


@tasks_router.post("/{task_id}/cancel", response={200: TaskResponseSchema})
@require_auth
def cancel_task(request, task_id: int):
    task = TaskService.cancel_task(request.auth_user, task_id)
    return TaskService.serialize(task)
