"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Check, Copy, Loader2 } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import {
  inviteAbsoluteUrl,
  invitesApi,
  type Invite,
} from "@/lib/api/invites"
import { getApiErrorMessage } from "@/lib/api/errors"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

const createInviteSchema = z.object({
  email: z.string().trim(),
  max_uses: z.number().int().min(1).max(100),
  expires_in_days: z.number().int().min(1).max(90),
}).superRefine((values, ctx) => {
  if (values.email && !z.string().email().safeParse(values.email).success) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["email"],
      message: "Enter a valid email",
    })
  }
})

type CreateInviteValues = z.infer<typeof createInviteSchema>

function statusLabel(status: string): string {
  switch (status) {
    case "pending":
      return "Pending"
    case "used":
      return "Used"
    case "expired":
      return "Expired"
    case "revoked":
      return "Revoked"
    default:
      return status
  }
}

function CopyInviteButton({ invite }: { invite: Invite }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    const url = inviteAbsoluteUrl(invite.invite_path)
    await navigator.clipboard.writeText(url)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1500)
  }

  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      onClick={handleCopy}
      disabled={invite.status !== "pending"}
    >
      {copied ? <Check className="size-4" /> : <Copy className="size-4" />}
      {copied ? "Copied" : "Copy link"}
    </Button>
  )
}

export function InvitesPanel() {
  const queryClient = useQueryClient()
  const [bannerMessage, setBannerMessage] = useState<string | null>(null)
  const [createdUrl, setCreatedUrl] = useState<string | null>(null)

  const invitesQuery = useQuery({
    queryKey: ["invites"],
    queryFn: invitesApi.list,
  })

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CreateInviteValues>({
    resolver: zodResolver(createInviteSchema),
    defaultValues: {
      email: "",
      max_uses: 1,
      expires_in_days: 7,
    },
  })

  const createMutation = useMutation({
    mutationFn: invitesApi.create,
    onSuccess: async (invite) => {
      setBannerMessage(null)
      setCreatedUrl(inviteAbsoluteUrl(invite.invite_path))
      reset({ email: "", max_uses: 1, expires_in_days: 7 })
      await queryClient.invalidateQueries({ queryKey: ["invites"] })
    },
    onError: (error) => {
      setCreatedUrl(null)
      setBannerMessage(getApiErrorMessage(error, "Could not create invite"))
    },
  })

  const revokeMutation = useMutation({
    mutationFn: invitesApi.revoke,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["invites"] })
    },
    onError: (error) => {
      setBannerMessage(getApiErrorMessage(error, "Could not revoke invite"))
    },
  })

  const onSubmit = (values: CreateInviteValues) => {
    setBannerMessage(null)
    createMutation.mutate({
      email: values.email?.trim() ? values.email.trim() : undefined,
      max_uses: values.max_uses,
      expires_in_days: values.expires_in_days,
    })
  }

  return (
    <div className="space-y-8">
      <Card>
        <CardHeader>
          <CardTitle>Create invite</CardTitle>
          <CardDescription>
            Leave email blank for an open shareable link. Copy the URL and send
            it yourself.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {bannerMessage ? (
            <p className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive">
              {bannerMessage}
            </p>
          ) : null}

          {createdUrl ? (
            <div className="space-y-2 rounded-md border-2 border-border bg-muted/40 p-3">
              <p className="text-xs font-bold uppercase tracking-wide text-muted-foreground">
                Invite link ready
              </p>
              <p className="break-all text-sm font-medium">{createdUrl}</p>
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={async () => {
                  await navigator.clipboard.writeText(createdUrl)
                }}
              >
                <Copy className="size-4" />
                Copy
              </Button>
            </div>
          ) : null}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
            <div className="space-y-2">
              <Label htmlFor="email">Email (optional)</Label>
              <Input
                id="email"
                type="email"
                placeholder="friend@example.com"
                aria-invalid={!!errors.email}
                {...register("email")}
              />
              {errors.email ? (
                <p className="text-xs font-medium text-destructive">
                  {errors.email.message}
                </p>
              ) : null}
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="max_uses">Max uses</Label>
                <Input
                  id="max_uses"
                  type="number"
                  min={1}
                  max={100}
                  aria-invalid={!!errors.max_uses}
                  {...register("max_uses", { valueAsNumber: true })}
                />
                {errors.max_uses ? (
                  <p className="text-xs font-medium text-destructive">
                    {errors.max_uses.message}
                  </p>
                ) : null}
              </div>
              <div className="space-y-2">
                <Label htmlFor="expires_in_days">Expires in (days)</Label>
                <Input
                  id="expires_in_days"
                  type="number"
                  min={1}
                  max={90}
                  aria-invalid={!!errors.expires_in_days}
                  {...register("expires_in_days", { valueAsNumber: true })}
                />
                {errors.expires_in_days ? (
                  <p className="text-xs font-medium text-destructive">
                    {errors.expires_in_days.message}
                  </p>
                ) : null}
              </div>
            </div>

            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? "Creating…" : "Create invite"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Invites</CardTitle>
          <CardDescription>
            Pending invites can be copied or revoked.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {invitesQuery.isLoading ? (
            <div className="flex items-center gap-2 py-6 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              Loading invites…
            </div>
          ) : null}

          {invitesQuery.isError ? (
            <p className="text-sm font-medium text-destructive">
              {getApiErrorMessage(invitesQuery.error, "Failed to load invites")}
            </p>
          ) : null}

          {invitesQuery.data && invitesQuery.data.length === 0 ? (
            <p className="text-sm font-medium text-muted-foreground">
              No invites yet.
            </p>
          ) : null}

          {invitesQuery.data && invitesQuery.data.length > 0 ? (
            <ul className="divide-y-2 divide-border rounded-md border-2 border-border">
              {invitesQuery.data.map((invite) => (
                <li
                  key={invite.id}
                  className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="space-y-1">
                    <p className="text-sm font-bold">
                      {invite.email || "Open shareable link"}
                    </p>
                    <p className="text-xs font-medium text-muted-foreground">
                      {statusLabel(invite.status)} · {invite.uses_count}/
                      {invite.max_uses} uses · expires{" "}
                      {new Date(invite.expires_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <CopyInviteButton invite={invite} />
                    {invite.status === "pending" ? (
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        disabled={revokeMutation.isPending}
                        onClick={() => revokeMutation.mutate(invite.id)}
                      >
                        Revoke
                      </Button>
                    ) : null}
                  </div>
                </li>
              ))}
            </ul>
          ) : null}
        </CardContent>
      </Card>
    </div>
  )
}
