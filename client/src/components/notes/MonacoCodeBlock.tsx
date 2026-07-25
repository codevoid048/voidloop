"use client"

import CodeBlock from "@tiptap/extension-code-block"
import {
  NodeViewWrapper,
  ReactNodeViewRenderer,
  type NodeViewProps,
} from "@tiptap/react"
import CodeMirror from "@uiw/react-codemirror"
import { loadLanguage, type LanguageName } from "@uiw/codemirror-extensions-langs"
import { vscodeDark } from "@uiw/codemirror-theme-vscode"
import { EditorView } from "@codemirror/view"
import { useEffect, useMemo, useRef, useState } from "react"
import { cn } from "@/lib/utils"

export const CODE_LANGUAGES = [
  { value: "typescript", label: "TypeScript" },
  { value: "javascript", label: "JavaScript" },
  { value: "tsx", label: "TSX" },
  { value: "jsx", label: "JSX" },
  { value: "python", label: "Python" },
  { value: "go", label: "Go" },
  { value: "rust", label: "Rust" },
  { value: "java", label: "Java" },
  { value: "json", label: "JSON" },
  { value: "html", label: "HTML" },
  { value: "css", label: "CSS" },
  { value: "sql", label: "SQL" },
  { value: "shell", label: "Shell" },
  { value: "markdown", label: "Markdown" },
  { value: "yaml", label: "YAML" },
] as const

type SupportedLang = (typeof CODE_LANGUAGES)[number]["value"]

function toCodeMirrorLang(language: string): LanguageName | null {
  const map: Record<string, LanguageName> = {
    typescript: "ts",
    javascript: "js",
    tsx: "tsx",
    jsx: "jsx",
    python: "python",
    go: "go",
    rust: "rs",
    java: "java",
    json: "json",
    html: "html",
    css: "css",
    sql: "sql",
    shell: "sh",
    markdown: "markdown",
    yaml: "yaml",
  }
  return map[language] ?? null
}

function CodeBlockView({
  node,
  updateAttributes,
  editor,
  getPos,
  selected,
}: NodeViewProps) {
  const language = (node.attrs.language as string) || "typescript"
  const code = node.textContent
  const editable = editor.isEditable
  const skipNextSync = useRef(false)
  const [localCode, setLocalCode] = useState(code)

  useEffect(() => {
    if (skipNextSync.current) {
      skipNextSync.current = false
      return
    }
    setLocalCode(code)
  }, [code])

  const extensions = useMemo(() => {
    const lang = toCodeMirrorLang(language)
    const loaded = lang ? loadLanguage(lang) : null
    return loaded
      ? [loaded, EditorView.lineWrapping]
      : [EditorView.lineWrapping]
  }, [language])

  const minHeight = useMemo(() => {
    const lines = Math.max(3, localCode.split("\n").length)
    return Math.min(420, Math.max(108, lines * 20 + 24))
  }, [localCode])

  const writeCode = (next: string) => {
    if (typeof getPos !== "function") return
    const pos = getPos()
    if (typeof pos !== "number") return
    if (next === node.textContent) return

    skipNextSync.current = true
    setLocalCode(next)
    editor.view.dispatch(
      editor.state.tr.insertText(next, pos + 1, pos + node.nodeSize - 1),
    )
  }

  return (
    <NodeViewWrapper
      className={cn(
        "my-3 w-full max-w-full overflow-hidden rounded-md border-2 border-border bg-[#1e1e1e]",
        selected && "ring-2 ring-primary ring-offset-2 ring-offset-background",
      )}
      data-drag-handle
    >
      <div
        className="flex items-center justify-between gap-2 border-b border-white/10 px-2 py-1.5"
        contentEditable={false}
      >
        <select
          value={
            CODE_LANGUAGES.some((l) => l.value === language)
              ? language
              : "typescript"
          }
          disabled={!editable}
          onChange={(e) =>
            updateAttributes({ language: e.target.value as SupportedLang })
          }
          className="h-7 rounded border border-white/20 bg-transparent px-1.5 text-xs font-semibold text-white/90 outline-none disabled:opacity-60"
          aria-label="Code language"
        >
          {CODE_LANGUAGES.map((lang) => (
            <option key={lang.value} value={lang.value} className="text-black">
              {lang.label}
            </option>
          ))}
        </select>
        <span className="text-[10px] font-bold uppercase tracking-wide text-white/40">
          Code
        </span>
      </div>

      <div contentEditable={false} className="relative w-full max-w-full overflow-x-auto">
        <CodeMirror
          value={localCode}
          height={`${minHeight}px`}
          width="100%"
          theme={vscodeDark}
          extensions={extensions}
          editable={editable}
          basicSetup={{
            lineNumbers: true,
            foldGutter: false,
            highlightActiveLine: editable,
            highlightActiveLineGutter: editable,
          }}
          onChange={(value) => {
            if (!editable) return
            writeCode(value)
          }}
          className="w-full max-w-full text-[13px] [&_.cm-editor]:max-w-full [&_.cm-editor]:outline-none [&_.cm-scroller]:font-mono"
        />
      </div>
    </NodeViewWrapper>
  )
}

/** TipTap code block with a client-side CodeMirror editor (no CDN / public assets). */
export const MonacoCodeBlock = CodeBlock.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      language: {
        default: "typescript",
        parseHTML: (element) =>
          element.getAttribute("data-language") ||
          element.getAttribute("class")?.replace(/^language-/, "") ||
          "typescript",
        renderHTML: (attributes) => {
          if (!attributes.language) return {}
          return {
            "data-language": attributes.language,
            class: `language-${attributes.language}`,
          }
        },
      },
    }
  },

  addNodeView() {
    return ReactNodeViewRenderer(CodeBlockView)
  },
})
