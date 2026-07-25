"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation } from "@tanstack/react-query"
import { useRouter, useSearchParams } from "next/navigation"
import { useForm } from "react-hook-form"
import { useState } from "react"
import { z } from "zod"
import { getApiErrorMessage } from "@/lib/api/errors"
import { useAuthStore } from "@/stores/useAuthStore"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

const loginSchema = z.object({
  email: z.string().min(1, "Email or username is required"),
  password: z.string().min(1, "Password is required"),
})

type LoginFormValues = z.infer<typeof loginSchema>

function resolveDestination(returnTo: string | null): string {
  if (returnTo && returnTo.startsWith("/") && !returnTo.startsWith("//")) {
    return returnTo
  }
  return "/today"
}

export function LoginForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const login = useAuthStore((state) => state.login)
  const [bannerMessage, setBannerMessage] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  })

  const mutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      router.replace(resolveDestination(searchParams.get("returnTo")))
    },
    onError: (error) => {
      setBannerMessage(getApiErrorMessage(error, "Invalid credentials"))
    },
  })

  const onSubmit = (values: LoginFormValues) => {
    setBannerMessage(null)
    mutation.mutate(values)
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
      <div className="space-y-2">
        <Label htmlFor="email">Email or username</Label>
        <Input
          id="email"
          type="text"
          autoComplete="username"
          placeholder="you@example.com"
          aria-invalid={!!errors.email}
          {...register("email")}
        />
        {errors.email ? (
          <p className="text-xs font-medium text-destructive">
            {errors.email.message}
          </p>
        ) : null}
      </div>

      <div className="space-y-2">
        <Label htmlFor="password">Password</Label>
        <Input
          id="password"
          type="password"
          autoComplete="current-password"
          placeholder="••••••••"
          aria-invalid={!!errors.password}
          {...register("password")}
        />
        {errors.password ? (
          <p className="text-xs font-medium text-destructive">
            {errors.password.message}
          </p>
        ) : null}
      </div>

      {bannerMessage ? (
        <p className="rounded-md border-2 border-destructive bg-destructive/10 px-3 py-2 text-xs font-bold text-destructive">
          {bannerMessage}
        </p>
      ) : null}

      <Button type="submit" className="w-full" disabled={mutation.isPending}>
        {mutation.isPending ? "Signing in..." : "Sign in"}
      </Button>
    </form>
  )
}
