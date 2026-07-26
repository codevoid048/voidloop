"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery } from "@tanstack/react-query"
import { useRouter, useSearchParams } from "next/navigation"
import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { authApi } from "@/lib/api/auth"
import { getApiErrorMessage } from "@/lib/api/errors"
import { useAuthStore } from "@/stores/useAuthStore"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { PasswordInput } from "@/components/auth/PasswordInput"
import { TurnstileField } from "@/components/auth/TurnstileField"
import Link from "next/link"
import { Loader2 } from "lucide-react"

const registerSchema = z.object({
  email: z.string().email("Enter a valid email"),
  username: z
    .string()
    .min(3, "Username must be at least 3 characters")
    .max(150, "Username is too long"),
  name: z.string().max(255).optional(),
  password: z.string().min(6, "Password must be at least 6 characters"),
})

type RegisterFormValues = z.infer<typeof registerSchema>

export function RegisterForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams.get("token")?.trim() ?? ""
  const registerUser = useAuthStore((state) => state.register)
  const [bannerMessage, setBannerMessage] = useState<string | null>(null)
  const [turnstileToken, setTurnstileToken] = useState("")
  const [turnstileKey, setTurnstileKey] = useState(0)

  const inviteQuery = useQuery({
    queryKey: ["invite-validate", token],
    queryFn: () => authApi.validateInvite(token),
    enabled: Boolean(token),
    retry: false,
  })

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: "",
      username: "",
      name: "",
      password: "",
    },
  })

  const emailLocked = Boolean(inviteQuery.data?.valid && inviteQuery.data.email)

  useEffect(() => {
    if (inviteQuery.data?.valid && inviteQuery.data.email) {
      setValue("email", inviteQuery.data.email)
    }
  }, [inviteQuery.data, setValue])

  const mutation = useMutation({
    mutationFn: registerUser,
    onSuccess: () => {
      router.replace("/today")
    },
    onError: (error) => {
      setBannerMessage(getApiErrorMessage(error, "Registration failed"))
      setTurnstileToken("")
      setTurnstileKey((key) => key + 1)
    },
  })

  const onSubmit = (values: RegisterFormValues) => {
    if (!token) return
    if (!turnstileToken) {
      setBannerMessage("Please complete the security check")
      return
    }
    setBannerMessage(null)
    mutation.mutate({
      email: values.email,
      username: values.username,
      password: values.password,
      name: values.name || "",
      invite_token: token,
      cf_turnstile_token: turnstileToken,
    })
  }

  if (!token) {
    return (
      <div className="space-y-4 text-center">
        <p className="text-sm font-medium text-destructive">
          An invite link is required to create an account.
        </p>
        <Button asChild variant="secondary">
          <Link href="/login">Back to sign in</Link>
        </Button>
      </div>
    )
  }

  if (inviteQuery.isLoading) {
    return (
      <div className="flex flex-col items-center gap-3 py-6">
        <Loader2 className="size-6 animate-spin text-primary" />
        <p className="text-sm font-medium text-muted-foreground">
          Checking invite…
        </p>
      </div>
    )
  }

  if (inviteQuery.isError || !inviteQuery.data?.valid) {
    const status = inviteQuery.data?.status ?? "invalid"
    const message =
      status === "expired"
        ? "This invite has expired."
        : status === "revoked"
          ? "This invite has been revoked."
          : status === "used"
            ? "This invite has already been used."
            : "This invite link is not valid."

    return (
      <div className="space-y-4 text-center">
        <p className="text-sm font-medium text-destructive">{message}</p>
        <Button asChild variant="secondary">
          <Link href="/login">Back to sign in</Link>
        </Button>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
      {bannerMessage ? (
        <p className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive">
          {bannerMessage}
        </p>
      ) : null}

      <div className="space-y-2">
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          type="email"
          autoComplete="email"
          readOnly={emailLocked}
          aria-invalid={!!errors.email}
          {...register("email")}
        />
        {emailLocked ? (
          <p className="text-xs font-medium text-muted-foreground">
            This invite is locked to this email.
          </p>
        ) : null}
        {errors.email ? (
          <p className="text-xs font-medium text-destructive">
            {errors.email.message}
          </p>
        ) : null}
      </div>

      <div className="space-y-2">
        <Label htmlFor="username">Username</Label>
        <Input
          id="username"
          type="text"
          autoComplete="username"
          aria-invalid={!!errors.username}
          {...register("username")}
        />
        {errors.username ? (
          <p className="text-xs font-medium text-destructive">
            {errors.username.message}
          </p>
        ) : null}
      </div>

      <div className="space-y-2">
        <Label htmlFor="name">Name (optional)</Label>
        <Input
          id="name"
          type="text"
          autoComplete="name"
          aria-invalid={!!errors.name}
          {...register("name")}
        />
        {errors.name ? (
          <p className="text-xs font-medium text-destructive">
            {errors.name.message}
          </p>
        ) : null}
      </div>

      <div className="space-y-2">
        <Label htmlFor="password">Password</Label>
        <PasswordInput
          id="password"
          autoComplete="new-password"
          aria-invalid={!!errors.password}
          {...register("password")}
        />
        {errors.password ? (
          <p className="text-xs font-medium text-destructive">
            {errors.password.message}
          </p>
        ) : null}
      </div>

      <TurnstileField key={turnstileKey} onTokenChange={setTurnstileToken} />

      <Button
        type="submit"
        className="w-full"
        disabled={mutation.isPending || !turnstileToken}
      >
        {mutation.isPending ? "Creating account…" : "Create account"}
      </Button>

      <p className="text-center text-xs font-medium text-muted-foreground">
        Already have an account?{" "}
        <Link href="/login" className="underline underline-offset-2">
          Sign in
        </Link>
      </p>
    </form>
  )
}
