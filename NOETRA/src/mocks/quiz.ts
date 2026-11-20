import type {
  Quiz,
  QuizQuestion,
  QuestionType,
  QuizDifficulty,
  QuizAttemptSummary,
} from '@/types/quiz'

/**
 * Deterministic mock quiz about Transformer architecture.
 *
 * This fixture provides realistic demonstration questions with explanations
 * and timestamp references. It is not extracted from the Sintel trailer —
 * that distinction is preserved deliberately.
 */

const TRANSFORMER_QUESTIONS: QuizQuestion[] = [
  {
    id: 'q1',
    type: 'single_select',
    question: 'What is the primary innovation of the Transformer architecture?',
    options: [
      { id: 'a', text: 'Recurrent connections for sequential processing' },
      { id: 'b', text: 'Self-attention mechanism for parallel processing' },
      { id: 'c', text: 'Convolutional layers for feature extraction' },
      { id: 'd', text: 'LSTM cells for long-term memory' },
    ],
    correctAnswers: ['b'],
    explanation:
      'The Transformer architecture introduced self-attention as the core mechanism, allowing all positions to attend to each other in parallel rather than processing sequentially like RNNs.',
    difficulty: 'medium',
    source: {
      videoId: 'demo-transformers',
      timestampSeconds: 265,
      excerpt: 'The key innovation is the self-attention mechanism...',
    },
  },
  {
    id: 'q2',
    type: 'true_false',
    question: 'Positional encoding is necessary because attention is permutation-invariant.',
    options: [
      { id: 'true', text: 'True' },
      { id: 'false', text: 'False' },
    ],
    correctAnswers: ['true'],
    explanation:
      'True. Self-attention treats the input as a set, not a sequence. Without positional encoding, shuffling the tokens would produce the same output. Positional encodings add order information to the embeddings.',
    difficulty: 'easy',
    source: {
      videoId: 'demo-transformers',
      timestampSeconds: 1470,
    },
  },
  {
    id: 'q3',
    type: 'multi_select',
    question:
      'Which components are part of the multi-head attention mechanism? (Select all that apply)',
    options: [
      { id: 'a', text: 'Query projection' },
      { id: 'b', text: 'Key projection' },
      { id: 'c', text: 'Value projection' },
      { id: 'd', text: 'Recurrent state' },
      { id: 'e', text: 'Output projection' },
    ],
    correctAnswers: ['a', 'b', 'c', 'e'],
    explanation:
      'Multi-head attention projects the input into multiple subspaces using query, key, and value projections for each head, then concatenates the results and applies an output projection. Recurrent state is not part of the Transformer.',
    difficulty: 'hard',
    source: {
      videoId: 'demo-transformers',
      timestampSeconds: 1035,
    },
  },
  {
    id: 'q4',
    type: 'single_select',
    question: 'Why is the attention score scaled by √dₖ?',
    options: [
      { id: 'a', text: 'To increase gradient magnitude' },
      { id: 'b', text: 'To prevent softmax saturation' },
      { id: 'c', text: 'To normalize the key vectors' },
      { id: 'd', text: 'To match the embedding dimension' },
    ],
    correctAnswers: ['b'],
    explanation:
      'Scaling by the square root of the key dimension prevents the dot products from growing too large, which would push the softmax into regions with vanishing gradients.',
    difficulty: 'medium',
    source: {
      videoId: 'demo-transformers',
      timestampSeconds: 640,
    },
  },
  {
    id: 'q5',
    type: 'true_false',
    question: 'The Transformer encoder and decoder have identical architectures.',
    options: [
      { id: 'true', text: 'True' },
      { id: 'false', text: 'False' },
    ],
    correctAnswers: ['false'],
    explanation:
      'False. While both use multi-head attention, the decoder includes an additional cross-attention layer that attends to the encoder output, and uses masked self-attention to prevent attending to future positions.',
    difficulty: 'easy',
    source: {
      videoId: 'demo-transformers',
      timestampSeconds: 2210,
    },
  },
  {
    id: 'q6',
    type: 'multi_select',
    question: 'Which of the following are benefits of the Transformer architecture?',
    options: [
      { id: 'a', text: 'Parallelizable training' },
      { id: 'b', text: 'Constant path length between any two positions' },
      { id: 'c', text: 'Lower memory requirements than RNNs' },
      { id: 'd', text: 'Better at capturing long-range dependencies' },
    ],
    correctAnswers: ['a', 'b', 'd'],
    explanation:
      'Transformers enable parallel training, have constant-length paths between positions (attention connects all pairs directly), and handle long-range dependencies well. However, they typically require more memory than RNNs due to the quadratic attention complexity.',
    difficulty: 'medium',
    source: {
      videoId: 'demo-transformers',
      timestampSeconds: 430,
    },
  },
  {
    id: 'q7',
    type: 'single_select',
    question: 'What is the time complexity of self-attention for a sequence of length n?',
    options: [
      { id: 'a', text: 'O(n)' },
      { id: 'b', text: 'O(n log n)' },
      { id: 'c', text: 'O(n²)' },
      { id: 'd', text: 'O(n³)' },
    ],
    correctAnswers: ['c'],
    explanation:
      'Self-attention computes a score between every pair of positions, resulting in O(n²) time complexity. This is both a strength (constant path length) and a limitation (expensive for long sequences).',
    difficulty: 'hard',
    source: {
      videoId: 'demo-transformers',
      timestampSeconds: 850,
    },
  },
  {
    id: 'q8',
    type: 'true_false',
    question: 'Feed-forward layers in the Transformer are applied position-wise independently.',
    options: [
      { id: 'true', text: 'True' },
      { id: 'false', text: 'False' },
    ],
    correctAnswers: ['true'],
    explanation:
      'True. Each position passes through the same feed-forward network independently, with no interaction between positions at this stage. This is why they are called "position-wise" feed-forward networks.',
    difficulty: 'easy',
    source: {
      videoId: 'demo-transformers',
      timestampSeconds: 1820,
    },
  },
  {
    id: 'q9',
    type: 'single_select',
    question:
      'In the original "Attention Is All You Need" paper, how many attention heads were used?',
    options: [
      { id: 'a', text: '4' },
      { id: 'b', text: '8' },
      { id: 'c', text: '12' },
      { id: 'd', text: '16' },
    ],
    correctAnswers: ['b'],
    explanation:
      'The original Transformer used 8 parallel attention heads. Each head operates on a dₖ = dᵥ = 64 dimensional subspace, with the model dimension being 512.',
    difficulty: 'medium',
    source: {
      videoId: 'demo-transformers',
      timestampSeconds: 1035,
    },
  },
  {
    id: 'q10',
    type: 'multi_select',
    question: 'Which of the following use the Transformer architecture?',
    options: [
      { id: 'a', text: 'BERT' },
      { id: 'b', text: 'GPT' },
      { id: 'c', text: 'ResNet' },
      { id: 'd', text: 'T5' },
      { id: 'e', text: 'LSTM' },
    ],
    correctAnswers: ['a', 'b', 'd'],
    explanation:
      'BERT (encoder-only), GPT (decoder-only), and T5 (encoder-decoder) all use Transformer architectures. ResNet is a convolutional network, and LSTM is a recurrent architecture.',
    difficulty: 'easy',
    source: {
      videoId: 'demo-transformers',
      timestampSeconds: 2850,
    },
  },
]

export function buildMockQuiz(config: {
  questionCount: number
  difficulty?: QuizDifficulty
  questionTypes?: QuestionType[]
}): Quiz {
  let filtered = [...TRANSFORMER_QUESTIONS]

  // Filter by difficulty
  if (config.difficulty && config.difficulty !== 'mixed') {
    filtered = filtered.filter((q) => q.difficulty === config.difficulty)
  }

  // Filter by question types
  if (config.questionTypes && config.questionTypes.length > 0) {
    filtered = filtered.filter((q) => config.questionTypes!.includes(q.type))
  }

  // Take requested count
  const questions = filtered.slice(0, config.questionCount)

  return {
    id: `mock-quiz-${Date.now()}`,
    videoId: 'demo-transformers',
    title: 'Transformer Architecture Quiz',
    config: {
      videoId: 'demo-transformers',
      questionCount: config.questionCount,
      difficulty: config.difficulty ?? 'mixed',
      questionTypes: config.questionTypes ?? ['single_select', 'multi_select', 'true_false'],
      context: 'video',
      showExplanations: true,
      timed: false,
      shuffleQuestions: false,
      shuffleOptions: false,
      mode: 'practice',
    },
    questions,
    createdAt: new Date().toISOString(),
    isDemo: true,
  }
}

/**
 * Grade a quiz attempt deterministically.
 *
 * This is only called in mock mode — real mode uses backend grading.
 */
export function gradeQuizAttempt(
  quiz: Quiz,
  answers: Record<string, string[]>,
): {
  score: number
  correctCount: number
  incorrectCount: number
  unansweredCount: number
} {
  let correctCount = 0
  let incorrectCount = 0
  let unansweredCount = 0

  for (const question of quiz.questions) {
    const userAnswers = answers[question.id] ?? []
    const correctAnswers = question.correctAnswers ?? []

    if (userAnswers.length === 0) {
      unansweredCount++
      continue
    }

    const isCorrect =
      userAnswers.length === correctAnswers.length &&
      userAnswers.every((ans) => correctAnswers.includes(ans))

    if (isCorrect) {
      correctCount++
    } else {
      incorrectCount++
    }
  }

  const score = correctCount
  return { score, correctCount, incorrectCount, unansweredCount }
}

export const mockQuizHistory: QuizAttemptSummary[] = [
  {
    id: 'attempt-1',
    quizId: 'mock-quiz-1',
    videoId: 'demo-transformers',
    videoTitle: 'Attention Is All You Need: The Transformer Architecture',
    questionCount: 10,
    difficulty: 'mixed',
    mode: 'practice',
    score: 8,
    percentage: 80,
    timeSpent: 420,
    attemptedAt: '2026-02-18T10:30:00.000Z',
    completed: true,
    isDemo: true,
  },
  {
    id: 'attempt-2',
    quizId: 'mock-quiz-2',
    videoId: 'demo-transformers',
    videoTitle: 'Attention Is All You Need: The Transformer Architecture',
    questionCount: 5,
    difficulty: 'easy',
    mode: 'practice',
    score: 5,
    percentage: 100,
    timeSpent: 180,
    attemptedAt: '2026-02-19T14:15:00.000Z',
    completed: true,
    isDemo: true,
  },
]
