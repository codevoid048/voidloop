"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Circle,
  Flame,
  ArrowRight,
} from "lucide-react"
import Link from "next/link"
import { useMemo, useState } from "react"
import { getApiErrorMessage } from "@/lib/api/errors"
import { habitsApi, type Habit } from "@/lib/api/habits"
import { tasksApi, type Task } from "@/lib/api/tasks"
import {
  formatDisplayDate,
  formatDueTime,
  formatScheduleRange,
  shiftISODate,
  todayISODate,
} from "@/lib/tasks/date"
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

function HabitQuickRow({
  habit,
  onDate,
  queryKey,
}: {
  habit: Habit
  onDate: string
  queryKey: unknown[]
}) {
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)

  const toggleMutation = useMutation({
    mutationFn: async () => {
      if (habit.checked_in) {
        await habitsApi.undoCheckIn(habit.id, onDate)
      } else {
        await habitsApi.checkIn(habit.id, { on_date: onDate })
      }
    },
    onSuccess: () => {
      setError(null)
      void queryClient.invalidateQueries({ queryKey })
    },
    onError: (err) => {
      setError(getApiErrorMessage(err, "Could not update check-in"))
    },
  })

  return (
    <div className="flex items-center gap-3 rounded-md border-2 border-border bg-background p-3">
      <button
        type="button"
        onClick={() => toggleMutation.mutate()}
        disabled={toggleMutation.isPending}
        aria-pressed={habit.checked_in}
        className="flex size-7 shrink-0 items-center justify-center rounded border-2 border-border"
        style={{
          backgroundColor: habit.checked_in ? habit.color : "transparent",
        }}
      >
        {habit.checked_in ? (
          <span className="text-xs font-black text-white">✓</span>
        ) : null}
      </button>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <p className="truncate text-sm font-black">{habit.name}</p>
          {habit.current_streak > 0 ? (
            <span className="inline-flex items-center gap-1 rounded border-2 border-border bg-secondary px-1.5 py-0.5 text-[10px] font-bold">
              <Flame className="size-3" />
              {habit.current_streak}
            </span>
          ) : null}
        </div>
        {error ? (
          <p className="text-xs font-medium text-destructive">{error}</p>
        ) : null}
      </div>
    </div>
  )
}

function TaskQuickRow({
  task,
  queryKey,
}: {
  task: Task
  queryKey: unknown[]
}) {
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)

  const toggleMutation = useMutation({
    mutationFn: async () => {
      if (task.is_done) {
        await tasksApi.reopen(task.id)
      } else {
        await tasksApi.complete(task.id)
      }
    },
    onSuccess: () => {
      setError(null)
      void queryClient.invalidateQueries({ queryKey })
    },
    onError: (err) => {
      setError(getApiErrorMessage(err, "Could not update task"))
    },
  })

  const timeLabel = formatDueTime(task.due_time)
  const scheduleLabel = formatScheduleRange(task.starts_at, task.ends_at)

  return (
    <div
      className={`flex items-center gap-3 rounded-md border-2 border-border p-3 ${
        task.is_done ? "bg-muted/60" : "bg-background"
      }`}
    >
      <button
        type="button"
        onClick={() => toggleMutation.mutate()}
        disabled={toggleMutation.isPending}
        aria-pressed={task.is_done}
        className="shrink-0 text-primary"
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
              task.is_done ? "text-muted-foreground line-through" : ""
            }`}
          >
            {task.title}
          </p>
          {task.priority !== "none" ? (
            <Badge variant={task.priority === "high" ? "destructive" : "secondary"}>
              {task.priority}
            </Badge>
          ) : null}
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
        {error ? (
          <p className="text-xs font-medium text-destructive">{error}</p>
        ) : null}
      </div>
    </div>
  )
}

export function TodayPanel() {
  const [onDate, setOnDate] = useState(todayISODate)
  const isToday = onDate === todayISODate()

  const habitsKey = useMemo(
    () => ["today", "habits", onDate] as const,
    [onDate],
  )
  const tasksKey = useMemo(
    () => ["today", "tasks", onDate] as const,
    [onDate],
  )

  const habitsQuery = useQuery({
    queryKey: habitsKey,
    queryFn: () => habitsApi.list({ onDate, archived: "active" }),
  })

  const tasksQuery = useQuery({
    queryKey: tasksKey,
    queryFn: () => tasksApi.list({ onDate, includeCancelled: false }),
  })

  const habits = habitsQuery.data ?? []
  const tasks = (tasksQuery.data ?? []).filter((t) => t.status !== "cancelled")

  const habitsDone = habits.filter((h) => h.checked_in).length
  const tasksOpen = tasks.filter((t) => t.status === "todo").length
  const tasksDone = tasks.filter((t) => t.status === "done").length

  return (
    <div className="mx-auto grid w-full max-w-3xl gap-6">
      <Card>
        <CardHeader className="space-y-4">
          <div>
            <CardTitle className="text-xl">
              {isToday ? "Today" : "Daily overview"}
            </CardTitle>
            <CardDescription>
              Habits and tasks in one place. Manage details on their pages.
            </CardDescription>
          </div>

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

          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            <div className="rounded-md border-2 border-border bg-muted p-3">
              <p className="text-[10px] font-bold uppercase tracking-wide text-muted-foreground">
                Habits
              </p>
              <p className="text-lg font-black">
                {habitsDone}/{habits.length}
              </p>
            </div>
            <div className="rounded-md border-2 border-border bg-muted p-3">
              <p className="text-[10px] font-bold uppercase tracking-wide text-muted-foreground">
                Tasks open
              </p>
              <p className="text-lg font-black">{tasksOpen}</p>
            </div>
            <div className="rounded-md border-2 border-border bg-muted p-3">
              <p className="text-[10px] font-bold uppercase tracking-wide text-muted-foreground">
                Tasks done
              </p>
              <p className="text-lg font-black">{tasksDone}</p>
            </div>
          </div>
        </CardHeader>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-3 space-y-0">
          <div>
            <CardTitle className="text-lg">Habits</CardTitle>
            <CardDescription>
              {habitsQuery.isLoading
                ? "Loading..."
                : habits.length === 0
                  ? "No active habits yet."
                  : `${habitsDone} of ${habits.length} checked in`}
            </CardDescription>
          </div>
          <Button asChild variant="outline" size="sm">
            <Link href="/habits">
              Manage
              <ArrowRight className="size-3.5" />
            </Link>
          </Button>
        </CardHeader>
        <CardContent className="space-y-2">
          {habitsQuery.isError ? (
            <p className="text-sm font-medium text-destructive">
              {getApiErrorMessage(habitsQuery.error, "Failed to load habits")}
            </p>
          ) : null}
          {habits.map((habit) => (
            <HabitQuickRow
              key={habit.id}
              habit={habit}
              onDate={onDate}
              queryKey={[...habitsKey]}
            />
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-3 space-y-0">
          <div>
            <CardTitle className="text-lg">Tasks</CardTitle>
            <CardDescription>
              {tasksQuery.isLoading
                ? "Loading..."
                : tasks.length === 0
                  ? "Nothing planned for this day."
                  : `${tasksOpen} open · ${tasksDone} done`}
            </CardDescription>
          </div>
          <Button asChild variant="outline" size="sm">
            <Link href="/tasks">
              Manage
              <ArrowRight className="size-3.5" />
            </Link>
          </Button>
        </CardHeader>
        <CardContent className="space-y-2">
          {tasksQuery.isError ? (
            <p className="text-sm font-medium text-destructive">
              {getApiErrorMessage(tasksQuery.error, "Failed to load tasks")}
            </p>
          ) : null}
          {tasks.map((task) => (
            <TaskQuickRow
              key={task.id}
              task={task}
              queryKey={[...tasksKey]}
            />
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
