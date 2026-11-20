import re
from typing import Optional

from app.models.source import SourceUnit


class ContentRoleClassifier:
    """
    Deterministic first-pass classifier.

    Important design principles:
    - Does NOT delete source units
    - Only assigns a content_role label
    - Uses generic heuristics that work across different documents
    - Avoids document-specific pattern matching
    - Classification signals: text characteristics, item type, position, bbox, patterns
    
    Classification strategy:
    1. Structural elements (headings) → structural
    2. Non-text content types (pictures, formulas, code) → content
    3. Text characteristics (page numbers, footers, noise) → furniture/noise
    4. Normal prose → content
    5. Uncertain cases → unknown
    
    Future enhancement:
    - Repetition across pages (requires document-level analysis)
    - Surrounding context (requires multi-unit analysis)
    - Document type awareness
    """

    def classify(self, unit: SourceUnit) -> str:
        """
        Classify a single SourceUnit.
        
        Returns one of: content, structural, furniture, noise, unknown
        """
        """
        Classify a single SourceUnit.
        
        Returns one of: content, structural, furniture, noise, unknown
        """
        
        text = (unit.text or "").strip()

        # -----------------------------------------
        # 1. Structural elements
        # -----------------------------------------

        if unit.type == "heading":
            return "structural"

        # -----------------------------------------
        # 2. Non-text content types (always preserve)
        # -----------------------------------------

        # Pictures, formulas, code, tables without text are likely content
        if unit.type in {"picture", "formula", "code", "table"}:
            if not text:
                return "content"
            # If they have text (captions), continue classification

        # Lists without text are likely noise (empty list markers)
        if unit.type == "list" and not text:
            return "noise"

        # Groups without text are structural containers
        if unit.type == "group" and not text:
            return "structural"

        # Unknown types without text are uncertain
        if unit.type == "unknown" and not text:
            return "unknown"

        # -----------------------------------------
        # 3. No text (after handling special types)
        # -----------------------------------------

        if not text:
            return "noise"

        # -----------------------------------------
        # 4. Page furniture detection
        # -----------------------------------------

        # Simple page numbers
        if self._is_page_number(text):
            # Use bbox position as additional signal if available
            if self._is_likely_page_number_position(unit):
                return "furniture"

        # Generic footer patterns
        if self._is_generic_footer(text):
            return "furniture"

        # Generic header patterns (conservative)
        if self._is_generic_header(text):
            return "furniture"

        # -----------------------------------------
        # 5. Extraction noise detection
        # -----------------------------------------

        if self._is_noise(text):
            return "noise"

        # -----------------------------------------
        # 6. Normal content by type
        # -----------------------------------------

        # Paragraphs, lists, and other content types with meaningful text
        if unit.type in {
            "paragraph",
            "list",
            "table",
            "formula",
            "code",
            "picture",
        }:
            # Additional check: very short text might be furniture
            if len(text) >= 3:  # At least 3 chars for real content
                return "content"

        # -----------------------------------------
        # 7. Unknown
        # -----------------------------------------

        return "unknown"

    def _is_page_number(self, text: str) -> bool:
        """
        Detect simple page numbers: 1, 2, 10, 123
        
        Conservative: only pure digits.
        """
        return bool(re.fullmatch(r"\d{1,4}", text))

    def _is_likely_page_number_position(self, unit: SourceUnit) -> bool:
        """
        Check if bbox position suggests page number (top or bottom of page).
        
        This is a heuristic - page numbers are typically at extremes.
        """
        bbox = unit.bbox
        
        if not bbox:
            return False
        
        # Page numbers are typically near top (<100 from top) or bottom (>500 from top)
        # These are rough heuristics that work for many page layouts
        # Top of page
        if bbox.top < 100:
            return True
        
        # Bottom of page (assuming typical page height ~800)
        if bbox.top > 550:
            return True
        
        return False

    def _is_generic_footer(self, text: str) -> bool:
        """
        Detect common footer patterns that appear across many documents.
        
        Uses generic patterns, not document-specific strings.
        
        Examples:
        - "Reprint 2024-25"
        - "Copyright © 2024"
        - "Page 5 of 10"
        - "Last updated: 2024"
        """
        normalized = text.lower().strip()

        # Don't classify long text as footer
        if len(text) > 100:
            return False

        patterns = [
            r"reprint\s+\d{4}[-/]\d{2}",        # Reprint 2024-25
            r"reprint\s+\d{4}",                  # Reprint 2024
            r"copyright\s+©?\s*\d{4}",           # Copyright 2024
            r"©\s*\d{4}",                        # © 2024
            r"page\s+\d+\s+of\s+\d+",            # Page 5 of 10
            r"page\s+\d+",                       # Page 5
            r"last\s+updated:?\s+\d{4}",        # Last updated 2024
            r"revised:?\s+\d{4}",                # Revised 2024
            r"version\s+\d+\.\d+",               # Version 1.2
            r"draft\s*-?\s*\d*",                 # Draft or Draft-1
        ]

        return any(re.search(pattern, normalized) for pattern in patterns)

    def _is_generic_header(self, text: str) -> bool:
        """
        Detect repeated header/running head patterns.
        
        Very conservative to avoid misclassifying real content.
        
        Avoids document-specific strings.
        """
        # Currently conservative - only using very obvious patterns
        # Most headers should be caught by repetition analysis (future)
        
        # Empty or very short ALL CAPS might be headers
        # But this is risky, so we skip for now
        
        return False

    def _is_noise(self, text: str) -> bool:
        """
        Detect obvious extraction artifacts.

        Examples:
        - "1 1 1 1 1" (repeated identical chars with spaces)
        - "2/" (stray digit with punctuation)
        - "---" (decorative lines)
        - "..." (ellipsis artifacts)
        - "*" (isolated symbols)
        """
        normalized = text.strip()

        # Very short fragments (1-2 chars) that are only punctuation/digits
        if len(normalized) <= 2:
            if not normalized.isalpha():
                return True

        # Repeated single characters with spaces: "1 1 1 1" or "a a a a"
        # Check if all non-space characters are the same
        if re.match(r'^(\S)(\s+\1)+$', normalized):
            return True

        # Stray digits with punctuation: "2/", "1/", "12/"
        if re.fullmatch(r"\d{1,3}/", normalized):
            return True

        # Decorative lines: "---", "===", "***", "___"
        if re.fullmatch(r"[-_=*\.]{3,}", normalized):
            return True

        # Isolated bullets or symbols
        if re.fullmatch(r"[•◦▪▫■□●○★☆→←↑↓]", normalized):
            return True

        # Obvious OCR artifacts: isolated single punctuation repeated
        if len(normalized) <= 5 and len(set(normalized)) == 1:
            if normalized[0] in ".,;:!?-_=*#@":
                return True

        return False