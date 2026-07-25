import axios from "axios"

export function getApiErrorMessage(
  error: unknown,
  fallback = "Something went wrong. Please try again.",
): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data

    if (typeof data === "string" && data.trim()) {
      return data
    }

    if (data && typeof data === "object") {
      const record = data as Record<string, unknown>

      if (typeof record.message === "string" && record.message.trim()) {
        return record.message
      }

      if (typeof record.detail === "string" && record.detail.trim()) {
        return record.detail
      }

      if (record.error && typeof record.error === "object") {
        const nested = record.error as Record<string, unknown>
        if (typeof nested.message === "string" && nested.message.trim()) {
          return nested.message
        }
      }
    }

    if (error.message) {
      return error.message
    }
  }

  if (error instanceof Error && error.message) {
    return error.message
  }

  return fallback
}
