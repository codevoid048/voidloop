import { apiClient } from "@/lib/api/client"

export type StatsRange = {
  since: string
  until: string
}

export type StatsSummary = {
  active_habits: number
  habit_completion_rate: number
  current_streaks_total: number
  best_streak: number
  tasks_done: number
  tasks_open: number
  tasks_overdue: number
}

export type HabitDayStat = {
  date: string
  completed: number
  total: number
}

export type HabitStreak = {
  id: number
  name: string
  color: string
  current_streak: number
}

export type TaskDayStat = {
  date: string
  done: number
  open: number
}

export type DashboardStats = {
  range: StatsRange
  summary: StatsSummary
  habits_by_day: HabitDayStat[]
  habit_streaks: HabitStreak[]
  tasks_by_day: TaskDayStat[]
}

export type StatsParams = {
  since?: string
  until?: string
}

export const statsApi = {
  get: async (params: StatsParams = {}): Promise<DashboardStats> => {
    const response = await apiClient.get<DashboardStats>("/stats", {
      params: {
        since: params.since,
        until: params.until,
      },
    })
    return response.data
  },
}
