import { apiClient } from "@/lib/api/client"

export interface Invite {
  id: number
  token: string
  email: string | null
  expires_at: string
  max_uses: number
  uses_count: number
  status: string
  invite_path: string
  created_at: string
  revoked_at: string | null
  created_by_id: number
}

export interface CreateInviteRequest {
  email?: string
  max_uses?: number
  expires_in_days?: number
}

export const invitesApi = {
  list: async (): Promise<Invite[]> => {
    const response = await apiClient.get<Invite[]>("/invites")
    return response.data
  },

  create: async (payload: CreateInviteRequest): Promise<Invite> => {
    const response = await apiClient.post<Invite>("/invites", payload)
    return response.data
  },

  revoke: async (id: number): Promise<Invite> => {
    const response = await apiClient.delete<Invite>(`/invites/${id}`)
    return response.data
  },
}

export function inviteAbsoluteUrl(invitePath: string): string {
  if (typeof window === "undefined") return invitePath
  return `${window.location.origin}${invitePath}`
}
