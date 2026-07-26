"use client"

import Link from "next/link"
import { useEffect } from "react"
import { ArrowLeft, LogOut, MailPlus } from "lucide-react"
import { useRouter } from "next/navigation"
import { useState } from "react"
import { RequireAuth } from "@/components/auth/RequireAuth"
import { InvitesPanel } from "@/components/invites/InvitesPanel"
import { Button } from "@/components/ui/button"
import { useAuthStore } from "@/stores/useAuthStore"
import { Loader2 } from "lucide-react"

function InvitesPageContent() {
  const router = useRouter()
  const user = useAuthStore((state) => state.user)
  const isHydrated = useAuthStore((state) => state.isHydrated)
  const logout = useAuthStore((state) => state.logout)
  const [isLoggingOut, setIsLoggingOut] = useState(false)

  useEffect(() => {
    if (!isHydrated || !user) return
    if (!user.is_staff) {
      router.replace("/today")
    }
  }, [isHydrated, user, router])

  const handleLogout = async () => {
    setIsLoggingOut(true)
    await logout()
  }

  if (!user?.is_staff) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="size-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="min-h-screen w-full bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] p-6 [background-size:16px_16px] md:p-12 dark:bg-[radial-gradient(#1f2937_1px,transparent_1px)]">
      <div className="mx-auto max-w-3xl space-y-8">
        <header className="flex items-center justify-between border-b-4 border-border pb-6">
          <div className="space-y-2">
            <Button asChild variant="ghost" size="sm" className="-ml-2">
              <Link href="/">
                <ArrowLeft className="size-4" />
                Home
              </Link>
            </Button>
            <h1 className="flex items-center gap-2 text-3xl font-black tracking-tight">
              <MailPlus className="size-7 text-primary" />
              Invites
            </h1>
            <p className="text-sm font-medium text-muted-foreground">
              Create invite links and share them manually.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button asChild variant="secondary">
              <Link href="/today">Today</Link>
            </Button>
            <Button asChild variant="secondary">
              <Link href="/dashboard">Dashboard</Link>
            </Button>
            <Button
              variant="outline"
              onClick={handleLogout}
              disabled={isLoggingOut}
            >
              <LogOut className="size-4" />
              {isLoggingOut ? "Signing out..." : "Sign out"}
            </Button>
          </div>
        </header>

        <InvitesPanel />
      </div>
    </div>
  )
}

export default function InvitesPage() {
  return (
    <RequireAuth>
      <InvitesPageContent />
    </RequireAuth>
  )
}
