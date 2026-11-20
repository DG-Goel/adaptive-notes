import type {
  LectureSummary,
  NoteDocument,
  NoteDocumentVersion,
  NoteSection,
  NotesExportCapability,
  NotesProcessingStatus,
  VisualArtifact,
} from '@/types/notes'

/**
 * Deterministic mock notes, summaries, and visual artifacts.
 * All AI-looking content is explicitly labelled as demo material.
 */

const demoSummary: LectureSummary = {
  videoId: 'demo-transformers',
  executive:
    'The Transformer replaces recurrence with attention. Every position can attend directly to every other position, which makes training parallelisable and captures long-range dependencies. Self-attention builds contextual representations, multiple heads capture different relationship types, and positional encodings restore order.',
  takeaways: [
    'Attention is a learned, differentiable lookup: queries match keys, and the resulting weights aggregate values.',
    'Self-attention turns each token into a context-aware representation.',
    'Multi-head attention runs several attentions in parallel for richer expressiveness.',
    'Positional encodings are necessary because attention alone is order-agnostic.',
    'Encoder–decoder stacks combine attention, feed-forward layers, residuals, and normalisation.',
  ],
  concepts: [
    { term: 'Scaled dot-product attention', definition: 'Scores queries against keys, scales by 1/sqrt(d_k), softmaxes, and aggregates values.' },
    { term: 'Self-attention', definition: 'Attention where queries, keys, and values come from the same sequence.' },
    { term: 'Multi-head attention', definition: 'Several attention heads in parallel subspaces, concatenated and projected.' },
    { term: 'Positional encoding', definition: 'Order information added to embeddings so the model is not permutation-invariant.' },
  ],
  recap:
    'Attention replaces recurrence, self-attention builds context, multiple heads add expressiveness, and positional encodings restore order.',
  variants: {
    concise:
      'Transformers replace recurrence with attention. Self-attention lets every token gather context from the whole sequence in parallel; multiple heads capture different relationships; positional encodings restore order. Encoders stack these blocks, and decoders add masking plus cross-attention. [00:00] [10:40] [24:30]',
    balanced:
      'The Transformer is built around scaled dot-product attention. Each position forms a query, and every position contributes a key and a value; the softmax of scaled query–key scores decides how much of each value to gather. Applied within a single sequence this is self-attention, producing contextual embeddings. Several heads run in parallel so the model can track different relationship types at once. Because attention is permutation-invariant, sinusoidal positional encodings are added to the inputs. Encoder blocks stack attention with feed-forward layers, residuals, and layer normalisation; decoder blocks add masked self-attention and cross-attention over the encoder output. [00:00] [04:25] [10:40] [17:15] [24:30] [31:20]',
    detailed:
      'This lecture builds the Transformer from first principles. It starts with the limitations of recurrent models — sequential processing that blocks parallel training and weakens long-range dependencies [00:00]. Attention is then introduced as a learned lookup: queries, keys, and values, combined as softmax(QK^T / sqrt(d_k))V [04:25]. Restricting attention to a single sequence gives self-attention, which produces contextual representations but is quadratic in sequence length [10:40]. Multi-head attention runs several attentions in parallel subspaces, concatenating and projecting the results so different heads can specialise [17:15]. Because attention ignores order, positional encodings — fixed sinusoids or learned embeddings — are added to the inputs [24:30]. Finally, encoder and decoder blocks are assembled from multi-head attention, feed-forward networks, residual connections, and layer normalisation, with the decoder adding masking and cross-attention [31:20]. The lecture closes with a survey of applications and a recap of the core ideas [38:10].',
  },
}

export const mockSummaries: LectureSummary[] = [demoSummary]

export function findMockSummary(videoId: string): LectureSummary | undefined {
  return mockSummaries.find((summary) => summary.videoId === videoId)
}

/* ------------------------------------------------------------------ *
 * Structured note document (demonstration data)
 * ------------------------------------------------------------------ */

const attentionCode = [
  'import math',
  '',
  'def attention(q, k, v):',
  '    """Scaled dot-product attention for a single head."""',
  '    d_k = q.shape[-1]',
  '    scores = q @ k.transpose(-2, -1) / math.sqrt(d_k)',
  '    weights = scores.softmax(dim=-1)',
  '    return weights @ v',
].join('\n')

const maskCode = [
  'def causal_mask(seq_len, device="cpu"):',
  '    # Additive mask: 0 where a position may attend, -inf where it may not.',
  '    future = torch.triu(torch.ones(seq_len, seq_len, device=device), diagonal=1).bool()',
  '    return torch.zeros(seq_len, seq_len, device=device).masked_fill(future, float("-inf"))',
].join('\n')

const mermaidSource = [
  'flowchart LR',
  '  A[Token embeddings] --> B[Multi-head attention]',
  '  B --> C[Add & norm]',
  '  C --> D[Feed-forward]',
  '  D --> E[Add & norm]',
].join('\n')

/**
 * Artifacts the visual pass placed at an explicit position. `blockId` points at
 * the inline block that renders the artifact, so the gallery and the document
 * always show the same data. `sequence` records the order the pass assigned it.
 */
const placedVisualArtifacts: VisualArtifact[] = [
  {
    id: 'vis-equation',
    kind: 'formula',
    title: 'Scaled dot-product attention',
    description: 'The core attention equation, including the 1/√dₖ scaling factor.',
    timestamp: 270,
    status: 'preview',
    blockId: 'blk-att-eq',
    sectionId: 'sec-attention',
    sequence: 2,
  },
  {
    id: 'vis-tensor-shapes',
    kind: 'table',
    title: 'Attention tensor shapes',
    description: 'Shapes of the query, key, and value matrices for a single head.',
    timestamp: 330,
    status: 'preview',
    blockId: 'blk-att-table',
    sectionId: 'sec-attention',
    sequence: 4,
  },
  {
    id: 'vis-variants',
    kind: 'table',
    title: 'Attention variants compared',
    description: 'Where queries, keys, and values come from, and what each variant is used for.',
    timestamp: 660,
    status: 'preview',
    blockId: 'blk-variants-table',
    sectionId: 'sec-variants',
    sequence: 3,
  },
  {
    id: 'vis-heads',
    kind: 'flowchart',
    title: 'Multi-head attention pipeline',
    description: 'Project, attend in parallel subspaces, concatenate, and project again.',
    timestamp: 1120,
    status: 'preview',
    blockId: 'blk-mha-flow',
    sectionId: 'sec-multihead',
    sequence: 3,
  },
  {
    id: 'vis-encoder-block',
    kind: 'flowchart',
    title: 'Encoder block flow',
    description: 'Input → multi-head attention → add & norm → feed-forward → add & norm.',
    timestamp: 1560,
    status: 'preview',
    blockId: 'blk-encoder-flow',
    sectionId: 'sec-encoder',
    sequence: 2,
  },
]

/**
 * Artifacts the visual pass returned without a usable placement target. They are
 * surfaced in a clearly labelled area rather than inserted at a guessed
 * position.
 */
const unplacedVisualArtifacts: VisualArtifact[] = [
  {
    id: 'vis-unplaced-heatmap',
    kind: 'diagram',
    title: 'Positional-encoding heat map',
    description:
      'Returned by the visual pass with a section but no explicit block or sequence position, so it cannot be placed inline without guessing.',
    timestamp: 1470,
    status: 'reserved',
    sectionId: 'sec-multihead',
    meta: { reason: 'no-placement-metadata', confidence: 0.61 },
  },
]

const demoNoteSections: NoteSection[] = [
  {
    id: 'sec-overview',
    title: '1. Why attention?',
    level: 1,
    startSeconds: 0,
    endSeconds: 265,
    blocks: [
      {
        id: 'blk-overview-notice',
        type: 'callout',
        order: 1,
        startSeconds: 0,
        tone: 'important',
        title: 'Demonstration notes — not extracted from the sample clip',
        content:
          'These notes describe transformer architectures. The bundled sample video is a short Sintel trailer that is unrelated to this topic, so the chapter markers and timestamps below refer to the lecture being described rather than to the playable clip. Every line here is hand-written demonstration data: no AI generation pipeline produced it.',
      },
      {
        id: 'blk-overview-p1',
        type: 'paragraph',
        order: 2,
        startSeconds: 0,
        content:
          'Recurrent networks read a sequence one token at a time, carrying a hidden state forward. That design has two practical costs: training cannot be parallelised across the sequence, and information from early positions fades as it is passed through many steps.',
      },
      {
        id: 'blk-overview-list',
        type: 'list',
        order: 3,
        startSeconds: 45,
        ordered: false,
        items: [
          {
            id: 'li-overview-1',
            content: 'Sequential processing blocks parallel training on long sequences.',
          },
          {
            id: 'li-overview-2',
            content: 'Long-range dependencies degrade as the hidden state is repeatedly rewritten.',
          },
          {
            id: 'li-overview-3',
            content:
              'Attention lets every position look at every other position **directly**, in one step.',
          },
        ],
      },
      {
        id: 'blk-overview-md',
        type: 'markdown',
        order: 4,
        startSeconds: 120,
        content: [
          'Each heading below carries the `[mm:ss]` marker it was derived from, and every visual artifact is rendered **inline** where the speaker introduced it — not collected into a separate gallery after the fact.',
          '',
          '- [x] Positions in the sequence are processed in parallel',
          '- [x] Every position can attend to every other position',
          '- [ ] Attention alone preserves order',
        ].join('\n'),
      },
      {
        id: 'blk-overview-tip',
        type: 'callout',
        order: 5,
        startSeconds: 210,
        tone: 'tip',
        title: 'Reading tip',
        content:
          'Read section 2 before section 3. The encoder block is only a composition of the pieces introduced earlier.',
      },
    ],
  },
  {
    id: 'sec-attention',
    title: '2. Scaled dot-product attention',
    level: 1,
    startSeconds: 265,
    endSeconds: 640,
    blocks: [
      {
        id: 'blk-att-p1',
        type: 'paragraph',
        order: 1,
        startSeconds: 265,
        content:
          'Attention is a learned, differentiable lookup. Every position forms a query, every position offers a key and a value, and the softmax of the scaled query–key scores decides how much of each value to gather. [04:25]',
      },
      {
        id: 'blk-att-eq',
        type: 'math',
        order: 2,
        startSeconds: 270,
        displayMode: 'block',
        latex: '\\mathrm{Attention}(Q, K, V) = \\mathrm{softmax}\\!\\left(\\frac{QK^{\\top}}{\\sqrt{d_k}}\\right) V',
        description: 'Softmax over scaled query–key scores, applied to the values.',
        meta: { notation: 'Batched over heads and positions.' },
      },
      {
        id: 'blk-att-md',
        type: 'markdown',
        order: 3,
        startSeconds: 300,
        content:
          'The scaling factor $1/\\sqrt{d_k}$ keeps dot products from growing with the head dimension. Without it, large logits push the softmax into a saturated region where gradients nearly vanish.',
      },
      {
        id: 'blk-att-inline',
        type: 'math',
        order: 4,
        startSeconds: 320,
        displayMode: 'inline',
        latex: '\\sqrt{d_k}',
        description: 'Scaling denominator.',
      },
      {
        id: 'blk-att-table',
        type: 'table',
        order: 5,
        startSeconds: 330,
        format: 'structured',
        caption: 'Tensor shapes for a single attention head, with sequence length n, memory length m, and head dimension d.',
        columns: [
          { id: 'col-symbol', header: 'Symbol', align: 'left' },
          { id: 'col-shape', header: 'Shape', align: 'center' },
          { id: 'col-role', header: 'Role', align: 'left' },
        ],
        rows: [
          { id: 'row-q', cells: ['Q', 'n × d_k', 'Queries — what each position is looking for'] },
          { id: 'row-k', cells: ['K', 'm × d_k', 'Keys — what each position offers'] },
          { id: 'row-v', cells: ['V', 'm × d_v', 'Values — the information that is aggregated'] },
          { id: 'row-dk', cells: ['d_k', 'scalar', 'Head dimension; the softmax scaling denominator'] },
        ],
      },
      {
        id: 'blk-att-code',
        type: 'code',
        order: 6,
        startSeconds: 400,
        language: 'python',
        title: 'Scaled dot-product attention',
        content: attentionCode,
      },
      {
        id: 'blk-att-quote',
        type: 'quote',
        order: 7,
        startSeconds: 430,
        content:
          'Attention is best understood as a soft, differentiable dictionary lookup — the query asks, the keys answer, and the values are what you get back.',
        attribution: 'Lecture narration, 04:25',
      },
    ],
  },
  {
    id: 'sec-variants',
    title: '2.1 Self-attention vs cross-attention',
    level: 2,
    startSeconds: 640,
    endSeconds: 1035,
    blocks: [
      {
        id: 'blk-variants-p1',
        type: 'paragraph',
        order: 1,
        startSeconds: 640,
        content:
          'The mechanism is unchanged; only the source of the three matrices moves. That single distinction explains almost every architectural variation in the paper. [10:40]',
      },
      {
        id: 'blk-variants-list',
        type: 'list',
        order: 2,
        startSeconds: 700,
        ordered: false,
        items: [
          {
            id: 'li-variants-self',
            content: '**Self-attention** — queries, keys, and values all come from the same sequence.',
            items: [
              { id: 'li-variants-self-a', content: 'Produces contextual representations.' },
              { id: 'li-variants-self-b', content: 'Cost grows quadratically with sequence length.' },
            ],
          },
          {
            id: 'li-variants-cross',
            content:
              '**Cross-attention** — queries come from one sequence, keys and values from another.',
            items: [
              { id: 'li-variants-cross-a', content: 'Used in decoders over encoder output.' },
              { id: 'li-variants-cross-b', content: 'Used in multimodal and retrieval models.' },
            ],
          },
        ],
      },
      {
        id: 'blk-variants-table',
        type: 'table',
        order: 3,
        startSeconds: 780,
        format: 'markdown',
        caption: 'Comparison of the attention variants introduced in the lecture.',
        markdown: [
          '| Variant | Q from | K, V from | Typical use |',
          '| --- | --- | --- | --- |',
          '| Self-attention | same sequence | same sequence | building contextual embeddings |',
          '| Masked self-attention | same sequence | same sequence (causally masked) | autoregressive decoding |',
          '| Cross-attention | decoder | encoder output | translation, speech, multimodal fusion |',
        ].join('\n'),
      },
      {
        id: 'blk-variants-callout',
        type: 'callout',
        order: 4,
        startSeconds: 960,
        tone: 'info',
        title: 'Why the distinction matters',
        content:
          'A decoder block contains both: masked self-attention so it cannot see the future, and cross-attention so it can read the encoder. Swapping which matrices come from where is the entire difference.',
      },
    ],
  },
  {
    id: 'sec-multihead',
    title: '2.2 Multi-head attention',
    level: 2,
    startSeconds: 1035,
    endSeconds: 1470,
    blocks: [
      {
        id: 'blk-mha-p1',
        type: 'paragraph',
        order: 1,
        startSeconds: 1035,
        content:
          'One attention operation yields one weighted average, which averages away distinct relationships. Multi-head attention instead runs several attentions in parallel subspaces and lets the model keep them separate. [17:15]',
      },
      {
        id: 'blk-mha-list',
        type: 'list',
        order: 2,
        startSeconds: 1080,
        ordered: true,
        items: [
          { id: 'li-mha-1', content: 'Project the input into `h` smaller subspaces.' },
          { id: 'li-mha-2', content: 'Run scaled dot-product attention independently in each subspace.' },
          { id: 'li-mha-3', content: 'Concatenate the head outputs back into one vector.' },
          { id: 'li-mha-4', content: 'Apply a final learned output projection.' },
        ],
      },
      {
        id: 'blk-mha-flow',
        type: 'flowchart',
        order: 3,
        startSeconds: 1120,
        direction: 'LR',
        caption: 'The multi-head pipeline: project, attend in parallel, concatenate, project again.',
        nodes: [
          { id: 'mha-input', label: 'Input', kind: 'start' },
          { id: 'mha-proj', label: 'Linear projections', kind: 'process' },
          { id: 'mha-heads', label: 'h heads in parallel', kind: 'process' },
          { id: 'mha-concat', label: 'Concatenate', kind: 'process' },
          { id: 'mha-out', label: 'Output projection', kind: 'end' },
        ],
        edges: [
          { id: 'mha-e1', source: 'mha-input', target: 'mha-proj' },
          { id: 'mha-e2', source: 'mha-proj', target: 'mha-heads', label: 'split' },
          { id: 'mha-e3', source: 'mha-heads', target: 'mha-concat', label: 'h × d_v' },
          { id: 'mha-e4', source: 'mha-concat', target: 'mha-out' },
        ],
      },
      {
        id: 'blk-mha-p2',
        type: 'paragraph',
        order: 4,
        startSeconds: 1400,
        content:
          'Because each head only sees a slice of the representation, the total cost stays comparable to a single full-width attention, while different heads can specialise. [24:30]',
      },
    ],
  },
  {
    id: 'sec-encoder',
    title: '3. The encoder block',
    level: 1,
    startSeconds: 1470,
    endSeconds: 1880,
    blocks: [
      {
        id: 'blk-encoder-p1',
        type: 'paragraph',
        order: 1,
        startSeconds: 1470,
        content:
          'An encoder layer is a small composition, not a new mechanism: multi-head attention, a feed-forward network, residual connections, and layer normalisation. Stacks of these layers are what produced the paper’s headline results. [31:20]',
      },
      {
        id: 'blk-encoder-flow',
        type: 'flowchart',
        order: 2,
        startSeconds: 1560,
        direction: 'TB',
        caption: 'Encoder block flow, with the residual path around each sub-layer.',
        nodes: [
          { id: 'enc-input', label: 'Input embeddings', kind: 'start' },
          { id: 'enc-attn', label: 'Multi-head attention', kind: 'process' },
          { id: 'enc-addnorm1', label: 'Add & norm', kind: 'process' },
          { id: 'enc-ffn', label: 'Feed-forward', kind: 'process' },
          { id: 'enc-addnorm2', label: 'Add & norm', kind: 'process' },
          { id: 'enc-out', label: 'To next layer', kind: 'end' },
        ],
        edges: [
          { id: 'enc-e1', source: 'enc-input', target: 'enc-attn' },
          { id: 'enc-e2', source: 'enc-attn', target: 'enc-addnorm1' },
          { id: 'enc-e3', source: 'enc-addnorm1', target: 'enc-ffn' },
          { id: 'enc-e4', source: 'enc-ffn', target: 'enc-addnorm2' },
          { id: 'enc-e5', source: 'enc-addnorm2', target: 'enc-out' },
          { id: 'enc-e6', source: 'enc-input', target: 'enc-addnorm1', label: 'residual' },
        ],
      },
      {
        id: 'blk-encoder-mermaid',
        type: 'diagram',
        order: 3,
        startSeconds: 1700,
        format: 'mermaid',
        caption: 'Equivalent sketch expressed as Mermaid source.',
        source: mermaidSource,
      },
      {
        id: 'blk-encoder-callout',
        type: 'callout',
        order: 4,
        startSeconds: 1800,
        tone: 'warning',
        title: 'Pre-norm vs post-norm',
        content:
          'The original paper normalises after the residual addition. Most modern stacks normalise before each sub-layer instead, which trains more stably without a learning-rate warm-up.',
      },
    ],
  },
  {
    id: 'sec-decoder',
    title: '4. Masking and the decoder',
    level: 1,
    startSeconds: 1880,
    endSeconds: 2290,
    blocks: [
      {
        id: 'blk-decoder-p1',
        type: 'paragraph',
        order: 1,
        startSeconds: 1880,
        content:
          'A decoder must predict the next token without seeing it. Causality is enforced by adding a mask to the attention scores before the softmax, so future positions receive no probability mass.',
      },
      {
        id: 'blk-decoder-code',
        type: 'code',
        order: 2,
        startSeconds: 1920,
        language: 'python',
        title: 'Causal mask',
        content: maskCode,
      },
      {
        id: 'blk-decoder-callout',
        type: 'callout',
        order: 3,
        startSeconds: 2050,
        tone: 'warning',
        title: 'Masking is additive, not multiplicative',
        content:
          'The mask is added to the scores before the softmax. Masking after the softmax would leave the remaining weights un-normalised.',
      },
      {
        id: 'blk-decoder-quote',
        type: 'quote',
        order: 4,
        startSeconds: 2150,
        content:
          'Training can score every position at once precisely because the mask makes the future invisible to each one.',
        attribution: 'Lecture narration, 38:10',
      },
      {
        id: 'blk-decoder-unknown',
        type: 'unknown',
        order: 5,
        startSeconds: 2210,
        originalType: 'attention-visualiser',
        meta: {
          note: 'An interactive attention-weight explorer attached to this timestamp.',
          embedUrl: 'https://example.invalid/attention-visualiser',
          addedBy: 'visual-pass',
        },
      },
    ],
  },
  {
    id: 'sec-training',
    title: '5. Training and inference',
    level: 1,
    startSeconds: 2290,
    endSeconds: 2650,
    blocks: [
      {
        id: 'blk-training-list',
        type: 'list',
        order: 1,
        startSeconds: 2290,
        ordered: true,
        items: [
          { id: 'li-training-1', content: 'Tokenise the corpus and build the vocabulary.' },
          { id: 'li-training-2', content: 'Add positional encodings to the embeddings.' },
          { id: 'li-training-3', content: 'Stack the encoder and decoder blocks.' },
          { id: 'li-training-4', content: 'Optimise with Adam and a warm-up schedule.' },
        ],
      },
      {
        id: 'blk-training-table',
        type: 'table',
        order: 2,
        startSeconds: 2400,
        format: 'markdown',
        caption: 'What changes between the two modes of use.',
        markdown: [
          '| Aspect | Training | Inference |',
          '| --- | --- | --- |',
          '| Targets | All positions at once | One token at a time |',
          '| Attention mask | Causal mask applied | Causal mask plus KV cache |',
          '| Parallelism | Across positions | Across requests |',
        ].join('\n'),
      },
      {
        id: 'blk-training-p1',
        type: 'paragraph',
        order: 3,
        startSeconds: 2550,
        content:
          'Inference is the harder engineering problem: the causal mask stays, and a key–value cache removes the need to recompute earlier positions on every step. [38:10]',
      },
    ],
  },
  {
    id: 'sec-recap',
    title: '6. Key takeaways',
    level: 1,
    startSeconds: 2650,
    blocks: [
      {
        id: 'blk-recap-list',
        type: 'list',
        order: 1,
        startSeconds: 2650,
        ordered: false,
        items: [
          { id: 'li-recap-1', content: 'Attention replaces recurrence with direct, parallelisable interactions.' },
          { id: 'li-recap-2', content: 'Self-attention produces contextual representations.' },
          { id: 'li-recap-3', content: 'Multiple heads let the model attend to different relationship types.' },
          { id: 'li-recap-4', content: 'Positional encodings restore the notion of order.' },
        ],
      },
      {
        id: 'blk-recap-md',
        type: 'markdown',
        order: 2,
        startSeconds: 2650,
        content:
          'Continue with the [original paper](https://arxiv.org/abs/1706.03762) for the full derivation, and with an implementation walk-through such as `Attention Is All You Need` revisited for the modern variants.',
      },
    ],
  },
]

export const demoNoteDocument: NoteDocument = {
  id: 'notes-demo-transformers',
  videoId: 'demo-transformers',
  title: 'Transformer Architectures',
  subtitle: 'Attention, multi-head parallelism, and encoder–decoder stacks',
  version: 1,
  status: 'demo',
  updatedAt: '2026-02-18T09:32:00.000Z',
  isDemonstration: true,
  sections: demoNoteSections,
  visualArtifacts: placedVisualArtifacts,
  unplacedArtifacts: unplacedVisualArtifacts,
  meta: {
    pipelineVersion: 'demo-1',
    template: 'lecture-structured',
    note: 'Hand-written demonstration document. Not produced by an AI pipeline and not derived from the bundled Sintel sample clip.',
  },
}

export function findMockNoteDocument(videoId: string): NoteDocument | undefined {
  return demoNoteDocument.videoId === videoId ? demoNoteDocument : undefined
}

export function findMockNoteVersions(videoId: string): NoteDocumentVersion[] {
  if (videoId !== demoNoteDocument.videoId) return []
  return [
    {
      version: demoNoteDocument.version,
      createdAt: demoNoteDocument.updatedAt,
      label: 'Demonstration document',
      isCurrent: true,
    },
  ]
}

export const mockVisualArtifacts: VisualArtifact[] = [
  ...placedVisualArtifacts,
  ...unplacedVisualArtifacts,
]

export function findMockVisuals(videoId: string): VisualArtifact[] {
  return videoId === demoNoteDocument.videoId ? mockVisualArtifacts : []
}

/**
 * Mock processing status.
 *
 * Mock mode does not run a generation pipeline, so it reports the first stage
 * and says so. No progress fraction is supplied, because the client must never
 * invent one — and no mock run ever reports `completed`.
 */
export function mockQueuedStatus(
  videoId: string,
  kind: 'notes' | 'visuals',
): NotesProcessingStatus {
  return {
    videoId,
    stage: 'queued',
    message:
      kind === 'notes'
        ? 'Demonstration only — mock mode does not start a backend job. Real stages appear here once the generation API is connected.'
        : 'Demonstration only — mock mode does not run the visual-enhancement pipeline.',
    updatedAt: '2026-02-18T09:32:00.000Z',
  }
}

/** Honest export matrix: client-side formats work, server-rendered ones do not. */
export function mockExportCapabilities(): NotesExportCapability[] {
  return [
    { format: 'markdown', label: 'Markdown (.md)', available: true },
    { format: 'html', label: 'Sanitised HTML (.html)', available: true },
    {
      format: 'pdf',
      label: 'PDF',
      available: false,
      reason: 'Server-side rendering is not connected in this build.',
    },
    {
      format: 'docx',
      label: 'Word (.docx)',
      available: false,
      reason: 'Server-side rendering is not connected in this build.',
    },
  ]
}
