import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * Clipboard helper with a transient "copied" flag.
 *
 * `navigator.clipboard` is only available in secure contexts, so the failure
 * path is explicit: callers can distinguish "copy worked" from "the browser
 * refused", instead of showing a success state that never happened.
 */
export interface CopyToClipboardState {
  copied: boolean
  copy: (text: string) => Promise<boolean>
}

export function useCopyToClipboard(resetDelay = 2000): CopyToClipboardState {
  const [copied, setCopied] = useState(false)
  const timerRef = useRef<number | null>(null)

  useEffect(
    () => () => {
      if (timerRef.current !== null) window.clearTimeout(timerRef.current)
    },
    [],
  )

  const copy = useCallback(
    async (text: string) => {
      try {
        await navigator.clipboard.writeText(text)
        setCopied(true)
        if (timerRef.current !== null) window.clearTimeout(timerRef.current)
        timerRef.current = window.setTimeout(() => setCopied(false), resetDelay)
        return true
      } catch {
        setCopied(false)
        return false
      }
    },
    [resetDelay],
  )

  return { copied, copy }
}
