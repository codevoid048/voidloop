import Link from "next/link"
import { Sparkles } from "lucide-react"
import type { ReactNode } from "react"

type AuthShellProps = {
  title: string
  subtitle: string
  children: ReactNode
}

export function AuthShell({ title, subtitle, children }: AuthShellProps) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] [background-size:16px_16px] p-6 dark:bg-[radial-gradient(#1f2937_1px,transparent_1px)]">
      <div className="w-full max-w-md space-y-6">
        <div className="space-y-2 text-center">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-2xl font-black tracking-tight"
          >
            Void Loop
          </Link>
          <h1 className="text-3xl font-black tracking-tight">{title}</h1>
          <p className="text-sm font-medium text-muted-foreground">{subtitle}</p>
        </div>

        <div className="rounded-md border-2 border-border bg-card p-6 shadow-brutalist">
          {children}
        </div>
      </div>
    </div>
  )
}
