"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { useAuthStore } from "@/stores/useAuthStore"

type StaffInvitesNavButtonProps = {
  variant?: "default" | "secondary" | "outline" | "ghost"
}

export function StaffInvitesNavButton({
  variant = "secondary",
}: StaffInvitesNavButtonProps) {
  const isStaff = useAuthStore((state) => state.user?.is_staff)

  if (!isStaff) return null

  return (
    <Button asChild variant={variant}>
      <Link href="/invites">Invites</Link>
    </Button>
  )
}
