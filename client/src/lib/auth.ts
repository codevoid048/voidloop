import { jwtDecode } from "jwt-decode"

export interface UserProfile {
  id: number
  email: string
  username: string
  name: string
  is_active: boolean
}

export interface AuthTokens {
  access: string
  refresh: string
}

const TOKEN_KEY = "auth_tokens"
const USER_KEY = "auth_user"

const AUTH_PAGES = ["/login"]

export class AuthService {
  static setTokens(tokens: AuthTokens): void {
    localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens))
  }

  static getTokens(): AuthTokens | null {
    const tokens = localStorage.getItem(TOKEN_KEY)
    return tokens ? JSON.parse(tokens) : null
  }

  static removeTokens(): void {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  static setUser(user: UserProfile): void {
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  }

  static getUser(): UserProfile | null {
    const user = localStorage.getItem(USER_KEY)
    return user ? JSON.parse(user) : null
  }

  static isTokenValid(token: string): boolean {
    try {
      const decoded = jwtDecode<{ exp?: number }>(token)
      if (!decoded.exp) return false
      // Small leeway so we refresh slightly before exact expiry
      return decoded.exp * 1000 > Date.now() + 5_000
    } catch {
      return false
    }
  }

  /** Session is alive if refresh token is still valid. */
  static isAuthenticated(): boolean {
    const tokens = this.getTokens()
    if (!tokens?.refresh) return false
    return this.isTokenValid(tokens.refresh)
  }

  static getAccessToken(): string | null {
    const tokens = this.getTokens()
    if (!tokens || !this.isTokenValid(tokens.access)) {
      return null
    }
    return tokens.access
  }

  static getRawAccessToken(): string | null {
    const tokens = this.getTokens()
    return tokens?.access || null
  }

  static async refreshToken(): Promise<boolean> {
    const tokens = this.getTokens()
    if (!tokens?.refresh || !this.isTokenValid(tokens.refresh)) {
      this.logout()
      return false
    }

    try {
      const { apiClient } = await import("@/lib/api/client")
      const response = await apiClient.post("/auth/refresh", {
        refresh: tokens.refresh,
      })

      const data = response.data as Partial<AuthTokens>
      if (!data.access) {
        this.logout()
        return false
      }

      const updatedTokens: AuthTokens = {
        access: data.access,
        refresh: data.refresh ?? tokens.refresh,
      }

      this.setTokens(updatedTokens)
      this.onTokenRefresh?.(updatedTokens)
      this.emitAuthChange()
      return true
    } catch {
      this.logout()
      return false
    }
  }

  static onTokenRefresh: ((tokens: AuthTokens) => void) | null = null

  static logout(): void {
    this.removeTokens()
    this.emitAuthChange()
  }

  static emitAuthChange(): void {
    if (typeof window !== "undefined") {
      window.dispatchEvent(new Event("auth-state-change"))
    }
  }

  static isAuthPage(pathname: string): boolean {
    return AUTH_PAGES.some(
      (page) => pathname === page || pathname.startsWith(`${page}/`),
    )
  }

  /** Clear session and hard-redirect to login (used on 401 / refresh failure). */
  static forceLoginRedirect(returnTo?: string): void {
    this.logout()

    if (typeof window === "undefined") return

    const pathname = window.location.pathname
    if (this.isAuthPage(pathname)) return

    const target =
      returnTo && returnTo.startsWith("/")
        ? returnTo
        : `${pathname}${window.location.search}`

    const params = new URLSearchParams()
    if (target && target !== "/") {
      params.set("returnTo", target)
    }

    const query = params.toString()
    window.location.href = query ? `/login?${query}` : "/login"
  }
}
