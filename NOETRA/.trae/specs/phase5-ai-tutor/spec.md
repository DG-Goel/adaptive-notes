# NOETRA Phase 5 — Intelligent AI Tutor & Contextual Learning

## Overview
- **Summary**: Build a complete AI Tutor frontend — a full conversation workspace at `/tutor`, an improved compact sidebar inside the video workspace, and Notes Studio integration — backed by the existing Python RAG backend (`POST /api/v1/ask`). All AI answers come from the backend in real mode; mock mode provides deterministic, clearly-labelled demo responses.
- **Purpose**: Give learners a context-aware, citation-grounded conversational companion that connects naturally to NOETRA's video player and structured notes, without fabricating AI capabilities or backend support.
- **Target Users**: Learners watching lectures, reviewing AI-generated notes, and asking follow-up questions with conversation continuity.

## Goals
- Full Tutor page (`/tutor`) with conversation list, message view, context selector, explanation-mode selector, and collapsible learning-context panel.
- Compact Tutor sidebar in the video workspace reusing the same components and state.
- Shared conversation state so the same conversation persists across sidebar ↔ full page.
- Rich response rendering (Markdown, KaTeX math, syntax-highlighted code, tables, citations, timestamp links, related note references) using existing Phase 4 renderers.
- Explicit typed context model (general / video / chapter / timestamp / notes) with capability-driven mapping to the backend.
- Explanation-style preferences (frontend-only, mapped to backend only where supported).
- Source citations with clickable timestamps that seek the mounted player or deep-link to `/learn/:videoId?t=`.
- Notes Studio actions ("Ask AI about this section", etc.) that open Tutor with the right context.
- Honest error and unavailable states — no fabricated responses, citations, streaming, or saves.

## Non-Goals
- No backend, AI model, RAG pipeline, vector store, or database.
- No API secrets stored or exposed.
- No simulated token streaming in real API mode.
- No quiz or knowledge-map work (Phase 6+).
- No redesign of landing/dashboard pages or the NOETRA design system.
- No destructive changes to the notes document schema.

## Background & Context
Existing code inspected:
- `src/types/tutor.ts` — `TutorMessage`, `TutorCitation` (label+timestamp), `AskRequest`/`AskResponse`.
- `src/services/api/tutor.ts` — `askTutor({ question, history, videoId, signal })`; mock returns `buildMockAnswer`; real mode calls `endpoints.ask` with `mode`/`top_k`/`conversation_history` (and `video_id` only when `askDefaults.includeVideoScope`).
- `src/mocks/tutor.ts` — `suggestedTutorPrompts`, `mockTutorConversation` seed, `buildMockAnswer` (deterministic canned replies).
- `src/components/video/TutorSidebar.tsx` — existing compact sidebar (local state, plain-text bubbles, citation chips, seek, copy, retry).
- `src/pages/TutorPage.tsx` — currently a `PlaceholderPage`.
- `src/config/endpoints.ts` — `endpoints.ask = '/ask'`, `askDefaults { mode: 'lecture', topK: 4, includeVideoScope: false }`.
- `src/components/notes/*` — `MarkdownBlock` (react-markdown + remark-gfm + remark-math + rehype-katex, no rehype-raw), `MathBlock`, `CodeBlock`, `TableBlock`, `NoteBlockRenderer`, `NotesDocumentRenderer`.
- `src/components/video/TimestampText.tsx` — `TimestampChip` seeks mounted player or deep-links.
- `src/context/notes-playback-context.ts` — `NotesPlaybackContext` seek bridge reused by notes.

## Functional Requirements
- **FR-1**: `/tutor` renders a three-column responsive workspace (conversation list | conversation | learning context), collapsing to two-column tablet and single-column mobile with a drawer.
- **FR-2**: Conversation list supports new conversation, search, time-grouped recent conversations, active highlighting, delete-with-confirmation, and a context label per conversation.
- **FR-3**: Message composer supports Enter-to-send, Shift+Enter newline, auto-growing textarea, stop/cancel (where supported), scroll-to-latest, and preserves scroll position when reading history.
- **FR-4**: Assistant messages render Markdown (headings, paragraphs, bold/italic, lists, tables, blockquotes, inline code, fenced code with syntax highlighting, KaTeX inline/block math) using existing renderers; user messages are compact.
- **FR-5**: Citations render as elegant chips with source preview; timestamp citations seek the mounted video player or deep-link to `/learn/:videoId?t=`. Missing citations are not invented.
- **FR-6**: Suggested follow-up questions are offered context-appropriately and clearly labelled as UI suggestions (not AI-generated) in real mode.
- **FR-7**: Context Selector offers general / full video / current chapter / selected timestamp range / selected notes; represented as a typed discriminated union; unavailable modes are disabled with explanation rather than silently substituted.
- **FR-8**: Explanation Mode Selector offers simple / detailed / step-by-step / examples / revision (plus optional length/examples/math/bullets toggles); treated as frontend preferences and mapped to backend only where supported.
- **FR-9**: Conversation state is shared between the compact sidebar and the full page; switching views does not discard the current conversation or draft.
- **FR-10**: Conversation history persists in mock mode via localStorage (clearly labelled "local demo history"); in real mode uses backend only if endpoints exist, otherwise clearly labelled session-only.
- **FR-11**: Notes Studio exposes "Ask AI about this section" / "Explain this" / "Give an example" / "Simplify" actions that open Tutor with videoId, sectionId, selected text, and source timestamp preserved.
- **FR-12**: Errors (timeout, network, rate limit, invalid response, cancelled, empty) show honest, retryable messages; no fallback to mock mode in real mode.
- **FR-13**: Backend adapter supports request cancellation (AbortSignal), standardized errors, conversation-history serialization, configurable top_k, and optional context fields only when confirmed.
- **FR-14**: Mock mode provides deterministic Transformer-themed conversations containing Markdown, tables, math, code, timestamp citations, and follow-up questions; clearly labelled as demo; preserves the Sintel-vs-Transformer distinction.

## Non-Functional Requirements
- **NFR-1**: Lazy-load the full Tutor page; avoid re-rendering all messages while typing; auto-scroll only when near the bottom.
- **NFR-2**: Respect `prefers-reduced-motion`; keyboard-accessible controls; screen-reader status messages; proper focus management for drawers/dialogs.
- **NFR-3**: Reuse existing Markdown/math/code renderers — no duplicate libraries.
- **NFR-4**: No untrusted raw HTML rendered from AI responses.
- **NFR-5**: `npm run lint` and `npm run build` pass with no errors.

## Constraints
- **Technical**: React 19 + Vite 7 + TypeScript; Tailwind + shadcn/ui; TanStack Query v5; react-markdown + KaTeX + highlight.js already present; NOETRA tokens (#F7F4EF, #252525, #D65A16, Instrument Serif, DM Sans).
- **Business**: No backend changes; no API keys in the browser; no fabrication of AI capabilities.
- **Dependencies**: Existing `askTutor` service, `MarkdownBlock`/`MathBlock`/`CodeBlock` renderers, `TimestampChip`, `VideoPlayerProvider`/`NotesPlaybackContext`, existing UI primitives (Dialog, DropdownMenu, Badge, Button, Input, ScrollArea, Tooltip).

## Assumptions
- The real backend accepts only `question`, `mode`, `top_k`, `conversation_history` (and optionally `video_id` behind the existing flag). Context/explanation fields are not sent unless a capability flag is confirmed.
- No streaming endpoint is confirmed; responses are rendered complete. A streaming interface is defined but unused until a real endpoint is configured.
- Conversation-history persistence endpoints are not confirmed; real mode falls back to session-only with clear labelling.

## Acceptance Criteria

### AC-1: Full Tutor page renders the three-column workspace
- **Type**: `rule`
- **Given**: the dev server is running and mock mode is enabled
- **When**: navigating to `/tutor`
- **Then**: a conversation list, a message area, and a collapsible learning-context panel are visible (or the responsive equivalent)
- **Pass Condition**: `/tutor` returns a rendered page with conversation list, composer, and context panel present in the DOM; console has no errors
- **Evidence**: browser snapshot of `/tutor` + console messages

### AC-2: Shared conversation survives sidebar ↔ full-page navigation
- **Type**: `rule`
- **Given**: a conversation with messages is open in the video-workspace Tutor sidebar
- **When**: the user navigates to `/tutor` (or opens Tutor from the sidebar)
- **Then**: the same messages and active conversation are present
- **Pass Condition**: messages array and active conversation ID are identical across both surfaces
- **Evidence**: browser interaction + snapshot comparison

### AC-3: Assistant Markdown, math, code, and tables render correctly
- **Type**: `rule`
- **Given**: an assistant message containing Markdown headings, a KaTeX block equation, a fenced code block, and a GFM table
- **When**: the message is rendered
- **Then**: each element renders using the existing renderers (no raw HTML, no crash)
- **Pass Condition**: rendered DOM contains the expected elements; no `dangerouslySetInnerHTML` of untrusted AI content
- **Evidence**: snapshot of a rendered assistant message

### AC-4: Timestamp citations seek the player or deep-link
- **Type**: `rule`
- **Given**: an assistant message with a timestamp citation
- **When**: the citation chip is clicked inside the video workspace
- **Then**: the mounted video player seeks to that timestamp
- **Pass Condition**: `seekTo` is called with the citation's seconds; outside the workspace, navigation to `/learn/:videoId?t=` occurs
- **Evidence**: code path + browser interaction

### AC-5: Context selector is typed and capability-driven
- **Type**: `rule`
- **Given**: the context selector is rendered
- **When**: a context mode has no confirmed backend support
- **Then**: that mode is disabled with an explanatory tooltip, not silently mapped to whole-video
- **Pass Condition**: `TutorContext` is a discriminated union; unsupported modes render disabled
- **Evidence**: type definitions + component inspection

### AC-6: Explanation modes are frontend-only and not falsely mapped
- **Type**: `rule`
- **Given**: an explanation mode is selected
- **When**: the request is sent to the backend
- **Then**: unsupported explanation fields are omitted from the request body
- **Pass Condition**: real-mode request payload contains only confirmed backend fields
- **Evidence**: service-layer inspection + network request

### AC-7: Mock history is local and clearly labelled
- **Type**: `rule`
- **Given**: mock mode is enabled
- **When**: conversations are listed
- **Then**: a "local demo history" label is visible and data is read from localStorage
- **Pass Condition**: UI shows the demo label; real mode does not claim server persistence
- **Evidence**: snapshot + storage inspection

### AC-8: Notes Studio "Ask AI" opens Tutor with preserved context
- **Type**: `rule`
- **Given**: a note section is open in the Notes Studio
- **When**: the user clicks "Ask AI about this section"
- **Then**: Tutor opens with context `{ type: 'notes', videoId, sectionId }` (and selected text if any)
- **Pass Condition**: Tutor's context reflects the originating section; return navigation works
- **Evidence**: browser interaction

### AC-9: Errors are honest and retryable, never fabricated
- **Type**: `rule`
- **Given**: the backend returns an error or is unreachable in real mode
- **When**: a question is submitted
- **Then**: an error message is shown with a retry action; no mock fallback, no invented answer
- **Pass Condition**: error UI renders; retry re-issues the request
- **Evidence**: network/error simulation + snapshot

### AC-10: No console errors on `/tutor` and no lint/build failures
- **Type**: `rule`
- **Given**: the implementation is complete
- **When**: `npm run lint`, `npm run build`, and loading `/tutor`
- **Then**: lint has 0 errors, build succeeds, and the browser console shows no errors
- **Pass Condition**: command exit codes 0; console error count 0
- **Evidence**: command output + console messages

### AC-11: Visual identity and readability
- **Type**: `rubric`
- **Dimension**: NOETRA visual coherence and reading comfort of the Tutor UI
- **Scale**: 1-5
- **Anchors**: 1 = breaks design system, unreadable; 3 = functional but generic; 5 = calm, luxurious, on-brand, exceptionally readable
- **Pass Threshold**: >= 4
- **Evidence**: visual inspection of `/tutor` and the sidebar

### AC-12: Performance and input responsiveness
- **Type**: `rubric`
- **Dimension**: typing responsiveness and avoidance of unnecessary re-renders
- **Scale**: 1-5
- **Anchors**: 1 = typing lags, whole list re-renders; 3 = acceptable; 5 = smooth input, targeted re-renders, lazy-loaded heavy deps
- **Pass Threshold**: >= 4
- **Evidence**: React DevTools / code inspection of memoization and composer state isolation

## Open Questions
- None blocking; backend field support is treated as unconfirmed and guarded by existing flags.
