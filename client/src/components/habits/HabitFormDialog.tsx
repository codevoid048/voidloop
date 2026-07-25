"use client"

import { FormEvent, useEffect, useState } from "react"
import type { Habit } from "@/lib/api/habits"
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

const HABIT_COLORS = [
  "#7c3aed",
  "#2563eb",
  "#059669",
  "#d97706",
  "#e11d48",
  "#0891b2",
  "#4b5563",
]

export type HabitFormValues = {
  name: string
  description: string
  color: string
}

function emptyValues(): HabitFormValues {
  return {
    name: "",
    description: "",
    color: HABIT_COLORS[0],
  }
}

function valuesFromHabit(habit: Habit): HabitFormValues {
  return {
    name: habit.name,
    description: habit.description,
    color: habit.color || HABIT_COLORS[0],
  }
}

type HabitFormDialogProps = {
  open: boolean
  mode: "create" | "edit"
  habit?: Habit | null
  isSubmitting?: boolean
  error?: string | null
  onOpenChange: (open: boolean) => void
  onSubmit: (values: HabitFormValues) => void
}

export function HabitFormDialog({
  open,
  mode,
  habit,
  isSubmitting,
  error,
  onOpenChange,
  onSubmit,
}: HabitFormDialogProps) {
  const [values, setValues] = useState<HabitFormValues>(emptyValues())

  useEffect(() => {
    if (!open) return
    setValues(habit ? valuesFromHabit(habit) : emptyValues())
  }, [open, habit])

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    onSubmit(values)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="font-black">
            {mode === "create" ? "Add habit" : "Edit habit"}
          </DialogTitle>
          <DialogDescription>
            One clear daily action. Color helps it stand out in the list.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="habit-name">Name</Label>
            <Input
              id="habit-name"
              value={values.name}
              onChange={(e) =>
                setValues((prev) => ({ ...prev, name: e.target.value }))
              }
              placeholder="e.g. Morning stretch"
              maxLength={120}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="habit-description">Description</Label>
            <Textarea
              id="habit-description"
              value={values.description}
              onChange={(e) =>
                setValues((prev) => ({
                  ...prev,
                  description: e.target.value,
                }))
              }
              placeholder="Why this matters"
              className="border-2 border-border"
            />
          </div>

          <div className="space-y-2">
            <Label>Color</Label>
            <div className="flex flex-wrap gap-2">
              {HABIT_COLORS.map((color) => (
                <button
                  key={color}
                  type="button"
                  onClick={() => setValues((prev) => ({ ...prev, color }))}
                  className={`size-8 rounded-md border-2 border-border ${
                    values.color === color ? "ring-2 ring-ring ring-offset-2" : ""
                  }`}
                  style={{ backgroundColor: color }}
                  aria-label={`Choose color ${color}`}
                  aria-pressed={values.color === color}
                />
              ))}
              <Input
                type="color"
                value={values.color}
                onChange={(e) =>
                  setValues((prev) => ({ ...prev, color: e.target.value }))
                }
                className="h-8 w-12 cursor-pointer p-1"
                aria-label="Custom color"
              />
            </div>
          </div>

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
            <Button
              type="submit"
              disabled={isSubmitting || !values.name.trim()}
            >
              {isSubmitting
                ? "Saving..."
                : mode === "create"
                  ? "Add habit"
                  : "Save changes"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
