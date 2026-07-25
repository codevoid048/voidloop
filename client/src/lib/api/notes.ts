import { apiClient } from "@/lib/api/client"

export interface NoteFolder {
  id: number
  name: string
  color: string
  parent_id: number | null
  sort_order: number
  created_at: string
  updated_at: string
}

export interface NoteListItem {
  id: number
  title: string
  folder_id: number | null
  is_pinned: boolean
  is_archived: boolean
  sort_order: number
  preview: string
  created_at: string
  updated_at: string
}

export interface Note {
  id: number
  title: string
  content: string
  folder_id: number | null
  is_pinned: boolean
  is_archived: boolean
  sort_order: number
  created_at: string
  updated_at: string
}

export type NotesArchivedFilter = "active" | "archived" | "all"

export interface NoteListParams {
  folderId?: number | null
  unfiled?: boolean
  archived?: NotesArchivedFilter
  pinnedOnly?: boolean
  q?: string
}

export interface NoteCreatePayload {
  title: string
  content?: string
  folder_id?: number | null
  is_pinned?: boolean
}

export interface NoteUpdatePayload {
  title?: string
  content?: string
  folder_id?: number | null
  is_pinned?: boolean
  is_archived?: boolean
}

export interface FolderCreatePayload {
  name: string
  color?: string
  parent_id?: number | null
}

export interface FolderUpdatePayload {
  name?: string
  color?: string
  parent_id?: number | null
}

export const notesApi = {
  listFolders: async (): Promise<NoteFolder[]> => {
    const response = await apiClient.get<NoteFolder[]>("/notes/folders")
    return response.data
  },

  createFolder: async (payload: FolderCreatePayload): Promise<NoteFolder> => {
    const response = await apiClient.post<NoteFolder>("/notes/folders", payload)
    return response.data
  },

  updateFolder: async (
    id: number,
    payload: FolderUpdatePayload,
  ): Promise<NoteFolder> => {
    const response = await apiClient.patch<NoteFolder>(
      `/notes/folders/${id}`,
      payload,
    )
    return response.data
  },

  deleteFolder: async (id: number): Promise<void> => {
    await apiClient.delete(`/notes/folders/${id}`)
  },

  list: async (params: NoteListParams = {}): Promise<NoteListItem[]> => {
    const response = await apiClient.get<NoteListItem[]>("/notes", {
      params: {
        folder_id: params.folderId ?? undefined,
        unfiled: params.unfiled ?? false,
        archived: params.archived ?? "active",
        pinned_only: params.pinnedOnly ?? false,
        q: params.q || undefined,
      },
    })
    return response.data
  },

  get: async (id: number): Promise<Note> => {
    const response = await apiClient.get<Note>(`/notes/${id}`)
    return response.data
  },

  create: async (payload: NoteCreatePayload): Promise<Note> => {
    const response = await apiClient.post<Note>("/notes", payload)
    return response.data
  },

  update: async (id: number, payload: NoteUpdatePayload): Promise<Note> => {
    const response = await apiClient.patch<Note>(`/notes/${id}`, payload)
    return response.data
  },

  remove: async (id: number): Promise<void> => {
    await apiClient.delete(`/notes/${id}`)
  },

  pin: async (id: number): Promise<Note> => {
    const response = await apiClient.post<Note>(`/notes/${id}/pin`)
    return response.data
  },

  unpin: async (id: number): Promise<Note> => {
    const response = await apiClient.post<Note>(`/notes/${id}/unpin`)
    return response.data
  },

  archive: async (id: number): Promise<Note> => {
    const response = await apiClient.post<Note>(`/notes/${id}/archive`)
    return response.data
  },

  unarchive: async (id: number): Promise<Note> => {
    const response = await apiClient.post<Note>(`/notes/${id}/unarchive`)
    return response.data
  },
}
