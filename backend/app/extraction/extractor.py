"""
Main knowledge extraction orchestrator.

Coordinates chunking, LLM calls, parsing, and knowledge document assembly
with token budget management and rate limit handling.
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List

from app.models.source import SourceDocument, SourceUnit
from app.models.knowledge import (
    KnowledgeDocument,
    Concept,
    Definition,
    Explanation,
    Example,
    Fact,
    Formula,
    Procedure,
    Relationship,
    ExtractionChunk
)
from app.extraction.llm_provider import LLMProvider
from app.extraction.chunker import ContentChunker
from app.extraction.chunk_splitter import ChunkSplitter, merge_extracted_items
from app.extraction.prompts import EXTRACTION_SYSTEM_PROMPT, build_extraction_prompt
from app.extraction.quote_repair import QuoteRepair
from app.extraction.token_budget import TokenBudgetManager


class KnowledgeExtractor:
    """
    Extracts structured knowledge from source documents.
    
    Orchestrates the extraction pipeline:
    1. Chunk source units
    2. Extract knowledge from each chunk using LLM
    3. Parse and validate responses
    4. Assemble knowledge document
    """
    
    def __init__(
        self,
        llm_provider: LLMProvider,
        max_tokens_per_chunk: int = 2000,
        verbose: bool = True,
        max_retries: int = 2,
        min_output_tokens: int = 500,
        preferred_output_tokens: int = 4000,
        max_split_depth: int = 2,
        strict_evidence: bool = False
    ):
        """
        Initialize extractor.
        
        Args:
            llm_provider: LLM provider for generation
            max_tokens_per_chunk: Maximum tokens per extraction chunk
            verbose: Print extraction progress
            max_retries: Maximum retry attempts for failed chunks (default: 2)
            min_output_tokens: Minimum acceptable output tokens
            preferred_output_tokens: Preferred output token budget
            max_split_depth: Maximum depth for adaptive chunk splitting (default: 2)
            strict_evidence: Require mechanically valid field-level source evidence (default: False)
        """
        self.strict_evidence = strict_evidence
        self._evidence_sources = {}
        self.llm = llm_provider
        self.chunker = ContentChunker(max_tokens_per_chunk=max_tokens_per_chunk)
        self.splitter = ChunkSplitter(max_split_depth=max_split_depth)
        self.quote_repairer = QuoteRepair(min_similarity=0.85, max_length_diff=20)
        self.verbose = verbose
        self.max_retries = max_retries
        self.min_output_tokens = min_output_tokens
        self.preferred_output_tokens = preferred_output_tokens
        self.knowledge_id_counter = 0
        self.valid_source_ids = set()  # Will be populated during extract()
        self.invalid_refs_count = 0  # Track validation failures
        
        # Initialize token budget manager
        tpm_limit = getattr(llm_provider, 'tokens_per_minute', 8000)
        self.token_budget = TokenBudgetManager(tokens_per_minute=tpm_limit)
        
        # Diagnostic tracking
        self.chunk_attempts = []  # List of dicts with attempt metadata
        self.failed_chunks = []   # List of chunk_ids that failed after retries
        self.split_chunks = []    # List of chunk_ids that were split
        self.repaired_quotes = []  # List of repaired quote metadata
    
    def _validate_source_ids(self, source_unit_ids: List[str], knowledge_id: str) -> List[str]:
        """
        Validate source_unit_ids against the source document.
        
        Args:
            source_unit_ids: List of source unit IDs to validate
            knowledge_id: Knowledge item ID for logging
            
        Returns:
            Filtered list containing only valid IDs
        """
        if not self.valid_source_ids:
            # Validation not initialized (shouldn't happen in normal flow)
            return source_unit_ids
        
        valid_ids = []
        invalid_ids = []
        
        for sid in source_unit_ids:
            if sid in self.valid_source_ids:
                valid_ids.append(sid)
            else:
                invalid_ids.append(sid)
        
        if invalid_ids:
            self.invalid_refs_count += len(invalid_ids)
            if self.verbose:
                print(f"  WARNING: {knowledge_id} references invalid source IDs: {invalid_ids}")
        
        return valid_ids
    
    def extract(self, source_document: SourceDocument) -> KnowledgeDocument:
        """
        Extract knowledge from source document.
        
        Args:
            source_document: Validated source document
            
        Returns:
            KnowledgeDocument with extracted knowledge
        """
        
        if self.verbose:
            print(f"\n{'=' * 80}")
            print(f"KNOWLEDGE EXTRACTION")
            print(f"{'=' * 80}")
            print(f"Document: {source_document.filename}")
            print(f"Source units: {len(source_document.source_units)}")
        
        self.knowledge_id_counter = 0
        self.invalid_refs_count = 0
        self.chunk_attempts = []
        self.failed_chunks = []
        self.split_chunks = []
        self.root_outcomes = {}
        self.child_outcomes = []
        self._split_complete = {}
        # Keep rolling provider rate-limit state; reset only document diagnostics.
        # Evidence-only text index: exclude ambiguous source IDs instead of overwriting them.
        source_groups = {}
        for unit in source_document.source_units:
            source_groups.setdefault(unit.source_id, []).append(unit.text or "")
        self._evidence_sources = {sid: texts[0] for sid, texts in source_groups.items() if len(texts) == 1}
        # Build valid source ID set for validation
        self.valid_source_ids = {unit.source_id for unit in source_document.source_units}
        
        # Initialize knowledge document
        knowledge_doc = KnowledgeDocument(
            document_id=source_document.document_id,
            source_filename=source_document.filename,
            extraction_timestamp=datetime.now().isoformat(),
            source_units_processed=len(source_document.source_units)
        )
        
        # Chunk source units
        chunks = self.chunker.chunk(
            source_units=source_document.source_units,
            document_id=source_document.document_id
        )
        
        if not chunks and source_document.source_units:
            chunks = [ExtractionChunk(
                chunk_id=f"{source_document.document_id}_INSPECTION",
                source_units=[unit.source_id for unit in source_document.source_units],
                text_content="",
            )]
        if len({chunk.chunk_id for chunk in chunks}) != len(chunks):
            raise ValueError("Scheduled root chunk IDs must be unique")
        if self.verbose:
            print(f"Created {len(chunks)} extraction chunks")
            print()
        
        # Extract from each chunk
        for i, chunk in enumerate(chunks, 1):
            if self.verbose:
                print(f"Processing chunk {i}/{len(chunks)}: {chunk.chunk_id}")
                print(f"  Section: {chunk.section or '(none)'}")
                print(f"  Pages: {chunk.page_range}")
                print(f"  Tokens: ~{chunk.token_count}")
            
            if not self._requires_extraction(chunk, source_document):
                self.root_outcomes[chunk.chunk_id] = self._outcome(
                    chunk, "SKIPPED_NO_EXTRACTABLE_CONTENT", [])
                continue
            # Check if we should back off due to recent rate limits
            should_wait, delay = self.token_budget.should_backoff()
            if should_wait:
                if self.verbose:
                    print(f"  Backing off for {delay:.1f}s due to recent rate limit...")
                time.sleep(delay)
            
            # Try extraction with retry logic
            items = None
            last_error = None
            is_rate_limit = False
            is_truncation = False
            
            for attempt in range(self.max_retries + 1):
                try:
                    items = self._extract_from_chunk(chunk, source_document.document_id)
                    
                    # Record successful attempt
                    self.chunk_attempts.append({
                        "chunk_id": chunk.chunk_id,
                        "attempt": attempt + 1,
                        "success": True,
                        "items_extracted": len(items),
                        "error": None
                    })
                    
                    if self.verbose:
                        print(f"  Extracted: {len(items)} knowledge items")
                    
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    last_error = e
                    error_str = str(e)
                    
                    # Check error type
                    is_rate_limit = ("rate_limit" in error_str.lower() or 
                                    "413" in error_str or 
                                    "TPM" in error_str or
                                    "tokens per minute" in error_str.lower())
                    
                    is_truncation = ("truncated" in error_str.lower() or
                                    "max_tokens limit" in error_str.lower())
                    
                    is_daily_quota = ("tokens per day" in error_str.lower() or 
                                     "TPD" in error_str)
                    
                    if is_rate_limit:
                        self.token_budget.record_rate_limit_error()
                    
                    # Check if this is a permanent error (don't retry)
                    is_permanent = ("authentication" in error_str.lower() or
                                   "api_key" in error_str.lower() or
                                   "401" in error_str or
                                   is_daily_quota)  # Treat daily quota as permanent for this run
                    
                    # Explicit provider classification takes precedence over legacy text checks.
                    retryable = getattr(e, "retryable", None)
                    if retryable is False:
                        is_permanent = True
                        is_truncation = False
                    elif retryable is True:
                        is_permanent = False

                    if is_permanent:
                        if self.verbose:
                            if is_daily_quota:
                                print(f"  DAILY QUOTA EXHAUSTED: {error_str[:200]}")
                            else:
                                print(f"  PERMANENT ERROR: {type(e).__name__}: {e}")
                        # Record failed attempt and stop retrying
                        self.chunk_attempts.append({
                            "chunk_id": chunk.chunk_id,
                            "attempt": attempt + 1,
                            "success": False,
                            "items_extracted": 0,
                            "error": error_str
                        })
                        break
                    
                    # Record failed attempt
                    self.chunk_attempts.append({
                        "chunk_id": chunk.chunk_id,
                        "attempt": attempt + 1,
                        "success": False,
                        "items_extracted": 0,
                        "error": error_str
                    })
                    
                    if attempt < self.max_retries:
                        if self.verbose:
                            print(f"  RETRY {attempt + 1}/{self.max_retries}: {type(e).__name__}: {e}")
                        
                        # If rate limit, wait before retry
                        if is_rate_limit:
                            backoff_delay = min(10 * (attempt + 1), 30)  # 10s, 20s, 30s
                            if self.verbose:
                                print(f"  Waiting {backoff_delay}s before retry...")
                            time.sleep(backoff_delay)
                    else:
                        # Final attempt failed
                        if self.verbose:
                            print(f"  FAILED after {self.max_retries + 1} attempts: {type(e).__name__}: {e}")
            
            # If all retries failed, try adaptive splitting for truncation errors
            if items is None and is_truncation:
                items = self._try_split_and_extract(chunk, source_document)
            
            split_required = chunk.chunk_id in self.split_chunks
            resolved = bool(items) and (not split_required or self._split_complete.get(chunk.chunk_id, False))
            status = ("RECOVERED" if split_required else "SUCCESS") if resolved else "FAILED"
            self.root_outcomes[chunk.chunk_id] = self._outcome(chunk, status, items or [])
            # Add items to knowledge document (whether from normal extraction or splitting)
            if items:
                for item in items:
                    self._add_knowledge_item(knowledge_doc, item)
            else:
                # Mark as failed
                self.failed_chunks.append(chunk.chunk_id)
                if self.verbose:
                    print(f"  WARNING: Chunk {chunk.chunk_id} could not be extracted")
        
        # Update statistics
        knowledge_doc.update_statistics()
        
        counts = {status: sum(row["outcome"] == status for row in self.root_outcomes.values())
                  for status in ("SUCCESS", "RECOVERED", "FAILED", "SKIPPED_NO_EXTRACTABLE_CONTENT")}
        scheduled = len(chunks)
        assert sum(counts.values()) == scheduled
        extractable = scheduled - counts["SKIPPED_NO_EXTRACTABLE_CONTENT"]
        resolution = ((counts["SUCCESS"] + counts["RECOVERED"] + counts["SKIPPED_NO_EXTRACTABLE_CONTENT"])
                      / scheduled if scheduled else None)
        completion = ((counts["SUCCESS"] + counts["RECOVERED"]) / extractable if extractable else None)
        failed_roots = [key for key, row in self.root_outcomes.items() if row["outcome"] == "FAILED"]
        cited = {sid for item in knowledge_doc.get_all_items() for sid in item.source_unit_ids}
        valid_sources = {unit.source_id for unit in source_document.source_units}
        partial = {key: row["knowledge_ids"] for key, row in self.root_outcomes.items()
                   if row["outcome"] == "FAILED" and row["knowledge_ids"]}
        knowledge_doc.extraction_metadata = {
            "total_chunks": scheduled,
            "successful_chunks": counts["SUCCESS"] + counts["RECOVERED"],
            "failed_chunks": list(dict.fromkeys(self.failed_chunks)),
            "failed_root_ids": failed_roots, "split_chunks": list(self.split_chunks),
            # Preserve the legacy empty-work sentinel; authoritative ratios use None.
            "completeness": resolution if resolution is not None else 1.0,
            "completeness_basis": "legacy resolution ratio; empty-work sentinel is 1.0",
            "chunk_attempts": [dict(row) for row in self.chunk_attempts],
            "scheduled_roots": scheduled, "successful_roots": counts["SUCCESS"],
            "recovered_roots": counts["RECOVERED"], "failed_roots": counts["FAILED"],
            "skipped_roots": counts["SKIPPED_NO_EXTRACTABLE_CONTENT"],
            "root_outcomes": list(self.root_outcomes.values()),
            "child_outcomes": list(self.child_outcomes),
            "retry_attempts": sum(row["attempt"] > 1 for row in self.chunk_attempts),
            "total_attempts": len(self.chunk_attempts), "partial_results": partial,
            "resolution_ratio": resolution, "extraction_completion_ratio": completion,
            "extraction_successful": bool(extractable) and counts["FAILED"] == 0,
            "source_coverage": {
                "total_units": len(valid_sources), "cited_units": sorted(cited & valid_sources),
                "uncited_units": sorted(valid_sources - cited),
                "citation_ratio": len(cited & valid_sources) / len(valid_sources) if valid_sources else None,
                "basis": "source-reference coverage, not semantic faithfulness or topic coverage",
            },
        }
        if self.verbose:
            print(f"Root outcomes: {counts}")
            print(f"Resolution ratio: {resolution}; extraction completion: {completion}")
            self._print_statistics(knowledge_doc)

        return knowledge_doc
    
    @staticmethod
    def _requires_extraction(chunk, source_document):
        """Skip only demonstrably empty/excluded content; visuals remain unresolved."""
        ids = set(chunk.source_units)
        return any(
            unit.source_id in ids and unit.content_role not in {"noise", "furniture"}
            and (bool((unit.text or "").strip()) or unit.type in {"picture", "table", "formula"})
            for unit in source_document.source_units
        )

    @staticmethod
    def _outcome(chunk, status, items):
        return {"chunk_id": chunk.chunk_id, "outcome": status,
                "source_unit_ids": list(chunk.source_units),
                "knowledge_ids": [item.knowledge_id for item in items], "items_extracted": len(items)}

    def _extract_from_chunk(
        self,
        chunk: ExtractionChunk,
        document_id: str
    ) -> List[Any]:
        """
        Extract knowledge from a single chunk with token budget management.
        
        Args:
            chunk: Extraction chunk
            document_id: Document identifier
            
        Returns:
            List of knowledge items
            
        Raises:
            ValueError: If response is malformed or truncated
            RuntimeError: If API call fails
        """
        
        # Build prompt
        prompt = build_extraction_prompt(
            chunk.text_content, chunk.chunk_id, allowed_source_ids=chunk.source_units
        )
        if getattr(self,'prompt_builder',None):
            prompt = self.prompt_builder(chunk)
        
        # Calculate token budget
        budget = self.token_budget.calculate_budget(
            input_text=prompt,
            system_text=getattr(self, "system_prompt", EXTRACTION_SYSTEM_PROMPT) + getattr(self, "budget_schema_text", ""),
            min_output_tokens=self.min_output_tokens,
            preferred_output_tokens=self.preferred_output_tokens
        )
        
        if not budget.is_safe:
            # Chunk is too large for even minimum output
            raise ValueError(
                f"Chunk {chunk.chunk_id} exceeds token budget: {budget.reason}. "
                f"Input: {budget.input_tokens} tokens, need {self.min_output_tokens} output minimum, "
                f"but TPM limit is {budget.tpm_limit}. Consider reducing chunk size."
            )
        
        # Call LLM with calculated budget
        response = self.llm.generate(
            prompt=prompt,
            system=getattr(self, "system_prompt", EXTRACTION_SYSTEM_PROMPT),
            temperature=0.0,
            max_tokens=budget.max_output_tokens
        )
        
        # Record token usage for TPM tracking
        self.token_budget.record_request(budget.total_tokens)
        
        # Parse response
        self.generation_wire_audit=[]
        if getattr(self,'response_transform',None):
            response = self.response_transform(response)
        items = self._parse_response(response, chunk, document_id)
        
        # Keep generation dispositions with existing mechanically validated evidence.
        # They never populate human semantic-review decisions.
        if items and self.strict_evidence:
            from app.models.source import SourceUnit,SourceDocument
            from app.extraction.no_invention import attach_generation_audit
            policy_source=SourceDocument(document_id=document_id,filename='authorized-source-view',page_count=0,
                source_units=[SourceUnit(source_id=sid,document_id=document_id,position=i,type='paragraph',text=text)
                    for i,(sid,text) in enumerate(self._evidence_sources.items())])
            attach_generation_audit(items,policy_source,getattr(self,'generation_wire_audit',[]))
        return items
    
    def _try_split_and_extract(
        self,
        chunk: ExtractionChunk,
        source_document: SourceDocument
    ) -> List[Any]:
        """
        Try to extract from a chunk by splitting it into smaller sub-chunks.
        
        This is called when extraction fails due to truncation.
        Recursively splits sub-chunks if they also fail with truncation.
        
        Args:
            chunk: Failed chunk
            source_document: Source document (for unit lookup)
            
        Returns:
            List of extracted items, or None if splitting fails completely
        """
        if not hasattr(self, "_split_complete"):
            self._split_complete = {}
            self.child_outcomes = []
        self._split_complete[chunk.chunk_id] = False
        if self.verbose:
            print(f"  Attempting adaptive splitting...")
        
        # Check if chunk can be split
        if not self.splitter.can_split(chunk, source_document.source_units):
            if self.verbose:
                print(f"  Cannot split chunk (depth limit or too few units)")
            return None
        
        # Split chunk
        sub_chunks = self.splitter.split_chunk(
            chunk=chunk,
            source_units=source_document.source_units,
            num_splits=2
        )
        
        if not sub_chunks:
            if self.verbose:
                print(f"  Splitting produced no sub-chunks")
            return None
        
        if self.verbose:
            print(f"  Split into {len(sub_chunks)} sub-chunks")
        
        self.split_chunks.append(chunk.chunk_id)
        
        # Extract from each sub-chunk
        all_sub_items = []
        failed_sub_chunks = []
        child_statuses = []
        
        for j, sub_chunk in enumerate(sub_chunks, 1):
            if not self._requires_extraction(sub_chunk, source_document):
                row = self._outcome(sub_chunk, "SKIPPED_NO_EXTRACTABLE_CONTENT", [])
                row["parent_chunk_id"] = chunk.chunk_id
                self.child_outcomes.append(row)
                child_statuses.append(row["outcome"])
                continue
            if self.verbose:
                print(f"    Sub-chunk {j}/{len(sub_chunks)}: {sub_chunk.chunk_id}")
                print(f"      Units: {len(sub_chunk.source_units)}, Tokens: ~{sub_chunk.token_count}")
            
            # Try extraction with retries
            sub_items = None
            last_error = None
            is_truncation_error = False
            
            for attempt in range(self.max_retries + 1):
                try:
                    sub_items = self._extract_from_chunk(sub_chunk, source_document.document_id)
                    
                    self.chunk_attempts.append({
                        "chunk_id": sub_chunk.chunk_id,
                        "attempt": attempt + 1,
                        "success": True,
                        "items_extracted": len(sub_items),
                        "error": None,
                        "parent_chunk": chunk.chunk_id
                    })
                    
                    if self.verbose:
                        print(f"      Extracted: {len(sub_items)} items")
                    
                    break
                    
                except Exception as e:
                    last_error = e
                    error_str = str(e)
                    
                    # Check if this is truncation
                    is_truncation_error = ("truncated" in error_str.lower() or
                                          "max_tokens limit" in error_str.lower())
                    
                    # Check if daily quota exhausted
                    is_daily_quota = ("tokens per day" in error_str.lower() or 
                                     "TPD" in error_str)
                    
                    self.chunk_attempts.append({
                        "chunk_id": sub_chunk.chunk_id,
                        "attempt": attempt + 1,
                        "success": False,
                        "items_extracted": 0,
                        "error": error_str,
                        "parent_chunk": chunk.chunk_id
                    })
                    
                    # Honor provider retryability; retain legacy daily-quota behavior.
                    retryable = getattr(e, "retryable", None)
                    is_permanent = retryable is False or (retryable is not True and is_daily_quota)
                    if is_permanent:
                        is_truncation_error = False
                    if is_permanent:
                        if self.verbose:
                            reason = "DAILY QUOTA EXHAUSTED" if is_daily_quota else "PERMANENT ERROR"
                            print(f"      {reason}: Stopping retries")
                        break
                    
                    if attempt < self.max_retries:
                        if self.verbose:
                            print(f"      RETRY {attempt + 1}/{self.max_retries}: {type(e).__name__}")
                        
                        # Check for rate limit
                        is_rate_limit = ("rate_limit" in error_str.lower() or "413" in error_str)
                        if is_rate_limit:
                            backoff_delay = min(10 * (attempt + 1), 30)
                            time.sleep(backoff_delay)
                    else:
                        if self.verbose:
                            print(f"      FAILED after {self.max_retries + 1} attempts")
            
            # If sub-chunk failed with truncation, try recursive splitting
            if sub_items is None and is_truncation_error:
                if self.verbose:
                    print(f"      Sub-chunk failed with truncation, trying recursive split...")
                
                recursive_items = self._try_split_and_extract(sub_chunk, source_document)
                if recursive_items:
                    sub_items = recursive_items
            
            required_split = sub_chunk.chunk_id in self.split_chunks
            child_resolved = bool(sub_items) and (
                not required_split or self._split_complete.get(sub_chunk.chunk_id, False))
            child_status = (("RECOVERED" if required_split else "SUCCESS") if child_resolved else "FAILED")
            row = self._outcome(sub_chunk, child_status, sub_items or [])
            row["parent_chunk_id"] = chunk.chunk_id
            self.child_outcomes.append(row)
            child_statuses.append(child_status)
            if sub_items:
                all_sub_items.append(sub_items)
            else:
                failed_sub_chunks.append(sub_chunk.chunk_id)
                self.failed_chunks.append(sub_chunk.chunk_id)
        
        self._split_complete[chunk.chunk_id] = (
            len(child_statuses) == len(sub_chunks) and all(status != "FAILED" for status in child_statuses)
        )
        # Check if any sub-chunks succeeded
        if not all_sub_items:
            if self.verbose:
                print(f"  All sub-chunks failed")
            return None
        
        # Merge results
        merged_items = merge_extracted_items(all_sub_items)
        
        if self.verbose:
            total_items = sum(len(items) for items in all_sub_items)
            print(f"  Split extraction: {len(merged_items)} unique items from {total_items} total")
            if failed_sub_chunks:
                print(f"  WARNING: {len(failed_sub_chunks)} sub-chunks failed: {failed_sub_chunks}")
        
        return merged_items
    
    def _parse_response(
        self,
        response: str,
        chunk: ExtractionChunk,
        document_id: str
    ) -> List[Any]:
        """
        Parse LLM response into knowledge items.
        
        Args:
            response: LLM JSON response (may be markdown-fenced)
            chunk: Source chunk
            document_id: Document identifier
            
        Returns:
            List of knowledge items
            
        Raises:
            ValueError: If JSON cannot be parsed
        """
        
        # Extract JSON from markdown fences if present
        json_str = response.strip()
        
        # Check for markdown code fence
        if json_str.startswith("```"):
            # Extract content between fences
            lines = json_str.split("\n")
            # Skip first line (```json or ```)
            # Find closing fence
            start_idx = 1
            end_idx = len(lines)
            for i in range(1, len(lines)):
                if lines[i].strip().startswith("```"):
                    end_idx = i
                    break
            json_str = "\n".join(lines[start_idx:end_idx])
        
        # Parse JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            # Save diagnostic info
            error_msg = f"Failed to parse JSON response: {e}"
            self._save_failed_response(response, chunk.chunk_id, error_msg)
            raise ValueError(error_msg)
        
        # Strict validation must inspect the supplied evidence unchanged.
        # Explicit catalog IDs are resolved and audited by the authorized adapter;
        # fuzzy quotation repair cannot establish support for a claim.
        if self.strict_evidence:
            self._validate_strict_raw_contract(data, chunk)

        items = []
        
        # Parse concepts
        for item_data in data.get("concepts", []):
            item = self._create_concept(item_data, chunk, document_id)
            if item:
                self._attach_source_evidence(item, item_data, chunk)
                items.append(item)
        
        # Parse definitions
        for item_data in data.get("definitions", []):
            item = self._create_definition(item_data, chunk, document_id)
            if item:
                self._attach_source_evidence(item, item_data, chunk)
                items.append(item)
        
        # Parse explanations
        for item_data in data.get("explanations", []):
            item = self._create_explanation(item_data, chunk, document_id)
            if item:
                self._attach_source_evidence(item, item_data, chunk)
                items.append(item)
        
        # Parse examples
        for item_data in data.get("examples", []):
            item = self._create_example(item_data, chunk, document_id)
            if item:
                self._attach_source_evidence(item, item_data, chunk)
                items.append(item)
        
        # Parse facts
        for item_data in data.get("facts", []):
            item = self._create_fact(item_data, chunk, document_id)
            if item:
                self._attach_source_evidence(item, item_data, chunk)
                items.append(item)
        
        # Parse formulas
        for item_data in data.get("formulas", []):
            item = self._create_formula(item_data, chunk, document_id)
            if item:
                self._attach_source_evidence(item, item_data, chunk)
                items.append(item)
        
        # Parse procedures
        for item_data in data.get("procedures", []):
            item = self._create_procedure(item_data, chunk, document_id)
            if item:
                self._attach_source_evidence(item, item_data, chunk)
                items.append(item)
        
        # Parse relationships
        for item_data in data.get("relationships", []):
            item = self._create_relationship(item_data, chunk, document_id)
            if item:
                self._attach_source_evidence(item, item_data, chunk)
                items.append(item)
        
        return items
    
    def _repair_quotes_in_response(self, data: Dict[str, Any], chunk: ExtractionChunk) -> Dict[str, Any]:
        """
        Repair inexact quotes in the response data before validation.
        
        Args:
            data: Parsed JSON response with categories and items
            chunk: The extraction chunk with source texts
            
        Returns:
            Modified data with repaired quotes
        """
        repair_count = 0
        
        for category in data:
            if not isinstance(data[category], list):
                continue
            
            for item in data[category]:
                if not isinstance(item, dict) or 'source_evidence' not in item:
                    continue
                
                for evidence in item['source_evidence']:
                    if not isinstance(evidence, dict):
                        continue
                    
                    source_id = evidence.get('source_id')
                    quote = evidence.get('quote')
                    
                    if not source_id or not quote or source_id not in self._evidence_sources:
                        continue
                    
                    source_text = self._evidence_sources[source_id]
                    
                    # Check if quote already matches exactly
                    if quote in source_text:
                        continue
                    
                    # Attempt repair
                    repair_result = self.quote_repairer.repair_quote(quote, source_text, source_id)
                    
                    if repair_result:
                        # Validate semantic equivalence
                        is_valid, reason = self.quote_repairer.validate_semantic_equivalence(
                            repair_result['original_quote'],
                            repair_result['repaired_quote'],
                            strict=True
                        )
                        
                        if is_valid:
                            # Apply repair
                            evidence['quote'] = repair_result['repaired_quote']
                            repair_count += 1
                            
                            # Log repair for diagnostics
                            self.repaired_quotes.append({
                                'chunk_id': chunk.chunk_id,
                                'category': category,
                                'source_id': source_id,
                                'fields': evidence.get('fields', []),
                                **repair_result,
                                'validation': reason
                            })
                            
                            if self.verbose:
                                print(f"  Repaired quote (similarity {repair_result['similarity']:.3f})")
                                print(f"    From: '{repair_result['original_quote'][:60]}...'")
                                print(f"    To:   '{repair_result['repaired_quote'][:60]}...'")
        
        if self.verbose and repair_count > 0:
            print(f"  Total quotes repaired: {repair_count}")
        
        return data
    

    def _validate_strict_raw_contract(self, data, chunk):
        """Check raw required fields before defaults; no semantic entailment claim."""
        models = {
            "concepts": Concept, "definitions": Definition, "explanations": Explanation,
            "examples": Example, "facts": Fact, "formulas": Formula,
            "procedures": Procedure, "relationships": Relationship,
        }
        errors = []
        if not isinstance(data, dict):
            raise ValueError("Source evidence validation failed: Strict raw contract: expected object")
        for category, model in models.items():
            rows = data.get(category, [])
            if not isinstance(rows, list):
                errors.append(f"/{category}: expected array")
                continue
            # IDs supplied by the application are not fields required from the model.
            required = {name for name, field in model.model_fields.items()
                        if field.is_required()} - {"knowledge_id", "document_id"}
            required.add("source_evidence")
            for index, row in enumerate(rows):
                base = f"/{category}/{index}"
                if not isinstance(row, dict):
                    errors.append(f"{base}: expected object")
                    continue
                for name in sorted(required):
                    path = f"{base}/{name}"
                    if name not in row:
                        errors.append(f"{path}: missing required field")
                        continue
                    value = row[name]
                    if name not in {"source_unit_ids", "source_evidence", "steps"}:
                        if not isinstance(value, str):
                            errors.append(f"{path}: expected string (explicit null is not a string)")
                        # Explicit empty strings retain existing schema semantics;
                        # they are not filled from another field or treated as missing.
                    elif name == "steps":
                        if not isinstance(value, list) or any(not isinstance(v, str) for v in value):
                            errors.append(f"{path}: expected string array")
                    elif name == "source_unit_ids":
                        if (not isinstance(value, list) or not value
                                or any(not isinstance(v, str) for v in value)):
                            errors.append(f"{path}: expected nonempty canonical source-ID array")
                        elif any(v == chunk.chunk_id or v not in chunk.source_units
                                 or (self.valid_source_ids and v not in self.valid_source_ids)
                                 for v in value):
                            errors.append(f"{path}: invalid canonical source ID; scheduling IDs are not provenance")
                    else:
                        if not isinstance(value, list) or not value:
                            errors.append(f"{path}: expected nonempty evidence array")
                            continue
                        for ei, entry in enumerate(value):
                            ep = f"{path}/{ei}"
                            if not isinstance(entry, dict):
                                errors.append(f"{ep}: expected evidence object")
                                continue
                            for key in ("source_id", "quote", "fields"):
                                if key not in entry:
                                    errors.append(f"{ep}/{key}: missing required field")
                            sid = entry.get("source_id")
                            refs = row.get("source_unit_ids")
                            if (not isinstance(sid, str) or sid == chunk.chunk_id
                                    or sid not in chunk.source_units
                                    or not isinstance(refs, list) or sid not in refs
                                    or (self.valid_source_ids and sid not in self.valid_source_ids)):
                                errors.append(f"{ep}/source_id: invalid canonical item/chunk source ID")
                            if not isinstance(entry.get("quote"), str):
                                errors.append(f"{ep}/quote: expected string")
                            fields = entry.get("fields")
                            if (not isinstance(fields, list) or not fields
                                    or any(not isinstance(v, str) for v in fields)):
                                errors.append(f"{ep}/fields: expected nonempty field-path array")
        if errors:
            raise ValueError("Source evidence validation failed: Strict raw contract: " + "; ".join(errors))

    @staticmethod
    def _substantive_fields(item):
        """JSON Pointer leaf paths; include optional fields only when populated."""
        ignored = {"knowledge_id", "knowledge_type", "document_id", "source_unit_ids",
                   "section", "page_range", "confidence", "extraction_metadata"}
        paths = set()
        def visit(value, path):
            if isinstance(value, dict):
                for key, child in value.items():
                    escaped = str(key).replace("~", "~0").replace("/", "~1")
                    child_path = path + "/" + escaped
                    if str(key):
                        paths.add(child_path)  # A populated dictionary key is substantive too.
                    visit(child, child_path)
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    visit(child, path + "/" + str(index))
            elif value is not None and value != "":
                paths.add(path)
        for name, value in item.model_dump(mode="json").items():
            if name not in ignored:
                visit(value, "/" + name)
        return paths

    def _attach_source_evidence(self, item, data, chunk):
        """Validate quotation location and field coverage, NOT semantic entailment."""
        evidence = data.get("source_evidence")
        if "source_evidence" not in data and not self.strict_evidence:
            return  # Existing legacy item behavior and metadata remain unchanged.
        required = self._substantive_fields(item)
        errors, validated, covered, cited = [], [], set(), set()
        raw_sources = data.get("source_unit_ids", [])
        if (not item.source_unit_ids or raw_sources != item.source_unit_ids
                or any(sid not in chunk.source_units for sid in item.source_unit_ids)):
            errors.append("Item references must be nonempty and belong to the actual chunk")
        if not isinstance(evidence, list) or not evidence:
            errors.append("Missing nonempty source_evidence list")
            evidence = []
        for index, entry in enumerate(evidence):
            if not isinstance(entry, dict):
                errors.append(f"Evidence {index}: expected object")
                continue
            sid, quote, fields = entry.get("source_id"), entry.get("quote"), entry.get("fields")
            if not isinstance(sid, str) or sid not in chunk.source_units or sid not in item.source_unit_ids:
                errors.append(f"Evidence {index}: source ID is not an item/chunk reference")
                continue
            text = self._evidence_sources.get(sid)
            if (text is None or not isinstance(quote, str) or not quote.strip()
                    or quote not in text or quote not in chunk.text_content):
                errors.append(f"Evidence {index}: quote does not match supplied source text exactly")
                continue
            if (not isinstance(fields, list) or not fields
                    or any(not isinstance(path, str) or path not in required for path in fields)):
                errors.append(f"Evidence {index}: invalid substantive field paths")
                continue
            span_start,span_end=(chunk.source_spans or {}).get(sid,(0,len(text)))
            positions, start = [], span_start
            while True:
                position = text.find(quote, start)
                if position < 0 or position+len(quote)>span_end:
                    break
                positions.append(position)
                start = position + 1
            if not positions:
                errors.append(f"Evidence {index}: quote is outside the supplied source span")
                continue
            validated.append({
                "source_id": sid, "quote": quote, "fields": list(dict.fromkeys(fields)),
                "match_count": len(positions),
                "start_char": positions[0] if len(positions) == 1 else None,
                "end_char": positions[0] + len(quote) if len(positions) == 1 else None,
                "offset_basis": "supplied_source_unit_text; zero-based; end exclusive",
            })
            covered.update(fields)
            cited.add(sid)
        missing = sorted(required - covered)
        if missing:
            errors.append("Missing evidence for fields: " + ", ".join(missing))
        if cited != set(item.source_unit_ids):
            errors.append("Each cited source requires validated evidence")
        if self.strict_evidence and errors:
            raise ValueError("Source evidence validation failed: " + "; ".join(errors))
        metadata = dict(item.extraction_metadata or {})
        metadata["source_grounding"] = {
            "validation_scope": "exact quotation, chunk membership and field coverage only",
            "mechanically_valid": not errors, "semantic_entailment_verified": False,
            "evidence": validated, "validation_errors": errors,
        }
        item.extraction_metadata = metadata

    def _create_concept(
        self,
        data: Dict[str, Any],
        chunk: ExtractionChunk,
        document_id: str
    ) -> Concept:
        """Create Concept from parsed data"""
        
        knowledge_id = self._next_id("CON")
        source_ids = data.get("source_unit_ids", [])
        validated_ids = self._validate_source_ids(source_ids, knowledge_id)
        
        return Concept(
            knowledge_id=knowledge_id,
            document_id=document_id,
            concept_name=data.get("concept_name", ""),
            aliases=data.get("aliases", []),
            content=data.get("content", data.get("concept_name", "")),
            source_unit_ids=validated_ids,
            section=chunk.section,
            page_range=chunk.page_range
        )
    
    def _create_definition(
        self,
        data: Dict[str, Any],
        chunk: ExtractionChunk,
        document_id: str
    ) -> Definition:
        """Create Definition from parsed data"""
        
        knowledge_id = self._next_id("DEF")
        source_ids = data.get("source_unit_ids", [])
        validated_ids = self._validate_source_ids(source_ids, knowledge_id)
        
        return Definition(
            knowledge_id=knowledge_id,
            document_id=document_id,
            term=data.get("term", ""),
            definition_text=data.get("definition_text", ""),
            context=data.get("context"),
            content=data.get("content", data.get("definition_text", "")),
            source_unit_ids=validated_ids,
            section=chunk.section,
            page_range=chunk.page_range
        )
    
    def _create_explanation(
        self,
        data: Dict[str, Any],
        chunk: ExtractionChunk,
        document_id: str
    ) -> Explanation:
        """Create Explanation from parsed data"""
        
        knowledge_id = self._next_id("EXP")
        source_ids = data.get("source_unit_ids", [])
        validated_ids = self._validate_source_ids(source_ids, knowledge_id)
        
        return Explanation(
            knowledge_id=knowledge_id,
            document_id=document_id,
            topic=data.get("topic", ""),
            explanation_text=data.get("explanation_text", ""),
            explanation_type=data.get("explanation_type"),
            content=data.get("content", data.get("explanation_text", "")),
            source_unit_ids=validated_ids,
            section=chunk.section,
            page_range=chunk.page_range
        )
    
    def _create_example(
        self,
        data: Dict[str, Any],
        chunk: ExtractionChunk,
        document_id: str
    ) -> Example:
        """Create Example from parsed data"""
        
        knowledge_id = self._next_id("EXM")
        source_ids = data.get("source_unit_ids", [])
        validated_ids = self._validate_source_ids(source_ids, knowledge_id)
        
        return Example(
            knowledge_id=knowledge_id,
            document_id=document_id,
            exemplifies=data.get("exemplifies", ""),
            example_text=data.get("example_text", ""),
            example_type=data.get("example_type"),
            content=data.get("content", data.get("example_text", "")),
            source_unit_ids=validated_ids,
            section=chunk.section,
            page_range=chunk.page_range
        )
    
    def _create_fact(
        self,
        data: Dict[str, Any],
        chunk: ExtractionChunk,
        document_id: str
    ) -> Fact:
        """Create Fact from parsed data"""
        
        knowledge_id = self._next_id("FCT")
        source_ids = data.get("source_unit_ids", [])
        validated_ids = self._validate_source_ids(source_ids, knowledge_id)
        
        return Fact(
            knowledge_id=knowledge_id,
            document_id=document_id,
            fact_text=data.get("fact_text", ""),
            fact_type=data.get("fact_type"),
            content=data.get("content", data.get("fact_text", "")),
            source_unit_ids=validated_ids,
            section=chunk.section,
            page_range=chunk.page_range
        )
    
    def _create_formula(
        self,
        data: Dict[str, Any],
        chunk: ExtractionChunk,
        document_id: str
    ) -> Formula:
        """Create Formula from parsed data"""
        
        knowledge_id = self._next_id("FRM")
        source_ids = data.get("source_unit_ids", [])
        validated_ids = self._validate_source_ids(source_ids, knowledge_id)
        
        return Formula(
            knowledge_id=knowledge_id,
            document_id=document_id,
            formula_text=data.get("formula_text", ""),
            variables=data.get("variables"),
            conditions=data.get("conditions"),
            derivation=data.get("derivation"),
            content=data.get("content", data.get("formula_text", "")),
            source_unit_ids=validated_ids,
            section=chunk.section,
            page_range=chunk.page_range
        )
    
    def _create_procedure(
        self,
        data: Dict[str, Any],
        chunk: ExtractionChunk,
        document_id: str
    ) -> Procedure:
        """Create Procedure from parsed data"""
        
        knowledge_id = self._next_id("PRC")
        source_ids = data.get("source_unit_ids", [])
        validated_ids = self._validate_source_ids(source_ids, knowledge_id)
        
        return Procedure(
            knowledge_id=knowledge_id,
            document_id=document_id,
            procedure_name=data.get("procedure_name", ""),
            steps=data.get("steps", []),
            prerequisites=data.get("prerequisites"),
            outcomes=data.get("outcomes"),
            content=data.get("content", data.get("procedure_name", "")),
            source_unit_ids=validated_ids,
            section=chunk.section,
            page_range=chunk.page_range
        )
    
    def _create_relationship(
        self,
        data: Dict[str, Any],
        chunk: ExtractionChunk,
        document_id: str
    ) -> Relationship:
        """Create Relationship from parsed data"""
        
        knowledge_id = self._next_id("REL")
        source_ids = data.get("source_unit_ids", [])
        validated_ids = self._validate_source_ids(source_ids, knowledge_id)
        
        return Relationship(
            knowledge_id=knowledge_id,
            document_id=document_id,
            relationship_type=data.get("relationship_type", ""),
            subject=data.get("subject", ""),
            object=data.get("object", ""),
            description=data.get("description"),
            content=data.get("content", ""),
            source_unit_ids=validated_ids,
            section=chunk.section,
            page_range=chunk.page_range
        )
    
    def _add_knowledge_item(self, doc: KnowledgeDocument, item: Any):
        """Add knowledge item to appropriate list in document"""
        
        if isinstance(item, Concept):
            doc.concepts.append(item)
        elif isinstance(item, Definition):
            doc.definitions.append(item)
        elif isinstance(item, Explanation):
            doc.explanations.append(item)
        elif isinstance(item, Example):
            doc.examples.append(item)
        elif isinstance(item, Fact):
            doc.facts.append(item)
        elif isinstance(item, Formula):
            doc.formulas.append(item)
        elif isinstance(item, Procedure):
            doc.procedures.append(item)
        elif isinstance(item, Relationship):
            doc.relationships.append(item)
    
    def _next_id(self, prefix: str) -> str:
        """Generate next knowledge ID"""
        self.knowledge_id_counter += 1
        return f"{prefix}_{self.knowledge_id_counter:04d}"
    
    def _save_failed_response(self, response: str, chunk_id: str, error_msg: str):
        """
        Save failed response for diagnostic purposes.
        
        Args:
            response: Raw LLM response
            chunk_id: Chunk identifier
            error_msg: Error message
        """
        from pathlib import Path
        import hashlib
        
        # Create diagnostics directory
        diag_dir = Path("data/diagnostics/failed_responses")
        diag_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename with timestamp and chunk ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_chunk_id = chunk_id.replace("/", "_")
        filename = f"{timestamp}_{safe_chunk_id}.txt"
        
        filepath = diag_dir / filename
        
        # Write diagnostic file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"FAILED EXTRACTION DIAGNOSTIC\n")
            f.write(f"{'=' * 80}\n")
            f.write(f"Chunk ID: {chunk_id}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Error: {error_msg}\n")
            f.write(f"{'=' * 80}\n\n")
            f.write(f"RAW RESPONSE:\n")
            f.write(f"{'-' * 80}\n")
            f.write(response)
            f.write(f"\n{'-' * 80}\n")
            f.write(f"\nResponse length: {len(response)} characters\n")
            f.write(f"Response hash: {hashlib.md5(response.encode()).hexdigest()}\n")
        
        if self.verbose:
            print(f"  Diagnostic saved: {filepath}")
    
    def _print_statistics(self, doc: KnowledgeDocument):
        """Print extraction statistics"""
        
        print(f"Total knowledge items: {doc.total_items}")
        print()
        print("By type:")
        print(f"  Concepts:      {len(doc.concepts):3d}")
        print(f"  Definitions:   {len(doc.definitions):3d}")
        print(f"  Explanations:  {len(doc.explanations):3d}")
        print(f"  Examples:      {len(doc.examples):3d}")
        print(f"  Facts:         {len(doc.facts):3d}")
        print(f"  Formulas:      {len(doc.formulas):3d}")
        print(f"  Procedures:    {len(doc.procedures):3d}")
        print(f"  Relationships: {len(doc.relationships):3d}")
        
        if self.invalid_refs_count > 0:
            print()
            print(f"WARNING - Validation warnings: {self.invalid_refs_count} invalid source_unit_id references")
