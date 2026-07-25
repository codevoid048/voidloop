import { apiClient } from "@/lib/api/client"

export type TaskStatus = "todo" | "done" | "cancelled"
export type TaskPriority = "none" | "low" | "medium" | "high"

export interface Task {
  id: number
  title: string
  description: string
  status: TaskStatus
  priority: TaskPriority
  due_date: string | null
  due_time: string | null
  starts_at: string | null
  ends_at: string | null
  completed_at: string | null
  sort_order: number
  is_done: boolean
  created_at: string
  updated_at: string
}

export interface TaskCreatePayload {
  title: string
  description?: string
  status?: TaskStatus
  priority?: TaskPriority
  due_date?: string | null
  due_time?: string | null
  starts_at?: string | null
  ends_at?: string | null
  sort_order?: number
  undated?: boolean
}

export interface TaskUpdatePayload {
  title?: string
  description?: string
  status?: TaskStatus
  priority?: TaskPriority
  due_date?: string | null
  due_time?: string | null
  starts_at?: string | null
  ends_at?: string | null
  sort_order?: number
}

export interface TaskListParams {
  onDate?: string
  status?: TaskStatus
  includeUndated?: boolean
  inboxOnly?: boolean
  includeCancelled?: boolean
}

export const tasksApi = {
  list: async (params: TaskListParams = {}): Promise<Task[]> => {
    const response = await apiClient.get<Task[]>("/tasks", {
      params: {
        on_date: params.onDate,
        status: params.status,
        include_undated: params.includeUndated ?? false,
        inbox_only: params.inboxOnly ?? false,
        include_cancelled: params.includeCancelled ?? false,
      },
    })
    return response.data
  },

  create: async (payload: TaskCreatePayload): Promise<Task> => {
    const response = await apiClient.post<Task>("/tasks", payload)
    return response.data
  },

  update: async (id: number, payload: TaskUpdatePayload): Promise<Task> => {
    const response = await apiClient.patch<Task>(`/tasks/${id}`, payload)
    return response.data
  },

  remove: async (id: number): Promise<void> => {
    await apiClient.delete(`/tasks/${id}`)
  },

  complete: async (id: number): Promise<Task> => {
    const response = await apiClient.post<Task>(`/tasks/${id}/complete`)
    return response.data
  },

  reopen: async (id: number): Promise<Task> => {
    const response = await apiClient.post<Task>(`/tasks/${id}/reopen`)
    return response.data
  },

  cancel: async (id: number): Promise<Task> => {
    const response = await apiClient.post<Task>(`/tasks/${id}/cancel`)
    return response.data
  },

  reorder: async (orderedIds: number[]): Promise<Task[]> => {
    const response = await apiClient.post<Task[]>("/tasks/reorder", {
      ordered_ids: orderedIds,
    })
    return response.data
  },
}
