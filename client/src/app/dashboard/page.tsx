"use client"

import Link from "next/link"
import { ArrowLeft, ChartColumn, LogOut } from "lucide-react"
import { useState } from "react"
import { RequireAuth } from "@/components/auth/RequireAuth"
import { DashboardPanel } from "@/components/dashboard/DashboardPanel"
import { Button } from "@/components/ui/button"
import { useAuthStore } from "@/stores/useAuthStore"

function DashboardPageContent() {
  const user = useAuthStore((state) => state.user)
  const logout = useAuthStore((state) => state.logout)
  const [isLoggingOut, setIsLoggingOut] = useState(false)

  const handleLogout = async () => {
    setIsLoggingOut(true)
    await logout()
  }

  return (
    <div className="min-h-screen w-full bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] p-6 [background-size:16px_16px] md:p-12 dark:bg-[radial-gradient(#1f2937_1px,transparent_1px)]">
      <div className="mx-auto max-w-5xl space-y-8">
        <header className="flex flex-col gap-4 border-b-4 border-border pb-6 sm:flex-row sm:items-start sm:justify-between">
          <div className="space-y-2">
            <Button asChild variant="ghost" size="sm" className="-ml-2">
              <Link href="/">
                <ArrowLeft className="size-4" />
                Home
              </Link>
            </Button>
            <h1 className="flex items-center gap-2 text-3xl font-black tracking-tight">
              <ChartColumn className="size-7 text-primary" />
              Dashboard
            </h1>
            <p className="text-sm font-medium text-muted-foreground">
              {user?.name || user?.username
                ? `Trends for ${user.name || user.username}`
                : "Habits and task trends"}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button asChild variant="secondary">
              <Link href="/today">Today</Link>
            </Button>
            <Button asChild variant="secondary">
              <Link href="/habits">Habits</Link>
            </Button>
            <Button asChild variant="secondary">
              <Link href="/tasks">Tasks</Link>
            </Button>
            <Button asChild variant="secondary">
              <Link href="/notes">Notes</Link>
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

        <DashboardPanel />
      </div>
    </div>
  )
}

export default function DashboardPage() {
  return (
    <RequireAuth>
      <DashboardPageContent />
    </RequireAuth>
  )
}
