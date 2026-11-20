"""Provider-neutral educational representation and future stage boundaries.

These are contracts only: no indexing, segmentation, routing, compression,
verification, repair, persistence or rendering algorithm runs in Phase 1.
"""
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SourceSnapshot:
    source_id: str
    sha256: str
    content: bytes
    media_type: str


@dataclass(frozen=True)
class Evidence:
    source_id: str
    source_sha256: str
    start: int
    end: int
    quote: str


@dataclass(frozen=True)
class KnowledgeItem:
    id: str
    text: str
    evidence: tuple[Evidence, ...]


@dataclass(frozen=True)
class KnowledgeLink:
    source: str
    target: str
    relation: str
    evidence: tuple[Evidence, ...]


@dataclass(frozen=True)
class EducationalKnowledge:
    items: tuple[KnowledgeItem, ...]
    links: tuple[KnowledgeLink, ...]


@dataclass(frozen=True)
class Segment:
    id: str
    source_ids: tuple[str, ...]
    knowledge: EducationalKnowledge


@dataclass(frozen=True)
class Route:
    segment_id: str
    category_id: str
    subcategory_id: str


@dataclass(frozen=True)
class TemplateSpec:
    id: str
    category_id: str
    renderer_template: str


@dataclass(frozen=True)
class VerificationReport:
    covered_item_ids: tuple[str, ...]
    missing_item_ids: tuple[str, ...]
    unsupported_item_ids: tuple[str, ...]
    issues: tuple[str, ...]


@dataclass(frozen=True)
class RenderRequest:
    knowledge: EducationalKnowledge
    template: TemplateSpec
    renderer_version: str
    seed: int
    width: int
    height: int


@dataclass(frozen=True)
class RenderedArtifact:
    content: bytes
    media_type: str
    sha256: str


@dataclass(frozen=True)
class Checkpoint:
    schema_version: int
    run_id: str
    stage: str
    source_hashes: tuple[tuple[str, str], ...]
    config_sha256: str  # Public settings only, never credentials.
    artifact_ids: tuple[str, ...]


class SourceReader(Protocol):
    """Read-only source port, deliberately without a write method."""
    def snapshot(self, source_id: str) -> SourceSnapshot: ...


class SourceIndexer(Protocol):
    def index(self, sources: tuple[SourceSnapshot, ...]) -> tuple[KnowledgeItem, ...]: ...


class ContextManager(Protocol):
    def select(self, segment: Segment, budget_tokens: int) -> tuple[KnowledgeItem, ...]: ...


class Segmenter(Protocol):
    def segment(self, sources: tuple[SourceSnapshot, ...]) -> tuple[Segment, ...]: ...


class HierarchicalRouter(Protocol):
    def route(self, segments: tuple[Segment, ...]) -> tuple[Route, ...]: ...


class Consolidator(Protocol):
    def consolidate(self, segments: tuple[Segment, ...]) -> tuple[Segment, ...]: ...


class TemplateSelector(Protocol):
    def select(self, segment: Segment, route: Route,
               templates: tuple[TemplateSpec, ...]) -> TemplateSpec: ...


class Compressor(Protocol):
    def compress(self, knowledge: EducationalKnowledge, budget_tokens: int) -> EducationalKnowledge: ...


class StructuredGenerator(Protocol):
    def generate(self, knowledge: EducationalKnowledge, template: TemplateSpec) -> EducationalKnowledge: ...


class Verifier(Protocol):
    def verify(self, original: EducationalKnowledge,
               candidate: EducationalKnowledge) -> VerificationReport: ...


class Repairer(Protocol):
    def repair(self, original: EducationalKnowledge, candidate: EducationalKnowledge,
               report: VerificationReport) -> EducationalKnowledge: ...


class Renderer(Protocol):
    """The implementation owns AntV syntax and pinned deterministic assets."""
    def render(self, request: RenderRequest) -> RenderedArtifact: ...


class ArtifactStore(Protocol):
    """Future adapter must be namespace-confined and create-only (no overwrites)."""
    def create(self, run_id: str, artifact: RenderedArtifact) -> str: ...
    def read(self, artifact_id: str) -> RenderedArtifact: ...


class CheckpointStore(Protocol):
    """Future immutable checkpoint revisions, separate from lecture jobs."""
    def append(self, checkpoint: Checkpoint) -> str: ...
    def latest(self, run_id: str) -> Checkpoint | None: ...


@dataclass(frozen=True)
class ModelInfo:
    name: str
    input_tokens: int
    output_tokens: int
    methods: tuple[str, ...]


@dataclass(frozen=True)
class Completion:
    text: str
    input_tokens: int | None
    output_tokens: int | None


class LLMTransport(Protocol):
    def model_info(self, model: str) -> ModelInfo: ...
    def complete(self, model: str, content: str, max_output_tokens: int) -> Completion: ...
    def close(self) -> None: ...
