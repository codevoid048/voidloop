import { Suspense } from "react"
import { AuthShell } from "@/components/auth/AuthShell"
import { GuestOnly } from "@/components/auth/GuestOnly"
import { RegisterForm } from "@/components/auth/RegisterForm"
import { Loader2 } from "lucide-react"

function AuthLoading() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <Loader2 className="size-8 animate-spin text-primary" />
    </div>
  )
}

export default function RegisterPage() {
  return (
    <Suspense fallback={<AuthLoading />}>
      <GuestOnly>
        <AuthShell
          title="Create account"
          subtitle="Use your invite link to join Void Loop."
        >
          <RegisterForm />
        </AuthShell>
      </GuestOnly>
    </Suspense>
  )
}
