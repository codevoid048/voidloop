"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  Ban,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  Circle,
  Inbox,
  Pencil,
  Plus,
  RotateCcw,
  Trash2,
} from "lucide-react"
import { useMemo, useState } from "react"
import { getApiErrorMessage } from "@/lib/api/errors"
import {
  tasksApi,
  type Task,
  type TaskPriority,
  type TaskStatus,
} from "@/lib/api/tasks"
import {
  formatDisplayDate,
  formatDueTime,
  formatScheduleRange,
  shiftISODate,
  todayISODate,
} from "@/lib/tasks/date"
import {
  TaskFormDialog,
  toCreatePayload,
  toUpdatePayload,
  type TaskFormValues,
} from "@/components/tasks/TaskFormDialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"

type ViewMode = "day" | "inbox"
type StatusFilter = "all" | TaskStatus

const PRIORITY_LABEL: Record<TaskPriority, string> = {
  none: "None",
  low: "Low",
  medium: "Medium",
  high: "High",
}

function priorityVariant(
  priority: TaskPriority,
): "default" | "secondary" | "outline" | "destructive" {
  if (priority === "high") return "destructive"
  if (priority === "medium") return "default"
  if (priority === "low") return "secondary"
  return "outline"
}

function TaskRow({
  task,
  queryKey,
  onEdit,
  canMoveUp,
  canMoveDown,
  onMove,
}: {
  task: Task
  queryKey: unknown[]
  onEdit: (task: Task) => void
  canMoveUp: boolean
  canMoveDown: boolean
  onMove: (taskId: number, direction: "up" | "down") => void
}) {
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey })

  const actionMutation = useMutation({
    mutationFn: async (
      action: "toggle" | "cancel" | "reopen" | "delete",
    ) => {
      if (action === "toggle") {
        if (task.is_done || task.status === "cancelled") {
          await tasksApi.reopen(task.id)
        } else {
          await tasksApi.complete(task.id)
        }
        return
      }
      if (action === "cancel") {
        await tasksApi.cancel(task.id)
        return
      }
      if (action === "reopen") {
        await tasksApi.reopen(task.id)
        return
      }
      await tasksApi.remove(task.id)
    },
    onSuccess: () => {
      setError(null)
      void invalidate()
    },
    onError: (err) => {
      setError(getApiErrorMessage(err, "Could not update task"))
    },
  })

  const timeLabel = formatDueTime(task.due_time)
  const scheduleLabel = formatScheduleRange(task.starts_at, task.ends_at)
  const isCancelled = task.status === "cancelled"

  return (
    <div
      className={`flex items-start gap-3 rounded-md border-2 border-border p-3 ${
        task.is_done || isCancelled ? "bg-muted/60" : "bg-background"
      }`}
    >
      <button
        type="button"
        onClick={() => actionMutation.mutate("toggle")}
        disabled={actionMutation.isPending || isCancelled}
        aria-pressed={task.is_done}
        aria-label={
          task.is_done ? `Reopen ${task.title}` : `Complete ${task.title}`
        }
        className="mt-0.5 shrink-0 text-primary disabled:opacity-40"
      >
        {task.is_done ? (
          <CheckCircle2 className="size-6 fill-primary/20" />
        ) : (
          <Circle className="size-6" />
        )}
      </button>

      <div className="min-w-0 flex-1 space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <p
            className={`truncate text-sm font-black ${
              task.is_done || isCancelled
                ? "text-muted-foreground line-through"
                : ""
            }`}
          >
            {task.title}
          </p>
          {task.priority !== "none" ? (
            <Badge variant={priorityVariant(task.priority)}>
              {PRIORITY_LABEL[task.priority]}
            </Badge>
          ) : null}
          {isCancelled ? <Badge variant="outline">Cancelled</Badge> : null}
          {timeLabel ? (
            <span className="rounded border-2 border-border bg-secondary px-1.5 py-0.5 text-[10px] font-bold">
              {timeLabel}
            </span>
          ) : null}
          {scheduleLabel ? (
            <span className="rounded border-2 border-border bg-accent/40 px-1.5 py-0.5 text-[10px] font-bold">
              {scheduleLabel}
            </span>
          ) : null}
        </div>
        {task.description ? (
          <p className="text-xs font-medium text-muted-foreground">
            {task.description}
          </p>
        ) : null}
        {error ? (
          <p className="text-xs font-medium text-destructive">{error}</p>
        ) : null}
      </div>

      <div className="flex shrink-0 flex-col gap-1">
        <div className="flex gap-1">
          <Button
            type="button"
            variant="ghost"
            size="icon-xs"
            disabled={!canMoveUp || actionMutation.isPending}
            onClick={() => onMove(task.id, "up")}
            aria-label="Move up"
          >
            <ChevronUp className="size-3.5" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon-xs"
            disabled={!canMoveDown || actionMutation.isPending}
            onClick={() => onMove(task.id, "down")}
            aria-label="Move down"
          >
            <ChevronDown className="size-3.5" />
          </Button>
        </div>
        <div className="flex gap-1">
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            onClick={() => onEdit(task)}
            aria-label={`Edit ${task.title}`}
          >
            <Pencil className="size-4" />
          </Button>
          {isCancelled ? (
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              disabled={actionMutation.isPending}
              onClick={() => actionMutation.mutate("reopen")}
              aria-label={`Reopen ${task.title}`}
            >
              <RotateCcw className="size-4" />
            </Button>
          ) : (
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              disabled={actionMutation.isPending}
              onClick={() => actionMutation.mutate("cancel")}
              aria-label={`Cancel ${task.title}`}
            >
              <Ban className="size-4" />
            </Button>
          )}
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            disabled={actionMutation.isPending}
            onClick={() => {
              if (window.confirm(`Delete “${task.title}”?`)) {
                actionMutation.mutate("delete")
              }
            }}
            aria-label={`Delete ${task.title}`}
          >
            <Trash2 className="size-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}

export function TasksPanel() {
  const queryClient = useQueryClient()
  const [viewMode, setViewMode] = useState<ViewMode>("day")
  const [onDate, setOnDate] = useState(todayISODate)
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all")
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingTask, setEditingTask] = useState<Task | null>(null)
  const [formError, setFormError] = useState<string | null>(null)

  const listParams = useMemo(
    () => ({
      onDate: viewMode === "day" ? onDate : undefined,
      inboxOnly: viewMode === "inbox",
      status: statusFilter === "all" ? undefined : statusFilter,
      includeCancelled: false,
    }),
    [viewMode, onDate, statusFilter],
  )

  const queryKey = useMemo(
    () => ["tasks", viewMode, onDate, statusFilter] as const,
    [viewMode, onDate, statusFilter],
  )

  const tasksQuery = useQuery({
    queryKey,
    queryFn: () =>
      tasksApi.list({
        onDate: listParams.onDate,
        inboxOnly: listParams.inboxOnly,
        status: listParams.status,
        includeCancelled: listParams.includeCancelled,
      }),
  })

  const saveMutation = useMutation({
    mutationFn: async (values: TaskFormValues) => {
      if (editingTask) {
        return tasksApi.update(editingTask.id, toUpdatePayload(values))
      }
      return tasksApi.create(toCreatePayload(values))
    },
    onSuccess: () => {
      setFormError(null)
      setDialogOpen(false)
      setEditingTask(null)
      void queryClient.invalidateQueries({ queryKey: ["tasks"] })
    },
    onError: (err) => {
      setFormError(getApiErrorMessage(err, "Could not save task"))
    },
  })

  const reorderMutation = useMutation({
    mutationFn: (orderedIds: number[]) => tasksApi.reorder(orderedIds),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey })
    },
  })

  const tasks = tasksQuery.data ?? []
  const openCount = tasks.filter((t) => t.status === "todo").length
  const doneCount = tasks.filter((t) => t.status === "done").length
  const cancelledCount = tasks.filter((t) => t.status === "cancelled").length

  const openEdit = (task: Task) => {
    setEditingTask(task)
    setFormError(null)
    setDialogOpen(true)
  }

  const openCreate = () => {
    setEditingTask(null)
    setFormError(null)
    setDialogOpen(true)
  }

  const moveTask = (taskId: number, direction: "up" | "down") => {
    const index = tasks.findIndex((task) => task.id === taskId)
    if (index < 0) return
    const target = direction === "up" ? index - 1 : index + 1
    if (target < 0 || target >= tasks.length) return

    const next = [...tasks]
    const [item] = next.splice(index, 1)
    next.splice(target, 0, item)
    reorderMutation.mutate(next.map((task) => task.id))
  }

  const filterButtons: { id: StatusFilter; label: string }[] = [
    { id: "all", label: "All" },
    { id: "todo", label: "Open" },
    { id: "done", label: "Done" },
    { id: "cancelled", label: "Cancelled" },
  ]

  return (
    <div className="mx-auto grid w-full max-w-3xl gap-6">
      <Card>
        <CardHeader className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <CardTitle className="text-xl">
                {viewMode === "day" ? "Daily tasks" : "Inbox"}
              </CardTitle>
              <CardDescription>
                {tasksQuery.isLoading
                  ? "Loading..."
                  : tasks.length === 0
                    ? viewMode === "inbox"
                      ? "Inbox is empty."
                      : "Nothing planned for this day."
                    : `${openCount} open · ${doneCount} done${
                        cancelledCount ? ` · ${cancelledCount} cancelled` : ""
                      }`}
              </CardDescription>
            </div>
            <Button type="button" onClick={openCreate}>
              <Plus className="size-4" />
              Add task
            </Button>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              size="sm"
              variant={viewMode === "day" ? "default" : "outline"}
              onClick={() => setViewMode("day")}
            >
              Day
            </Button>
            <Button
              type="button"
              size="sm"
              variant={viewMode === "inbox" ? "default" : "outline"}
              onClick={() => setViewMode("inbox")}
            >
              <Inbox className="size-3.5" />
              Inbox
            </Button>
          </div>

          {viewMode === "day" ? (
            <div className="flex flex-wrap items-center gap-2">
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={() => setOnDate((prev) => shiftISODate(prev, -1))}
                aria-label="Previous day"
              >
                <ChevronLeft className="size-4" />
              </Button>
              <Input
                type="date"
                value={onDate}
                onChange={(e) => setOnDate(e.target.value)}
                className="w-auto"
              />
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={() => setOnDate((prev) => shiftISODate(prev, 1))}
                aria-label="Next day"
              >
                <ChevronRight className="size-4" />
              </Button>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => setOnDate(todayISODate())}
              >
                Today
              </Button>
              <span className="text-xs font-bold text-muted-foreground">
                {formatDisplayDate(onDate)}
              </span>
            </div>
          ) : null}

          <div className="flex flex-wrap gap-2">
            {filterButtons.map((filter) => (
              <Button
                key={filter.id}
                type="button"
                size="sm"
                variant={statusFilter === filter.id ? "default" : "outline"}
                onClick={() => setStatusFilter(filter.id)}
              >
                {filter.label}
              </Button>
            ))}
          </div>
        </CardHeader>

        <CardContent className="space-y-3">
          {tasksQuery.isError ? (
            <p className="text-sm font-medium text-destructive">
              {getApiErrorMessage(tasksQuery.error, "Failed to load tasks")}
            </p>
          ) : null}

          {tasks.map((task, index) => (
            <TaskRow
              key={task.id}
              task={task}
              queryKey={[...queryKey]}
              onEdit={openEdit}
              canMoveUp={index > 0}
              canMoveDown={index < tasks.length - 1}
              onMove={moveTask}
            />
          ))}
        </CardContent>
      </Card>

      <TaskFormDialog
        open={dialogOpen}
        mode={editingTask ? "edit" : "create"}
        defaultDate={viewMode === "day" ? onDate : todayISODate()}
        task={editingTask}
        isSubmitting={saveMutation.isPending}
        error={formError}
        onOpenChange={(open) => {
          setDialogOpen(open)
          if (!open) {
            setEditingTask(null)
            setFormError(null)
          }
        }}
        onSubmit={(values) => saveMutation.mutate(values)}
      />
    </div>
  )
}
