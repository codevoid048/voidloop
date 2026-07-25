"use client"

import Link from "next/link"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card"
import {
  Calendar,
  Code,
  Sparkles,
  Moon,
  Sun,
  ArrowRight,
  LogOut,
  LogIn,
} from "lucide-react"
import { useAuthStore } from "@/stores/useAuthStore"

export default function Home() {
  const user = useAuthStore((state) => state.user)
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const isHydrated = useAuthStore((state) => state.isHydrated)
  const logout = useAuthStore((state) => state.logout)
  const [darkMode, setDarkMode] = useState(false)
  const [isLoggingOut, setIsLoggingOut] = useState(false)

  const toggleDarkMode = () => {
    setDarkMode(!darkMode)
    if (!darkMode) {
      document.documentElement.classList.add("dark")
    } else {
      document.documentElement.classList.remove("dark")
    }
  }

  const handleLogout = async () => {
    setIsLoggingOut(true)
    await logout()
  }

  return (
    <div className="min-h-screen w-full bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] p-6 transition-colors duration-200 [background-size:16px_16px] md:p-12 dark:bg-[radial-gradient(#1f2937_1px,transparent_1px)]">
      <div className="mx-auto max-w-6xl space-y-10">
        <header className="flex items-center justify-between border-b-4 border-border pb-6">
          <div className="space-y-1">
            <h1 className="flex items-center gap-2 text-4xl font-black tracking-tight">
              Void Loop
            </h1>
            <p className="font-medium text-muted-foreground">
              {isAuthenticated && (user?.name || user?.username)
                ? `Signed in as ${user.name || user.username}`
                : "Habits, tasks, notes — your daily loop"}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="icon"
              onClick={toggleDarkMode}
              aria-label="Toggle theme"
            >
              {darkMode ? <Sun className="size-5" /> : <Moon className="size-5" />}
            </Button>
            {isHydrated && isAuthenticated ? (
              <>
                <Button asChild variant="default">
                  <Link href="/today">Today</Link>
                </Button>
                <Button asChild variant="secondary">
                  <Link href="/dashboard">Dashboard</Link>
                </Button>
                <Button asChild variant="secondary">
                  <Link href="/tasks">Tasks</Link>
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
              </>
            ) : (
              <Button asChild>
                <Link href="/login">
                  <LogIn className="size-4" />
                  Login
                </Link>
              </Button>
            )}
          </div>
        </header>

        <section className="grid grid-cols-1 gap-6 md:grid-cols-3">
          <Card className="transition-transform hover:rotate-1">
            <CardHeader>
              <div className="mb-2 flex size-10 items-center justify-center rounded border-2 border-border bg-primary/10">
                <Calendar className="size-6 text-primary" />
              </div>
              <CardTitle>Daily Tasks</CardTitle>
              <CardDescription>
                Plan today, mark done, leave room for timed schedule blocks.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm font-medium">
                Built for daily todos now — ready for calendar slots and sync
                later.
              </p>
              <Button asChild variant="secondary" className="w-full justify-between">
                <Link href={isAuthenticated ? "/tasks" : "/login?returnTo=/tasks"}>
                  Open tasks
                  <ArrowRight className="size-4" />
                </Link>
              </Button>
            </CardContent>
          </Card>

          <Card className="transition-transform hover:-rotate-1">
            <CardHeader>
              <div className="mb-2 flex size-10 items-center justify-center rounded border-2 border-border bg-secondary/10">
                <Code className="size-6 text-secondary-foreground" />
              </div>
              <CardTitle>Notes</CardTitle>
              <CardDescription>
                Rich text notes with folders, pin, and archive.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm font-medium">
                Write like a doc — headings, lists, checklists. No Markdown
                required.
              </p>
              <Button asChild variant="secondary" className="w-full justify-between">
                <Link href={isAuthenticated ? "/notes" : "/login?returnTo=/notes"}>
                  Open notes
                  <ArrowRight className="size-4" />
                </Link>
              </Button>
            </CardContent>
          </Card>

          <Card className="transition-transform hover:rotate-1">
            <CardHeader>
              <div className="mb-2 flex size-10 items-center justify-center rounded border-2 border-border bg-accent/20">
                <Sparkles className="size-6 text-accent-foreground" />
              </div>
              <CardTitle>Habits & Streaks</CardTitle>
              <CardDescription>
                Log everyday patterns and maintain consistent streaks.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm font-medium">
                Check in daily, track streaks, and keep the loop small enough to
                stick.
              </p>
              <Button asChild variant="secondary" className="w-full justify-between">
                <Link href={isAuthenticated ? "/habits" : "/login?returnTo=/habits"}>
                  Open habits
                  <ArrowRight className="size-4" />
                </Link>
              </Button>
            </CardContent>
          </Card>
        </section>

        <section className="pt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-xl">Technical Blueprint Status</CardTitle>
              <CardDescription>
                Core loops are live — including stats dashboard.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex items-center justify-between rounded border border-border bg-muted p-2 text-xs font-bold">
                <span>JWT Auth + Refresh Redirects</span>
                <span className="text-primary">Ready</span>
              </div>
              <div className="flex items-center justify-between rounded border border-border bg-muted p-2 text-xs font-bold">
                <span>Today dashboard</span>
                <span className="text-primary">Ready</span>
              </div>
              <div className="flex items-center justify-between rounded border border-border bg-muted p-2 text-xs font-bold">
                <span>Stats / trends dashboard</span>
                <span className="text-primary">Ready</span>
              </div>
              <div className="flex items-center justify-between rounded border border-border bg-muted p-2 text-xs font-bold">
                <span>Habits + Check-ins</span>
                <span className="text-primary">Ready</span>
              </div>
              <div className="flex items-center justify-between rounded border border-border bg-muted p-2 text-xs font-bold">
                <span>Daily Tasks / Schedules</span>
                <span className="text-primary">Ready</span>
              </div>
              <div className="flex items-center justify-between rounded border border-border bg-muted p-2 text-xs font-bold">
                <span>Notes (rich text + folders)</span>
                <span className="text-primary">Ready</span>
              </div>
              <div className="flex items-center justify-between rounded border border-border bg-muted p-2 text-xs font-bold">
                <span>Calendar sync</span>
                <span className="text-muted-foreground">Later</span>
              </div>
            </CardContent>
            <CardFooter>
              <Button asChild variant="secondary" className="group w-full justify-between">
                <Link href={isAuthenticated ? "/dashboard" : "/login?returnTo=/dashboard"}>
                  Open dashboard
                  <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
                </Link>
              </Button>
            </CardFooter>
          </Card>
        </section>
      </div>
    </div>
  )
}
