"use client"

import { useEffect } from "react"
import {
  syncAuthStoreFromStorage,
  useAuthStore,
} from "@/stores/useAuthStore"

/**
 * Boots auth state from localStorage and keeps the store in sync
 * with interceptor-driven logout / token refresh events.
 */
export function AuthBootstrap() {
  const checkAuthStatus = useAuthStore((state) => state.checkAuthStatus)
  const setHydrated = useAuthStore((state) => state.setHydrated)

  useEffect(() => {
    let cancelled = false

    const boot = async () => {
      await checkAuthStatus()
      if (!cancelled) {
        setHydrated()
      }
    }

    void boot()

    const onAuthChange = () => {
      syncAuthStoreFromStorage()
    }

    window.addEventListener("auth-state-change", onAuthChange)
    return () => {
      cancelled = true
      window.removeEventListener("auth-state-change", onAuthChange)
    }
  }, [checkAuthStatus, setHydrated])

  return null
}
