import type { TranscriptSegment, VideoTranscript } from '@/types/transcript'

/**
 * Deterministic mock transcript for the demo lecture.
 * Timestamps describe the lecture content (see `mocks/videos.ts`).
 */

const demoTransformersSegments: TranscriptSegment[] = [
  { id: 't-1', startTime: 0, endTime: 42, speaker: 'Instructor', text: "Welcome. Today we're building an intuition for the Transformer — the architecture behind almost every modern language model." },
  { id: 't-2', startTime: 42, endTime: 118, speaker: 'Instructor', text: 'Before transformers, sequence models relied on recurrence: processing one token at a time and carrying a hidden state forward.' },
  { id: 't-3', startTime: 118, endTime: 197, speaker: 'Instructor', text: 'That sequential design made training slow, because you could not parallelise across the sequence.' },
  { id: 't-4', startTime: 197, endTime: 265, speaker: 'Instructor', text: 'The Transformer paper asked a simple question — what if we drop recurrence entirely and let every position attend to every other position?' },
  { id: 't-5', startTime: 265, endTime: 348, speaker: 'Instructor', text: 'Attention takes three inputs: queries, keys, and values. Think of a query as a question, and keys as labels that describe what each position offers.' },
  { id: 't-6', startTime: 348, endTime: 431, speaker: 'Instructor', text: 'We score every query against every key with a dot product, producing a matrix of compatibility scores.' },
  { id: 't-7', startTime: 431, endTime: 520, speaker: 'Instructor', text: 'Those scores are scaled by the square root of the key dimension, which keeps the softmax in a well-behaved range.' },
  { id: 't-8', startTime: 520, endTime: 640, speaker: 'Instructor', text: 'A softmax turns the scaled scores into a probability distribution, and we use it to take a weighted sum of the values.' },
  { id: 't-9', startTime: 640, endTime: 729, speaker: 'Instructor', text: 'Self-attention is the special case where queries, keys, and values all come from the same sequence.' },
  { id: 't-10', startTime: 729, endTime: 842, speaker: 'Instructor', text: 'Each token builds a new representation by gathering information from every other token in the sequence.' },
  { id: 't-11', startTime: 842, endTime: 938, speaker: 'Instructor', text: 'This is what makes the output contextual: the embedding for a word now depends on the words around it.' },
  { id: 't-12', startTime: 938, endTime: 1035, speaker: 'Instructor', text: 'It is worth noting the cost — attention is quadratic in sequence length, because every position attends to every other position.' },
  { id: 't-13', startTime: 1035, endTime: 1141, speaker: 'Instructor', text: 'A single attention operation can only express one kind of relationship. Multi-head attention runs several of them in parallel.' },
  { id: 't-14', startTime: 1141, endTime: 1256, speaker: 'Instructor', text: 'Each head projects the input into its own smaller subspace, so different heads can specialise — some track syntax, others track meaning.' },
  { id: 't-15', startTime: 1256, endTime: 1372, speaker: 'Instructor', text: 'We concatenate the head outputs and pass them through a final linear projection to return to the model dimension.' },
  { id: 't-16', startTime: 1372, endTime: 1470, speaker: 'Instructor', text: 'Crucially, the heads are computed in parallel, so the extra expressiveness comes at modest cost.' },
  { id: 't-17', startTime: 1470, endTime: 1567, speaker: 'Instructor', text: 'Attention is permutation-invariant — shuffle the tokens and each one still sees the same set of others.' },
  { id: 't-18', startTime: 1567, endTime: 1668, speaker: 'Instructor', text: 'To give the model a sense of order we add positional encodings to the input embeddings.' },
  { id: 't-19', startTime: 1668, endTime: 1779, speaker: 'Instructor', text: 'The original paper uses fixed sinusoids of different frequencies, which allows the model to generalise to sequence lengths it never saw in training.' },
  { id: 't-20', startTime: 1779, endTime: 1880, speaker: 'Instructor', text: 'Learned positional embeddings are an alternative, but they do not extrapolate as gracefully.' },
  { id: 't-21', startTime: 1880, endTime: 1993, speaker: 'Instructor', text: 'Now we can assemble a block: multi-head attention, a position-wise feed-forward network, residual connections, and layer normalisation.' },
  { id: 't-22', startTime: 1993, endTime: 2104, speaker: 'Instructor', text: 'The encoder stacks these blocks, letting each layer refine the representation of the whole sequence.' },
  { id: 't-23', startTime: 2104, endTime: 2210, speaker: 'Instructor', text: 'The decoder adds a masked self-attention layer — masking prevents a position from looking at future tokens — plus cross-attention over the encoder output.' },
  { id: 't-24', startTime: 2210, endTime: 2290, speaker: 'Instructor', text: "Cross-attention is where the decoder asks questions of the encoded input, using the encoder's outputs as keys and values." },
  { id: 't-25', startTime: 2290, endTime: 2398, speaker: 'Instructor', text: 'Transformers now power translation, summarisation, code generation, speech recognition, and even vision.' },
  { id: 't-26', startTime: 2398, endTime: 2510, speaker: 'Instructor', text: 'To recap: attention replaces recurrence; self-attention builds context; multiple heads add expressiveness; positional encodings restore order.' },
  { id: 't-27', startTime: 2510, endTime: 2602, speaker: 'Instructor', text: 'If you remember one idea, remember this — attention lets every position decide, dynamically, where to look for information.' },
  { id: 't-28', startTime: 2602, endTime: 2650, speaker: 'Instructor', text: 'In the next lecture we will implement a single attention head from scratch and trace its gradients.' },
]

export const mockTranscripts: VideoTranscript[] = [
  { videoId: 'demo-transformers', language: 'en', segments: demoTransformersSegments },
]

export function findMockTranscript(videoId: string): VideoTranscript | undefined {
  return mockTranscripts.find((transcript) => transcript.videoId === videoId)
}
