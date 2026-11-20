/**
 * Safe KaTeX typesetting for note equations.
 *
 * KaTeX is called with `throwOnError: true` so malformed LaTeX raises instead
 * of silently rendering red error text, and the error is turned into a readable
 * fallback by the caller. `trust` stays off, which keeps `\href`/`\url`/
 * `\includegraphics` from becoming an HTML injection vector on untrusted input.
 *
 * Results are memoised because a document re-renders on every edit, search
 * highlight and reading-mode change while its LaTeX never changes.
 */

import katex from 'katex'

export interface LatexRenderResult {
  /** KaTeX HTML, or an empty string when typesetting failed. */
  html: string
  /** Human-readable reason the input could not be typeset, when it failed. */
  error: string | null
}

const cache = new Map<string, LatexRenderResult>()

export function renderLatex(latex: string, displayMode: boolean): LatexRenderResult {
  const key = `${displayMode ? 'block' : 'inline'}\u0000${latex}`
  const cached = cache.get(key)
  if (cached) return cached

  let result: LatexRenderResult
  try {
    result = {
      html: katex.renderToString(latex, {
        displayMode,
        throwOnError: true,
        output: 'htmlAndMathml',
        trust: false,
        strict: 'ignore',
      }),
      error: null,
    }
  } catch (error) {
    result = {
      html: '',
      error: error instanceof Error ? error.message : 'The expression could not be typeset.',
    }
  }

  cache.set(key, result)
  return result
}
