"use client"

import { useQuery } from "@tanstack/react-query"
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { Flame } from "lucide-react"
import { useMemo, useState } from "react"
import { getApiErrorMessage } from "@/lib/api/errors"
import { statsApi } from "@/lib/api/stats"
import {
  formatDisplayDate,
  shiftISODate,
  todayISODate,
} from "@/lib/tasks/date"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

type RangeDays = 7 | 30

function shortDayLabel(iso: string): string {
  const date = new Date(`${iso}T12:00:00`)
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" })
}

function KpiCard({
  label,
  value,
  hint,
}: {
  label: string
  value: string | number
  hint?: string
}) {
  return (
    <Card className="border-2 border-border shadow-brutalist">
      <CardHeader className="pb-2">
        <CardDescription className="text-[11px] font-bold uppercase tracking-wide">
          {label}
        </CardDescription>
        <CardTitle className="text-3xl font-black tabular-nums">{value}</CardTitle>
      </CardHeader>
      {hint ? (
        <CardContent className="pt-0">
          <p className="text-xs font-medium text-muted-foreground">{hint}</p>
        </CardContent>
      ) : null}
    </Card>
  )
}

export function DashboardPanel() {
  const [rangeDays, setRangeDays] = useState<RangeDays>(30)

  const { since, until } = useMemo(() => {
    const untilDate = todayISODate()
    const sinceDate = shiftISODate(untilDate, -(rangeDays - 1))
    return { since: sinceDate, until: untilDate }
  }, [rangeDays])

  const statsQuery = useQuery({
    queryKey: ["stats", since, until],
    queryFn: () => statsApi.get({ since, until }),
  })

  const habitsChart = useMemo(() => {
    const rows = statsQuery.data?.habits_by_day ?? []
    return rows.map((row) => ({
      ...row,
      label: shortDayLabel(row.date),
      rate:
        row.total > 0
          ? Math.round((row.completed / row.total) * 100)
          : 0,
    }))
  }, [statsQuery.data?.habits_by_day])

  const tasksChart = useMemo(() => {
    const rows = statsQuery.data?.tasks_by_day ?? []
    return rows.map((row) => ({
      ...row,
      label: shortDayLabel(row.date),
    }))
  }, [statsQuery.data?.tasks_by_day])

  if (statsQuery.isLoading) {
    return (
      <p className="text-sm font-medium text-muted-foreground">
        Loading dashboard…
      </p>
    )
  }

  if (statsQuery.isError) {
    return (
      <p className="text-sm font-bold text-destructive">
        {getApiErrorMessage(statsQuery.error, "Failed to load stats")}
      </p>
    )
  }

  const summary = statsQuery.data!.summary
  const streaks = statsQuery.data!.habit_streaks
  const empty =
    summary.active_habits === 0 &&
    summary.tasks_done === 0 &&
    summary.tasks_open === 0

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-muted-foreground">
            {formatDisplayDate(since)} → {formatDisplayDate(until)}
          </p>
        </div>
        <div className="flex gap-1.5">
          {([7, 30] as const).map((days) => (
            <Button
              key={days}
              type="button"
              size="sm"
              variant={rangeDays === days ? "default" : "outline"}
              onClick={() => setRangeDays(days)}
            >
              {days}d
            </Button>
          ))}
        </div>
      </div>

      {empty ? (
        <Card className="border-2 border-border shadow-brutalist">
          <CardHeader>
            <CardTitle className="font-black">Nothing to chart yet</CardTitle>
            <CardDescription>
              Check in habits and complete tasks — trends show up here.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          label="Habit completion"
          value={`${summary.habit_completion_rate}%`}
          hint={`${summary.active_habits} active habit${summary.active_habits === 1 ? "" : "s"}`}
        />
        <KpiCard
          label="Best streak"
          value={summary.best_streak}
          hint={`${summary.current_streaks_total} total streak days`}
        />
        <KpiCard
          label="Tasks done"
          value={summary.tasks_done}
          hint="In this range"
        />
        <KpiCard
          label="Open / overdue"
          value={`${summary.tasks_open} / ${summary.tasks_overdue}`}
          hint="Open todos · overdue count"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="border-2 border-border shadow-brutalist">
          <CardHeader>
            <CardTitle className="font-black">Habit check-ins</CardTitle>
            <CardDescription>Daily completion rate (%)</CardDescription>
          </CardHeader>
          <CardContent className="h-64">
            {habitsChart.every((r) => r.total === 0) ? (
              <p className="text-sm text-muted-foreground">No active habits.</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={habitsChart}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
                  <Tooltip
                    formatter={(value) => [`${value}%`, "Completion"]}
                    labelFormatter={(_, payload) => {
                      const row = payload?.[0]?.payload as
                        | { date?: string }
                        | undefined
                      return row?.date ? formatDisplayDate(row.date) : ""
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="rate"
                    stroke="var(--primary)"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card className="border-2 border-border shadow-brutalist">
          <CardHeader>
            <CardTitle className="font-black">Tasks by day</CardTitle>
            <CardDescription>Done vs open (by due / completed date)</CardDescription>
          </CardHeader>
          <CardContent className="h-64">
            {tasksChart.every((r) => r.done === 0 && r.open === 0) ? (
              <p className="text-sm text-muted-foreground">
                No dated tasks in this range.
              </p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={tasksChart}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                  <Tooltip
                    labelFormatter={(_, payload) => {
                      const row = payload?.[0]?.payload as
                        | { date?: string }
                        | undefined
                      return row?.date ? formatDisplayDate(row.date) : ""
                    }}
                  />
                  <Legend />
                  <Bar dataKey="done" name="Done" fill="var(--primary)" />
                  <Bar dataKey="open" name="Open" fill="var(--secondary)" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="border-2 border-border shadow-brutalist">
        <CardHeader>
          <CardTitle className="font-black">Habit streaks</CardTitle>
          <CardDescription>Current streaks on active habits</CardDescription>
        </CardHeader>
        <CardContent>
          {streaks.length === 0 ? (
            <p className="text-sm text-muted-foreground">No active habits.</p>
          ) : (
            <ul className="space-y-2">
              {streaks.map((habit) => (
                <li
                  key={habit.id}
                  className="flex items-center justify-between gap-3 rounded-md border-2 border-border bg-background px-3 py-2"
                >
                  <div className="flex min-w-0 items-center gap-2">
                    <span
                      className="size-3 shrink-0 rounded-full border border-border"
                      style={{ backgroundColor: habit.color }}
                    />
                    <span className="truncate text-sm font-bold">
                      {habit.name}
                    </span>
                  </div>
                  <span className="inline-flex items-center gap-1 rounded border-2 border-border bg-secondary px-2 py-0.5 text-xs font-black tabular-nums">
                    <Flame className="size-3.5" />
                    {habit.current_streak}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
