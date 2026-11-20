"""
Content analyzer for identifying structural characteristics.

Main entry point for the Content Analysis layer.
"""

from datetime import datetime
from typing import List

from app.models.knowledge import KnowledgeDocument, KnowledgeItem
from app.analysis.characteristics import (
    AnalyzedKnowledge,
    AnalyzedKnowledgeDocument,
    ContentCharacteristic
)
from app.analysis.rules import ClassificationRules


class ContentAnalyzer:
    """
    Analyzes extracted knowledge to identify structural characteristics.
    
    This is a rule-based analyzer that uses no LLM calls - it's fully
    deterministic and runs locally.
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize content analyzer.
        
        Args:
            verbose: Print analysis progress
        """
        self.verbose = verbose
    
    def analyze(self, knowledge_doc: KnowledgeDocument) -> AnalyzedKnowledgeDocument:
        """
        Analyze all knowledge items in a document.
        
        Args:
            knowledge_doc: Extracted knowledge document
            
        Returns:
            AnalyzedKnowledgeDocument with characteristics identified
        """
        
        if self.verbose:
            print("\n" + "=" * 80)
            print("CONTENT ANALYSIS")
            print("=" * 80)
            print(f"Document: {knowledge_doc.source_filename}")
            print(f"Knowledge items: {knowledge_doc.total_items}")
            print()
        
        # Create analyzed document
        analyzed_doc = AnalyzedKnowledgeDocument(
            document_id=knowledge_doc.document_id,
            source_filename=knowledge_doc.source_filename,
            analysis_timestamp=datetime.now().isoformat(),
            extraction_timestamp=knowledge_doc.extraction_timestamp,
            source_units_processed=knowledge_doc.source_units_processed
        )
        
        # Analyze each knowledge item
        all_items = knowledge_doc.get_all_items()
        
        for i, item in enumerate(all_items, 1):
            if self.verbose:
                print(f"Analyzing {i}/{len(all_items)}: {item.knowledge_type} {item.knowledge_id}")
            
            analyzed_item = self._analyze_item(item)
            analyzed_doc.analyzed_items.append(analyzed_item)
            
            if self.verbose:
                chars_str = ", ".join(c.value for c in analyzed_item.characteristics)
                print(f"  Characteristics: {chars_str}")
                print(f"  Confidence: {analyzed_item.analysis_confidence}")
                print()
        
        # Update statistics
        analyzed_doc.update_statistics()
        
        if self.verbose:
            print("=" * 80)
            print("ANALYSIS COMPLETE")
            print("=" * 80)
            self._print_statistics(analyzed_doc)
        
        return analyzed_doc
    
    def _analyze_item(self, item: KnowledgeItem) -> AnalyzedKnowledge:
        """
        Analyze a single knowledge item.
        
        Args:
            item: Knowledge item to analyze
            
        Returns:
            AnalyzedKnowledge with characteristics
        """
        
        # Apply classification rules
        characteristics, confidence, reasoning = ClassificationRules.classify(item)
        
        return AnalyzedKnowledge(
            knowledge_item=item,
            characteristics=characteristics,
            analysis_confidence=confidence,
            analysis_reasoning=reasoning
        )
    
    def _print_statistics(self, doc: AnalyzedKnowledgeDocument):
        """Print analysis statistics"""
        
        stats = doc.statistics
        
        print(f"Items analyzed: {stats.items_analyzed}")
        print()
        print("Characteristics distribution:")
        for char, count in sorted(stats.characteristics_distribution.items(), key=lambda x: -x[1]):
            print(f"  {char.value:25s} {count:3d}")
        
        print()
        print("Confidence distribution:")
        for conf, count in sorted(stats.confidence_distribution.items()):
            print(f"  {conf:15s} {count:3d}")
        
        print()
        print(f"Items with multiple characteristics: {stats.multiple_characteristics_count}")
        print(f"Items marked as unknown: {stats.unknown_count}")
