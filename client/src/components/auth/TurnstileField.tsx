"use client"

import { Turnstile } from "@marsidev/react-turnstile"

const siteKey = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY ?? ""

type TurnstileFieldProps = {
  onTokenChange: (token: string) => void
}

export function TurnstileField({ onTokenChange }: TurnstileFieldProps) {
  if (!siteKey) {
    return (
      <p className="text-xs font-medium text-destructive">
        Turnstile site key is not configured (NEXT_PUBLIC_TURNSTILE_SITE_KEY).
      </p>
    )
  }

  return (
    <div className="flex justify-center">
      <Turnstile
        siteKey={siteKey}
        onSuccess={(token) => onTokenChange(token)}
        onError={() => onTokenChange("")}
        onExpire={() => onTokenChange("")}
        options={{ theme: "auto" }}
      />
    </div>
  )
}
