from datetime import date, datetime, time
from typing import Optional

from django.db.models import Case, IntegerField, Q, QuerySet, Value, When
from django.utils import timezone

from _sdk.exceptions import ResourceNotFoundException, ValidationException
from tasks.models import Task, TaskPriority, TaskStatus

PRIORITY_ORDER = {
    TaskPriority.HIGH: 0,
    TaskPriority.MEDIUM: 1,
    TaskPriority.LOW: 2,
    TaskPriority.NONE: 3,
}


def _soft_delete(instance) -> None:
    instance.deleted_at = timezone.now()
    instance.save(update_fields=["deleted_at", "updated_at"])


def _today() -> date:
    return timezone.localdate()


def _ordered(qs: QuerySet[Task]) -> QuerySet[Task]:
    return qs.annotate(
        priority_rank=Case(
            When(priority=TaskPriority.HIGH, then=Value(0)),
            When(priority=TaskPriority.MEDIUM, then=Value(1)),
            When(priority=TaskPriority.LOW, then=Value(2)),
            default=Value(3),
            output_field=IntegerField(),
        )
    ).order_by("priority_rank", "due_time", "starts_at", "sort_order", "id")


class TaskService:
    @staticmethod
    def get_task(user, task_id: int) -> Task:
        task = Task.objects.filter(user=user, id=task_id).first()
        if not task:
            raise ResourceNotFoundException(message="Task not found")
        return task

    @staticmethod
    def list_tasks(
        user,
        *,
        on_date: Optional[date] = None,
        status: Optional[str] = None,
        include_undated: bool = False,
        inbox_only: bool = False,
        include_cancelled: bool = False,
    ) -> list[Task]:
        """
        List tasks.

        Modes:
        - Day view (default): due_date == on_date OR starts_at on on_date
        - inbox_only: undated open/done tasks (no due_date, no starts_at)
        - include_undated: also merge inbox todos into the day view
        """
        qs: QuerySet[Task] = Task.objects.filter(user=user)

        if inbox_only:
            qs = qs.filter(due_date__isnull=True, starts_at__isnull=True)
        else:
            target = on_date or _today()
            day_filter = Q(due_date=target) | Q(starts_at__date=target)
            if include_undated:
                day_filter = day_filter | Q(
                    due_date__isnull=True,
                    starts_at__isnull=True,
                )
            qs = qs.filter(day_filter)

        if status:
            if status not in TaskStatus.values:
                raise ValidationException(message=f"Invalid status: {status}")
            qs = qs.filter(status=status)
        elif not include_cancelled:
            qs = qs.exclude(status=TaskStatus.CANCELLED)

        return list(_ordered(qs))

    @staticmethod
    def create_task(
        user,
        *,
        title: str,
        description: str = "",
        status: str = TaskStatus.TODO,
        priority: str = TaskPriority.NONE,
        due_date: Optional[date] = None,
        due_time: Optional[time] = None,
        starts_at: Optional[datetime] = None,
        ends_at: Optional[datetime] = None,
        sort_order: int = 0,
        undated: bool = False,
    ) -> Task:
        title = title.strip()
        if not title:
            raise ValidationException(message="Task title is required")

        if status not in TaskStatus.values:
            raise ValidationException(message=f"Invalid status: {status}")
        if priority not in TaskPriority.values:
            raise ValidationException(message=f"Invalid priority: {priority}")

        if starts_at and ends_at and ends_at < starts_at:
            raise ValidationException(message="ends_at must be after starts_at")

        if undated and starts_at:
            raise ValidationException(
                message="Inbox tasks cannot have a schedule block"
            )

        if undated:
            due_date = None
            due_time = None
            starts_at = None
            ends_at = None
        elif due_date is None and starts_at is None:
            due_date = _today()

        completed_at = timezone.now() if status == TaskStatus.DONE else None

        return Task.objects.create(
            user=user,
            title=title,
            description=description.strip(),
            status=status,
            priority=priority,
            due_date=due_date,
            due_time=due_time,
            starts_at=starts_at,
            ends_at=ends_at,
            sort_order=sort_order,
            completed_at=completed_at,
        )

    @staticmethod
    def update_task(user, task_id: int, **fields) -> Task:
        task = TaskService.get_task(user, task_id)

        if "title" in fields and fields["title"] is not None:
            title = fields["title"].strip()
            if not title:
                raise ValidationException(message="Task title is required")
            task.title = title

        if "description" in fields and fields["description"] is not None:
            task.description = fields["description"].strip()

        if "priority" in fields and fields["priority"] is not None:
            if fields["priority"] not in TaskPriority.values:
                raise ValidationException(
                    message=f"Invalid priority: {fields['priority']}"
                )
            task.priority = fields["priority"]

        if "due_date" in fields:
            task.due_date = fields["due_date"]

        if "due_time" in fields:
            task.due_time = fields["due_time"]

        if "starts_at" in fields:
            task.starts_at = fields["starts_at"]

        if "ends_at" in fields:
            task.ends_at = fields["ends_at"]

        if "sort_order" in fields and fields["sort_order"] is not None:
            task.sort_order = fields["sort_order"]

        if "status" in fields and fields["status"] is not None:
            TaskService._apply_status(task, fields["status"])

        starts = task.starts_at
        ends = task.ends_at
        if starts and ends and ends < starts:
            raise ValidationException(message="ends_at must be after starts_at")

        task.save()
        return task

    @staticmethod
    def _apply_status(task: Task, status: str) -> None:
        if status not in TaskStatus.values:
            raise ValidationException(message=f"Invalid status: {status}")

        previous = task.status
        task.status = status

        if status == TaskStatus.DONE and previous != TaskStatus.DONE:
            task.completed_at = timezone.now()
        elif status != TaskStatus.DONE:
            task.completed_at = None

    @staticmethod
    def complete_task(user, task_id: int) -> Task:
        task = TaskService.get_task(user, task_id)
        TaskService._apply_status(task, TaskStatus.DONE)
        task.save(update_fields=["status", "completed_at", "updated_at"])
        return task

    @staticmethod
    def reopen_task(user, task_id: int) -> Task:
        task = TaskService.get_task(user, task_id)
        TaskService._apply_status(task, TaskStatus.TODO)
        task.save(update_fields=["status", "completed_at", "updated_at"])
        return task

    @staticmethod
    def cancel_task(user, task_id: int) -> Task:
        task = TaskService.get_task(user, task_id)
        TaskService._apply_status(task, TaskStatus.CANCELLED)
        task.save(update_fields=["status", "completed_at", "updated_at"])
        return task

    @staticmethod
    def reorder_tasks(user, ordered_ids: list[int]) -> list[Task]:
        if not ordered_ids:
            return []

        tasks = {
            task.id: task
            for task in Task.objects.filter(user=user, id__in=ordered_ids)
        }
        missing = [task_id for task_id in ordered_ids if task_id not in tasks]
        if missing:
            raise ResourceNotFoundException(
                message=f"Task not found: {missing[0]}"
            )

        updated: list[Task] = []
        for index, task_id in enumerate(ordered_ids):
            task = tasks[task_id]
            if task.sort_order != index:
                task.sort_order = index
                task.save(update_fields=["sort_order", "updated_at"])
            updated.append(task)
        return updated

    @staticmethod
    def delete_task(user, task_id: int) -> None:
        task = TaskService.get_task(user, task_id)
        _soft_delete(task)

    @staticmethod
    def serialize(task: Task) -> dict:
        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "due_date": task.due_date,
            "due_time": task.due_time,
            "starts_at": task.starts_at,
            "ends_at": task.ends_at,
            "completed_at": task.completed_at,
            "sort_order": task.sort_order,
            "is_done": task.is_done,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
        }
