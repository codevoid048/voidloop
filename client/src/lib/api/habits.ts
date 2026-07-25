import { apiClient } from "@/lib/api/client"

export interface Habit {
  id: number
  name: string
  description: string
  color: string
  is_archived: boolean
  sort_order: number
  checked_in: boolean
  checked_in_today: boolean
  current_streak: number
  created_at: string
  updated_at: string
}

export interface HabitCheckIn {
  id: number
  habit_id: number
  date: string
  note: string
  created_at: string
}

export interface HabitCreatePayload {
  name: string
  description?: string
  color?: string
  sort_order?: number
}

export interface HabitUpdatePayload {
  name?: string
  description?: string
  color?: string
  is_archived?: boolean
  sort_order?: number
}

export type HabitArchivedFilter = "active" | "archived" | "all"

export interface HabitListParams {
  onDate?: string
  archived?: HabitArchivedFilter
}

export const habitsApi = {
  list: async (params: HabitListParams = {}): Promise<Habit[]> => {
    const response = await apiClient.get<Habit[]>("/habits", {
      params: {
        on_date: params.onDate,
        archived: params.archived ?? "active",
      },
    })
    return response.data
  },

  create: async (payload: HabitCreatePayload): Promise<Habit> => {
    const response = await apiClient.post<Habit>("/habits", payload)
    return response.data
  },

  update: async (id: number, payload: HabitUpdatePayload): Promise<Habit> => {
    const response = await apiClient.patch<Habit>(`/habits/${id}`, payload)
    return response.data
  },

  remove: async (id: number): Promise<void> => {
    await apiClient.delete(`/habits/${id}`)
  },

  archive: async (id: number): Promise<Habit> => {
    const response = await apiClient.post<Habit>(`/habits/${id}/archive`)
    return response.data
  },

  unarchive: async (id: number): Promise<Habit> => {
    const response = await apiClient.post<Habit>(`/habits/${id}/unarchive`)
    return response.data
  },

  reorder: async (orderedIds: number[]): Promise<Habit[]> => {
    const response = await apiClient.post<Habit[]>("/habits/reorder", {
      ordered_ids: orderedIds,
    })
    return response.data
  },

  listCheckIns: async (
    id: number,
    params: { since?: string; until?: string; limit?: number } = {},
  ): Promise<HabitCheckIn[]> => {
    const response = await apiClient.get<HabitCheckIn[]>(
      `/habits/${id}/check-ins`,
      {
        params: {
          since: params.since,
          until: params.until,
          limit: params.limit,
        },
      },
    )
    return response.data
  },

  checkIn: async (
    id: number,
    payload: { on_date?: string; note?: string } = {},
  ): Promise<HabitCheckIn> => {
    const response = await apiClient.post<HabitCheckIn>(
      `/habits/${id}/check-ins`,
      payload,
    )
    return response.data
  },

  undoCheckIn: async (id: number, onDate?: string): Promise<void> => {
    await apiClient.delete(`/habits/${id}/check-ins`, {
      params: { on_date: onDate },
    })
  },
}
