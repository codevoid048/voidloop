import { Suspense } from "react"
import { AuthShell } from "@/components/auth/AuthShell"
import { GuestOnly } from "@/components/auth/GuestOnly"
import { LoginForm } from "@/components/auth/LoginForm"
import { Loader2 } from "lucide-react"

function AuthLoading() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <Loader2 className="size-8 animate-spin text-primary" />
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={<AuthLoading />}>
      <GuestOnly>
        <AuthShell
          title="Sign in"
          subtitle="Welcome back. Pick up where you left off."
        >
          <LoginForm />
        </AuthShell>
      </GuestOnly>
    </Suspense>
  )
}
