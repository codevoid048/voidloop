"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  Archive,
  ArchiveRestore,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  Flame,
  Pencil,
  Plus,
  Trash2,
} from "lucide-react"
import { useMemo, useState } from "react"
import { getApiErrorMessage } from "@/lib/api/errors"
import {
  habitsApi,
  type Habit,
  type HabitArchivedFilter,
} from "@/lib/api/habits"
import {
  formatDisplayDate,
  shiftISODate,
  todayISODate,
} from "@/lib/tasks/date"
import {
  HabitFormDialog,
  type HabitFormValues,
} from "@/components/habits/HabitFormDialog"
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

function HabitRow({
  habit,
  onDate,
  queryKey,
  onEdit,
  canMoveUp,
  canMoveDown,
  onMove,
}: {
  habit: Habit
  onDate: string
  queryKey: unknown[]
  onEdit: (habit: Habit) => void
  canMoveUp: boolean
  canMoveDown: boolean
  onMove: (habitId: number, direction: "up" | "down") => void
}) {
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)

  const invalidate = () => queryClient.invalidateQueries({ queryKey })

  const actionMutation = useMutation({
    mutationFn: async (
      action: "toggle" | "archive" | "unarchive" | "delete",
    ) => {
      if (action === "toggle") {
        if (habit.checked_in) {
          await habitsApi.undoCheckIn(habit.id, onDate)
        } else {
          await habitsApi.checkIn(habit.id, { on_date: onDate })
        }
        return
      }
      if (action === "archive") {
        await habitsApi.archive(habit.id)
        return
      }
      if (action === "unarchive") {
        await habitsApi.unarchive(habit.id)
        return
      }
      await habitsApi.remove(habit.id)
    },
    onSuccess: () => {
      setError(null)
      void invalidate()
    },
    onError: (err) => {
      setError(getApiErrorMessage(err, "Could not update habit"))
    },
  })

  return (
    <div
      className={`flex items-start gap-3 rounded-md border-2 border-border p-3 ${
        habit.is_archived ? "bg-muted/60" : "bg-background"
      }`}
    >
      <button
        type="button"
        onClick={() => actionMutation.mutate("toggle")}
        disabled={actionMutation.isPending || habit.is_archived}
        aria-pressed={habit.checked_in}
        aria-label={
          habit.checked_in
            ? `Undo check-in for ${habit.name}`
            : `Check in ${habit.name}`
        }
        className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded border-2 border-border transition-colors disabled:opacity-40"
        style={{
          backgroundColor: habit.checked_in ? habit.color : "transparent",
        }}
      >
        {habit.checked_in ? (
          <span className="text-xs font-black text-white">✓</span>
        ) : null}
      </button>

      <div className="min-w-0 flex-1 space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <span
            className="size-2.5 shrink-0 rounded-full border border-border"
            style={{ backgroundColor: habit.color }}
          />
          <p
            className={`truncate text-sm font-black ${
              habit.is_archived ? "text-muted-foreground" : ""
            }`}
          >
            {habit.name}
          </p>
          {habit.current_streak > 0 ? (
            <span className="inline-flex items-center gap-1 rounded border-2 border-border bg-secondary px-1.5 py-0.5 text-[10px] font-bold">
              <Flame className="size-3" />
              {habit.current_streak} day
              {habit.current_streak === 1 ? "" : "s"}
            </span>
          ) : null}
          {habit.is_archived ? <Badge variant="outline">Archived</Badge> : null}
        </div>
        {habit.description ? (
          <p className="text-xs font-medium text-muted-foreground">
            {habit.description}
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
            onClick={() => onMove(habit.id, "up")}
            aria-label="Move up"
          >
            <ChevronUp className="size-3.5" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon-xs"
            disabled={!canMoveDown || actionMutation.isPending}
            onClick={() => onMove(habit.id, "down")}
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
            onClick={() => onEdit(habit)}
            aria-label={`Edit ${habit.name}`}
          >
            <Pencil className="size-4" />
          </Button>
          {habit.is_archived ? (
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              disabled={actionMutation.isPending}
              onClick={() => actionMutation.mutate("unarchive")}
              aria-label={`Unarchive ${habit.name}`}
            >
              <ArchiveRestore className="size-4" />
            </Button>
          ) : (
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              disabled={actionMutation.isPending}
              onClick={() => actionMutation.mutate("archive")}
              aria-label={`Archive ${habit.name}`}
            >
              <Archive className="size-4" />
            </Button>
          )}
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            disabled={actionMutation.isPending}
            onClick={() => {
              if (window.confirm(`Delete “${habit.name}”?`)) {
                actionMutation.mutate("delete")
              }
            }}
            aria-label={`Delete ${habit.name}`}
          >
            <Trash2 className="size-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}

export function HabitsPanel() {
  const queryClient = useQueryClient()
  const [onDate, setOnDate] = useState(todayISODate)
  const [archivedFilter, setArchivedFilter] =
    useState<HabitArchivedFilter>("active")
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingHabit, setEditingHabit] = useState<Habit | null>(null)
  const [formError, setFormError] = useState<string | null>(null)

  const queryKey = useMemo(
    () => ["habits", onDate, archivedFilter] as const,
    [onDate, archivedFilter],
  )

  const habitsQuery = useQuery({
    queryKey,
    queryFn: () =>
      habitsApi.list({
        onDate,
        archived: archivedFilter,
      }),
  })

  const saveMutation = useMutation({
    mutationFn: async (values: HabitFormValues) => {
      const payload = {
        name: values.name.trim(),
        description: values.description.trim(),
        color: values.color,
      }
      if (editingHabit) {
        return habitsApi.update(editingHabit.id, payload)
      }
      return habitsApi.create(payload)
    },
    onSuccess: () => {
      setFormError(null)
      setDialogOpen(false)
      setEditingHabit(null)
      void queryClient.invalidateQueries({ queryKey: ["habits"] })
    },
    onError: (err) => {
      setFormError(getApiErrorMessage(err, "Could not save habit"))
    },
  })

  const reorderMutation = useMutation({
    mutationFn: (orderedIds: number[]) => habitsApi.reorder(orderedIds),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey })
    },
  })

  const habits = habitsQuery.data ?? []
  const doneCount = habits.filter((h) => h.checked_in).length
  const isToday = onDate === todayISODate()

  const openEdit = (habit: Habit) => {
    setEditingHabit(habit)
    setFormError(null)
    setDialogOpen(true)
  }

  const openCreate = () => {
    setEditingHabit(null)
    setFormError(null)
    setDialogOpen(true)
  }

  const moveHabit = (habitId: number, direction: "up" | "down") => {
    const index = habits.findIndex((habit) => habit.id === habitId)
    if (index < 0) return
    const target = direction === "up" ? index - 1 : index + 1
    if (target < 0 || target >= habits.length) return

    const next = [...habits]
    const [item] = next.splice(index, 1)
    next.splice(target, 0, item)
    reorderMutation.mutate(next.map((habit) => habit.id))
  }

  const filterButtons: { id: HabitArchivedFilter; label: string }[] = [
    { id: "active", label: "Active" },
    { id: "archived", label: "Archived" },
    { id: "all", label: "All" },
  ]

  return (
    <div className="mx-auto grid w-full max-w-3xl gap-6">
      <Card>
        <CardHeader className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <CardTitle className="text-xl">
                {isToday ? "Today" : "Check-ins"}
              </CardTitle>
              <CardDescription>
                {habitsQuery.isLoading
                  ? "Loading habits..."
                  : habits.length === 0
                    ? archivedFilter === "archived"
                      ? "No archived habits."
                      : "No habits yet — add your first one."
                    : `${doneCount} of ${habits.length} checked in`}
              </CardDescription>
            </div>
            <Button type="button" onClick={openCreate}>
              <Plus className="size-4" />
              Add habit
            </Button>
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

          <div className="flex flex-wrap gap-2">
            {filterButtons.map((filter) => (
              <Button
                key={filter.id}
                type="button"
                size="sm"
                variant={archivedFilter === filter.id ? "default" : "outline"}
                onClick={() => setArchivedFilter(filter.id)}
              >
                {filter.label}
              </Button>
            ))}
          </div>
        </CardHeader>

        <CardContent className="space-y-3">
          {habitsQuery.isError ? (
            <p className="text-sm font-medium text-destructive">
              {getApiErrorMessage(habitsQuery.error, "Failed to load habits")}
            </p>
          ) : null}

          {habits.map((habit, index) => (
            <HabitRow
              key={habit.id}
              habit={habit}
              onDate={onDate}
              queryKey={[...queryKey]}
              onEdit={openEdit}
              canMoveUp={index > 0}
              canMoveDown={index < habits.length - 1}
              onMove={moveHabit}
            />
          ))}
        </CardContent>
      </Card>

      <HabitFormDialog
        open={dialogOpen}
        mode={editingHabit ? "edit" : "create"}
        habit={editingHabit}
        isSubmitting={saveMutation.isPending}
        error={formError}
        onOpenChange={(open) => {
          setDialogOpen(open)
          if (!open) {
            setEditingHabit(null)
            setFormError(null)
          }
        }}
        onSubmit={(values) => saveMutation.mutate(values)}
      />
    </div>
  )
}
