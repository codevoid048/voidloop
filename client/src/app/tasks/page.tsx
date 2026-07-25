"use client"

import Link from "next/link"
import { ArrowLeft, CalendarDays, LogOut } from "lucide-react"
import { useState } from "react"
import { RequireAuth } from "@/components/auth/RequireAuth"
import { TasksPanel } from "@/components/tasks/TasksPanel"
import { Button } from "@/components/ui/button"
import { useAuthStore } from "@/stores/useAuthStore"

function TasksPageContent() {
  const user = useAuthStore((state) => state.user)
  const logout = useAuthStore((state) => state.logout)
  const [isLoggingOut, setIsLoggingOut] = useState(false)

  const handleLogout = async () => {
    setIsLoggingOut(true)
    await logout()
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
              <CalendarDays className="size-7 text-primary" />
              Tasks
            </h1>
            <p className="text-sm font-medium text-muted-foreground">
              {user?.name || user?.username
                ? `Daily plan for ${user.name || user.username}`
                : "Daily tasks and schedule"}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button asChild variant="default">
              <Link href="/today">Today</Link>
            </Button>
            <Button asChild variant="secondary">
              <Link href="/dashboard">Dashboard</Link>
            </Button>
            <Button asChild variant="secondary">
              <Link href="/habits">Habits</Link>
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

        <TasksPanel />
      </div>
    </div>
  )
}

export default function TasksPage() {
  return (
    <RequireAuth>
      <TasksPageContent />
    </RequireAuth>
  )
}
