import axios from "axios"
import { AuthService } from "@/lib/auth"

const isServerRuntime = typeof window === "undefined"

/**
 * BFF: browser always hits same-origin /api/v1 (Next rewrite).
 * Server uses API_URL directly (never NEXT_PUBLIC_ — that would leak to the client bundle).
 */
const resolvedApiBaseUrl = isServerRuntime
  ? (process.env.API_URL || "http://127.0.0.1:8000/api/v1").replace(/\/$/, "")
  : "/api/v1"

export const apiClient = axios.create({
  baseURL: resolvedApiBaseUrl,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
})

const NON_RETRY_AUTH_ENDPOINTS = [
  "/auth/refresh",
  "/auth/login",
  "/auth/logout",
]

const shouldSkipRefreshForRequest = (url?: string) => {
  if (!url) return false
  return NON_RETRY_AUTH_ENDPOINTS.some((endpoint) => url.includes(endpoint))
}

const shouldForceLoginOnAuthFailure = (url?: string) => {
  if (!url) return true
  // Credential failures on login should stay on the form
  return !url.includes("/auth/login")
}

let refreshTokenPromise: Promise<boolean> | null = null

apiClient.interceptors.request.use(
  (config) => {
    if (typeof window === "undefined") {
      return config
    }

    const token = AuthService.getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

apiClient.interceptors.response.use(
  (response) => {
    if (
      response.data &&
      typeof response.data === "object" &&
      response.data.success === true &&
      "data" in response.data
    ) {
      const pagination =
        ("pagination" in response.data && response.data.pagination) ||
        (response.data.meta && response.data.meta.pagination)

      if (pagination) {
        response.data = {
          data: response.data.data,
          pagination,
          message: response.data.message,
        }
      } else {
        const data = response.data.data
        const message = response.data.message

        if (data && typeof data === "object" && !Array.isArray(data) && message) {
          response.data = { ...data, message }
        } else {
          response.data = data
        }
      }
    }
    return response
  },
  async (error) => {
    const originalRequest = error.config
    if (!originalRequest) {
      return Promise.reject(error)
    }

    const status = error.response?.status
    const requestUrl = originalRequest.url as string | undefined

    if (status !== 401) {
      return Promise.reject(error)
    }

    // Refresh (or logout) itself returned 401 → session is dead
    if (shouldSkipRefreshForRequest(requestUrl)) {
      if (shouldForceLoginOnAuthFailure(requestUrl)) {
        AuthService.forceLoginRedirect()
      }
      return Promise.reject(error)
    }

    if (originalRequest._retry) {
      AuthService.forceLoginRedirect()
      return Promise.reject(error)
    }

    originalRequest._retry = true

    try {
      if (!refreshTokenPromise) {
        refreshTokenPromise = AuthService.refreshToken()
      }

      const refreshed = await refreshTokenPromise
      refreshTokenPromise = null

      if (refreshed) {
        const newToken = AuthService.getRawAccessToken()
        if (newToken) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`
          return apiClient(originalRequest)
        }
      }

      AuthService.forceLoginRedirect()
    } catch {
      refreshTokenPromise = null
      AuthService.forceLoginRedirect()
    }

    return Promise.reject(error)
  },
)
