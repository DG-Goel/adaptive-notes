# NOETRA Phase 5 — AI Tutor Implementation Plan

## Task 1: Extend tutor types (context, explanations, conversations, citations)
- **Status**: `pending`
- **Priority**: high
- **Depends On**: None
- **Description**:
  - Add `TutorContext` discriminated union (`general` | `video` | `chapter` | `timestamp` | `notes`) per spec §6.
  - Add `ExplanationMode` (`simple` | `detailed` | `step-by-step` | `examples` | `revision`) and `ExplanationPreferences` (length, includeExamples, includeMath, preferBullets) per spec §7.
  - Expand `TutorCitation` to the extensible model (`video` | `transcript` | `notes` | `document`, with optional videoId/sectionId/startSeconds/endSeconds/title/excerpt/sourceId) while keeping the existing `label`+`timestamp` shape backward-compatible.
  - Add `TutorConversation` (id, title, videoId?, context, messages[], createdAt, updatedAt, isDemo).
  - Add streaming-capable interfaces (`askTutorStream`) with an SSE-shaped callback, unused until a real streaming endpoint is confirmed.
- **Acceptance Criteria Addressed**: AC-5, AC-6
- **Test Requirements**:
  - `rule` TR-1.1: `TutorContext` is a discriminated union with exactly the five variants and required fields; TypeScript compiles.
  - `rule` TR-1.2: Existing `TutorMessage`, `AskRequest`, `AskResponse` remain assignable (no breaking change to `TutorSidebar` consumers).
  - `rule` TR-1.3: `ExplanationMode` values are limited to the five spec modes; `ExplanationPreferences` fields are optional.

## Task 2: Extend tutor service with capability-driven mapping and streaming interface
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 1
- **Description**:
  - Add a `tutorCapabilities` object (e.g. `supportsVideoScope`, `supportsChapterScope`, `supportsTimestampScope`, `supportsNotesScope`, `supportsStreaming`, `supportsConversationPersistence`) defaulting to the currently-confirmed state (only `video_id` behind the existing `includeVideoScope` flag; everything else false).
  - Centralize context→request mapping: only send fields the backend is confirmed to accept. Unsupported context modes are still represented in the UI but the request falls back to the supported subset (never silently to whole-video — the caller disables unsupported modes).
  - Keep `askTutor` signature stable; add `context?` and `preferences?` params that are no-ops unless capability flags allow.
  - Add `askTutorStream` interface (async iterable or callback) that throws "streaming not supported" in real mode unless `supportsStreaming`; mock mode can yield the full answer in one chunk (not simulated token streaming).
  - Add conversation-list/create/delete helpers backed by localStorage in mock mode and clearly labelled session-only in real mode.
- **Acceptance Criteria Addressed**: AC-5, AC-6, AC-7, AC-9, AC-13
- **Test Requirements**:
  - `rule` TR-2.1: In real mode with default capabilities, `askTutor` request body contains only `question`, `mode`, `top_k`, `conversation_history` (no context/explanation fields).
  - `rule` TR-2.2: `askTutorStream` rejects with a clear "streaming not supported" error when `supportsStreaming` is false.
  - `rule` TR-2.3: Conversation helpers read/write localStorage in mock mode and are labelled demo; real mode does not write to localStorage.

## Task 3: Create shared conversation state layer (context + hook)
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 1, Task 2
- **Description**:
  - Create `TutorConversationProvider` (React context) holding the active conversation, conversation list, draft input, context, and explanation preferences.
  - Provide `useTutorConversation` hook with actions: `newConversation`, `selectConversation`, `deleteConversation`, `sendMessage`, `retry`, `regenerate`, `stop`, `setContext`, `setExplanationPreferences`, `renameConversation`.
  - State is shared so the sidebar and full page read the same conversation; switching views does not discard messages or draft.
  - Persist list to localStorage in mock mode; session-only in real mode with a clear label.
  - Use TanStack Query mutation for sending (retry/cancel via AbortController).
- **Acceptance Criteria Addressed**: AC-2, AC-9
- **Test Requirements**:
  - `rule` TR-3.1: Two components consuming `useTutorConversation` within the same provider see identical `messages` and `activeConversationId`.
  - `rule` TR-3.2: `sendMessage` appends user + assistant messages; failed requests surface an error with retry.
  - `rule` TR-3.3: Draft input persists when switching from sidebar to full page.

## Task 4: Build tutor UI components (workspace, list, messages, composer)
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 3
- **Description**:
  - `TutorWorkspace`: three-column responsive layout (conversation list | conversation | learning-context panel), collapsible right panel, mobile drawer for the list.
  - `ConversationList`: new conversation, search, time-grouped items, active state, delete confirmation, context label.
  - `ConversationHeader`: title, context badge, explanation-mode indicator, open-in-full-page / collapse controls.
  - `MessageList` + `MessageBubble`: user messages compact; assistant messages render via existing `MarkdownBlock` (Markdown + KaTeX + code + tables, no raw HTML). Copy, regenerate, retry actions. Loading skeleton. Scroll-to-latest only when near bottom.
  - `MessageComposer`: auto-growing textarea, Enter send / Shift+Enter newline, stop button while pending, send button.
  - `SourceCitation`: citation chips with excerpt preview popover; timestamp citations reuse `TimestampChip` (seek or deep-link).
  - `ContextSelector` and `ExplanationModeSelector`: dropdowns reflecting the typed model; unsupported modes disabled with tooltip.
  - `SuggestedQuestions`: context-appropriate deterministic suggestions, labelled as UI suggestions in real mode.
- **Acceptance Criteria Addressed**: AC-1, AC-3, AC-4, AC-5, AC-6, AC-8, AC-11, AC-12
- **Test Requirements**:
  - `rule` TR-4.1: Assistant message containing headings, math, code, and table renders each element without raw HTML injection.
  - `rule` TR-4.2: Clicking a timestamp citation calls `seekTo` when a player is mounted.
  - `rule` TR-4.3: Unsupported context modes are disabled and show an explanation.
  - `rubric` TR-4.4: Visual coherence and readability; scale 1-5; anchors 1=off-brand/unreadable, 3=functional/generic, 5=calm/luxurious/on-brand; threshold >=4; evidence = visual inspection.

## Task 5: Implement the full `/tutor` page (replace placeholder)
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 4
- **Description**:
  - Replace `TutorPage`'s `PlaceholderPage` with `TutorWorkspace` wrapped in `TutorConversationProvider`.
  - Lazy-load the page (already route-level; ensure the heavy Tutor bundle is split).
  - Learning-context panel shows selected lecture / current chapter / selected note section / related concepts and quick links to notes.
- **Acceptance Criteria Addressed**: AC-1, AC-10
- **Test Requirements**:
  - `rule` TR-5.1: `/tutor` renders the workspace (conversation list + composer + context panel) with no console errors.

## Task 6: Refactor TutorSidebar to reuse shared components and state
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 4
- **Description**:
  - Replace the local `useState` message list with `useTutorConversation` so the sidebar and full page share state.
  - Reuse `MessageList`/`MessageBubble`/`MessageComposer`/`SourceCitation`/`SuggestedQuestions`.
  - Keep the compact layout and collapse behaviour; add "expand to full Tutor" button navigating to `/tutor`.
  - Do not interrupt video playback when messages arrive.
  - Mobile drawer behaviour preserved.
- **Acceptance Criteria Addressed**: AC-2, AC-11
- **Test Requirements**:
  - `rule` TR-6.1: Messages sent in the sidebar appear when navigating to `/tutor` and vice versa.
  - `rule` TR-6.2: Tutor sidebar still collapses to a narrow strip and expands without losing state.

## Task 7: Notes Studio "Ask AI" integration
- **Status**: `pending`
- **Priority**: medium
- **Depends On**: Task 3
- **Description**:
  - Add per-section actions in the Notes Studio: "Ask AI about this section", "Explain this", "Give an example", "Simplify this".
  - These open Tutor (navigate to `/tutor` or open the existing conversation) with `TutorContext = { type: 'notes', videoId, sectionId, selectedText? }` and a suggested question.
  - Preserve videoId, sectionId, selected text, source timestamp; provide return navigation.
  - If backend notes-scope is unsupported, show an honest unsupported state (the UI still opens with the context, but the request uses only supported fields).
- **Acceptance Criteria Addressed**: AC-8
- **Test Requirements**:
  - `rule` TR-7.1: Clicking "Ask AI about this section" opens Tutor with context reflecting the section and pre-fills a question.

## Task 8: Extend mock data with rich Transformer conversations
- **Status**: `pending`
- **Priority**: medium
- **Depends On**: Task 1
- **Description**:
  - Add seed conversations to `mocks/tutor.ts` containing Markdown headings, a GFM table, a KaTeX block equation, a fenced code block, timestamp citations, and suggested follow-ups.
  - Keep the Sintel-vs-Transformer distinction (mock citations refer to illustrative lecture data, not the sample clip).
  - Label all mock responses as demo.
- **Acceptance Criteria Addressed**: AC-3, AC-4, AC-7, AC-14
- **Test Requirements**:
  - `rule` TR-8.1: Seed conversation includes at least one table, one math block, one code block, and one timestamp citation.

## Task 9: Wire up, lint, build, and browser-verify
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Tasks 5, 6, 7, 8
- **Description**:
  - Ensure all imports resolve; no duplicate message models.
  - Run `npm run lint` and `npm run build`; fix any errors.
  - Browser-test `/tutor`, video-workspace sidebar, and Notes→Tutor navigation; confirm no console errors.
- **Acceptance Criteria Addressed**: AC-10
- **Test Requirements**:
  - `rule` TR-9.1: `npm run lint` exits 0 with 0 errors.
  - `rule` TR-9.2: `npm run build` exits 0.
  - `rule` TR-9.3: `/tutor`, `/learn/demo-transformers` (sidebar), and Notes→Tutor flow render with 0 console errors.
