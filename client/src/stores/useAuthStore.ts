import { create } from "zustand"
import { authApi, type LoginRequest, type RegisterRequest } from "@/lib/api/auth"
import { AuthService, type UserProfile } from "@/lib/auth"

interface AuthState {
  user: UserProfile | null
  isAuthenticated: boolean
  isLoading: boolean
  isHydrated: boolean

  login: (credentials: LoginRequest) => Promise<void>
  register: (payload: RegisterRequest) => Promise<void>
  logout: () => Promise<void>
  checkAuthStatus: () => Promise<void>
  setHydrated: () => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  isHydrated: false,

  setHydrated: () => set({ isHydrated: true }),

  clearAuth: () =>
    set({
      user: null,
      isAuthenticated: false,
      isLoading: false,
    }),

  login: async (credentials) => {
    const response = await authApi.login(credentials)
    AuthService.setTokens({
      access: response.access,
      refresh: response.refresh,
    })
    AuthService.setUser(response.user)
    set({
      user: response.user,
      isAuthenticated: true,
      isLoading: false,
    })
    AuthService.emitAuthChange()
  },

  register: async (payload) => {
    const response = await authApi.register(payload)
    AuthService.setTokens({
      access: response.access,
      refresh: response.refresh,
    })
    AuthService.setUser(response.user)
    set({
      user: response.user,
      isAuthenticated: true,
      isLoading: false,
    })
    AuthService.emitAuthChange()
  },

  logout: async () => {
    const tokens = AuthService.getTokens()
    try {
      await authApi.logout(tokens?.refresh)
    } catch {
      // Ignore logout API failures — clear local session anyway
    } finally {
      AuthService.logout()
      get().clearAuth()
      if (typeof window !== "undefined") {
        window.location.href = "/login"
      }
    }
  },

  checkAuthStatus: async () => {
    set({ isLoading: true })

    if (!AuthService.isAuthenticated()) {
      AuthService.removeTokens()
      get().clearAuth()
      return
    }

    const cachedUser = AuthService.getUser()
    if (cachedUser) {
      set({
        user: cachedUser,
        isAuthenticated: true,
      })
    }

    try {
      if (!AuthService.getAccessToken()) {
        const refreshed = await AuthService.refreshToken()
        if (!refreshed) {
          get().clearAuth()
          return
        }
      }

      const user = await authApi.me()
      AuthService.setUser(user)
      set({
        user,
        isAuthenticated: true,
        isLoading: false,
      })
    } catch {
      AuthService.logout()
      get().clearAuth()
    }
  },
}))

export function syncAuthStoreFromStorage() {
  if (!AuthService.isAuthenticated()) {
    useAuthStore.getState().clearAuth()
    return
  }

  useAuthStore.setState({
    user: AuthService.getUser(),
    isAuthenticated: true,
    isLoading: false,
  })
}
