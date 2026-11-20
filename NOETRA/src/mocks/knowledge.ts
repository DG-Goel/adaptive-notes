import type { KnowledgeGraph, KnowledgeNode, KnowledgeEdge } from '@/types/knowledge'

/**
 * Deterministic mock knowledge graph for Transformer architecture.
 *
 * This provides a realistic demonstration of concept relationships, not
 * extracted from the bundled Sintel trailer.
 */

const nodes: KnowledgeNode[] = [
  {
    id: 'transformer',
    label: 'Transformer Architecture',
    type: 'main',
    description:
      'A neural network architecture based entirely on self-attention mechanisms, introduced in "Attention Is All You Need" (2017).',
    videoId: 'demo-transformers',
    timestampSeconds: 0,
    importance: 5,
  },
  {
    id: 'attention',
    label: 'Attention Mechanism',
    type: 'topic',
    description:
      'A mechanism that allows the model to focus on different parts of the input when producing each element of the output.',
    videoId: 'demo-transformers',
    timestampSeconds: 265,
    importance: 5,
  },
  {
    id: 'self-attention',
    label: 'Self-Attention',
    type: 'subtopic',
    description:
      'Attention where queries, keys, and values all come from the same sequence, allowing each position to attend to all positions.',
    videoId: 'demo-transformers',
    timestampSeconds: 640,
    importance: 5,
  },
  {
    id: 'scaled-dot-product',
    label: 'Scaled Dot-Product Attention',
    type: 'formula',
    description:
      'The core attention calculation: Attention(Q, K, V) = softmax(QK^T / √dₖ)V',
    videoId: 'demo-transformers',
    timestampSeconds: 640,
    importance: 4,
  },
  {
    id: 'multi-head',
    label: 'Multi-Head Attention',
    type: 'subtopic',
    description:
      'Running multiple attention mechanisms in parallel, each learning different aspects of the relationships.',
    videoId: 'demo-transformers',
    timestampSeconds: 1035,
    importance: 5,
  },
  {
    id: 'positional-encoding',
    label: 'Positional Encoding',
    type: 'topic',
    description:
      'Sinusoidal functions added to input embeddings to inject sequence order information, since attention is permutation-invariant.',
    videoId: 'demo-transformers',
    timestampSeconds: 1470,
    importance: 4,
  },
  {
    id: 'encoder',
    label: 'Encoder',
    type: 'topic',
    description:
      'Stacked layers of self-attention and feed-forward networks that process the input sequence into contextual representations.',
    videoId: 'demo-transformers',
    timestampSeconds: 1820,
    importance: 4,
  },
  {
    id: 'decoder',
    label: 'Decoder',
    type: 'topic',
    description:
      'Stacked layers with masked self-attention, cross-attention to encoder output, and feed-forward networks for sequential generation.',
    videoId: 'demo-transformers',
    timestampSeconds: 2210,
    importance: 4,
  },
  {
    id: 'cross-attention',
    label: 'Cross-Attention',
    type: 'subtopic',
    description:
      'Attention where queries come from the decoder and keys/values from the encoder output.',
    videoId: 'demo-transformers',
    timestampSeconds: 2210,
    importance: 4,
  },
  {
    id: 'feed-forward',
    label: 'Position-wise Feed-Forward',
    type: 'subtopic',
    description:
      'Two-layer fully connected network applied independently to each position with a ReLU activation.',
    videoId: 'demo-transformers',
    timestampSeconds: 1820,
    importance: 3,
  },
  {
    id: 'layer-norm',
    label: 'Layer Normalization',
    type: 'subtopic',
    description:
      'Normalization applied after each sub-layer with residual connections for training stability.',
    videoId: 'demo-transformers',
    timestampSeconds: 1920,
    importance: 3,
  },
  {
    id: 'bert',
    label: 'BERT',
    type: 'application',
    description:
      'Bidirectional Encoder Representations from Transformers - encoder-only architecture for understanding tasks.',
    videoId: 'demo-transformers',
    timestampSeconds: 2850,
    importance: 4,
  },
  {
    id: 'gpt',
    label: 'GPT',
    type: 'application',
    description:
      'Generative Pre-trained Transformer - decoder-only architecture for text generation.',
    videoId: 'demo-transformers',
    timestampSeconds: 2850,
    importance: 4,
  },
  {
    id: 't5',
    label: 'T5',
    type: 'application',
    description:
      'Text-to-Text Transfer Transformer - full encoder-decoder architecture treating all tasks as text generation.',
    videoId: 'demo-transformers',
    timestampSeconds: 2850,
    importance: 3,
  },
  {
    id: 'complexity',
    label: 'Computational Complexity',
    type: 'subtopic',
    description:
      'Self-attention has O(n²) time complexity but constant path length between positions.',
    videoId: 'demo-transformers',
    timestampSeconds: 850,
    importance: 3,
  },
]

const edges: KnowledgeEdge[] = [
  {
    id: 'e1',
    source: 'transformer',
    target: 'attention',
    relationship: 'contains',
    label: 'based on',
  },
  {
    id: 'e2',
    source: 'transformer',
    target: 'encoder',
    relationship: 'contains',
    label: 'contains',
  },
  {
    id: 'e3',
    source: 'transformer',
    target: 'decoder',
    relationship: 'contains',
    label: 'contains',
  },
  {
    id: 'e4',
    source: 'transformer',
    target: 'positional-encoding',
    relationship: 'contains',
    label: 'requires',
  },
  {
    id: 'e5',
    source: 'attention',
    target: 'self-attention',
    relationship: 'contains',
    label: 'type of',
  },
  {
    id: 'e6',
    source: 'self-attention',
    target: 'scaled-dot-product',
    relationship: 'depends_on',
    label: 'uses',
  },
  {
    id: 'e7',
    source: 'self-attention',
    target: 'multi-head',
    relationship: 'related_to',
    label: 'extended by',
  },
  {
    id: 'e8',
    source: 'encoder',
    target: 'self-attention',
    relationship: 'contains',
    label: 'uses',
  },
  {
    id: 'e9',
    source: 'encoder',
    target: 'feed-forward',
    relationship: 'contains',
    label: 'includes',
  },
  {
    id: 'e10',
    source: 'encoder',
    target: 'layer-norm',
    relationship: 'contains',
    label: 'applies',
  },
  {
    id: 'e11',
    source: 'decoder',
    target: 'self-attention',
    relationship: 'contains',
    label: 'masked',
  },
  {
    id: 'e12',
    source: 'decoder',
    target: 'cross-attention',
    relationship: 'contains',
    label: 'uses',
  },
  {
    id: 'e13',
    source: 'decoder',
    target: 'feed-forward',
    relationship: 'contains',
    label: 'includes',
  },
  {
    id: 'e14',
    source: 'decoder',
    target: 'layer-norm',
    relationship: 'contains',
    label: 'applies',
  },
  {
    id: 'e15',
    source: 'cross-attention',
    target: 'encoder',
    relationship: 'depends_on',
    label: 'attends to',
  },
  {
    id: 'e16',
    source: 'self-attention',
    target: 'complexity',
    relationship: 'related_to',
    label: 'has',
  },
  {
    id: 'e17',
    source: 'transformer',
    target: 'bert',
    relationship: 'applied_in',
    label: 'enables',
  },
  {
    id: 'e18',
    source: 'transformer',
    target: 'gpt',
    relationship: 'applied_in',
    label: 'enables',
  },
  {
    id: 'e19',
    source: 'transformer',
    target: 't5',
    relationship: 'applied_in',
    label: 'enables',
  },
  {
    id: 'e20',
    source: 'encoder',
    target: 'bert',
    relationship: 'applied_in',
    label: 'basis of',
  },
  {
    id: 'e21',
    source: 'decoder',
    target: 'gpt',
    relationship: 'applied_in',
    label: 'basis of',
  },
]

export const mockKnowledgeGraph: KnowledgeGraph = {
  videoId: 'demo-transformers',
  videoTitle: 'Attention Is All You Need: The Transformer Architecture',
  nodes,
  edges,
  createdAt: '2026-02-18T09:00:00.000Z',
  isDemo: true,
}
