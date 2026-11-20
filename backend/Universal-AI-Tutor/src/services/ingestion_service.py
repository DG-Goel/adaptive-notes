"""
Document ingestion service for Universal AI Tutor.

Handles the complete pipeline: loading → validation → chunking → embedding → indexing.
"""

import hashlib
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid5, NAMESPACE_DNS
from dataclasses import dataclass
from datetime import datetime, timezone

from llama_index.core import Document
from qdrant_client import models

from ..core.embedding_service import get_embedding_service
from ..core.vector_store import VectorStore
from ..services.chunking import get_chunking_service

logger = logging.getLogger(__name__)

# Namespace UUID for deterministic UUIDv5 generation
# Using NAMESPACE_DNS with our project domain
TUTOR_NAMESPACE = uuid5(NAMESPACE_DNS, "universal-ai-tutor.local")


@dataclass
class IngestionResult:
    """Result of document ingestion operation."""
    
    success: bool
    doc_id: str
    doc_path: str
    chunks_created: int
    chunks_indexed: int
    was_update: bool
    error: Optional[str] = None
    processing_time_seconds: float = 0.0


@dataclass
class BatchIngestionResult:
    """Result of batch ingestion operation."""
    
    total_files: int
    successful: int
    failed: int
    total_chunks_indexed: int
    results: List[IngestionResult]
    processing_time_seconds: float = 0.0


def generate_doc_id(file_path: str) -> str:
    """
    Generate deterministic document ID using UUIDv5.
    
    Uses the file path as the name component to ensure:
    - Same file always gets same ID
    - Different files get different IDs
    - IDs are valid UUIDs for Qdrant
    
    Args:
        file_path: Absolute or relative path to the document
        
    Returns:
        String representation of UUID
    """
    # Normalize path for consistency across platforms
    normalized_path = str(Path(file_path).as_posix())
    doc_uuid = uuid5(TUTOR_NAMESPACE, normalized_path)
    return str(doc_uuid)


def generate_chunk_id(doc_id: str, chunk_index: int) -> str:
    """
    Generate deterministic chunk ID using UUIDv5.
    
    Args:
        doc_id: Document UUID
        chunk_index: Position of chunk in document (0-indexed)
        
    Returns:
        String representation of UUID
    """
    chunk_name = f"{doc_id}:chunk:{chunk_index}"
    chunk_uuid = uuid5(TUTOR_NAMESPACE, chunk_name)
    return str(chunk_uuid)


def compute_content_hash(text: str) -> str:
    """
    Compute SHA-256 hash of document content for version detection.
    
    Args:
        text: Document text content
        
    Returns:
        Hex string of content hash
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class IngestionService:
    """
    Service for ingesting educational documents into the knowledge base.
    
    Handles:
    - Document loading and validation
    - Structure detection and metadata extraction
    - Hierarchical chunking with enrichment
    - Batch embedding generation
    - Qdrant indexing with duplicate/update detection
    - Progress tracking and error handling
    """
    
    def __init__(
        self,
        embedding_batch_size: int = 32,
        collection_name: str = "tutor_knowledge"
    ):
        """
        Initialize ingestion service.
        
        Args:
            embedding_batch_size: Number of chunks to embed in one batch
            collection_name: Qdrant collection name
        """
        self.embedding_service = get_embedding_service()
        self.vector_store = VectorStore(collection_name=collection_name)
        self.chunking_service = get_chunking_service()
        self.embedding_batch_size = embedding_batch_size
        self.collection_name = collection_name
        
        logger.info(
            f"IngestionService initialized with collection '{collection_name}'"
        )
    
    def load_document(self, file_path: str) -> tuple[str, Dict[str, Any]]:
        """
        Load document from file with encoding detection.
        
        Args:
            file_path: Path to document file
            
        Returns:
            Tuple of (text content, basic metadata)
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file type is not supported
            UnicodeDecodeError: If encoding detection fails
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        # Check file extension
        suffix = path.suffix.lower()
        if suffix not in [".txt", ".md", ".markdown"]:
            raise ValueError(
                f"Unsupported file type: {suffix}. "
                "Supported types: .txt, .md, .markdown"
            )
        
        # Try UTF-8 first, then fallback to latin-1
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            logger.warning(f"UTF-8 decode failed for {file_path}, trying latin-1")
            text = path.read_text(encoding="latin-1")
        
        # Basic validation
        if not text.strip():
            raise ValueError(f"Document is empty: {file_path}")
        
        # Extract basic metadata
        metadata = {
            "file_path": str(path.absolute()),
            "file_name": path.name,
            "file_size_bytes": path.stat().st_size,
            "file_extension": suffix,
            "loaded_at": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(
            f"Loaded document: {path.name} ({len(text)} chars, {len(text.split())} words)"
        )
        
        return text, metadata
    
    def detect_structure(
        self, 
        text: str, 
        file_name: str
    ) -> Dict[str, Any]:
        """
        Detect document structure and extract metadata.
        
        Args:
            text: Document text content
            file_name: Name of the file
            
        Returns:
            Dictionary with detected structure metadata
        """
        metadata = {}
        
        # Extract title (first non-empty line or H1 heading)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        
        if lines:
            first_line = lines[0]
            # Check for markdown H1
            if first_line.startswith("# "):
                metadata["title"] = first_line[2:].strip()
            else:
                # Use first line as title, or fallback to filename
                metadata["title"] = first_line[:100] if len(first_line) <= 100 else file_name
        else:
            metadata["title"] = file_name
        
        # Detect content type hints
        has_code_blocks = "```" in text
        has_math = any(marker in text for marker in ["$$", "\\[", "\\("])
        has_headings = any(line.startswith("#") for line in text.split("\n"))
        has_lists = any(
            line.strip().startswith(("-", "*", "+")) or 
            (len(line.strip()) > 0 and line.strip()[0].isdigit() and ". " in line)
            for line in text.split("\n")
        )
        
        metadata["content_hints"] = {
            "has_code_blocks": has_code_blocks,
            "has_math": has_math,
            "has_headings": has_headings,
            "has_lists": has_lists
        }
        
        logger.debug(f"Detected structure: {metadata}")
        
        return metadata
    
    def check_existing_document(self, doc_id: str) -> Optional[str]:
        """
        Check if document already exists and get its content hash.
        
        Args:
            doc_id: Document UUID
            
        Returns:
            Content hash if document exists, None otherwise
        """
        try:
            # Use scroll with filter to find any chunk with this doc_id
            filter_condition = models.Filter(
                must=[
                    models.FieldCondition(
                        key="doc_id",
                        match=models.MatchValue(value=doc_id)
                    )
                ]
            )
            
            records = self.vector_store.scroll_points(
                filter_condition=filter_condition,
                limit=1,  # We only need one to get the content hash
                with_payload=True,
                with_vectors=False
            )
            
            if records and len(records) > 0:
                content_hash = records[0].payload.get("content_hash")
                if content_hash:
                    logger.debug(
                        f"Found existing document",
                        extra={"doc_id": doc_id, "content_hash": content_hash}
                    )
                    return content_hash
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not check existing document: {e}")
            return None
    
    def delete_document_chunks(self, doc_id: str) -> int:
        """
        Delete all chunks belonging to a document.
        
        Uses Qdrant's filter-based deletion to remove all points
        with matching doc_id.
        
        Args:
            doc_id: Document UUID
            
        Returns:
            Number of chunks deleted
        """
        try:
            # Create filter for this doc_id
            filter_condition = models.Filter(
                must=[
                    models.FieldCondition(
                        key="doc_id",
                        match=models.MatchValue(value=doc_id)
                    )
                ]
            )
            
            # Delete all matching chunks
            deleted_count = self.vector_store.delete_by_filter(filter_condition)
            
            logger.info(
                f"Deleted old document chunks",
                extra={"doc_id": doc_id, "deleted_count": deleted_count}
            )
            
            return deleted_count
            
        except Exception as e:
            logger.error(
                f"Failed to delete document chunks: {e}",
                exc_info=True
            )
            raise RuntimeError(f"Document cleanup failed: {str(e)}") from e
    
    def ingest_document(
        self,
        file_path: str,
        overwrite: bool = False
    ) -> IngestionResult:
        """
        Ingest a single document into the knowledge base.
        
        Pipeline:
        1. Load and validate document
        2. Detect structure and extract metadata
        3. Generate deterministic document ID
        4. Check for duplicates/updates
        5. Chunk document hierarchically
        6. Enrich chunks with context
        7. Generate embeddings in batches
        8. Index in Qdrant
        9. Verify indexing
        
        Args:
            file_path: Path to document file
            overwrite: If True, reindex even if content unchanged
            
        Returns:
            IngestionResult with operation details
        """
        import time
        start_time = time.time()
        
        try:
            # Step 1: Load document
            text, file_metadata = self.load_document(file_path)
            
            # Step 2: Detect structure
            structure_metadata = self.detect_structure(text, file_metadata["file_name"])
            
            # Step 3: Generate deterministic doc_id
            doc_id = generate_doc_id(file_path)
            content_hash = compute_content_hash(text)
            
            logger.info(f"Processing document {doc_id} from {file_path}")
            
            # Step 4: Check for duplicates/updates
            existing_hash = self.check_existing_document(doc_id)
            was_update = False
            
            if existing_hash == content_hash and not overwrite:
                logger.info(
                    f"Document {doc_id} unchanged (hash match). Skipping ingestion."
                )
                return IngestionResult(
                    success=True,
                    doc_id=doc_id,
                    doc_path=file_path,
                    chunks_created=0,
                    chunks_indexed=0,
                    was_update=False,
                    processing_time_seconds=time.time() - start_time
                )
            
            if existing_hash and existing_hash != content_hash:
                logger.info(
                    f"Document {doc_id} content changed. Reindexing."
                )
                was_update = True
                self.delete_document_chunks(doc_id)
            
            # Step 5: Chunk document
            # Create LlamaIndex Document object
            document = Document(
                text=text,
                metadata={
                    "doc_id": doc_id,
                    "doc_title": structure_metadata["title"],
                    "section_path": [],  # Will be populated if we parse headings
                }
            )
            
            parent_chunks, child_chunks = self.chunking_service.chunk_document(
                document=document,
                doc_id=doc_id,
                doc_title=structure_metadata["title"]
            )
            
            # Override chunk IDs with deterministic UUIDv5
            # This ensures stable IDs for the same document content
            global_chunk_index = 0
            
            # Assign deterministic IDs to parents
            parent_id_mapping = {}  # old_id -> new_id
            for parent in parent_chunks:
                old_id = parent.id
                new_id = generate_chunk_id(doc_id, global_chunk_index)
                parent.id = new_id
                parent_id_mapping[old_id] = new_id
                global_chunk_index += 1
            
            # Assign deterministic IDs to children and update parent references
            for child in child_chunks:
                # Update parent_id reference
                if child.parent_id and child.parent_id in parent_id_mapping:
                    child.parent_id = parent_id_mapping[child.parent_id]
                
                # Assign deterministic child ID
                child.id = generate_chunk_id(doc_id, global_chunk_index)
                global_chunk_index += 1
            
            # Combine all chunks for indexing
            chunks = parent_chunks + child_chunks
            
            logger.info(
                f"Created {len(chunks)} chunks for {doc_id}",
                extra={
                    "parents": len(parent_chunks),
                    "children": len(child_chunks)
                }
            )
            
            # Step 6: Prepare chunk data for indexing
            chunk_ids = []
            chunk_texts = []
            chunk_payloads = []
            
            for idx, chunk in enumerate(chunks):
                # Use chunk.id which is UUID generated by ChunkingService
                chunk_id = chunk.id
                chunk_ids.append(chunk_id)
                
                # Use contextual_text for embedding (enriched for retrieval)
                chunk_texts.append(chunk.contextual_text)
                
                # Build comprehensive metadata
                payload = {
                    # Source identification
                    "doc_id": doc_id,
                    "chunk_id": chunk_id,
                    "doc_path": file_metadata["file_path"],
                    "doc_title": structure_metadata["title"],
                    
                    # Content versioning
                    "content_hash": content_hash,
                    "indexed_at": datetime.now(timezone.utc).isoformat(),
                    
                    # Chunk metadata from ChunkingService
                    "chunk_index": idx,
                    "chunk_type": chunk.metadata.get("chunk_type", "unknown"),
                    "is_parent": chunk.metadata.get("chunk_type") == "parent",
                    "parent_id": chunk.parent_id,
                    
                    # Original authoritative content (separate from enrichment)
                    "text": chunk.original_text,
                    
                    # Enrichment metadata (for transparency)
                    "enriched_text": chunk.contextual_text,
                    "deterministic_context": chunk.contextual_text if chunk.metadata.get("is_contextualized") else None,
                    
                    # Structure metadata
                    "section_path": chunk.metadata.get("section_path", []),
                    
                    # File metadata
                    "file_name": file_metadata["file_name"],
                    "file_extension": file_metadata["file_extension"],
                    
                    # Content hints
                    **structure_metadata["content_hints"]
                }
                
                chunk_payloads.append(payload)
            
            # Step 7: Generate embeddings in batches
            logger.info(f"Generating embeddings for {len(chunk_texts)} chunks")
            
            all_embeddings = []
            for i in range(0, len(chunk_texts), self.embedding_batch_size):
                batch_texts = chunk_texts[i:i + self.embedding_batch_size]
                batch_embeddings = self.embedding_service.embed_batch(batch_texts)
                all_embeddings.extend(batch_embeddings)
                
                logger.debug(
                    f"Embedded batch {i // self.embedding_batch_size + 1}/"
                    f"{(len(chunk_texts) + self.embedding_batch_size - 1) // self.embedding_batch_size}"
                )
            
            # Step 8: Index in Qdrant
            logger.info(f"Indexing {len(chunk_ids)} chunks in Qdrant")
            
            self.vector_store.insert_batch(
                ids=chunk_ids,
                vectors=all_embeddings,
                payloads=chunk_payloads
            )
            
            # Step 9: Verify indexing
            indexed_count = len(chunk_ids)
            
            logger.info(
                f"Successfully ingested {file_path}: "
                f"{indexed_count} chunks indexed"
            )
            
            return IngestionResult(
                success=True,
                doc_id=doc_id,
                doc_path=file_path,
                chunks_created=len(chunks),
                chunks_indexed=indexed_count,
                was_update=was_update,
                processing_time_seconds=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(
                f"Failed to ingest {file_path}: {str(e)}",
                exc_info=True
            )
            
            return IngestionResult(
                success=False,
                doc_id=generate_doc_id(file_path),
                doc_path=file_path,
                chunks_created=0,
                chunks_indexed=0,
                was_update=False,
                error=str(e),
                processing_time_seconds=time.time() - start_time
            )
    
    def ingest_documents(
        self,
        file_paths: List[str],
        overwrite: bool = False
    ) -> BatchIngestionResult:
        """
        Ingest multiple documents.
        
        Args:
            file_paths: List of paths to document files
            overwrite: If True, reindex all documents
            
        Returns:
            BatchIngestionResult with summary
        """
        import time
        start_time = time.time()
        
        logger.info(f"Starting batch ingestion of {len(file_paths)} documents")
        
        results = []
        successful = 0
        failed = 0
        total_chunks = 0
        
        for idx, file_path in enumerate(file_paths, 1):
            logger.info(f"Processing document {idx}/{len(file_paths)}: {file_path}")
            
            result = self.ingest_document(file_path, overwrite=overwrite)
            results.append(result)
            
            if result.success:
                successful += 1
                total_chunks += result.chunks_indexed
            else:
                failed += 1
        
        processing_time = time.time() - start_time
        
        logger.info(
            f"Batch ingestion complete: {successful} successful, {failed} failed, "
            f"{total_chunks} total chunks indexed in {processing_time:.2f}s"
        )
        
        return BatchIngestionResult(
            total_files=len(file_paths),
            successful=successful,
            failed=failed,
            total_chunks_indexed=total_chunks,
            results=results,
            processing_time_seconds=processing_time
        )


def get_ingestion_service(
    embedding_batch_size: int = 32,
    collection_name: Optional[str] = None
) -> IngestionService:
    """
    Get IngestionService instance (factory function).
    
    Args:
        embedding_batch_size: Batch size for embedding generation
        collection_name: Qdrant collection name (defaults to settings.qdrant_collection_name)
        
    Returns:
        IngestionService instance
    """
    if collection_name is None:
        from src.config import get_settings
        settings = get_settings()
        collection_name = settings.qdrant_collection_name
    
    return IngestionService(
        embedding_batch_size=embedding_batch_size,
        collection_name=collection_name
    )
