"use client"

import { FormEvent, useEffect, useState } from "react"
import type { Task, TaskCreatePayload, TaskPriority, TaskUpdatePayload } from "@/lib/api/tasks"
import {
  fromDateTimeLocal,
  fromTimeInput,
  toDateTimeLocal,
  toTimeInput,
} from "@/lib/tasks/date"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

const selectClassName =
  "h-9 w-full rounded-md border-2 border-border bg-background px-3 text-sm outline-none focus-visible:border-ring"

export type TaskFormValues = {
  title: string
  description: string
  priority: TaskPriority
  dueDate: string
  dueTime: string
  startsAt: string
  endsAt: string
  undated: boolean
}

function emptyValues(defaultDate: string): TaskFormValues {
  return {
    title: "",
    description: "",
    priority: "none",
    dueDate: defaultDate,
    dueTime: "",
    startsAt: "",
    endsAt: "",
    undated: false,
  }
}

function valuesFromTask(task: Task): TaskFormValues {
  return {
    title: task.title,
    description: task.description,
    priority: task.priority,
    dueDate: task.due_date ?? "",
    dueTime: toTimeInput(task.due_time),
    startsAt: toDateTimeLocal(task.starts_at),
    endsAt: toDateTimeLocal(task.ends_at),
    undated: !task.due_date && !task.starts_at,
  }
}

export function toCreatePayload(values: TaskFormValues): TaskCreatePayload {
  if (values.undated) {
    return {
      title: values.title.trim(),
      description: values.description.trim(),
      priority: values.priority,
      undated: true,
    }
  }

  return {
    title: values.title.trim(),
    description: values.description.trim(),
    priority: values.priority,
    due_date: values.dueDate || null,
    due_time: fromTimeInput(values.dueTime),
    starts_at: fromDateTimeLocal(values.startsAt),
    ends_at: fromDateTimeLocal(values.endsAt),
    undated: false,
  }
}

export function toUpdatePayload(values: TaskFormValues): TaskUpdatePayload {
  if (values.undated) {
    return {
      title: values.title.trim(),
      description: values.description.trim(),
      priority: values.priority,
      due_date: null,
      due_time: null,
      starts_at: null,
      ends_at: null,
    }
  }

  return {
    title: values.title.trim(),
    description: values.description.trim(),
    priority: values.priority,
    due_date: values.dueDate || null,
    due_time: fromTimeInput(values.dueTime),
    starts_at: fromDateTimeLocal(values.startsAt),
    ends_at: fromDateTimeLocal(values.endsAt),
  }
}

type TaskFormDialogProps = {
  open: boolean
  mode: "create" | "edit"
  defaultDate: string
  task?: Task | null
  isSubmitting?: boolean
  error?: string | null
  onOpenChange: (open: boolean) => void
  onSubmit: (values: TaskFormValues) => void
}

export function TaskFormDialog({
  open,
  mode,
  defaultDate,
  task,
  isSubmitting,
  error,
  onOpenChange,
  onSubmit,
}: TaskFormDialogProps) {
  const [values, setValues] = useState<TaskFormValues>(emptyValues(defaultDate))

  useEffect(() => {
    if (!open) return
    setValues(task ? valuesFromTask(task) : emptyValues(defaultDate))
  }, [open, task, defaultDate])

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    onSubmit(values)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="font-black">
            {mode === "create" ? "Add task" : "Edit task"}
          </DialogTitle>
          <DialogDescription>
            Set priority, timing, or a schedule block. Skip the date to keep it
            in the inbox.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="task-title">Title</Label>
            <Input
              id="task-title"
              value={values.title}
              onChange={(e) =>
                setValues((prev) => ({ ...prev, title: e.target.value }))
              }
              placeholder="What needs doing?"
              maxLength={255}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="task-description">Description</Label>
            <Textarea
              id="task-description"
              value={values.description}
              onChange={(e) =>
                setValues((prev) => ({ ...prev, description: e.target.value }))
              }
              placeholder="Notes, links, context…"
              className="border-2 border-border"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="task-priority">Priority</Label>
            <select
              id="task-priority"
              className={selectClassName}
              value={values.priority}
              onChange={(e) =>
                setValues((prev) => ({
                  ...prev,
                  priority: e.target.value as TaskPriority,
                }))
              }
            >
              <option value="none">None</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>

          <label className="flex items-center gap-2 text-sm font-medium">
            <input
              type="checkbox"
              checked={values.undated}
              onChange={(e) =>
                setValues((prev) => ({
                  ...prev,
                  undated: e.target.checked,
                  dueDate: e.target.checked ? "" : prev.dueDate || defaultDate,
                  dueTime: e.target.checked ? "" : prev.dueTime,
                  startsAt: e.target.checked ? "" : prev.startsAt,
                  endsAt: e.target.checked ? "" : prev.endsAt,
                }))
              }
              className="size-4 accent-primary"
            />
            Save to inbox (no date)
          </label>

          {!values.undated ? (
            <>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="task-due-date">Due date</Label>
                  <Input
                    id="task-due-date"
                    type="date"
                    value={values.dueDate}
                    onChange={(e) =>
                      setValues((prev) => ({
                        ...prev,
                        dueDate: e.target.value,
                      }))
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="task-due-time">Due time</Label>
                  <Input
                    id="task-due-time"
                    type="time"
                    value={values.dueTime}
                    onChange={(e) =>
                      setValues((prev) => ({
                        ...prev,
                        dueTime: e.target.value,
                      }))
                    }
                  />
                </div>
              </div>

              <div className="space-y-3 rounded-md border-2 border-border p-3">
                <p className="text-xs font-bold uppercase tracking-wide text-muted-foreground">
                  Schedule block (optional)
                </p>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="task-starts">Starts</Label>
                    <Input
                      id="task-starts"
                      type="datetime-local"
                      value={values.startsAt}
                      onChange={(e) =>
                        setValues((prev) => ({
                          ...prev,
                          startsAt: e.target.value,
                          dueDate:
                            prev.dueDate ||
                            e.target.value.slice(0, 10) ||
                            prev.dueDate,
                        }))
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="task-ends">Ends</Label>
                    <Input
                      id="task-ends"
                      type="datetime-local"
                      value={values.endsAt}
                      onChange={(e) =>
                        setValues((prev) => ({
                          ...prev,
                          endsAt: e.target.value,
                        }))
                      }
                    />
                  </div>
                </div>
              </div>
            </>
          ) : null}

          {error ? (
            <p className="text-xs font-bold text-destructive">{error}</p>
          ) : null}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting || !values.title.trim()}>
              {isSubmitting
                ? "Saving..."
                : mode === "create"
                  ? "Add task"
                  : "Save changes"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
