/**
 * highlight.js ships each language grammar as an untyped CommonJS module
 * (`highlight.js/lib/languages/<name>`). The package documents them as
 * `LanguageFn` values, so the wildcard declaration below restores that shape
 * without pulling in the full 190-language bundle.
 */
declare module 'highlight.js/lib/languages/*' {
  import type { LanguageFn } from 'highlight.js'
  const language: LanguageFn
  export default language
}
