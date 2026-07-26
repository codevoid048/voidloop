"use client"

import Link from "next/link"
import { ArrowLeft, LogOut, NotebookPen } from "lucide-react"
import { useState } from "react"
import { RequireAuth } from "@/components/auth/RequireAuth"
import { StaffInvitesNavButton } from "@/components/auth/StaffInvitesNavButton"
import { NotesPanel } from "@/components/notes/NotesPanel"
import { Button } from "@/components/ui/button"
import { useAuthStore } from "@/stores/useAuthStore"

function NotesPageContent() {
  const user = useAuthStore((state) => state.user)
  const logout = useAuthStore((state) => state.logout)
  const [isLoggingOut, setIsLoggingOut] = useState(false)

  const handleLogout = async () => {
    setIsLoggingOut(true)
    await logout()
  }

  return (
    <div className="min-h-screen w-full bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] p-3 [background-size:16px_16px] sm:p-6 md:p-10 dark:bg-[radial-gradient(#1f2937_1px,transparent_1px)]">
      <div className="mx-auto max-w-6xl space-y-5 sm:space-y-8">
        <header className="flex flex-col gap-4 border-b-4 border-border pb-4 sm:flex-row sm:items-start sm:justify-between sm:pb-6">
          <div className="space-y-1.5 sm:space-y-2">
            <Button asChild variant="ghost" size="sm" className="-ml-2">
              <Link href="/">
                <ArrowLeft className="size-4" />
                Home
              </Link>
            </Button>
            <h1 className="flex items-center gap-2 text-2xl font-black tracking-tight sm:text-3xl">
              <NotebookPen className="size-6 text-primary sm:size-7" />
              Notes
            </h1>
            <p className="text-sm font-medium text-muted-foreground">
              {user?.name || user?.username
                ? `Rich notes for ${user.name || user.username}`
                : "Folders, rich text, pin and archive"}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button asChild variant="default" size="sm">
              <Link href="/today">Today</Link>
            </Button>
            <Button asChild variant="secondary" size="sm">
              <Link href="/dashboard">Dashboard</Link>
            </Button>
            <Button asChild variant="secondary" size="sm">
              <Link href="/habits">Habits</Link>
            </Button>
            <Button asChild variant="secondary" size="sm">
              <Link href="/tasks">Tasks</Link>
            </Button>
            <StaffInvitesNavButton />
            <Button
              variant="outline"
              size="sm"
              onClick={handleLogout}
              disabled={isLoggingOut}
            >
              <LogOut className="size-4" />
              {isLoggingOut ? "Signing out..." : "Sign out"}
            </Button>
          </div>
        </header>

        <NotesPanel />
      </div>
    </div>
  )
}

export default function NotesPage() {
  return (
    <RequireAuth>
      <NotesPageContent />
    </RequireAuth>
  )
}
