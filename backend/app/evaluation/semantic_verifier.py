"""
Semantic Faithfulness Verifier.

Verifies that generated knowledge items and rendered notes are semantically
supported by their original source units.

This module provides deterministic checks for:
- Source text support (does the source contain supporting evidence?)
- Contradictions (does the claim conflict with the source?)
- Unsupported additions (factual details not in source?)
- Numeric accuracy (numbers, dates, units preserved?)
- Provenance validity (can claims be traced to valid source units?)

Optional LLM-assisted semantic verification can be added but is clearly
separated and requires explicit configuration.
"""

from typing import List, Dict, Set, Optional, Literal
from dataclasses import dataclass
from datetime import datetime
import re
from collections import defaultdict

from pydantic import BaseModel, Field

from app.models.source import SourceDocument, SourceUnit
from app.models.knowledge import KnowledgeItem, KnowledgeDocument


# ============================================================================
# Data Models
# ============================================================================

class SemanticVerificationStatus(BaseModel):
    """Status of semantic verification for a single claim."""
    
    status: Literal["SUPPORTED", "UNSUPPORTED", "CONTRADICTED", "INCONCLUSIVE", "INSUFFICIENT_EVIDENCE"]
    confidence: float = Field(ge=0.0, le=1.0)  # 0.0 to 1.0
    reason: str
    evidence_snippets: List[str] = Field(default_factory=list)  # Supporting text from source
    
    # Detailed findings
    has_numeric_match: Optional[bool] = None
    has_entity_match: Optional[bool] = None
    has_keyword_match: Optional[bool] = None


class NumericVerification(BaseModel):
    """Verification of numeric accuracy."""
    
    claimed_numbers: List[str] = Field(default_factory=list)
    source_numbers: List[str] = Field(default_factory=list)
    all_matched: bool = True
    mismatches: List[Dict[str, str]] = Field(default_factory=list)


class EntityVerification(BaseModel):
    """Verification of named entities (proper nouns, dates)."""
    
    claimed_entities: List[str] = Field(default_factory=list)
    source_entities: List[str] = Field(default_factory=list)
    all_matched: bool = True
    mismatches: List[Dict[str, str]] = Field(default_factory=list)


class ClaimVerification(BaseModel):
    """Complete verification result for a single knowledge item."""
    
    knowledge_id: str
    knowledge_type: str
    claim_text: str
    source_unit_ids: List[str]
    
    # Overall verdict
    verification_status: SemanticVerificationStatus
    
    # Detailed checks
    numeric_verification: Optional[NumericVerification] = None
    entity_verification: Optional[EntityVerification] = None
    
    # Source evidence
    source_snippets: List[str] = Field(default_factory=list)
    source_full_text: str = ""
    
    # Method used
    verification_method: Literal["deterministic", "llm_assisted", "hybrid"] = "deterministic"


class SemanticVerificationReport(BaseModel):
    """Complete semantic verification report for a document."""
    
    # Metadata
    verification_timestamp: str
    document_id: str
    source_filename: str
    
    # Summary
    total_claims_verified: int = 0
    claims_supported: int = 0
    claims_unsupported: int = 0
    claims_contradicted: int = 0
    claims_inconclusive: int = 0
    claims_insufficient_evidence: int = 0
    
    # Verification results per claim
    claim_verifications: List[ClaimVerification] = Field(default_factory=list)
    
    # Overall assessment
    semantic_faithfulness_verified: bool = False
    verification_complete: bool = False
    verification_method: str = "deterministic"
    
    # Limitations
    limitations: List[str] = Field(default_factory=list)
    
    @property
    def support_rate(self) -> float:
        """Percentage of claims that are supported."""
        if self.total_claims_verified == 0:
            return 0.0
        return self.claims_supported / self.total_claims_verified


# ============================================================================
# Deterministic Verifier
# ============================================================================

class DeterministicSemanticVerifier:
    """
    Deterministic semantic verifier using text matching and heuristics.
    
    This verifier performs basic semantic checks without LLM assistance:
    - Keyword/phrase matching
    - Numeric accuracy verification
    - Named entity matching
    - Basic contradiction detection
    
    Limitations:
    - Cannot understand paraphrasing or semantic equivalence
    - May miss subtle contradictions
    - Limited to surface-level text matching
    - Returns INCONCLUSIVE for ambiguous cases
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize deterministic verifier.
        
        Args:
            verbose: Print verification progress
        """
        self.verbose = verbose
    
    def verify(
        self,
        knowledge_doc: KnowledgeDocument,
        source_doc: SourceDocument
    ) -> SemanticVerificationReport:
        """
        Verify all knowledge items against their source units.
        
        Args:
            knowledge_doc: Extracted knowledge items
            source_doc: Original source document with source units
            
        Returns:
            Complete verification report
        """
        
        if self.verbose:
            print("=" * 80)
            print("SEMANTIC FAITHFULNESS VERIFICATION (Deterministic)")
            print("=" * 80)
            print(f"Document: {source_doc.filename}")
            print()
        
        # Build source unit lookup
        source_units_map = {unit.source_id: unit for unit in source_doc.source_units}
        
        # Collect all knowledge items
        all_items = knowledge_doc.get_all_items()
        
        if self.verbose:
            print(f"Verifying {len(all_items)} knowledge items...")
            print()
        
        # Verify each item
        claim_verifications: List[ClaimVerification] = []
        
        for item in all_items:
            verification = self._verify_knowledge_item(item, source_units_map)
            claim_verifications.append(verification)
        
        # Calculate summary statistics
        status_counts = defaultdict(int)
        for cv in claim_verifications:
            status_counts[cv.verification_status.status] += 1
        
        # Determine if verification is complete
        # We consider verification complete if:
        # 1. All items were checked
        # 2. No claims are INSUFFICIENT_EVIDENCE
        # 3. Most claims are either SUPPORTED or INCONCLUSIVE (not CONTRADICTED/UNSUPPORTED)
        
        total = len(claim_verifications)
        supported = status_counts["SUPPORTED"]
        unsupported = status_counts["UNSUPPORTED"]
        contradicted = status_counts["CONTRADICTED"]
        inconclusive = status_counts["INCONCLUSIVE"]
        insufficient = status_counts["INSUFFICIENT_EVIDENCE"]
        
        # Semantic faithfulness is verified only if:
        # - At least 80% of claims are SUPPORTED
        # - No claims are CONTRADICTED
        # - Less than 10% are UNSUPPORTED
        # - No INSUFFICIENT_EVIDENCE cases
        
        verification_complete = (insufficient == 0)
        
        support_rate = supported / total if total > 0 else 0.0
        unsupport_rate = unsupported / total if total > 0 else 0.0
        
        semantic_faithfulness_verified = (
            verification_complete and
            contradicted == 0 and
            support_rate >= 0.8 and
            unsupport_rate < 0.1
        )
        
        # Document limitations
        limitations = [
            "This verification uses deterministic text matching and heuristics only.",
            "Cannot detect paraphrasing or semantic equivalence beyond keyword matching.",
            "May produce false negatives (marking valid claims as INCONCLUSIVE).",
            "Returns INCONCLUSIVE when evidence is ambiguous rather than making guesses.",
            "Numeric and entity matching is case-sensitive and exact.",
            "Does not understand context, inference, or implicit information."
        ]
        
        if self.verbose:
            print("=" * 80)
            print("VERIFICATION SUMMARY")
            print("=" * 80)
            print(f"Total claims: {total}")
            print(f"  SUPPORTED: {supported} ({support_rate:.1%})")
            print(f"  UNSUPPORTED: {unsupported}")
            print(f"  CONTRADICTED: {contradicted}")
            print(f"  INCONCLUSIVE: {inconclusive}")
            print(f"  INSUFFICIENT_EVIDENCE: {insufficient}")
            print()
            print(f"Semantic faithfulness verified: {semantic_faithfulness_verified}")
            print("=" * 80)
            print()
        
        return SemanticVerificationReport(
            verification_timestamp=datetime.now().isoformat(),
            document_id=knowledge_doc.document_id,
            source_filename=knowledge_doc.source_filename,
            total_claims_verified=total,
            claims_supported=supported,
            claims_unsupported=unsupported,
            claims_contradicted=contradicted,
            claims_inconclusive=inconclusive,
            claims_insufficient_evidence=insufficient,
            claim_verifications=claim_verifications,
            semantic_faithfulness_verified=semantic_faithfulness_verified,
            verification_complete=verification_complete,
            verification_method="deterministic",
            limitations=limitations
        )
    
    def _verify_knowledge_item(
        self,
        item: KnowledgeItem,
        source_units_map: Dict[str, SourceUnit]
    ) -> ClaimVerification:
        """
        Verify a single knowledge item against its source units.
        
        Args:
            item: Knowledge item to verify
            source_units_map: Map of source_id to SourceUnit
            
        Returns:
            Verification result for this claim
        """
        
        # Extract claim text from item
        claim_text = self._extract_claim_text(item)
        
        # Gather source text
        source_texts = []
        source_snippets = []
        
        for source_id in item.source_unit_ids:
            if source_id in source_units_map:
                unit = source_units_map[source_id]
                if unit.text:
                    source_texts.append(unit.text)
                    # Keep snippet short for evidence
                    snippet = unit.text[:200] if len(unit.text) > 200 else unit.text
                    source_snippets.append(f"{source_id}: {snippet}")
        
        source_full_text = " ".join(source_texts)
        
        # Check if we have sufficient source text
        if not source_full_text.strip():
            return ClaimVerification(
                knowledge_id=item.knowledge_id,
                knowledge_type=item.knowledge_type,
                claim_text=claim_text,
                source_unit_ids=item.source_unit_ids,
                verification_status=SemanticVerificationStatus(
                    status="INSUFFICIENT_EVIDENCE",
                    confidence=1.0,
                    reason="No source text available for verification",
                    evidence_snippets=[]
                ),
                source_snippets=[],
                source_full_text="",
                verification_method="deterministic"
            )
        
        # Perform verification checks
        numeric_verification = self._verify_numerics(claim_text, source_full_text, item.knowledge_type)
        entity_verification = self._verify_entities(claim_text, source_full_text)
        keyword_match = self._verify_keywords(claim_text, source_full_text)
        
        # Determine overall verification status
        verification_status = self._determine_verification_status(
            claim_text,
            source_full_text,
            numeric_verification,
            entity_verification,
            keyword_match,
            source_snippets
        )
        
        return ClaimVerification(
            knowledge_id=item.knowledge_id,
            knowledge_type=item.knowledge_type,
            claim_text=claim_text,
            source_unit_ids=item.source_unit_ids,
            verification_status=verification_status,
            numeric_verification=numeric_verification,
            entity_verification=entity_verification,
            source_snippets=source_snippets,
            source_full_text=source_full_text,
            verification_method="deterministic"
        )
    
    def _extract_claim_text(self, item: KnowledgeItem) -> str:
        """Extract the main claim text from a knowledge item."""
        
        # Different item types store content in different fields
        if hasattr(item, 'definition_text'):
            return item.definition_text
        elif hasattr(item, 'explanation_text'):
            return item.explanation_text
        elif hasattr(item, 'example_text'):
            return item.example_text
        elif hasattr(item, 'fact_text'):
            return item.fact_text
        elif hasattr(item, 'formula_text'):
            return item.formula_text
        elif hasattr(item, 'steps') and item.steps:
            return " ".join(item.steps)
        elif hasattr(item, 'description') and item.description:
            return item.description
        elif hasattr(item, 'content'):
            return item.content
        else:
            return ""
    
    def _verify_numerics(
        self,
        claim_text: str,
        source_text: str,
        knowledge_type: str = "concept"
    ) -> NumericVerification:
        """
        Verify that all numbers in the claim appear in the source.
        
        Implements knowledge-type-aware verification:
        - Examples/Procedures: More lenient on code literals and illustrative values
        - Definitions/Facts: Strict matching of factual numeric claims
        - Formulas: Focus on mathematical expressions, not operand values
        - Concepts: Flexible on illustrative examples
        
        Improved version normalizes number formats (e.g., "100,000" == "100000")
        before comparison to avoid false positives.
        """
        
        # Extract numbers from claim and source
        # Pattern: matches integers, decimals, percentages, years
        number_pattern = r'\b\d+(?:[.,]\d+)?%?\b'
        
        claimed_numbers = re.findall(number_pattern, claim_text)
        source_numbers = re.findall(number_pattern, source_text)
        
        # Remove duplicates but preserve order
        claimed_numbers = list(dict.fromkeys(claimed_numbers))
        source_numbers = list(dict.fromkeys(source_numbers))
        
        # Normalize numbers for comparison (remove commas, handle decimal separators)
        def normalize_number(num_str: str) -> str:
            """Normalize number string for comparison"""
            # Remove commas used as thousands separators
            normalized = num_str.replace(',', '')
            # Keep periods as decimal points
            return normalized
        
        claimed_normalized = [normalize_number(n) for n in claimed_numbers]
        source_normalized = [normalize_number(n) for n in source_numbers]
        
        # Create normalized set for lookup
        source_normalized_set = set(source_normalized)
        
        # Detect code/illustrative contexts in examples and procedures
        # These indicate numbers are likely illustrative, not factual claims
        is_likely_code = self._is_likely_code_context(claim_text, knowledge_type)
        
        # Check if all claimed numbers appear in source (after normalization)
        mismatches = []
        for i, claimed_num in enumerate(claimed_numbers):
            normalized = claimed_normalized[i]
            
            # Type-aware verification
            if normalized not in source_normalized_set:
                # Determine if this mismatch should be treated as an error
                if is_likely_code:
                    # In code context, numbers might be illustrative
                    # Mark as mismatch but with lower severity
                    mismatches.append({
                        "claimed": claimed_num,
                        "status": "illustrative_value_not_in_source",
                        "severity": "low"
                    })
                else:
                    # In factual context, missing numbers are serious
                    mismatches.append({
                        "claimed": claimed_num,
                        "status": "not_found_in_source",
                        "severity": "high"
                    })
        
        # Determine if all matched based on knowledge type
        # For examples/procedures with code, only fail on high-severity mismatches
        if is_likely_code:
            high_severity_mismatches = [m for m in mismatches if m.get("severity") == "high"]
            all_matched = len(high_severity_mismatches) == 0
        else:
            all_matched = len(mismatches) == 0
        
        return NumericVerification(
            claimed_numbers=claimed_numbers,
            source_numbers=source_numbers,
            all_matched=all_matched,
            mismatches=mismatches
        )
    
    def _is_likely_code_context(self, text: str, knowledge_type: str) -> bool:
        """
        Detect if text contains code or illustrative examples.
        
        Indicators:
        - Code syntax: brackets [], parentheses (), semicolons, operators
        - Variable assignments: =, :=, <-
        - Array/list syntax: new int[], [], {}
        - Method calls: .method(), function()
        - Type declarations: int, double, float, String
        - Mathematical formulas with symbols
        
        Knowledge types that often contain code:
        - example: Most likely to contain illustrative code
        - procedure: Often contains code snippets or algorithm steps
        - formula: Contains mathematical expressions
        """
        
        # Formulas are always illustrative by nature
        if knowledge_type == "formula":
            return True
        
        # Examples and procedures may contain code
        if knowledge_type not in ["example", "procedure"]:
            return False
        
        # Code syntax indicators
        code_indicators = [
            r'\[\d+\]',  # Array indexing: numbers[0]
            r'new\s+\w+\[',  # Array creation: new int[5]
            r'\w+\s*=\s*\d+',  # Assignment: x = 5
            r'\w+\s*\(\s*\d+',  # Function call with numeric arg: func(10)
            r'\{.*\d+.*\}',  # Object/array literal with numbers: {1,2,3}
            r'\w+\[\d+\]',  # Array access: arr[0]
            r'for\s*\(',  # For loop
            r'if\s*\(',  # If statement
            r'\w+\s*[<>=!]+\s*\d+',  # Comparison: value > 100
        ]
        
        code_pattern = '|'.join(code_indicators)
        if re.search(code_pattern, text):
            return True
        
        # Check for programming keywords combined with numbers
        programming_keywords = [
            'array', 'index', 'length', 'size', 'capacity',
            'initialize', 'declare', 'assign', 'allocate',
            'parameter', 'argument', 'return', 'variable'
        ]
        
        text_lower = text.lower()
        for keyword in programming_keywords:
            if keyword in text_lower and re.search(r'\d+', text):
                return True
        
        return False
    
    def _verify_entities(
        self,
        claim_text: str,
        source_text: str
    ) -> EntityVerification:
        """
        Verify that named entities (capitalized proper nouns) match.
        
        Extracts words starting with capital letters (likely names, places)
        and checks if they appear in the source.
        
        Improved version filters out:
        - Imperative verbs (common in procedure steps)
        - Java/programming keywords
        - Case-insensitive matches
        """
        
        # Extract capitalized words (potential proper nouns)
        entity_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        
        claimed_entities = re.findall(entity_pattern, claim_text)
        source_entities = re.findall(entity_pattern, source_text)
        
        # Filter out common words
        common_words = {
            "The", "A", "An", "In", "On", "At", "To", "For", "Of", "With",
            "By", "From", "This", "That", "These", "Those", "Such", "Some",
            "Many", "Much", "More", "Most", "Each", "Every", "All", "Both",
            "Few", "Several", "Other", "Another"
        }
        
        # Filter out imperative verbs (common in procedures)
        imperative_verbs = {
            "Accept", "Download", "Double", "Click", "Install", "Enter", "Finish", "Move",
            "Open", "Ensure", "Project", "Next", "Create", "Set", "Run", "Select", "Date",
            "Press", "Tab", "Use", "Assign", "Import", "Call", "Pass", "System", "Cast",
            "Perform", "Right", "Refactor", "Rename", "Type", "Store", "Identify", "Read",
            "Compute", "Apply", "Format", "Remove", "Delete", "Reformat", "Declare", "Write",
            "Follow", "Provide", "Add", "Prompt", "Convert", "Echo", "Start", "Place", "Close",
            "Keep", "Extract", "Check", "If", "Otherwise", "While", "Instantiate", "Continue",
            "Drag", "Drop", "Save", "Load", "Edit", "Copy", "Paste", "Cut", "Undo", "Redo",
            "Navigate", "Browse", "Search", "Find", "Replace", "Update", "Upgrade", "Build",
            "Compile", "Deploy", "Test", "Debug", "Run", "Execute", "Launch", "Terminate",
            "Calling"  # Gerund form also excluded
        }
        
        # Filter out Java/programming keywords and common class names
        programming_keywords = {
            "String", "Scanner", "System", "Arrays", "Main", "Integer", "Double", "Boolean",
            "Array", "Object", "Class", "Method", "Function", "Variable", "Type", "Value",
            "Software", "Java", "Runtime", "Environment", "Development", "Edition", "Standard",
            "Application", "Package", "Library", "Framework", "Interface", "Compilation",
            "Bytecode", "Virtual", "Machine", "Compiler", "Code", "Program", "Syntax",
            "Statement", "Expression", "Operator", "Keyword", "Identifier", "Literal"
        }
        
        all_filters = common_words | imperative_verbs | programming_keywords
        
        claimed_entities = [e for e in claimed_entities if e not in all_filters]
        source_entities = [e for e in source_entities if e not in all_filters]
        
        # Remove duplicates
        claimed_entities = list(dict.fromkeys(claimed_entities))
        source_entities = list(dict.fromkeys(source_entities))
        
        # Check if all claimed entities appear in source
        # First try exact match, then case-insensitive
        mismatches = []
        for entity in claimed_entities:
            if entity not in source_entities:
                # Try case-insensitive match
                entity_lower = entity.lower()
                source_lower = source_text.lower()
                if entity_lower not in source_lower:
                    mismatches.append({
                        "claimed": entity,
                        "status": "not_found_in_source"
                    })
        
        all_matched = len(mismatches) == 0
        
        return EntityVerification(
            claimed_entities=claimed_entities,
            source_entities=source_entities,
            all_matched=all_matched,
            mismatches=mismatches
        )
    
    def _verify_keywords(
        self,
        claim_text: str,
        source_text: str
    ) -> Dict[str, any]:
        """
        Verify keyword overlap between claim and source.
        
        Returns metrics about keyword matching.
        """
        from nltk.stem import PorterStemmer
        
        # Normalize text: lowercase, remove punctuation
        claim_normalized = re.sub(r'[^\w\s]', ' ', claim_text.lower())
        source_normalized = re.sub(r'[^\w\s]', ' ', source_text.lower())
        
        # Extract words (length > 3 to skip articles, conjunctions)
        claim_words = [w for w in claim_normalized.split() if len(w) > 3]
        source_words = [w for w in source_normalized.split() if len(w) > 3]
        
        # Also compute stemmed overlap (reduces, reducing, reduced → reduc)
        stemmer = PorterStemmer()
        claim_stems = {stemmer.stem(w) for w in claim_words}
        source_stems = {stemmer.stem(w) for w in source_words}
        
        # Calculate surface-level overlap
        claim_word_set = set(claim_words)
        source_word_set = set(source_words)
        surface_overlap = claim_word_set & source_word_set
        
        # Calculate stemmed overlap
        stem_overlap = claim_stems & source_stems
        unique_to_claim = claim_word_set - source_word_set
        
        # Use stemmed overlap for ratio (more generous for paraphrases)
        overlap_ratio = len(stem_overlap) / len(claim_stems) if claim_stems else 0.0
        
        # Check if this is a short quote paraphrase (special handling)
        is_short_source = len(source_words) <= 30
        has_high_stem_overlap = len(stem_overlap) / len(claim_stems) >= 0.5 if claim_stems else False
        
        return {
            "claim_word_count": len(claim_words),
            "source_word_count": len(source_words),
            "overlap_count": len(surface_overlap),
            "stem_overlap_count": len(stem_overlap),
            "overlap_ratio": overlap_ratio,  # Now based on stems
            "unique_to_claim": list(unique_to_claim),
            "is_short_source": is_short_source,
            "has_high_stem_overlap": has_high_stem_overlap
        }
    
    def _determine_verification_status(
        self,
        claim_text: str,
        source_text: str,
        numeric_verification: NumericVerification,
        entity_verification: EntityVerification,
        keyword_match: Dict[str, any],
        source_snippets: List[str]
    ) -> SemanticVerificationStatus:
        """
        Determine overall verification status based on all checks.
        
        Logic:
        - CONTRADICTED: Numeric or entity mismatches
        - SUPPORTED: High keyword overlap + all numerics/entities match
        - UNSUPPORTED: Very low keyword overlap
        - INCONCLUSIVE: Ambiguous evidence
        """
        
        # Check for contradictions (numeric/entity mismatches)
        # Only flag as CONTRADICTED if source HAS numbers and they don't match
        # If source has no numbers, claim's numbers are UNSUPPORTED, not CONTRADICTED
        if not numeric_verification.all_matched and numeric_verification.claimed_numbers:
            # Check if source has numbers at all
            has_source_numbers = len(numeric_verification.source_numbers) > 0
            
            # Check severity of mismatches (high severity = factual claims, low = illustrative)
            high_severity_mismatches = [
                m for m in numeric_verification.mismatches 
                if m.get("severity", "high") == "high"
            ]
            
            if has_source_numbers and high_severity_mismatches:
                # Source has numbers but they don't match - CONTRADICTION
                return SemanticVerificationStatus(
                    status="CONTRADICTED",
                    confidence=0.9,
                    reason=f"Numeric contradiction: claimed {[m['claimed'] for m in high_severity_mismatches]} but source has {numeric_verification.source_numbers}",
                    evidence_snippets=source_snippets[:2],
                    has_numeric_match=False
                )
            # If source has no numbers or only low-severity mismatches, handle as UNSUPPORTED below
        
        if not entity_verification.all_matched and len(entity_verification.claimed_entities) > 2:
            # Only flag as contradiction if significant entities are missing
            # (more than 30% of entities not found)
            mismatch_rate = len(entity_verification.mismatches) / len(entity_verification.claimed_entities)
            if mismatch_rate > 0.3:
                mismatches = entity_verification.mismatches
                return SemanticVerificationStatus(
                    status="CONTRADICTED",
                    confidence=0.8,
                    reason=f"Entity mismatch: claimed entities {[m['claimed'] for m in mismatches]} not found in source",
                    evidence_snippets=source_snippets[:2],
                    has_entity_match=False
                )
        
        # Check for added numbers/entities BEFORE accepting high overlap as support
        # This prevents high keyword overlap from masking unsupported details
        has_added_numbers = (
            len(numeric_verification.source_numbers) == 0 and 
            len(numeric_verification.claimed_numbers) > 0
        )
        
        has_significant_added_entities = (
            not entity_verification.all_matched and
            len(entity_verification.mismatches) > 0 and
            len(entity_verification.claimed_entities) >= 3  # Only flag if claim has multiple entities
        )
        
        # Check for strong support
        overlap_ratio = keyword_match["overlap_ratio"]
        is_short_source = keyword_match.get("is_short_source", False)
        has_high_stem_overlap = keyword_match.get("has_high_stem_overlap", False)
        
        # Special handling for short source quotes with high stem overlap
        # These are likely paraphrases even if exact word overlap is lower
        if is_short_source and has_high_stem_overlap and overlap_ratio >= 0.3:
            if has_added_numbers:
                return SemanticVerificationStatus(
                    status="UNSUPPORTED",
                    confidence=0.7,
                    reason=f"Short quote paraphrase but added numbers: {numeric_verification.claimed_numbers}",
                    evidence_snippets=source_snippets[:2],
                    has_numeric_match=False,
                    has_entity_match=entity_verification.all_matched,
                    has_keyword_match=True
                )
            
            # Short quote with high stem overlap = likely paraphrase = SUPPORTED
            return SemanticVerificationStatus(
                status="SUPPORTED",
                confidence=0.75,
                reason=f"Short quote paraphrase: {overlap_ratio:.1%} stem overlap, source <30 words",
                evidence_snippets=source_snippets[:2],
                has_numeric_match=numeric_verification.all_matched,
                has_entity_match=entity_verification.all_matched,
                has_keyword_match=True
            )
        
        if overlap_ratio >= 0.7:
            # High keyword overlap, but check if details were added
            if has_added_numbers:
                # High overlap BUT number was added = UNSUPPORTED
                return SemanticVerificationStatus(
                    status="UNSUPPORTED",
                    confidence=0.8,
                    reason=f"High keyword overlap ({overlap_ratio:.1%}) but added numbers not in source: {numeric_verification.claimed_numbers}",
                    evidence_snippets=source_snippets[:2],
                    has_numeric_match=False,
                    has_entity_match=entity_verification.all_matched,
                    has_keyword_match=True
                )
            
            # High keyword overlap + no contradictions + no added details = SUPPORTED
            return SemanticVerificationStatus(
                status="SUPPORTED",
                confidence=min(0.95, 0.7 + overlap_ratio * 0.3),
                reason=f"Strong keyword overlap ({overlap_ratio:.1%}) with source text, no contradictions detected",
                evidence_snippets=source_snippets[:3],
                has_numeric_match=numeric_verification.all_matched,
                has_entity_match=entity_verification.all_matched,
                has_keyword_match=True
            )
        
        if overlap_ratio >= 0.4:
            # Moderate overlap - check for added details
            if has_added_numbers:
                # Moderate overlap BUT number was added = UNSUPPORTED
                return SemanticVerificationStatus(
                    status="UNSUPPORTED",
                    confidence=0.75,
                    reason=f"Moderate keyword overlap ({overlap_ratio:.1%}) but added numbers not in source: {numeric_verification.claimed_numbers}",
                    evidence_snippets=source_snippets[:2],
                    has_numeric_match=False,
                    has_entity_match=entity_verification.all_matched,
                    has_keyword_match=True
                )
            
            # Moderate overlap = SUPPORTED with lower confidence
            return SemanticVerificationStatus(
                status="SUPPORTED",
                confidence=0.5 + overlap_ratio * 0.4,
                reason=f"Moderate keyword overlap ({overlap_ratio:.1%}) with source text, no contradictions",
                evidence_snippets=source_snippets[:2],
                has_numeric_match=numeric_verification.all_matched,
                has_entity_match=entity_verification.all_matched,
                has_keyword_match=True
            )
        
        # Check for unsupported claims with added details
        # Look for claims that add numbers/entities not in source
        has_added_numbers = (
            not numeric_verification.all_matched and 
            len(numeric_verification.source_numbers) == 0 and 
            len(numeric_verification.claimed_numbers) > 0
        )
        
        has_added_entities = (
            not entity_verification.all_matched and
            len(entity_verification.mismatches) > 0 and
            overlap_ratio < 0.5  # Low overlap suggests unsupported, not just paraphrase
        )
        
        if overlap_ratio < 0.2 or has_added_numbers or has_added_entities:
            # Very low overlap or added details = UNSUPPORTED
            unique_words = keyword_match.get("unique_to_claim", [])
            
            if has_added_numbers:
                reason = f"Added numbers not in source: {numeric_verification.claimed_numbers}; low keyword overlap ({overlap_ratio:.1%})"
            elif has_added_entities:
                added_ents = [m['claimed'] for m in entity_verification.mismatches]
                reason = f"Added entities not in source: {added_ents[:3]}; low keyword overlap ({overlap_ratio:.1%})"
            else:
                reason = f"Low keyword overlap ({overlap_ratio:.1%}), claim contains many terms not in source: {', '.join(unique_words[:5])}"
            
            return SemanticVerificationStatus(
                status="UNSUPPORTED",
                confidence=0.7,
                reason=f"Low keyword overlap ({overlap_ratio:.1%}), claim contains many terms not in source: {', '.join(unique_words[:5])}",
                evidence_snippets=source_snippets[:2],
                has_numeric_match=numeric_verification.all_matched,
                has_entity_match=entity_verification.all_matched,
                has_keyword_match=False
            )
        
        # Ambiguous case = INCONCLUSIVE
        return SemanticVerificationStatus(
            status="INCONCLUSIVE",
            confidence=0.5,
            reason=f"Moderate keyword overlap ({overlap_ratio:.1%}) but insufficient evidence for strong verdict",
            evidence_snippets=source_snippets[:2],
            has_numeric_match=numeric_verification.all_matched,
            has_entity_match=entity_verification.all_matched,
            has_keyword_match=overlap_ratio > 0.3
        )
