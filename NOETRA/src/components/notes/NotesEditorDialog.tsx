import { Suspense, lazy, useMemo, useState } from 'react'
import { Loader2, TriangleAlert } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { PrimaryButton } from '@/components/common/PrimaryButton'
import { SecondaryButton } from '@/components/common/SecondaryButton'
import { Skeleton } from '@/components/ui/skeleton'
import { BLOCK_TYPE_LABELS } from '@/lib/notes/blocks'
import { applyEditorHtml, blockToEditorHtml } from '@/lib/notes/markdown-html'
import { timestampLabel } from '@/lib/timestamps'
import { cn } from '@/lib/utils'
import type { EditableNoteBlock, NoteBlock } from '@/types/notes'

/**
 * Editor for a single text block.
 *
 * Applying an edit replaces *only* that block's text: the block keeps its id,
 * document order, and timestamps, and every other block — including all visual
 * artifacts — is passed through untouched. Tiptap itself is code-split here so
 * it never loads until the reader opens the editor.
 */

const BlockEditor = lazy(() => import('./BlockEditor'))

export interface NotesEditorDialogProps {
  block: EditableNoteBlock | null
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Receives the updated block, ready to be written into the draft document. */
  onApply: (block: NoteBlock) => void
  saving?: boolean
}

interface EditorPaneProps {
  block: EditableNoteBlock
  saving: boolean
  onCancel: () => void
  onApply: (block: NoteBlock) => void
}

/**
 * The editing surface.
 *
 * Rendered only while the dialog is open, so the working copy starts fresh from
 * the block every time and no state has to be reset from an effect.
 */
function EditorPane({ block, saving, onCancel, onApply }: EditorPaneProps) {
  const initialHtml = useMemo(() => blockToEditorHtml(block), [block])
  const [html, setHtml] = useState(initialHtml)
  const dirty = html !== initialHtml

  return (
    <>
      <DialogHeader>
        <DialogTitle className="flex items-center gap-2 font-serif text-xl">
          Edit block
          <Badge variant="secondary" className="text-[10px] font-normal">
            {BLOCK_TYPE_LABELS[block.type]}
          </Badge>
          {typeof block.startSeconds === 'number' && (
            <span className="font-mono text-[11px] font-normal tabular-nums text-muted-foreground">
              {timestampLabel(block.startSeconds)}
            </span>
          )}
        </DialogTitle>
        <DialogDescription>
          Only this block’s text changes. Tables, flowcharts, diagrams, equations, and timestamps are left exactly
          as they are.
        </DialogDescription>
      </DialogHeader>

      <Suspense
        fallback={
          <div className="space-y-3 rounded-xl border border-border p-4">
            <Skeleton className="h-8 w-40" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
            <Skeleton className="h-4 w-2/3" />
          </div>
        }
      >
        <BlockEditor initialHtml={initialHtml} onChange={setHtml} />
      </Suspense>

      <div className="flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground">
        <span
          className={cn(
            'inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5',
            dirty ? 'border-amber-400/50 bg-amber-400/10 text-amber-700' : 'border-border',
          )}
        >
          <span
            className={cn('h-1.5 w-1.5 rounded-full', dirty ? 'bg-amber-500' : 'bg-muted-foreground/50')}
            aria-hidden
          />
          {dirty ? 'Unapplied changes' : 'No changes yet'}
        </span>
        <span>Applying writes to the local draft; the document is saved separately.</span>
      </div>

      <DialogFooter className="gap-2 sm:justify-end">
        <SecondaryButton onClick={onCancel} disabled={saving}>
          Cancel
        </SecondaryButton>
        <PrimaryButton onClick={() => onApply(applyEditorHtml(block, html))} disabled={!dirty || saving}>
          {saving && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
          Apply changes
        </PrimaryButton>
      </DialogFooter>
    </>
  )
}

export function NotesEditorDialog({ block, open, onOpenChange, onApply, saving = false }: NotesEditorDialogProps) {
  const requestClose = (next: boolean) => {
    if (saving) return
    onOpenChange(next)
  }

  return (
    <Dialog open={open} onOpenChange={requestClose}>
      <DialogContent className="max-h-[88vh] max-w-2xl overflow-y-auto">
        {block ? (
          <EditorPane
            block={block}
            saving={saving}
            onCancel={() => requestClose(false)}
            onApply={onApply}
          />
        ) : (
          <>
            <DialogHeader>
              <DialogTitle className="font-serif text-xl">Edit block</DialogTitle>
            </DialogHeader>
            <p className="flex items-center gap-2 text-xs text-muted-foreground">
              <TriangleAlert className="h-3.5 w-3.5" aria-hidden />
              No editable block is selected.
            </p>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
