"""
Note assembler - organizes representations into coherent sections.

Implements deterministic, content-preserving assembly with no invented content.
"""

import re
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple, Optional

from app.representation.models import RepresentationDocument, SelectedRepresentation
from app.assembly.models import (
    AssembledItem,
    AssembledSection,
    AssemblyMetadata,
    AssembledNotesDocument
)


class NoteAssembler:
    """
    Assembles selected representations into organized, ordered notes.
    
    Uses deterministic ordering based on section metadata and source positions.
    Does not invent content or modify representations.
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize note assembler.
        
        Args:
            verbose: Print assembly progress
        """
        self.verbose = verbose
    
    def assemble(self, rep_doc: RepresentationDocument) -> AssembledNotesDocument:
        """
        Assemble representations into organized notes.
        
        Args:
            rep_doc: Document with selected representations
            
        Returns:
            AssembledNotesDocument with organized sections
        """
        
        if self.verbose:
            print("\n" + "=" * 80)
            print("NOTE ASSEMBLY")
            print("=" * 80)
            print(f"Document: {rep_doc.source_filename}")
            print(f"Items to assemble: {len(rep_doc.representations)}")
            print()
        
        # Handle empty input
        if len(rep_doc.representations) == 0:
            if self.verbose:
                print("[WARN] Empty representations list")
            
            return self._create_empty_document(rep_doc)
        
        # Detect duplicate IDs
        duplicate_count = self._detect_duplicates(rep_doc.representations)
        if duplicate_count > 0 and self.verbose:
            print(f"[WARN] Found {duplicate_count} duplicate knowledge_ids")
        
        # Group representations by section
        sections_map, ordering_strategy = self._group_by_section(rep_doc.representations)
        
        if self.verbose:
            print(f"Ordering strategy: {ordering_strategy}")
            print(f"Sections found: {len(sections_map)}")
            print()
        
        # Create assembled sections
        sections = self._create_sections(sections_map, ordering_strategy)
        
        # Count items with/without sections
        items_with_section = sum(
            len(items) for section_name, items in sections_map.items()
            if section_name != "Main Content"
        )
        items_without_section = sum(
            len(items) for section_name, items in sections_map.items()
            if section_name == "Main Content"
        )
        
        # Create assembly metadata
        metadata = AssemblyMetadata(
            assembly_timestamp=datetime.now().isoformat(),
            ordering_strategy=ordering_strategy,
            total_sections=len(sections),
            total_items=len(rep_doc.representations),
            items_with_section=items_with_section,
            items_without_section=items_without_section,
            duplicate_ids_found=duplicate_count
        )
        
        # Create assembled document
        assembled_doc = AssembledNotesDocument(
            document_id=rep_doc.document_id,
            source_filename=rep_doc.source_filename,
            assembly_timestamp=metadata.assembly_timestamp,
            representation_timestamp=rep_doc.representation_timestamp,
            analysis_timestamp=rep_doc.analysis_timestamp,
            extraction_timestamp=rep_doc.extraction_timestamp,
            source_units_processed=rep_doc.source_units_processed,
            sections=sections,
            metadata=metadata
        )
        
        # Update statistics
        assembled_doc.update_statistics()
        
        if self.verbose:
            print("=" * 80)
            print("ASSEMBLY COMPLETE")
            print("=" * 80)
            self._print_summary(assembled_doc)
        
        return assembled_doc
    
    def _detect_duplicates(self, representations: List[SelectedRepresentation]) -> int:
        """Detect duplicate knowledge IDs"""
        id_counts: Dict[str, int] = {}
        
        for rep in representations:
            id_counts[rep.knowledge_id] = id_counts.get(rep.knowledge_id, 0) + 1
        
        duplicate_count = sum(1 for count in id_counts.values() if count > 1)
        
        return duplicate_count
    
    def _group_by_section(
        self, 
        representations: List[SelectedRepresentation]
    ) -> Tuple[Dict[str, List[SelectedRepresentation]], str]:
        """
        Group representations by section.
        
        Returns:
            (sections_map, ordering_strategy)
        """
        
        sections_map: Dict[str, List[SelectedRepresentation]] = defaultdict(list)
        
        # We don't have direct access to original knowledge item section field
        # from SelectedRepresentation, so we use a heuristic based on source_unit_ids
        # For now, group all into "Main Content" and use source-order
        
        # TODO: In a full implementation, we'd need to:
        # 1. Load original knowledge document
        # 2. Map knowledge_id to original item
        # 3. Extract section from original item
        
        # For this implementation, use simple strategy:
        # All items go to "Main Content", ordered by source_unit_ids
        
        for rep in representations:
            sections_map[rep.section or "Main Content"].append(rep)
        
        ordering_strategy = "source-order"
        
        return dict(sections_map), ordering_strategy
    
    def _create_sections(
        self,
        sections_map: Dict[str, List[SelectedRepresentation]],
        ordering_strategy: str
    ) -> List[AssembledSection]:
        """
        Create assembled sections from grouped representations.
        
        Args:
            sections_map: Representations grouped by section name
            ordering_strategy: Strategy used for grouping
            
        Returns:
            List of AssembledSection objects
        """
        
        sections = []
        
        # Sort section names (deterministic)
        # "Main Content" always first
        section_names = sorted(sections_map.keys())
        if any(r.source_position is not None for r in sum(list(sections_map.values()),[])):
            section_names=sorted(sections_map,key=lambda name:min((r.source_position for r in sections_map[name] if r.source_position is not None),default=float('inf')))
        if "Main Content" in section_names:
            section_names.remove("Main Content")
            section_names.insert(0, "Main Content")
        
        for section_idx, section_name in enumerate(section_names):
            representations = sections_map[section_name]
            
            # Order items within section
            ordered_reps, item_ordering_strategy = self._order_items(representations)
            
            # Create assembled items
            items = []
            for position, rep in enumerate(ordered_reps):
                item = AssembledItem(
                    knowledge_id=rep.knowledge_id,
                    educational_context=rep.educational_context.copy(),
                    document_id=rep.document_id,
                    knowledge_type=rep.knowledge_type,
                    primary_format=rep.primary_format,
                    format_content=rep.format_content.copy(),
                    secondary_format=rep.secondary_format,
                    secondary_content=rep.secondary_content.copy() if rep.secondary_content else None,
                    selection_confidence=rep.selection_confidence,
                    confidence_label=rep.confidence_label,
                    selection_reasoning=rep.selection_reasoning,
                    source_unit_ids=rep.source_unit_ids.copy(),
                    position_in_section=position,
                    ordering_rationale=item_ordering_strategy
                )
                items.append(item)
            
            # Determine section type
            section_type = "default_section" if section_name == "Main Content" else "named_section"
            
            # Create section
            section = AssembledSection(
                section_id=f"section_{section_idx}",
                section_name=section_name,
                section_type=section_type,
                items=items
            )
            sections.append(section)
        
        return sections
    
    def _order_items(
        self,
        representations: List[SelectedRepresentation]
    ) -> Tuple[List[SelectedRepresentation], str]:
        """
        Order items within a section.
        
        Priority:
        1. By minimum source_unit_id (if all have source_unit_ids)
        2. By knowledge_id (fallback)
        
        Returns:
            (ordered_representations, strategy_used)
        """
        
        if all(rep.source_position is not None for rep in representations):
            roles={'deliberately_incorrect_demonstration':0,'identified_mistake':1,'explanation_of_mistake':2,'corrected_approach':4,'alternative_valid_approach':5}
            return sorted(representations,key=lambda r:(r.source_position,roles.get(r.educational_context.get('instructional_role'),3))), 'source-order'
        # Check if all items have source_unit_ids
        all_have_sources = all(len(rep.source_unit_ids) > 0 for rep in representations)
        
        if all_have_sources:
            # Sort by minimum source_unit_id
            # Source IDs are like "S0001", "S0022", etc.
            def get_sort_key(rep: SelectedRepresentation) -> str:
                return min(rep.source_unit_ids)
            
            sorted_reps = sorted(representations, key=get_sort_key)
            return sorted_reps, "source-order"
        else:
            # Fallback to knowledge_id ordering
            sorted_reps = sorted(representations, key=lambda r: r.knowledge_id)
            return sorted_reps, "id-based"
    
    def _create_empty_document(self, rep_doc: RepresentationDocument) -> AssembledNotesDocument:
        """Create an empty assembled document"""
        
        metadata = AssemblyMetadata(
            assembly_timestamp=datetime.now().isoformat(),
            ordering_strategy="none",
            total_sections=0,
            total_items=0,
            items_with_section=0,
            items_without_section=0,
            duplicate_ids_found=0
        )
        
        return AssembledNotesDocument(
            document_id=rep_doc.document_id,
            source_filename=rep_doc.source_filename,
            assembly_timestamp=metadata.assembly_timestamp,
            representation_timestamp=rep_doc.representation_timestamp,
            analysis_timestamp=rep_doc.analysis_timestamp,
            extraction_timestamp=rep_doc.extraction_timestamp,
            source_units_processed=rep_doc.source_units_processed,
            sections=[],
            metadata=metadata
        )
    
    def _print_summary(self, doc: AssembledNotesDocument):
        """Print assembly summary"""
        
        print(f"Total sections: {doc.statistics.total_sections}")
        print(f"Total items: {doc.statistics.total_items}")
        print(f"Average items per section: {doc.statistics.average_items_per_section:.1f}")
        print()
        
        print("Sections:")
        for section in doc.sections:
            print(f"  {section.section_name}: {section.item_count} items")
        
        print()
        print("Format distribution:")
        for fmt, count in sorted(doc.statistics.items_by_format.items(), key=lambda x: -x[1]):
            print(f"  {fmt.value:25s} {count:3d}")
