"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  Archive,
  ArchiveRestore,
  ArrowLeft,
  BookOpen,
  FilePlus,
  FolderPlus,
  Pin,
  PinOff,
  Search,
  Trash2,
  X,
} from "lucide-react"
import { useEffect, useMemo, useRef, useState } from "react"
import { getApiErrorMessage } from "@/lib/api/errors"
import {
  notesApi,
  type NoteListItem,
  type NotesArchivedFilter,
} from "@/lib/api/notes"
import { NoteRichEditor } from "@/components/notes/NoteRichEditor"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

type Scope =
  | { kind: "all" }
  | { kind: "unfiled" }
  | { kind: "pinned" }
  | { kind: "folder"; folderId: number }

function formatUpdated(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ""
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  })
}

export function NotesPanel() {
  const queryClient = useQueryClient()
  const [scope, setScope] = useState<Scope>({ kind: "all" })
  const [archivedFilter, setArchivedFilter] =
    useState<NotesArchivedFilter>("active")
  const [search, setSearch] = useState("")
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [draftTitle, setDraftTitle] = useState("")
  const [draftContent, setDraftContent] = useState("")
  const [draftFolderId, setDraftFolderId] = useState<number | null>(null)
  const [editorKey, setEditorKey] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [newFolderName, setNewFolderName] = useState("")
  const [lastAutosavedAt, setLastAutosavedAt] = useState<number | null>(null)
  const [readingMode, setReadingMode] = useState(false)
  const [mobileEditorOpen, setMobileEditorOpen] = useState(false)
  const [confirm, setConfirm] = useState<{
    title: string
    description: string
    confirmLabel?: string
    onConfirm: () => void
  } | null>(null)
  const dirtyRef = useRef(false)
  const savePendingRef = useRef(false)
  const saveNoteRef = useRef<() => void>(() => {})

  const foldersQuery = useQuery({
    queryKey: ["note-folders"],
    queryFn: () => notesApi.listFolders(),
  })

  const listParams = useMemo(() => {
    if (scope.kind === "unfiled") {
      return { unfiled: true, archived: archivedFilter, q: search }
    }
    if (scope.kind === "pinned") {
      return { pinnedOnly: true, archived: archivedFilter, q: search }
    }
    if (scope.kind === "folder") {
      return {
        folderId: scope.folderId,
        archived: archivedFilter,
        q: search,
      }
    }
    return { archived: archivedFilter, q: search }
  }, [scope, archivedFilter, search])

  const notesQuery = useQuery({
    queryKey: ["notes", listParams],
    queryFn: () => notesApi.list(listParams),
  })

  const noteQuery = useQuery({
    queryKey: ["note", selectedId],
    queryFn: () => notesApi.get(selectedId!),
    enabled: selectedId != null,
  })

  // Sync drafts only when switching notes — not after autosave (avoids remount).
  useEffect(() => {
    if (!noteQuery.data) return
    setDraftTitle(noteQuery.data.title)
    setDraftContent(noteQuery.data.content)
    setDraftFolderId(noteQuery.data.folder_id)
    setEditorKey((key) => key + 1)
    setLastAutosavedAt(null)
    setError(null)
  }, [noteQuery.data?.id])

  const invalidateLists = () => {
    void queryClient.invalidateQueries({ queryKey: ["notes"] })
    void queryClient.invalidateQueries({ queryKey: ["note-folders"] })
  }

  const createNoteMutation = useMutation({
    mutationFn: () =>
      notesApi.create({
        title: "Untitled note",
        content: "",
        folder_id: scope.kind === "folder" ? scope.folderId : null,
      }),
    onSuccess: (note) => {
      invalidateLists()
      setSelectedId(note.id)
      setMobileEditorOpen(true)
    },
    onError: (err) => setError(getApiErrorMessage(err, "Could not create note")),
  })

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (selectedId == null) return null
      return notesApi.update(selectedId, {
        title: draftTitle.trim() || "Untitled note",
        content: draftContent,
        folder_id: draftFolderId,
      })
    },
    onSuccess: (note) => {
      if (!note) return
      setError(null)
      setLastAutosavedAt(Date.now())
      // Keep cache in sync without remounting the editor
      queryClient.setQueryData(["note", note.id], note)
      invalidateLists()
    },
    onError: (err) => setError(getApiErrorMessage(err, "Could not save note")),
  })

  const actionMutation = useMutation({
    mutationFn: async (
      action: "pin" | "unpin" | "archive" | "unarchive" | "delete",
    ) => {
      if (selectedId == null) return
      if (action === "pin") await notesApi.pin(selectedId)
      if (action === "unpin") await notesApi.unpin(selectedId)
      if (action === "archive") await notesApi.archive(selectedId)
      if (action === "unarchive") await notesApi.unarchive(selectedId)
      if (action === "delete") {
        await notesApi.remove(selectedId)
        setSelectedId(null)
        setMobileEditorOpen(false)
      }
    },
    onSuccess: () => {
      setError(null)
      if (selectedId != null) {
        void queryClient.invalidateQueries({ queryKey: ["note", selectedId] })
      }
      invalidateLists()
    },
    onError: (err) =>
      setError(getApiErrorMessage(err, "Could not update note")),
  })

  const createFolderMutation = useMutation({
    mutationFn: () =>
      notesApi.createFolder({ name: newFolderName.trim() || "New folder" }),
    onSuccess: (folder) => {
      setNewFolderName("")
      invalidateLists()
      setScope({ kind: "folder", folderId: folder.id })
    },
    onError: (err) =>
      setError(getApiErrorMessage(err, "Could not create folder")),
  })

  const deleteFolderMutation = useMutation({
    mutationFn: (folderId: number) => notesApi.deleteFolder(folderId),
    onSuccess: () => {
      setScope({ kind: "all" })
      invalidateLists()
    },
    onError: (err) =>
      setError(getApiErrorMessage(err, "Could not delete folder")),
  })

  const folders = foldersQuery.data ?? []
  const notes = notesQuery.data ?? []
  const selectedNote = noteQuery.data

  const isDirty =
    selectedNote != null &&
    (draftTitle !== selectedNote.title ||
      draftContent !== selectedNote.content ||
      draftFolderId !== selectedNote.folder_id)

  dirtyRef.current = isDirty
  savePendingRef.current = saveMutation.isPending
  saveNoteRef.current = () => {
    if (selectedId == null) return
    if (!dirtyRef.current || savePendingRef.current) return
    saveMutation.mutate()
  }

  // Autosave open notes every 30s when there are unsaved changes
  useEffect(() => {
    if (selectedId == null) return
    const timer = window.setInterval(() => {
      saveNoteRef.current()
    }, 30_000)
    return () => window.clearInterval(timer)
  }, [selectedId])

  useEffect(() => {
    setReadingMode(false)
  }, [selectedId])

  useEffect(() => {
    if (!readingMode) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setReadingMode(false)
    }
    const prevOverflow = document.body.style.overflow
    document.body.style.overflow = "hidden"
    window.addEventListener("keydown", onKeyDown)
    return () => {
      document.body.style.overflow = prevOverflow
      window.removeEventListener("keydown", onKeyDown)
    }
  }, [readingMode])

  const saveStatus = (() => {
    if (saveMutation.isPending) return "Saving…"
    if (isDirty) return "Unsaved · autosaves every 30s"
    if (lastAutosavedAt != null) {
      return `Saved ${formatUpdated(new Date(lastAutosavedAt).toISOString())}`
    }
    return null
  })()

  return (
    <div className="grid min-h-[70vh] overflow-hidden rounded-md border-2 border-border bg-card shadow-brutalist lg:h-[min(75vh,720px)] lg:min-h-0 lg:grid-cols-[320px_1fr]">
      {/* Sidebar: filters + folders + note list */}
      <aside
        className={`flex max-h-[70vh] flex-col border-b-2 border-border lg:max-h-none lg:border-r-2 lg:border-b-0 ${
          mobileEditorOpen ? "hidden lg:flex" : "flex"
        }`}
      >
        <div className="space-y-3 border-b-2 border-border p-4">
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-sm font-black uppercase tracking-wide">Notes</h2>
            <Button
              type="button"
              size="sm"
              onClick={() => createNoteMutation.mutate()}
              disabled={createNoteMutation.isPending}
            >
              <FilePlus className="size-4" />
              New
            </Button>
          </div>

          <div className="relative">
            <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search…"
              className="pl-8"
            />
          </div>

          <div className="flex flex-wrap gap-1.5">
            {(
              [
                ["active", "Active"],
                ["archived", "Archived"],
                ["all", "All"],
              ] as const
            ).map(([id, label]) => (
              <Button
                key={id}
                type="button"
                size="xs"
                variant={archivedFilter === id ? "default" : "outline"}
                onClick={() => setArchivedFilter(id)}
              >
                {label}
              </Button>
            ))}
          </div>

          <div className="flex flex-wrap gap-1.5">
            <ScopeChip
              active={scope.kind === "all"}
              label="All"
              onClick={() => setScope({ kind: "all" })}
            />
            <ScopeChip
              active={scope.kind === "pinned"}
              label="Pinned"
              onClick={() => setScope({ kind: "pinned" })}
            />
            <ScopeChip
              active={scope.kind === "unfiled"}
              label="Unfiled"
              onClick={() => setScope({ kind: "unfiled" })}
            />
            {folders.map((folder) => (
              <ScopeChip
                key={folder.id}
                active={scope.kind === "folder" && scope.folderId === folder.id}
                label={folder.name}
                color={folder.color}
                onClick={() =>
                  setScope({ kind: "folder", folderId: folder.id })
                }
                onDelete={() => {
                  setConfirm({
                    title: `Delete folder “${folder.name}”?`,
                    description:
                      "Notes in this folder will stay available as unfiled.",
                    confirmLabel: "Delete folder",
                    onConfirm: () => deleteFolderMutation.mutate(folder.id),
                  })
                }}
              />
            ))}
          </div>

          <div className="flex gap-2">
            <Input
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              placeholder="New folder"
              className="h-8"
              onKeyDown={(e) => {
                if (e.key === "Enter") createFolderMutation.mutate()
              }}
            />
            <Button
              type="button"
              size="icon-sm"
              variant="outline"
              onClick={() => createFolderMutation.mutate()}
              disabled={createFolderMutation.isPending}
              aria-label="Add folder"
            >
              <FolderPlus className="size-4" />
            </Button>
          </div>
        </div>

        <div className="flex-1 space-y-2 overflow-y-auto p-3">
          {notesQuery.isError ? (
            <p className="px-1 text-sm font-medium text-destructive">
              {getApiErrorMessage(notesQuery.error, "Failed to load notes")}
            </p>
          ) : null}
          {notes.length === 0 && !notesQuery.isLoading ? (
            <p className="px-1 text-sm font-medium text-muted-foreground">
              No notes here yet.
            </p>
          ) : null}
          {notes.map((note) => (
            <NoteListButton
              key={note.id}
              note={note}
              active={selectedId === note.id}
              onClick={() => {
                setSelectedId(note.id)
                setMobileEditorOpen(true)
              }}
            />
          ))}
        </div>
      </aside>

      {/* Main editor pane */}
      <section
        className={`min-h-[520px] flex-col lg:min-h-0 lg:h-full ${
          mobileEditorOpen ? "flex" : "hidden lg:flex"
        }`}
      >
        {selectedId == null ? (
          <div className="flex flex-1 flex-col items-center justify-center gap-3 p-8 text-center">
            <p className="text-lg font-black">Pick a note or start a new one</p>
            <p className="max-w-sm text-sm text-muted-foreground">
              Write with the toolbar — headings, lists, checklists, links. No
              Markdown required.
            </p>
            <Button
              type="button"
              onClick={() => createNoteMutation.mutate()}
              disabled={createNoteMutation.isPending}
            >
              <FilePlus className="size-4" />
              New note
            </Button>
          </div>
        ) : noteQuery.isLoading || !selectedNote ? (
          <div className="flex flex-1 items-center justify-center p-8 text-sm text-muted-foreground">
            Loading note…
          </div>
        ) : (
          <>
            <div className="flex flex-wrap items-center justify-between gap-3 border-b-2 border-border p-3 sm:p-4">
              <div className="flex min-w-0 flex-1 items-center gap-2">
                <Button
                  type="button"
                  size="icon-sm"
                  variant="outline"
                  className="shrink-0 lg:hidden"
                  onClick={() => setMobileEditorOpen(false)}
                  aria-label="Back to notes list"
                >
                  <ArrowLeft className="size-4" />
                </Button>
                <Input
                  value={draftTitle}
                  onChange={(e) => setDraftTitle(e.target.value)}
                  placeholder="Note title"
                  className="h-10 min-w-0 flex-1 border-0 bg-transparent px-0 text-xl font-black shadow-none focus-visible:ring-0 sm:h-11 sm:text-2xl"
                />
              </div>

              <div className="flex w-full flex-wrap items-center gap-1 sm:w-auto sm:justify-end">
                <select
                  id="note-folder"
                  aria-label="Folder"
                  title="Folder"
                  className="h-8 max-w-[40%] rounded-md border-2 border-border bg-background px-2 text-xs font-bold outline-none sm:max-w-none"
                  value={draftFolderId ?? ""}
                  onChange={(e) =>
                    setDraftFolderId(
                      e.target.value ? Number(e.target.value) : null,
                    )
                  }
                >
                  <option value="">Unfiled</option>
                  {folders.map((folder) => (
                    <option key={folder.id} value={folder.id}>
                      {folder.name}
                    </option>
                  ))}
                </select>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => setReadingMode(true)}
                  title="Reading mode"
                >
                  <BookOpen className="size-4" />
                  <span className="hidden sm:inline">Read</span>
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() =>
                    actionMutation.mutate(
                      selectedNote.is_pinned ? "unpin" : "pin",
                    )
                  }
                >
                  {selectedNote.is_pinned ? (
                    <PinOff className="size-4" />
                  ) : (
                    <Pin className="size-4" />
                  )}
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() =>
                    actionMutation.mutate(
                      selectedNote.is_archived ? "unarchive" : "archive",
                    )
                  }
                >
                  {selectedNote.is_archived ? (
                    <ArchiveRestore className="size-4" />
                  ) : (
                    <Archive className="size-4" />
                  )}
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setConfirm({
                      title: "Delete this note?",
                      description:
                        "This permanently removes the note. This can’t be undone.",
                      confirmLabel: "Delete note",
                      onConfirm: () => actionMutation.mutate("delete"),
                    })
                  }}
                >
                  <Trash2 className="size-4" />
                </Button>
                <Button
                  type="button"
                  size="sm"
                  onClick={() => saveMutation.mutate()}
                  disabled={!isDirty || saveMutation.isPending}
                  title={saveStatus ?? undefined}
                >
                  {saveMutation.isPending ? "Saving..." : "Save"}
                </Button>
              </div>
            </div>

            <div className="flex min-h-0 flex-1 flex-col overflow-hidden p-4">
              {error ? (
                <p className="mb-3 shrink-0 text-xs font-bold text-destructive">
                  {error}
                </p>
              ) : null}
              {!readingMode ? (
                <div className="min-h-0 flex-1">
                  <NoteRichEditor
                    key={`${selectedNote.id}-${editorKey}`}
                    content={draftContent}
                    onChange={setDraftContent}
                  />
                </div>
              ) : null}
            </div>

            {readingMode ? (
              <div className="fixed inset-0 z-50 flex flex-col bg-background">
                <div className="flex shrink-0 justify-end p-4 md:p-6">
                  <Button
                    type="button"
                    size="icon"
                    variant="outline"
                    onClick={() => setReadingMode(false)}
                    aria-label="Close reading mode"
                    title="Close (Esc)"
                  >
                    <X className="size-5" />
                  </Button>
                </div>
                <div className="flex-1 overflow-y-auto px-6 pb-16 md:px-10">
                  <article className="mx-auto w-full max-w-2xl">
                    <h1 className="mb-8 text-3xl font-black tracking-tight md:text-4xl">
                      {draftTitle.trim() || "Untitled note"}
                    </h1>
                    <NoteRichEditor
                      content={draftContent}
                      variant="read"
                      editable={false}
                    />
                  </article>
                </div>
              </div>
            ) : null}
          </>
        )}
      </section>

      <Dialog
        open={confirm != null}
        onOpenChange={(open) => {
          if (!open) setConfirm(null)
        }}
      >
        <DialogContent className="sm:max-w-md" showCloseButton>
          <DialogHeader>
            <DialogTitle className="font-black">
              {confirm?.title ?? "Confirm"}
            </DialogTitle>
            <DialogDescription>{confirm?.description}</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setConfirm(null)}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="destructive"
              onClick={() => {
                confirm?.onConfirm()
                setConfirm(null)
              }}
            >
              {confirm?.confirmLabel ?? "Confirm"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function ScopeChip({
  active,
  label,
  color,
  onClick,
  onDelete,
}: {
  active: boolean
  label: string
  color?: string
  onClick: () => void
  onDelete?: () => void
}) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md border-2 px-2 py-1 text-[11px] font-bold ${
        active
          ? "border-border bg-primary text-primary-foreground"
          : "border-border bg-background"
      }`}
    >
      <button type="button" onClick={onClick} className="inline-flex items-center gap-1">
        {color ? (
          <span
            className="size-2 rounded-full border border-border"
            style={{ backgroundColor: color }}
          />
        ) : null}
        {label}
      </button>
      {onDelete ? (
        <button
          type="button"
          onClick={onDelete}
          className="opacity-60 hover:opacity-100"
          aria-label={`Delete ${label}`}
        >
          ×
        </button>
      ) : null}
    </span>
  )
}

function NoteListButton({
  note,
  active,
  onClick,
}: {
  note: NoteListItem
  active: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-full rounded-md border-2 p-3 text-left transition-colors ${
        active
          ? "border-border bg-primary/10"
          : "border-border bg-background hover:bg-muted/50"
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <p className="truncate text-sm font-black">{note.title}</p>
        {note.is_pinned ? <Pin className="size-3.5 shrink-0" /> : null}
      </div>
      {note.preview ? (
        <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">
          {note.preview.replace(/<[^>]+>/g, " ")}
        </p>
      ) : null}
      <p className="mt-2 text-[10px] font-bold uppercase tracking-wide text-muted-foreground">
        {formatUpdated(note.updated_at)}
      </p>
    </button>
  )
}
