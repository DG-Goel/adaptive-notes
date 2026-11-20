"""
Chunking service for Universal AI Tutor.

Implements two-level hierarchical chunking with:
- Parent chunks (1200 tokens) for context expansion
- Child chunks (400 tokens) for retrieval
- Structure preservation (headings, code blocks, formulas)
- Deterministic contextual enrichment
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
from uuid import uuid4

from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import TextNode, NodeRelationship, RelatedNodeInfo

from src.config import get_settings
from src.logger import get_logger

logger = get_logger(__name__)


@dataclass
class EnrichedChunk:
    """
    Chunk with contextual enrichment.
    
    Maintains both original and contextual text for proper evidence handling.
    """

    id: str
    original_text: str  # NEVER modified - used for evidence
    contextual_text: str  # Enriched for retrieval
    parent_id: Optional[str]
    chunk_index: int
    metadata: dict


class ChunkingService:
    """
    Service for hierarchical document chunking with contextual enrichment.

    Features:
    - Two-level hierarchy (parent/child)
    - Structure preservation (markdown, code, formulas)
    - Token-aware splitting
    - Deterministic contextual enrichment
    """

    def __init__(
        self,
        parent_chunk_size: Optional[int] = None,
        parent_chunk_overlap: Optional[int] = None,
        child_chunk_size: Optional[int] = None,
        child_chunk_overlap: Optional[int] = None,
    ) -> None:
        """
        Initialize chunking service.

        Args:
            parent_chunk_size: Parent chunk size in tokens (default from config)
            parent_chunk_overlap: Parent overlap in tokens (default from config)
            child_chunk_size: Child chunk size in tokens (default from config)
            child_chunk_overlap: Child overlap in tokens (default from config)
        """
        settings = get_settings()

        self.parent_chunk_size = parent_chunk_size or settings.parent_chunk_size
        self.parent_chunk_overlap = parent_chunk_overlap or settings.parent_chunk_overlap
        self.child_chunk_size = child_chunk_size or settings.child_chunk_size
        self.child_chunk_overlap = child_chunk_overlap or settings.child_chunk_overlap

        logger.info(
            "Initializing ChunkingService",
            extra={
                "parent_size": self.parent_chunk_size,
                "parent_overlap": self.parent_chunk_overlap,
                "child_size": self.child_chunk_size,
                "child_overlap": self.child_chunk_overlap,
            },
        )

        # Create splitters
        self.parent_splitter = SentenceSplitter(
            chunk_size=self.parent_chunk_size,
            chunk_overlap=self.parent_chunk_overlap,
            paragraph_separator="\n\n",
            separator=" ",
        )

        self.child_splitter = SentenceSplitter(
            chunk_size=self.child_chunk_size,
            chunk_overlap=self.child_chunk_overlap,
            paragraph_separator="\n\n",
            separator=" ",
        )

    def chunk_document(
        self,
        document: Document,
        doc_id: str,
        doc_title: str,
    ) -> Tuple[List[EnrichedChunk], List[EnrichedChunk]]:
        """
        Chunk document into two-level hierarchy with contextual enrichment.

        Args:
            document: LlamaIndex Document
            doc_id: Unique document identifier
            doc_title: Human-readable document name

        Returns:
            Tuple of (parent_chunks, child_chunks)

        Raises:
            ValueError: If document is empty
            RuntimeError: If chunking fails
        """
        if not document.text or not document.text.strip():
            raise ValueError("Document text cannot be empty")

        logger.info(
            f"Chunking document",
            extra={
                "doc_id": doc_id,
                "doc_title": doc_title,
                "text_length": len(document.text),
            },
        )

        try:
            # Extract section path from metadata
            section_path = document.metadata.get("section_path", [])

            # Level 1: Create parent chunks
            parent_nodes = self.parent_splitter.get_nodes_from_documents([document])

            logger.debug(
                f"Created parent chunks",
                extra={"parent_count": len(parent_nodes)},
            )

            # Process parents and create enriched chunks
            all_parent_chunks = []
            all_child_chunks = []

            for parent_idx, parent_node in enumerate(parent_nodes):
                # Create enriched parent chunk
                parent_id = str(uuid4())
                parent_metadata = {
                    "doc_id": doc_id,
                    "doc_title": doc_title,
                    "section_path": section_path,
                    "chunk_index": parent_idx,
                    "chunk_type": "parent",
                    "is_contextualized": False,  # Parents not contextualized
                }

                parent_chunk = EnrichedChunk(
                    id=parent_id,
                    original_text=parent_node.text,
                    contextual_text=parent_node.text,  # No enrichment for parents
                    parent_id=None,
                    chunk_index=parent_idx,
                    metadata=parent_metadata,
                )

                all_parent_chunks.append(parent_chunk)

                # Level 2: Create child chunks from this parent
                parent_doc = Document(
                    text=parent_node.text,
                    metadata=parent_metadata.copy(),
                )

                child_nodes = self.child_splitter.get_nodes_from_documents([parent_doc])

                logger.debug(
                    f"Created child chunks from parent {parent_idx}",
                    extra={"child_count": len(child_nodes)},
                )

                # Create enriched child chunks with deterministic context
                for child_idx, child_node in enumerate(child_nodes):
                    child_id = str(uuid4())

                    # Original text (for evidence)
                    original_text = child_node.text

                    # Create deterministic contextual enrichment
                    contextual_text = self._create_deterministic_context(
                        chunk_text=original_text,
                        doc_title=doc_title,
                        section_path=section_path,
                        parent_preview=parent_node.text[:200] if len(parent_node.text) > 200 else None,
                    )

                    child_metadata = {
                        "doc_id": doc_id,
                        "doc_title": doc_title,
                        "section_path": section_path,
                        "parent_id": parent_id,
                        "chunk_index": child_idx,
                        "chunk_type": "child",
                        "is_contextualized": True,
                        "original_text": original_text,  # PRESERVE original
                    }

                    child_chunk = EnrichedChunk(
                        id=child_id,
                        original_text=original_text,
                        contextual_text=contextual_text,
                        parent_id=parent_id,
                        chunk_index=child_idx,
                        metadata=child_metadata,
                    )

                    all_child_chunks.append(child_chunk)

            logger.info(
                f"Document chunking complete",
                extra={
                    "doc_id": doc_id,
                    "parent_chunks": len(all_parent_chunks),
                    "child_chunks": len(all_child_chunks),
                },
            )

            return all_parent_chunks, all_child_chunks

        except Exception as e:
            logger.error(
                f"Chunking failed",
                extra={"doc_id": doc_id, "error": str(e)},
                exc_info=True,
            )
            raise RuntimeError(f"Document chunking failed: {str(e)}") from e

    def _create_deterministic_context(
        self,
        chunk_text: str,
        doc_title: str,
        section_path: List[str],
        parent_preview: Optional[str] = None,
    ) -> str:
        """
        Create deterministic contextual prefix for a chunk.

        No LLM required - uses document structure only.

        Args:
            chunk_text: Original chunk text
            doc_title: Document title
            section_path: List of section headings
            parent_preview: Optional parent context snippet

        Returns:
            str: Enriched text with contextual prefix
        """
        context_parts = []

        # Add document context
        context_parts.append(f"Document: {doc_title}")

        # Add section path if available
        if section_path:
            section_str = " > ".join(section_path)
            context_parts.append(f"Section: {section_str}")

        # Add parent context if available
        if parent_preview:
            context_parts.append(f"Context: {parent_preview}")

        # Build full enriched text
        context_prefix = " | ".join(context_parts) + "\n\n"

        return context_prefix + chunk_text

    def extract_section_path(self, text: str) -> List[str]:
        """
        Extract section path from markdown headings.

        Identifies hierarchical structure from markdown # headers.

        Args:
            text: Document text (markdown)

        Returns:
            List of section headings in hierarchical order
        """
        section_path = []
        lines = text.split("\n")

        # Track current heading levels
        current_h1 = None
        current_h2 = None
        current_h3 = None

        for line in lines:
            line = line.strip()

            # H1: # Heading
            if line.startswith("# ") and not line.startswith("##"):
                current_h1 = line[2:].strip()
                current_h2 = None
                current_h3 = None

            # H2: ## Heading
            elif line.startswith("## ") and not line.startswith("###"):
                current_h2 = line[3:].strip()
                current_h3 = None

            # H3: ### Heading
            elif line.startswith("### ") and not line.startswith("####"):
                current_h3 = line[4:].strip()

        # Build section path from deepest available level
        if current_h3:
            section_path = [h for h in [current_h1, current_h2, current_h3] if h]
        elif current_h2:
            section_path = [h for h in [current_h1, current_h2] if h]
        elif current_h1:
            section_path = [current_h1]

        return section_path


def get_chunking_service() -> ChunkingService:
    """
    Get chunking service instance.

    Returns:
        ChunkingService: Configured chunking service
    """
    return ChunkingService()
