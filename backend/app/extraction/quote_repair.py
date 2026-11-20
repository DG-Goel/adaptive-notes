"""Automatic repair of inexact evidence quotes using fuzzy matching and semantic validation."""
import re
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher


class QuoteRepair:
    """Repairs model-generated quotes that don't exactly match source text."""
    
    def __init__(self, min_similarity: float = 0.85, max_length_diff: int = 20):
        """
        Initialize quote repair.
        
        Args:
            min_similarity: Minimum similarity ratio (0-1) to consider a match
            max_length_diff: Maximum character difference between quote and candidate
        """
        self.min_similarity = min_similarity
        self.max_length_diff = max_length_diff
    
    def find_best_match(
        self,
        inexact_quote: str,
        source_text: str,
        context_window: int = 200
    ) -> Optional[Tuple[str, int, float]]:
        """
        Find the best matching substring in source text for an inexact quote.
        
        Args:
            inexact_quote: The quote that doesn't exactly match
            source_text: The full source text to search
            context_window: Size of sliding window for matching
            
        Returns:
            Tuple of (exact_match, start_position, similarity) or None if no good match
        """
        if not inexact_quote or not source_text:
            return None
        
        quote_len = len(inexact_quote)
        best_match = None
        best_similarity = 0.0
        best_position = -1
        
        # Normalize for comparison (but preserve original text for return)
        quote_normalized = self._normalize_text(inexact_quote)
        
        # Try to find the quote with some flexibility
        # 1. First try simple case-insensitive search
        quote_lower = inexact_quote.lower()
        source_lower = source_text.lower()
        
        if quote_lower in source_lower:
            pos = source_lower.index(quote_lower)
            return (source_text[pos:pos + len(inexact_quote)], pos, 1.0)
        
        # 2. Try with minor punctuation/contraction differences
        variants = self._generate_quote_variants(inexact_quote)
        for variant in variants:
            variant_lower = variant.lower()
            if variant_lower in source_lower:
                pos = source_lower.index(variant_lower)
                similarity = self._compute_similarity(inexact_quote, source_text[pos:pos + len(variant)])
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = source_text[pos:pos + len(variant)]
                    best_position = pos
        
        if best_similarity >= self.min_similarity:
            return (best_match, best_position, best_similarity)
        
        # 3. Try sliding window with fuzzy matching
        min_len = max(5, quote_len - self.max_length_diff)
        max_len = quote_len + self.max_length_diff
        
        for window_size in range(quote_len - 5, max_len + 1):
            if window_size < min_len:
                continue
            
            for i in range(len(source_text) - window_size + 1):
                candidate = source_text[i:i + window_size]
                similarity = self._compute_similarity(quote_normalized, self._normalize_text(candidate))
                
                if similarity > best_similarity and similarity >= self.min_similarity:
                    best_similarity = similarity
                    best_match = candidate
                    best_position = i
        
        if best_match:
            return (best_match, best_position, best_similarity)
        
        return None
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison (lowercase, collapse whitespace)."""
        # Lowercase
        text = text.lower()
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text)
        # Strip
        text = text.strip()
        return text
    
    def _generate_quote_variants(self, quote: str) -> List[str]:
        """
        Generate common variants of a quote that might appear in transcripts.
        
        Handles:
        - Contractions vs expansions (you'll -> you will)
        - Pronoun variations (we -> you, I -> we)
        - Minor punctuation differences
        """
        variants = [quote]
        
        # Contraction expansions
        contractions = {
            "you'll": "you will",
            "we'll": "we will",
            "I'll": "I will",
            "you're": "you are",
            "we're": "we are",
            "I'm": "I am",
            "that's": "that is",
            "it's": "it is",
            "don't": "do not",
            "can't": "cannot",
            "won't": "will not",
            "isn't": "is not",
            "aren't": "are not",
            "wasn't": "was not",
            "weren't": "were not",
            "hasn't": "has not",
            "haven't": "have not",
            "doesn't": "does not",
        }
        
        # Try expanding contractions
        expanded = quote
        for contraction, expansion in contractions.items():
            if contraction in quote:
                expanded = expanded.replace(contraction, expansion)
        
        if expanded != quote:
            variants.append(expanded)
        
        # Try contracting expansions
        contracted = quote
        for contraction, expansion in contractions.items():
            if expansion in quote:
                contracted = contracted.replace(expansion, contraction)
        
        if contracted != quote:
            variants.append(contracted)
        
        # Try pronoun variants (only for quotes starting with pronouns)
        words = quote.split()
        if len(words) > 3 and words[0].lower() in ['you', 'we', 'i']:
            pronoun_variants = {
                'you': ['we', 'I'],
                'we': ['you', 'I'],
                'i': ['you', 'we']
            }
            
            first_word_lower = words[0].lower()
            if first_word_lower in pronoun_variants:
                for alt_pronoun in pronoun_variants[first_word_lower]:
                    # Match case
                    if words[0][0].isupper():
                        alt_pronoun = alt_pronoun.capitalize()
                    
                    variant_words = [alt_pronoun] + words[1:]
                    variants.append(' '.join(variant_words))
        
        # Also try with auxiliary verb adjustments for pronoun changes
        # "you can" <-> "we can", "I can" <-> "you can"
        if len(words) > 1:
            first_two = ' '.join(words[:2]).lower()
            pronoun_aux_map = {
                'you can': ['we can', 'i can'],
                'we can': ['you can', 'i can'],
                'i can': ['you can', 'we can'],
                'you will': ['we will', 'i will'],
                'we will': ['you will', 'i will'],
            }
            
            for pattern, replacements in pronoun_aux_map.items():
                if quote.lower().startswith(pattern):
                    for replacement in replacements:
                        # Match case of original
                        if quote[0].isupper():
                            replacement = replacement[0].upper() + replacement[1:]
                        variants.append(replacement + quote[len(pattern):])
        
        # Try case variations for proper nouns
        # "Java se" vs "Java SE"
        if 'SE' in quote or 'se' in quote:
            variants.append(quote.replace('SE', 'se'))
            variants.append(quote.replace('se', 'SE'))
        
        return list(dict.fromkeys(variants))  # Remove duplicates, preserve order
    
    def _compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute similarity ratio between two strings.
        
        Uses SequenceMatcher which gives good results for near-matches.
        """
        return SequenceMatcher(None, text1, text2).ratio()
    
    def repair_quote(
        self,
        inexact_quote: str,
        source_text: str,
        source_id: str
    ) -> Optional[Dict[str, any]]:
        """
        Attempt to repair an inexact quote.
        
        Args:
            inexact_quote: The quote that failed exact matching
            source_text: The source text to search
            source_id: Source unit ID for logging
            
        Returns:
            Dict with repair info or None if repair not possible
        """
        match_result = self.find_best_match(inexact_quote, source_text)
        
        if not match_result:
            return None
        
        exact_quote, position, similarity = match_result
        
        return {
            'original_quote': inexact_quote,
            'repaired_quote': exact_quote,
            'source_id': source_id,
            'similarity': similarity,
            'position': position,
            'repair_type': 'fuzzy_match' if similarity < 1.0 else 'case_insensitive'
        }
    
    def validate_semantic_equivalence(
        self,
        original: str,
        repaired: str,
        strict: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that the repaired quote is semantically equivalent to original.
        
        Args:
            original: Original inexact quote from model
            repaired: Repaired exact quote from source
            strict: If True, require very high similarity
            
        Returns:
            Tuple of (is_valid, reason)
        """
        # Normalize both for comparison
        orig_norm = self._normalize_text(original)
        rep_norm = self._normalize_text(repaired)
        
        similarity = self._compute_similarity(orig_norm, rep_norm)
        
        threshold = 0.90 if strict else 0.85
        
        if similarity < threshold:
            return False, f"Similarity {similarity:.2f} below threshold {threshold}"
        
        # Check that key content words are preserved
        orig_words = set(re.findall(r'\b\w+\b', orig_norm))
        rep_words = set(re.findall(r'\b\w+\b', rep_norm))
        
        # Remove common stop words for content comparison
        stop_words = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'to', 'of', 'for', 'in', 'on', 'at', 'and', 'or', 'but'}
        orig_content = orig_words - stop_words
        rep_content = rep_words - stop_words
        
        if len(orig_content) == 0:
            return True, "Short quote, similarity sufficient"
        
        # Check content word overlap
        overlap = len(orig_content & rep_content) / len(orig_content)
        
        if overlap < 0.8:
            missing = orig_content - rep_content
            return False, f"Content words missing: {missing}"
        
        return True, "Semantically equivalent"


def repair_evidence_quotes(
    items: List[Dict],
    sources: Dict[str, str],
    repairer: Optional[QuoteRepair] = None
) -> Tuple[List[Dict], List[Dict]]:
    """
    Repair inexact quotes in extracted items.
    
    Args:
        items: List of extracted knowledge items with source_evidence
        sources: Dict mapping source_id to full text
        repairer: QuoteRepair instance (creates default if None)
        
    Returns:
        Tuple of (repaired_items, repair_log)
    """
    if repairer is None:
        repairer = QuoteRepair()
    
    repair_log = []
    repaired_items = []
    
    for item in items:
        repaired_item = dict(item)
        evidence_list = item.get('source_evidence', [])
        repaired_evidence = []
        
        for evidence in evidence_list:
            source_id = evidence.get('source_id')
            quote = evidence.get('quote')
            
            if not source_id or not quote or source_id not in sources:
                repaired_evidence.append(evidence)
                continue
            
            source_text = sources[source_id]
            
            # Check if quote is already exact
            if quote in source_text:
                repaired_evidence.append(evidence)
                continue
            
            # Attempt repair
            repair_result = repairer.repair_quote(quote, source_text, source_id)
            
            if repair_result:
                # Validate semantic equivalence
                is_valid, reason = repairer.validate_semantic_equivalence(
                    repair_result['original_quote'],
                    repair_result['repaired_quote'],
                    strict=True
                )
                
                if is_valid:
                    # Apply repair
                    repaired_ev = dict(evidence)
                    repaired_ev['quote'] = repair_result['repaired_quote']
                    repaired_evidence.append(repaired_ev)
                    
                    repair_log.append({
                        'item_id': item.get('knowledge_id'),
                        'source_id': source_id,
                        'fields': evidence.get('fields', []),
                        **repair_result,
                        'validation': reason
                    })
                else:
                    # Repair failed validation, keep original
                    repaired_evidence.append(evidence)
                    repair_log.append({
                        'item_id': item.get('knowledge_id'),
                        'source_id': source_id,
                        'repair_failed': True,
                        'reason': reason,
                        'original_quote': quote,
                        'attempted_repair': repair_result['repaired_quote']
                    })
            else:
                # No repair possible
                repaired_evidence.append(evidence)
                repair_log.append({
                    'item_id': item.get('knowledge_id'),
                    'source_id': source_id,
                    'repair_failed': True,
                    'reason': 'No similar match found',
                    'original_quote': quote
                })
        
        repaired_item['source_evidence'] = repaired_evidence
        repaired_items.append(repaired_item)
    
    return repaired_items, repair_log
