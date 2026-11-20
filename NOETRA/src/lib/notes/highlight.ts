/**
 * Syntax highlighting for note code blocks.
 *
 * Only the grammars a lecture-notes document realistically contains are
 * registered, so the full highlight.js bundle (190+ languages) never ships.
 * Results are memoised: a code block re-renders on every search highlight and
 * reading-mode change, while its source never changes.
 *
 * The token classes emitted here are styled by the scoped `.note-code` rules in
 * `src/index.css`, which keeps syntax colours on the NOETRA palette instead of
 * importing a third-party theme.
 */

import hljs from 'highlight.js/lib/core'
import type { LanguageFn } from 'highlight.js'
import bash from 'highlight.js/lib/languages/bash'
import css from 'highlight.js/lib/languages/css'
import javascript from 'highlight.js/lib/languages/javascript'
import json from 'highlight.js/lib/languages/json'
import markdown from 'highlight.js/lib/languages/markdown'
import python from 'highlight.js/lib/languages/python'
import sql from 'highlight.js/lib/languages/sql'
import typescript from 'highlight.js/lib/languages/typescript'
import xml from 'highlight.js/lib/languages/xml'
import yaml from 'highlight.js/lib/languages/yaml'

const LANGUAGES: Record<string, LanguageFn> = {
  bash,
  css,
  javascript,
  json,
  markdown,
  python,
  sql,
  typescript,
  xml,
  yaml,
}

/** Common aliases found in fenced code blocks and backend payloads. */
const ALIASES: Record<string, string> = {
  js: 'javascript',
  jsx: 'javascript',
  mjs: 'javascript',
  cjs: 'javascript',
  node: 'javascript',
  ts: 'typescript',
  tsx: 'typescript',
  py: 'python',
  python3: 'python',
  sh: 'bash',
  shell: 'bash',
  zsh: 'bash',
  console: 'bash',
  html: 'xml',
  svg: 'xml',
  xhtml: 'xml',
  md: 'markdown',
  yml: 'yaml',
  postgres: 'sql',
  postgresql: 'sql',
  jsonc: 'json',
  'json5': 'json',
}

let registered = false

function ensureLanguagesRegistered(): void {
  if (registered) return
  for (const [name, language] of Object.entries(LANGUAGES)) {
    hljs.registerLanguage(name, language)
  }
  registered = true
}

/** Languages this build can highlight, for the "supported" label in the UI. */
export const SUPPORTED_LANGUAGES = Object.keys(LANGUAGES)

/** Resolve an alias (`py`) to a registered language (`python`), or null. */
export function normalizeLanguage(language: string | undefined): string | null {
  if (!language) return null
  const key = language.trim().toLowerCase()
  if (!key) return null
  const resolved = ALIASES[key] ?? key
  return resolved in LANGUAGES ? resolved : null
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

export interface HighlightedCode {
  /** Highlighted markup, or escaped plain text when the language is unknown. */
  html: string
  /** The language that was actually used, or null when none was applied. */
  language: string | null
}

const cache = new Map<string, HighlightedCode>()

export function highlightCode(code: string, language: string | undefined): HighlightedCode {
  const resolved = normalizeLanguage(language)
  const key = `${resolved ?? 'plain'}\u0000${code}`
  const cached = cache.get(key)
  if (cached) return cached

  let result: HighlightedCode
  if (!resolved) {
    result = { html: escapeHtml(code), language: null }
  } else {
    ensureLanguagesRegistered()
    // `ignoreIllegals` keeps partially-formed snippets (common in narration
    // code) from throwing, so a block always renders something readable.
    result = { html: hljs.highlight(code, { language: resolved, ignoreIllegals: true }).value, language: resolved }
  }

  cache.set(key, result)
  return result
}
