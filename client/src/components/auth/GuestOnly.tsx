"use client"

import { useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Loader2 } from "lucide-react"
import { useAuthStore } from "@/stores/useAuthStore"

interface GuestOnlyProps {
  children: React.ReactNode
}

function resolveDestination(returnTo: string | null): string {
  if (returnTo && returnTo.startsWith("/") && !returnTo.startsWith("//")) {
    return returnTo
  }
  return "/today"
}

/**
 * For login/register: if a valid session exists, send the user into the app.
 */
export function GuestOnly({ children }: GuestOnlyProps) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const isHydrated = useAuthStore((state) => state.isHydrated)

  useEffect(() => {
    if (!isHydrated) return
    if (isAuthenticated) {
      router.replace(resolveDestination(searchParams.get("returnTo")))
    }
  }, [isAuthenticated, isHydrated, router, searchParams])

  if (!isHydrated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="size-8 animate-spin text-primary" />
          <p className="text-sm font-bold text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  if (isAuthenticated) {
    return null
  }

  return <>{children}</>
}
