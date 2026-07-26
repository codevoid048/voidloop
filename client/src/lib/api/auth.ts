import { apiClient } from "@/lib/api/client"
import type { AuthTokens, UserProfile } from "@/lib/auth"

export interface LoginRequest {
  email: string
  password: string
  cf_turnstile_token: string
}

export interface RegisterRequest {
  email: string
  username: string
  password: string
  name?: string
  invite_token: string
  cf_turnstile_token: string
}

export interface AuthResponse extends AuthTokens {
  user: UserProfile
}

export interface InviteValidateResponse {
  valid: boolean
  email: string | null
  status: string
  expires_at: string | null
}

export const authApi = {
  login: async (payload: LoginRequest): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>("/auth/login", payload)
    return response.data
  },

  register: async (payload: RegisterRequest): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>("/auth/register", payload)
    return response.data
  },

  validateInvite: async (token: string): Promise<InviteValidateResponse> => {
    const response = await apiClient.get<InviteValidateResponse>(
      `/auth/invites/${encodeURIComponent(token)}`,
    )
    return response.data
  },

  logout: async (refresh?: string | null): Promise<void> => {
    if (!refresh) return
    await apiClient.post("/auth/logout", { refresh })
  },

  me: async (): Promise<UserProfile> => {
    const response = await apiClient.get<UserProfile>("/auth/me")
    return response.data
  },
}
