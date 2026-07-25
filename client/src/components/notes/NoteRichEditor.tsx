"use client"

import { useEditor, EditorContent, useEditorState } from "@tiptap/react"
import StarterKit from "@tiptap/starter-kit"
import Placeholder from "@tiptap/extension-placeholder"
import Link from "@tiptap/extension-link"
import Underline from "@tiptap/extension-underline"
import TaskList from "@tiptap/extension-task-list"
import TaskItem from "@tiptap/extension-task-item"
import { Table } from "@tiptap/extension-table"
import { TableRow } from "@tiptap/extension-table-row"
import { TableCell } from "@tiptap/extension-table-cell"
import { TableHeader } from "@tiptap/extension-table-header"
import {
  Bold,
  Italic,
  Underline as UnderlineIcon,
  Strikethrough,
  Heading1,
  Heading2,
  Heading3,
  List,
  ListOrdered,
  ListTodo,
  Quote,
  Code,
  SquareCode,
  Link2,
  Undo2,
  Redo2,
  Table as TableIcon,
  Plus,
  Minus,
  Trash2,
} from "lucide-react"
import { useEffect, useRef, useState } from "react"
import { MonacoCodeBlock } from "@/components/notes/MonacoCodeBlock"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { cn } from "@/lib/utils"

const LINE_SPACING = [
  { label: "Compact", value: "1.25" },
  { label: "Normal", value: "1.5" },
  { label: "Relaxed", value: "1.75" },
  { label: "Double", value: "2" },
] as const

const TABLE_GRID_SIZE = 10

/** Turn legacy plain/markdown text into basic HTML for the rich editor. */
export function toEditorHtml(content: string): string {
  const trimmed = content.trim()
  if (!trimmed) return ""
  if (trimmed.startsWith("<")) return content

  const escaped = content
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")

  return escaped
    .split(/\n{2,}/)
    .map((block) => `<p>${block.replace(/\n/g, "<br>")}</p>`)
    .join("")
}

type NoteRichEditorProps = {
  content: string
  onChange?: (html: string) => void
  editable?: boolean
  /** Immersive reading: no toolbar/chrome, larger type */
  variant?: "edit" | "read"
}

function ToolbarButton({
  onClick,
  active,
  disabled,
  label,
  children,
}: {
  onClick: () => void
  active?: boolean
  disabled?: boolean
  label: string
  children: React.ReactNode
}) {
  return (
    <Button
      type="button"
      variant={active ? "default" : "ghost"}
      size="icon-sm"
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      aria-pressed={active}
      title={label}
      className="shrink-0"
    >
      {children}
    </Button>
  )
}

function TableInsertPicker({
  onInsert,
}: {
  onInsert: (rows: number, cols: number) => void
}) {
  const [open, setOpen] = useState(false)
  const [hover, setHover] = useState({ rows: 0, cols: 0 })
  const rootRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const onPointerDown = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false)
        setHover({ rows: 0, cols: 0 })
      }
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false)
        setHover({ rows: 0, cols: 0 })
      }
    }
    document.addEventListener("mousedown", onPointerDown)
    document.addEventListener("keydown", onKeyDown)
    return () => {
      document.removeEventListener("mousedown", onPointerDown)
      document.removeEventListener("keydown", onKeyDown)
    }
  }, [open])

  const select = (rows: number, cols: number) => {
    onInsert(rows, cols)
    setOpen(false)
    setHover({ rows: 0, cols: 0 })
  }

  const cellPx = 18
  const gapPx = 3
  const gridWidth =
    TABLE_GRID_SIZE * cellPx + (TABLE_GRID_SIZE - 1) * gapPx

  return (
    <div ref={rootRef} className="relative">
      <ToolbarButton
        label="Insert table"
        active={open}
        onClick={() =>
          setOpen((value) => {
            if (value) setHover({ rows: 0, cols: 0 })
            return !value
          })
        }
      >
        <TableIcon className="size-4" />
      </ToolbarButton>

      {open ? (
        <div
          className="absolute top-full left-0 z-50 mt-0 pt-2"
          // pt-2 keeps a hover/click bridge so the panel doesn’t vanish
        >
          <div className="rounded-md border-2 border-border bg-background p-3 shadow-brutalist">
            <p className="mb-2 text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
              Insert table
            </p>
            <div
              role="grid"
              aria-label="Choose table size"
              style={{
                display: "grid",
                width: gridWidth,
                gridTemplateColumns: `repeat(${TABLE_GRID_SIZE}, ${cellPx}px)`,
                gap: gapPx,
              }}
            >
              {Array.from(
                { length: TABLE_GRID_SIZE * TABLE_GRID_SIZE },
                (_, i) => {
                  const rows = Math.floor(i / TABLE_GRID_SIZE) + 1
                  const cols = (i % TABLE_GRID_SIZE) + 1
                  const active =
                    hover.rows > 0 &&
                    rows <= hover.rows &&
                    cols <= hover.cols
                  return (
                    <button
                      key={i}
                      type="button"
                      role="gridcell"
                      aria-label={`${rows} by ${cols}`}
                      className={cn(
                        "rounded-[2px] border border-border transition-colors",
                        active
                          ? "border-primary bg-primary"
                          : "bg-muted/50 hover:border-foreground/40",
                      )}
                      style={{ width: cellPx, height: cellPx }}
                      onMouseEnter={() => setHover({ rows, cols })}
                      onFocus={() => setHover({ rows, cols })}
                      onClick={() => select(rows, cols)}
                    />
                  )
                },
              )}
            </div>
            <p className="mt-2 text-center text-xs font-bold tabular-nums">
              {hover.rows > 0
                ? `${hover.rows} × ${hover.cols}`
                : "Hover to size"}
            </p>
          </div>
        </div>
      ) : null}
    </div>
  )
}

function TableControls({
  onAddRow,
  onDeleteRow,
  onAddCol,
  onDeleteCol,
  onDeleteTable,
}: {
  onAddRow: () => void
  onDeleteRow: () => void
  onAddCol: () => void
  onDeleteCol: () => void
  onDeleteTable: () => void
}) {
  return (
    <div className="flex flex-wrap items-center gap-1 border-b-2 border-border bg-primary/10 px-2 py-1.5">
      <span className="mr-1 text-[10px] font-black uppercase tracking-wide text-muted-foreground">
        Table
      </span>
      <Button
        type="button"
        size="xs"
        variant="outline"
        onClick={onAddRow}
        title="Add row below"
      >
        <Plus className="size-3.5" />
        Row
      </Button>
      <Button
        type="button"
        size="xs"
        variant="outline"
        onClick={onDeleteRow}
        title="Delete current row"
      >
        <Minus className="size-3.5" />
        Row
      </Button>
      <Button
        type="button"
        size="xs"
        variant="outline"
        onClick={onAddCol}
        title="Add column right"
      >
        <Plus className="size-3.5" />
        Col
      </Button>
      <Button
        type="button"
        size="xs"
        variant="outline"
        onClick={onDeleteCol}
        title="Delete current column"
      >
        <Minus className="size-3.5" />
        Col
      </Button>
      <Button
        type="button"
        size="xs"
        variant="outline"
        onClick={onDeleteTable}
        title="Delete table"
        className="text-destructive"
      >
        <Trash2 className="size-3.5" />
        Delete
      </Button>
    </div>
  )
}

export function NoteRichEditor({
  content,
  onChange,
  editable = true,
  variant = "edit",
}: NoteRichEditorProps) {
  const [lineHeight, setLineHeight] = useState("1.5")
  const [linkOpen, setLinkOpen] = useState(false)
  const [linkText, setLinkText] = useState("")
  const [linkUrl, setLinkUrl] = useState("https://")
  const isRead = variant === "read"
  const canEdit = editable && !isRead

  const editor = useEditor({
    immediatelyRender: false,
    extensions: [
      StarterKit.configure({
        heading: { levels: [1, 2, 3] },
        codeBlock: false,
        // TipTap v3 StarterKit already ships these — configure, don’t re-add
        link: false,
        underline: false,
      }),
      MonacoCodeBlock,
      Underline,
      Link.configure({
        openOnClick: isRead,
        HTMLAttributes: { class: "text-primary underline" },
      }),
      TaskList,
      TaskItem.configure({ nested: true }),
      Table.configure({
        resizable: canEdit,
        HTMLAttributes: {
          class: "note-table",
        },
      }),
      TableRow,
      TableHeader,
      TableCell,
      Placeholder.configure({
        placeholder: "Start writing…",
      }),
    ],
    content: toEditorHtml(content),
    editable: canEdit,
    editorProps: {
      attributes: {
        class: cn(
          "prose dark:prose-invert max-w-none focus:outline-none",
          isRead
            ? "prose-base min-h-0 px-0 py-0"
            : "prose-sm min-h-full px-4 py-3",
          "[&_p]:my-1 [&_li]:my-0 [&_ul]:my-1.5 [&_ol]:my-1.5",
          "[&_h1]:mt-3 [&_h1]:mb-1.5 [&_h2]:mt-3 [&_h2]:mb-1 [&_h3]:mt-2.5 [&_h3]:mb-1",
          "[&_blockquote]:my-2 [&_pre]:my-2",
          "[&_ul[data-type=taskList]]:list-none [&_ul[data-type=taskList]]:pl-0",
          "[&_ul[data-type=taskList]_li]:flex [&_ul[data-type=taskList]_li]:items-start [&_ul[data-type=taskList]_li]:gap-2",
          "[&_table]:w-full [&_table]:border-collapse [&_table]:my-3 [&_table]:table-fixed",
          "[&_td]:border-2 [&_td]:border-border [&_td]:px-2 [&_td]:py-1.5 [&_td]:align-top",
          "[&_th]:border-2 [&_th]:border-border [&_th]:bg-muted/60 [&_th]:px-2 [&_th]:py-1.5 [&_th]:text-left [&_th]:font-semibold",
          "[&_.selectedCell]:bg-primary/10",
        ),
      },
    },
    onUpdate: ({ editor: current }) => {
      onChange?.(current.getHTML())
    },
  })

  const inTable =
    useEditorState({
      editor,
      selector: (ctx) => ctx.editor?.isActive("table") ?? false,
    }) ?? false

  useEffect(() => {
    if (!editor) return
    const next = toEditorHtml(content)
    const current = editor.getHTML()
    if (next !== current && editor.isEmpty && !content) {
      editor.commands.setContent("")
      return
    }
    if (next !== current && !editor.isFocused) {
      editor.commands.setContent(next, { emitUpdate: false })
    }
  }, [content, editor])

  useEffect(() => {
    if (!editor) return
    editor.setEditable(canEdit)
  }, [editor, canEdit])

  if (!editor) {
    return (
      <div
        className={cn(
          "p-4 text-sm text-muted-foreground",
          !isRead &&
            "flex h-full min-h-[320px] items-center rounded-md border-2 border-border bg-muted/40",
        )}
      >
        Loading…
      </div>
    )
  }

  if (isRead) {
    return (
      <div
        style={{ lineHeight: "1.7" }}
        className="[&_.ProseMirror]:leading-[inherit]"
      >
        <EditorContent editor={editor} />
      </div>
    )
  }

  const openLinkDialog = () => {
    const { from, to, empty } = editor.state.selection
    let text = empty ? "" : editor.state.doc.textBetween(from, to, " ")
    let url = ""

    if (editor.isActive("link")) {
      url = (editor.getAttributes("link").href as string) || ""
      if (empty) {
        // Expand to full linked text when caret is inside a link
        const attrs = editor.getAttributes("link")
        editor.chain().focus().extendMarkRange("link").run()
        const sel = editor.state.selection
        text = editor.state.doc.textBetween(sel.from, sel.to, " ")
        url = (attrs.href as string) || url
      }
    }

    setLinkText(text)
    setLinkUrl(url || "https://")
    setLinkOpen(true)
  }

  const applyLink = () => {
    const text = linkText.trim()
    const url = linkUrl.trim()

    if (!url) {
      editor.chain().focus().extendMarkRange("link").unsetLink().run()
      setLinkOpen(false)
      return
    }

    if (!text) return

    const { from, to, empty } = editor.state.selection
    const selected = empty
      ? ""
      : editor.state.doc.textBetween(from, to, " ")

    if (empty) {
      editor
        .chain()
        .focus()
        .insertContent({
          type: "text",
          text,
          marks: [{ type: "link", attrs: { href: url } }],
        })
        .run()
    } else if (selected === text) {
      editor.chain().focus().extendMarkRange("link").setLink({ href: url }).run()
    } else {
      editor
        .chain()
        .focus()
        .insertContent({
          type: "text",
          text,
          marks: [{ type: "link", attrs: { href: url } }],
        })
        .run()
    }

    setLinkOpen(false)
  }

  const removeLink = () => {
    editor.chain().focus().extendMarkRange("link").unsetLink().run()
    setLinkOpen(false)
  }

  return (
    <div className="flex h-full min-h-[320px] flex-col overflow-hidden rounded-md border-2 border-border bg-background">
      <div className="flex shrink-0 flex-wrap items-center gap-0.5 border-b-2 border-border bg-muted/40 p-1.5">
        <ToolbarButton
          label="Undo"
          onClick={() => editor.chain().focus().undo().run()}
        >
          <Undo2 className="size-4" />
        </ToolbarButton>
        <ToolbarButton
          label="Redo"
          onClick={() => editor.chain().focus().redo().run()}
        >
          <Redo2 className="size-4" />
        </ToolbarButton>

        <span className="mx-1 h-5 w-px bg-border" />

        <ToolbarButton
          label="Heading 1"
          active={editor.isActive("heading", { level: 1 })}
          onClick={() =>
            editor.chain().focus().toggleHeading({ level: 1 }).run()
          }
        >
          <Heading1 className="size-4" />
        </ToolbarButton>
        <ToolbarButton
          label="Heading 2"
          active={editor.isActive("heading", { level: 2 })}
          onClick={() =>
            editor.chain().focus().toggleHeading({ level: 2 }).run()
          }
        >
          <Heading2 className="size-4" />
        </ToolbarButton>
        <ToolbarButton
          label="Heading 3"
          active={editor.isActive("heading", { level: 3 })}
          onClick={() =>
            editor.chain().focus().toggleHeading({ level: 3 }).run()
          }
        >
          <Heading3 className="size-4" />
        </ToolbarButton>

        <span className="mx-1 h-5 w-px bg-border" />

        <ToolbarButton
          label="Bold"
          active={editor.isActive("bold")}
          onClick={() => editor.chain().focus().toggleBold().run()}
        >
          <Bold className="size-4" />
        </ToolbarButton>
        <ToolbarButton
          label="Italic"
          active={editor.isActive("italic")}
          onClick={() => editor.chain().focus().toggleItalic().run()}
        >
          <Italic className="size-4" />
        </ToolbarButton>
        <ToolbarButton
          label="Underline"
          active={editor.isActive("underline")}
          onClick={() => editor.chain().focus().toggleUnderline().run()}
        >
          <UnderlineIcon className="size-4" />
        </ToolbarButton>
        <ToolbarButton
          label="Strikethrough"
          active={editor.isActive("strike")}
          onClick={() => editor.chain().focus().toggleStrike().run()}
        >
          <Strikethrough className="size-4" />
        </ToolbarButton>
        <ToolbarButton
          label="Inline code"
          active={editor.isActive("code")}
          onClick={() => editor.chain().focus().toggleCode().run()}
        >
          <Code className="size-4" />
        </ToolbarButton>
        <ToolbarButton
          label="Code block"
          active={editor.isActive("codeBlock")}
          onClick={() => editor.chain().focus().toggleCodeBlock().run()}
        >
          <SquareCode className="size-4" />
        </ToolbarButton>
        <ToolbarButton
          label="Link"
          active={editor.isActive("link")}
          onClick={openLinkDialog}
        >
          <Link2 className="size-4" />
        </ToolbarButton>

        <span className="mx-1 h-5 w-px bg-border" />

        <ToolbarButton
          label="Bullet list"
          active={editor.isActive("bulletList")}
          onClick={() => editor.chain().focus().toggleBulletList().run()}
        >
          <List className="size-4" />
        </ToolbarButton>
        <ToolbarButton
          label="Numbered list"
          active={editor.isActive("orderedList")}
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
        >
          <ListOrdered className="size-4" />
        </ToolbarButton>
        <ToolbarButton
          label="Task list"
          active={editor.isActive("taskList")}
          onClick={() => editor.chain().focus().toggleTaskList().run()}
        >
          <ListTodo className="size-4" />
        </ToolbarButton>
        <ToolbarButton
          label="Quote"
          active={editor.isActive("blockquote")}
          onClick={() => editor.chain().focus().toggleBlockquote().run()}
        >
          <Quote className="size-4" />
        </ToolbarButton>

        <span className="mx-1 h-5 w-px bg-border" />

        <TableInsertPicker
          onInsert={(rows, cols) =>
            editor
              .chain()
              .focus()
              .insertTable({ rows, cols, withHeaderRow: true })
              .run()
          }
        />

        <span className="mx-1 h-5 w-px bg-border" />

        <label className="flex items-center gap-1 px-1 text-xs text-muted-foreground">
          <span className="sr-only">Line spacing</span>
          <select
            value={lineHeight}
            onChange={(e) => setLineHeight(e.target.value)}
            className="h-7 rounded-md border border-border bg-background px-1.5 text-xs font-medium text-foreground"
            aria-label="Line spacing"
            title="Line spacing"
          >
            {LINE_SPACING.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {inTable ? (
        <TableControls
          onAddRow={() => editor.chain().focus().addRowAfter().run()}
          onDeleteRow={() => editor.chain().focus().deleteRow().run()}
          onAddCol={() => editor.chain().focus().addColumnAfter().run()}
          onDeleteCol={() => editor.chain().focus().deleteColumn().run()}
          onDeleteTable={() => editor.chain().focus().deleteTable().run()}
        />
      ) : null}

      <div
        style={{ lineHeight }}
        className="min-h-0 flex-1 overflow-y-auto [&_.ProseMirror]:min-h-full [&_.ProseMirror]:leading-[inherit]"
      >
        <EditorContent editor={editor} />
      </div>

      <Dialog open={linkOpen} onOpenChange={setLinkOpen}>
        <DialogContent className="sm:max-w-md" showCloseButton>
          <DialogHeader>
            <DialogTitle className="font-black">Add link</DialogTitle>
            <DialogDescription>
              Set the display text and destination URL.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-1">
            <div className="space-y-1.5">
              <Label htmlFor="note-link-text">Text</Label>
              <Input
                id="note-link-text"
                value={linkText}
                onChange={(e) => setLinkText(e.target.value)}
                placeholder="Link label"
                autoFocus
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="note-link-url">URL</Label>
              <Input
                id="note-link-url"
                value={linkUrl}
                onChange={(e) => setLinkUrl(e.target.value)}
                placeholder="https://"
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault()
                    applyLink()
                  }
                }}
              />
            </div>
          </div>
          <DialogFooter className="gap-2 sm:justify-between">
            <Button
              type="button"
              variant="ghost"
              onClick={removeLink}
              disabled={!editor.isActive("link")}
            >
              Remove link
            </Button>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setLinkOpen(false)}
              >
                Cancel
              </Button>
              <Button
                type="button"
                onClick={applyLink}
                disabled={!linkText.trim() || !linkUrl.trim()}
              >
                Apply
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
