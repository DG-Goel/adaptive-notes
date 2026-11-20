import type { VideoLecture } from '@/types/video'

/**
 * Deterministic demo lecture used when `VITE_USE_MOCK_API=true`.
 *
 * The chapter timestamps below describe the *lecture* "Understanding
 * Transformers" and span its full `duration` (0 → 2650s), so the lecture
 * metadata and its chapters stay consistent with each other.
 *
 * The bundled playback fixture is an unrelated, much shorter sample clip
 * (public-domain "Sintel" trailer). Because it does not match the topic or
 * length, the lecture is flagged as a playback demonstration
 * (`isPlaybackDemo` / `playbackNote`) and its chapters and transcript are
 * labelled illustrative rather than presented as the clip's real content.
 */

/**
 * Served from `public/videos/` so playback is same-origin, works offline, and
 * never depends on a third-party host staying publicly readable. The previous
 * Google sample-bucket URL started returning HTTP 403, which surfaced as
 * MEDIA_ERR_SRC_NOT_SUPPORTED in the player.
 */
const DEMO_SOURCE_URL = '/videos/demo-lecture.mp4'

const demoTransformers: VideoLecture = {
  id: 'demo-transformers',
  title: 'Understanding Transformers: From Attention to Architecture',
  description:
    'A guided walkthrough of the Transformer architecture — starting from the intuition behind attention, building up to self-attention and multi-head attention, and finishing with how encoders and decoders are assembled. Designed for learners who already know the basics of neural networks.',
  course: 'Deep Learning Specialization',
  instructor: 'NOETRA Faculty',
  duration: 2650,
  source: {
    url: DEMO_SOURCE_URL,
    provider: 'Bundled sample clip (Sintel trailer)',
  },
  status: 'ready',
  updatedAt: '2026-02-18T09:30:00.000Z',
  isPlaybackDemo: true,
  playbackNote:
    'Playback demonstration: this lecture streams a short bundled sample clip (about 52 seconds) that is unrelated to the topic. The chapters and transcript below are illustrative — their timestamps describe the lecture, not the sample clip.',
  objectives: [
    'Explain why attention replaced recurrence for sequence modelling.',
    'Describe how queries, keys, and values produce an attention distribution.',
    'Differentiate self-attention from cross-attention.',
    'Explain the purpose of multiple attention heads.',
    'Summarise how positional encoding injects order information.',
    'Trace a forward pass through an encoder–decoder stack.',
  ],
  keyConcepts: [
    'Attention',
    'Query / Key / Value',
    'Scaled dot-product',
    'Self-attention',
    'Multi-head attention',
    'Positional encoding',
    'Encoder–decoder',
    'Residual connections',
    'Layer normalisation',
  ],
  chapters: [
    {
      id: 'ch-1',
      title: 'Introduction to Transformers',
      startTime: 0,
      endTime: 265,
      summary: 'Motivation: the limits of recurrent networks and the case for attention.',
    },
    {
      id: 'ch-2',
      title: 'Attention Mechanism',
      startTime: 265,
      endTime: 640,
      summary: 'Queries, keys, and values; scaled dot-product attention from first principles.',
    },
    {
      id: 'ch-3',
      title: 'Self-Attention',
      startTime: 640,
      endTime: 1035,
      summary: 'How a sequence attends to itself and builds contextual representations.',
    },
    {
      id: 'ch-4',
      title: 'Multi-Head Attention',
      startTime: 1035,
      endTime: 1470,
      summary: 'Parallel attention heads, concatenation, and the output projection.',
    },
    {
      id: 'ch-5',
      title: 'Positional Encoding',
      startTime: 1470,
      endTime: 1880,
      summary: 'Injecting order with sinusoidal encodings and why they generalise.',
    },
    {
      id: 'ch-6',
      title: 'Encoder and Decoder',
      startTime: 1880,
      endTime: 2290,
      summary: 'Stacking blocks, residual paths, layer norm, and cross-attention.',
    },
    {
      id: 'ch-7',
      title: 'Applications and Summary',
      startTime: 2290,
      endTime: 2650,
      summary: 'Where transformers are used today, and the key takeaways of the lecture.',
    },
  ],
  resources: [
    {
      id: 'res-1',
      label: 'Lecture slides (PDF)',
      kind: 'link',
      url: 'https://example.com/noetra/transformers-slides.pdf',
      description: 'Presentation deck used in the lecture.',
    },
    {
      id: 'res-2',
      label: 'Attention reference notes',
      kind: 'link',
      url: 'https://example.com/noetra/attention-notes',
      description: 'Supplementary reading on scaled dot-product attention.',
    },
  ],
}

/** The full mock catalogue. Only the demo lecture is bundled in this phase. */
export const mockVideoLectures: VideoLecture[] = [demoTransformers]

export function findMockLecture(id: string): VideoLecture | undefined {
  return mockVideoLectures.find((lecture) => lecture.id === id)
}
