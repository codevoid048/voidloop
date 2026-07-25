import { apiClient } from "@/lib/api/client"
import type { AuthTokens, UserProfile } from "@/lib/auth"

export interface LoginRequest {
  email: string
  password: string
}

export interface AuthResponse extends AuthTokens {
  user: UserProfile
}

export const authApi = {
  login: async (payload: LoginRequest): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>("/auth/login", payload)
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
