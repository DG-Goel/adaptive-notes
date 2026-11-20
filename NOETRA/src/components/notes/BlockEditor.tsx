import { useEffect, useRef, useState } from 'react'
import { EditorContent, useEditor, useEditorState } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import {
  Bold,
  Braces,
  Code,
  Italic,
  Link2,
  List,
  ListOrdered,
  Quote,
  Redo2,
  Undo2,
} from 'lucide-react'
import { cn } from '@/lib/utils'

/**
 * The rich-text editing surface for a single note block.
 *
 * This module is the only place that imports Tiptap, and it is loaded lazily by
 * the editor dialog so the editor bundle is never part of the initial Notes
 * Studio payload. It edits text only — visual artifacts are read-only and are
 * never routed through here.
 *
 * `shouldRerenderOnTransaction: false` keeps typing from re-rendering the whole
 * component; the toolbar state is read separately through `useEditorState`.
 */

const CONTENT_CLASSES = [
  '[&_.tiptap]:min-h-[12rem] [&_.tiptap]:outline-none',
  '[&_.tiptap>*+*]:mt-3',
  '[&_h2]:font-serif [&_h2]:text-xl [&_h2]:font-medium [&_h2]:tracking-tight [&_h2]:text-foreground',
  '[&_h3]:font-serif [&_h3]:text-lg [&_h3]:font-medium [&_h3]:text-foreground',
  '[&_h4]:text-base [&_h4]:font-semibold [&_h4]:text-foreground',
  '[&_p]:leading-relaxed [&_p]:text-foreground/90',
  '[&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5 [&_li]:leading-relaxed [&_li]:text-foreground/90',
  '[&_blockquote]:border-l-2 [&_blockquote]:border-accent/50 [&_blockquote]:pl-3 [&_blockquote]:text-muted-foreground [&_blockquote]:italic',
  '[&_code]:rounded [&_code]:bg-muted [&_code]:px-1 [&_code]:py-0.5 [&_code]:font-mono [&_code]:text-[0.85em]',
  '[&_pre]:overflow-x-auto [&_pre]:rounded-xl [&_pre]:bg-sidebar [&_pre]:p-3 [&_pre]:font-mono [&_pre]:text-[0.82rem] [&_pre]:text-sidebar-foreground',
  '[&_pre_code]:bg-transparent [&_pre_code]:p-0 [&_pre_code]:text-inherit',
  '[&_a]:text-accent [&_a]:underline [&_a]:underline-offset-2',
  '[&_hr]:border-border',
  '[&_strong]:font-semibold [&_strong]:text-foreground',
].join(' ')

export interface BlockEditorProps {
  /** Initial editor HTML, produced by `blockToEditorHtml`. */
  initialHtml: string
  /** Called on every change with the editor's current HTML. */
  onChange: (html: string) => void
}

interface ToolbarButtonProps {
  label: string
  active?: boolean
  disabled?: boolean
  onClick: () => void
  children: React.ReactNode
}

function ToolbarButton({ label, active, disabled, onClick, children }: ToolbarButtonProps) {
  return (
    <button
      type="button"
      onMouseDown={(event) => event.preventDefault()}
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      aria-pressed={active}
      title={label}
      className={cn(
        'inline-flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-40',
        active && 'bg-accent/10 text-accent hover:bg-accent/15 hover:text-accent',
      )}
    >
      {children}
    </button>
  )
}

export default function BlockEditor({ initialHtml, onChange }: BlockEditorProps) {
  const onChangeRef = useRef(onChange)
  useEffect(() => {
    onChangeRef.current = onChange
  }, [onChange])

  const [linkOpen, setLinkOpen] = useState(false)
  const [linkValue, setLinkValue] = useState('')

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: { levels: [2, 3, 4] },
        link: { openOnClick: false, autolink: true },
      }),
    ],
    content: initialHtml,
    shouldRerenderOnTransaction: false,
    editorProps: {
      attributes: { class: 'tiptap', 'aria-label': 'Block content' },
    },
    onUpdate: ({ editor: instance }) => onChangeRef.current(instance.getHTML()),
  })

  const state = useEditorState({
    editor,
    selector: ({ editor: instance }) => ({
      bold: instance.isActive('bold'),
      italic: instance.isActive('italic'),
      bulletList: instance.isActive('bulletList'),
      orderedList: instance.isActive('orderedList'),
      blockquote: instance.isActive('blockquote'),
      codeBlock: instance.isActive('codeBlock'),
      code: instance.isActive('code'),
      link: instance.isActive('link'),
      h2: instance.isActive('heading', { level: 2 }),
      h3: instance.isActive('heading', { level: 3 }),
      canUndo: instance.can().undo(),
      canRedo: instance.can().redo(),
    }),
  })

  const applyLink = () => {
    const href = linkValue.trim()
    if (!href) return
    editor.chain().focus().extendMarkRange('link').setLink({ href }).run()
    setLinkOpen(false)
    setLinkValue('')
  }

  return (
    <div className="rounded-xl border border-border bg-background">
      <div className="flex flex-wrap items-center gap-0.5 border-b border-border p-1.5">
        <ToolbarButton
          label="Heading level 2"
          active={state.h2}
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
        >
          <span className="text-[11px] font-semibold">H2</span>
        </ToolbarButton>
        <ToolbarButton
          label="Heading level 3"
          active={state.h3}
          onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
        >
          <span className="text-[11px] font-semibold">H3</span>
        </ToolbarButton>

        <span className="mx-1 h-5 w-px bg-border" aria-hidden />

        <ToolbarButton
          label="Bold"
          active={state.bold}
          onClick={() => editor.chain().focus().toggleBold().run()}
        >
          <Bold className="h-4 w-4" />
        </ToolbarButton>
        <ToolbarButton
          label="Italic"
          active={state.italic}
          onClick={() => editor.chain().focus().toggleItalic().run()}
        >
          <Italic className="h-4 w-4" />
        </ToolbarButton>
        <ToolbarButton
          label="Inline code"
          active={state.code}
          onClick={() => editor.chain().focus().toggleCode().run()}
        >
          <Code className="h-4 w-4" />
        </ToolbarButton>
        <ToolbarButton
          label="Link"
          active={state.link}
          onClick={() => {
            setLinkValue(editor.getAttributes('link').href ?? '')
            setLinkOpen((value) => !value)
          }}
        >
          <Link2 className="h-4 w-4" />
        </ToolbarButton>

        <span className="mx-1 h-5 w-px bg-border" aria-hidden />

        <ToolbarButton
          label="Bullet list"
          active={state.bulletList}
          onClick={() => editor.chain().focus().toggleBulletList().run()}
        >
          <List className="h-4 w-4" />
        </ToolbarButton>
        <ToolbarButton
          label="Numbered list"
          active={state.orderedList}
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
        >
          <ListOrdered className="h-4 w-4" />
        </ToolbarButton>
        <ToolbarButton
          label="Blockquote"
          active={state.blockquote}
          onClick={() => editor.chain().focus().toggleBlockquote().run()}
        >
          <Quote className="h-4 w-4" />
        </ToolbarButton>
        <ToolbarButton
          label="Code block"
          active={state.codeBlock}
          onClick={() => editor.chain().focus().toggleCodeBlock().run()}
        >
          <Braces className="h-4 w-4" />
        </ToolbarButton>

        <span className="mx-1 h-5 w-px bg-border" aria-hidden />

        <ToolbarButton
          label="Undo"
          disabled={!state.canUndo}
          onClick={() => editor.chain().focus().undo().run()}
        >
          <Undo2 className="h-4 w-4" />
        </ToolbarButton>
        <ToolbarButton
          label="Redo"
          disabled={!state.canRedo}
          onClick={() => editor.chain().focus().redo().run()}
        >
          <Redo2 className="h-4 w-4" />
        </ToolbarButton>
      </div>

      {linkOpen && (
        <div className="flex items-center gap-2 border-b border-border bg-muted/40 p-2">
          <input
            type="url"
            value={linkValue}
            onChange={(event) => setLinkValue(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                event.preventDefault()
                applyLink()
              }
            }}
            placeholder="https://example.com"
            aria-label="Link URL"
            className="h-8 flex-1 rounded-lg border border-input bg-background px-2.5 text-[13px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
          <button
            type="button"
            onClick={applyLink}
            className="h-8 rounded-lg bg-accent px-3 text-[12px] font-medium text-accent-foreground transition-colors hover:bg-accent-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            Apply
          </button>
          <button
            type="button"
            onClick={() => {
              editor.chain().focus().extendMarkRange('link').unsetLink().run()
              setLinkOpen(false)
            }}
            className="h-8 rounded-lg border border-border px-3 text-[12px] font-medium text-foreground transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            Remove
          </button>
        </div>
      )}

      <div className={cn('px-3 py-3', CONTENT_CLASSES)}>
        <EditorContent editor={editor} />
      </div>
    </div>
  )
}
