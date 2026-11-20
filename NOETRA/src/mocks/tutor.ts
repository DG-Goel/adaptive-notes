import type {
  ExplanationMode,
  TutorCitation,
  TutorContext,
  TutorConversation,
  TutorMessage,
} from '@/types/tutor'

/** Suggested prompts surfaced in the tutor panel. */
export const suggestedTutorPrompts: string[] = [
  'Explain self-attention simply.',
  'What is the purpose of positional encoding?',
  'Compare self-attention and cross-attention.',
  'Give me an example from this lecture.',
]

/** Suggestions tailored to a notes context. */
export const notesSuggestedPrompts: string[] = [
  'Summarize this section.',
  'Explain this formula.',
  'Give a practical example.',
  'Compare these two ideas.',
]

const RICH_ASSISTANT_CONTENT = `## Self-attention, briefly

Self-attention lets every token in a sequence weigh the relevance of every other token. Each token produces three vectors — a **query**, a **key**, and a **value** — and the attention score is the scaled dot-product of the query with each key:

$$\\text{Attention}(Q, K, V) = \\text{softmax}\\!\\left(\\frac{QK^\\top}{\\sqrt{d_k}}\\right)V$$

### Why the scaling factor

Without \\(\\sqrt{d_k}\\), large dot products push the softmax into a saturated region where gradients vanish. Dividing keeps the distribution well-behaved.

### A minimal example

\`\`\`python
import torch
import torch.nn.functional as F

def attention(q, k, v):
    scores = q @ k.transpose(-2, -1) / (q.size(-1) ** 0.5)
    return F.softmax(scores, dim=-1) @ v
\`\`\`

### Heads at a glance

| Head count | Effect |
| --- | --- |
| 1 | Standard attention |
| 8 | The original Transformer default |
| More | Parallel relationship types, but costlier |

> Multi-head attention concatenates the outputs of several attention heads and projects the result back to the model dimension.`

/**
 * Seeded conversation so the panel is never empty in demo mode.
 *
 * The citations reference the illustrative Transformer lecture, not the
 * bundled Sintel sample clip. That distinction is intentional and must be
 * preserved.
 */
export const mockTutorConversation: TutorConversation = {
  id: 'conv-attention-intro',
  title: 'Attention & self-attention',
  videoId: 'demo-transformers',
  context: { type: 'video', videoId: 'demo-transformers' },
  isDemo: true,
  createdAt: '2026-02-18T09:36:00.000Z',
  updatedAt: '2026-02-18T09:36:04.000Z',
  messages: [
    {
      id: 'msg-1',
      role: 'user',
      content: 'What is the core idea behind attention?',
      createdAt: '2026-02-18T09:36:00.000Z',
    },
    {
      id: 'msg-2',
      role: 'assistant',
      content:
        'Attention is a learned lookup. Each position forms a query, every position offers a key and a value, and the softmax of the scaled query–key scores decides how much of each value to gather. The result is a representation that can pull in information from anywhere in the sequence.',
      createdAt: '2026-02-18T09:36:04.000Z',
      citations: [
        { id: 'cit-1', type: 'video', label: 'Attention Mechanism', timestamp: 265, videoId: 'demo-transformers' },
      ],
      isDemo: true,
    },
    {
      id: 'msg-3',
      role: 'user',
      content: 'Walk me through self-attention with the math and some code.',
      createdAt: '2026-02-18T09:37:00.000Z',
    },
    {
      id: 'msg-4',
      role: 'assistant',
      content: RICH_ASSISTANT_CONTENT,
      createdAt: '2026-02-18T09:37:04.000Z',
      citations: [
        { id: 'cit-2', type: 'video', label: 'Self-Attention', timestamp: 640, videoId: 'demo-transformers' },
        { id: 'cit-3', type: 'video', label: 'Multi-Head Attention', timestamp: 1035, videoId: 'demo-transformers' },
      ],
      isDemo: true,
    },
  ],
}

/** Backwards-compatible seed message list (used by the legacy sidebar until refactored). */
export const mockTutorMessages: TutorMessage[] = mockTutorConversation.messages

interface CannedAnswer {
  /** Lower-case substring used to match a question. */
  match: string
  answer: string
  citations: TutorCitation[]
}

const cannedAnswers: CannedAnswer[] = [
  {
    match: 'self-attention simply',
    answer:
      'Think of a sentence where every word gets to ask every other word "how relevant are you to me?". Self-attention is that: the queries, keys, and values all come from the same sequence, so each token rebuilds its meaning using the context of the whole sentence.',
    citations: [{ id: 'c-self', type: 'video', label: 'Self-Attention', timestamp: 640, videoId: 'demo-transformers' }],
  },
  {
    match: 'self-attention and cross-attention',
    answer:
      'In self-attention the queries, keys, and values all come from the same sequence, so tokens enrich each other. In cross-attention the queries come from one sequence (the decoder) while the keys and values come from another (the encoder output) — that is how the decoder asks questions of the encoded input.',
    citations: [
      { id: 'c-self2', type: 'video', label: 'Self-Attention', timestamp: 640, videoId: 'demo-transformers' },
      { id: 'c-enc', type: 'video', label: 'Encoder and Decoder', timestamp: 2210, videoId: 'demo-transformers' },
    ],
  },
  {
    match: 'purpose of positional encoding',
    answer:
      'Attention is permutation-invariant: shuffle the tokens and each one still sees the same set of neighbours. Positional encodings add order information to the input embeddings so the model can reason about sequence position. The original paper uses fixed sinusoids, which extrapolate better to unseen lengths.',
    citations: [{ id: 'c-pos', type: 'video', label: 'Positional Encoding', timestamp: 1470, videoId: 'demo-transformers' }],
  },
  {
    match: 'example from this lecture',
    answer:
      'Use the multi-head attention section as a concrete example: the input is projected into several smaller subspaces, each head runs its own attention, then the outputs are concatenated and projected back to the model dimension. That lets different heads track different relationship types in parallel.',
    citations: [{ id: 'c-mha', type: 'video', label: 'Multi-Head Attention', timestamp: 1035, videoId: 'demo-transformers' }],
  },
]

const fallbackAnswer =
  'This demo tutor only has a small set of prepared answers. Try one of the suggested questions — in a later phase the tutor will query the retrieval backend and return grounded answers with citations.'

/**
 * Deterministic demo reply for a question.
 *
 * This never invents content in real API mode — the service layer only calls
 * this helper when `VITE_USE_MOCK_API=true`.
 */
export function buildMockAnswer(question: string): {
  answer: string
  citations: TutorCitation[]
  isDemo: true
} {
  const normalised = question.toLowerCase()
  const canned = cannedAnswers.find((entry) => normalised.includes(entry.match))

  if (canned) {
    return { answer: canned.answer, citations: canned.citations, isDemo: true }
  }

  return { answer: fallbackAnswer, citations: [], isDemo: true }
}

/** Explanation mode metadata for the selector UI. */
export const EXPLANATION_MODES: {
  value: ExplanationMode
  label: string
  description: string
}[] = [
  { value: 'simple', label: 'Simple', description: 'Beginner-friendly explanation' },
  { value: 'detailed', label: 'Detailed', description: 'Comprehensive explanation' },
  { value: 'step-by-step', label: 'Step-by-step', description: 'Structured reasoning and examples' },
  { value: 'examples', label: 'Examples', description: 'Practical applications' },
  { value: 'revision', label: 'Revision', description: 'Concise exam-oriented explanation' },
]

/** Context option metadata for the selector UI. */
export const CONTEXT_OPTIONS: {
  value: TutorContext['type']
  label: string
  description: string
  supported: boolean
}[] = [
  { value: 'general', label: 'General Tutor', description: 'Ask without a specific video or notes context', supported: true },
  { value: 'video', label: 'Full Video', description: 'Ask using the selected lecture as context', supported: true },
  { value: 'chapter', label: 'Current Chapter', description: 'Ask about the video chapter currently being played', supported: false },
  { value: 'timestamp', label: 'Selected Timestamp Range', description: 'Ask about a chosen portion of a video', supported: false },
  { value: 'notes', label: 'Selected Notes', description: 'Ask about a specific note section or selected text', supported: false },
]
