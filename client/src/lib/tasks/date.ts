/** Local calendar helpers for the tasks UI (no UTC date drift). */

export function todayISODate(): string {
  return formatISODate(new Date())
}

export function formatISODate(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, "0")
  const day = String(date.getDate()).padStart(2, "0")
  return `${year}-${month}-${day}`
}

export function parseISODate(value: string): Date {
  const [year, month, day] = value.split("-").map(Number)
  return new Date(year, month - 1, day)
}

export function shiftISODate(value: string, days: number): string {
  const date = parseISODate(value)
  date.setDate(date.getDate() + days)
  return formatISODate(date)
}

export function formatDisplayDate(value: string): string {
  return parseISODate(value).toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
  })
}

export function formatDueTime(dueTime: string | null): string | null {
  if (!dueTime) return null
  return dueTime.slice(0, 5)
}

export function toTimeInput(dueTime: string | null): string {
  return formatDueTime(dueTime) ?? ""
}

export function fromTimeInput(value: string): string | null {
  if (!value) return null
  return `${value}:00`
}

/** Convert API ISO datetime → `datetime-local` value. */
export function toDateTimeLocal(iso: string | null): string {
  if (!iso) return ""
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ""
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, "0")
  const day = String(date.getDate()).padStart(2, "0")
  const hours = String(date.getHours()).padStart(2, "0")
  const minutes = String(date.getMinutes()).padStart(2, "0")
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

/** Convert `datetime-local` → ISO string for the API. */
export function fromDateTimeLocal(value: string): string | null {
  if (!value) return null
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return null
  return date.toISOString()
}

export function formatScheduleRange(
  startsAt: string | null,
  endsAt: string | null,
): string | null {
  if (!startsAt) return null
  const start = new Date(startsAt)
  if (Number.isNaN(start.getTime())) return null

  const startLabel = start.toLocaleTimeString(undefined, {
    hour: "numeric",
    minute: "2-digit",
  })

  if (!endsAt) return startLabel

  const end = new Date(endsAt)
  if (Number.isNaN(end.getTime())) return startLabel

  const endLabel = end.toLocaleTimeString(undefined, {
    hour: "numeric",
    minute: "2-digit",
  })
  return `${startLabel} – ${endLabel}`
}
