"use client"

import { useEffect } from "react"
import { usePathname, useRouter } from "next/navigation"
import { Loader2 } from "lucide-react"
import { useAuthStore } from "@/stores/useAuthStore"

interface RequireAuthProps {
  children: React.ReactNode
}

export function RequireAuth({ children }: RequireAuthProps) {
  const router = useRouter()
  const pathname = usePathname()
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const isHydrated = useAuthStore((state) => state.isHydrated)

  useEffect(() => {
    if (!isHydrated) return
    if (!isAuthenticated) {
      const returnTo = pathname && pathname !== "/" ? pathname : undefined
      const query = returnTo
        ? `?returnTo=${encodeURIComponent(returnTo)}`
        : ""
      router.replace(`/login${query}`)
    }
  }, [isAuthenticated, isHydrated, pathname, router])

  if (!isHydrated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="size-8 animate-spin text-primary" />
          <p className="text-sm font-bold text-muted-foreground">
            Checking session...
          </p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  return <>{children}</>
}
