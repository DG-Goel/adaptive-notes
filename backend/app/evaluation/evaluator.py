"""
Faithfulness and Coverage Evaluator.

Provides deterministic evaluation of pipeline output without modifying any data.
"""

from datetime import datetime
from typing import Dict, List, Set, Tuple
from collections import Counter

from app.models.source import SourceDocument
from app.models.knowledge import KnowledgeDocument
from app.analysis.characteristics import AnalyzedKnowledgeDocument
from app.representation.models import RepresentationDocument
from app.assembly.models import AssembledNotesDocument
from app.rendering.models import RenderManifest
from app.representation.formats import RepresentationFormat

from app.evaluation.models import (
    EvaluationResult,
    EvaluationStatus,
    CoverageMetrics,
    ProvenanceError,
    RepresentationError,
    ContentWarning,
    ItemFinding
)


class FaithfulnessEvaluator:
    """
    Evaluates faithfulness and coverage of the notes generation pipeline.
    
    Performs deterministic structural validation without semantic verification.
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize evaluator.
        
        Args:
            verbose: Print evaluation progress
        """
        self.verbose = verbose
    
    def evaluate(
        self,
        source_doc: SourceDocument,
        knowledge_doc: KnowledgeDocument,
        analyzed_doc: AnalyzedKnowledgeDocument,
        represented_doc: RepresentationDocument,
        assembled_doc: AssembledNotesDocument,
        render_manifest: RenderManifest
    ) -> EvaluationResult:
        """
        Evaluate complete pipeline output.
        
        Args:
            source_doc: Original source units
            knowledge_doc: Extracted knowledge
            analyzed_doc: Analyzed knowledge with characteristics
            represented_doc: Knowledge with representation formats
            assembled_doc: Assembled notes
            render_manifest: Rendering manifest
            
        Returns:
            Structured evaluation result
        """
        
        if self.verbose:
            print("=" * 80)
            print("FAITHFULNESS AND COVERAGE EVALUATION")
            print("=" * 80)
            print(f"Document: {source_doc.filename}")
            print()
        
        # Extract all knowledge IDs from each layer
        extracted_ids = self._get_extracted_knowledge_ids(knowledge_doc)
        analyzed_ids = self._get_analyzed_knowledge_ids(analyzed_doc)
        represented_ids = self._get_represented_knowledge_ids(represented_doc)
        assembled_ids = self._get_assembled_knowledge_ids(assembled_doc)
        rendered_ids = self._get_rendered_knowledge_ids(render_manifest)
        
        # Valid source unit IDs
        valid_source_ids = {unit.source_id for unit in source_doc.source_units}
        
        if self.verbose:
            print(f"Source units: {len(source_doc.source_units)}")
            print(f"Extracted knowledge: {len(extracted_ids)}")
            print(f"Analyzed: {len(analyzed_ids)}")
            print(f"Represented: {len(represented_ids)}")
            print(f"Assembled: {len(assembled_ids)}")
            print(f"Rendered: {len(rendered_ids)}")
            print()
        
        # Collect findings
        provenance_errors: List[ProvenanceError] = []
        representation_errors: List[RepresentationError] = []
        content_warnings: List[ContentWarning] = []
        item_findings: List[ItemFinding] = []
        
        # 1. Check coverage
        coverage = self._calculate_coverage(
            source_doc,
            knowledge_doc,
            analyzed_doc,
            assembled_doc,
            render_manifest,
            extracted_ids,
            analyzed_ids,
            assembled_ids,
            rendered_ids
        )
        
        if self.verbose:
            print("COVERAGE METRICS")
            print(f"  Extraction coverage (structural proxy): {coverage.extraction_coverage_ratio:.1%}")
            print(f"  Analysis coverage: {coverage.analysis_coverage_ratio:.1%}")
            print(f"  Assembly coverage: {coverage.assembly_coverage_ratio:.1%}")
            print(f"  Rendering coverage: {coverage.rendering_coverage_ratio:.1%}")
            print(f"  End-to-end coverage: {coverage.end_to_end_coverage_ratio:.1%}")
            print()
        
        # 2. Check provenance integrity
        provenance_errors.extend(
            self._check_provenance(
                knowledge_doc,
                assembled_doc,
                render_manifest,
                valid_source_ids,
                extracted_ids
            )
        )
        
        # 2.5. Check pipeline stage consistency
        provenance_errors.extend(
            self._check_pipeline_consistency(
                source_doc,
                knowledge_doc,
                analyzed_doc,
                represented_doc,
                assembled_doc,
                extracted_ids,
                analyzed_ids,
                represented_ids,
                assembled_ids
            )
        )
        
        if self.verbose and provenance_errors:
            print(f"PROVENANCE ERRORS: {len(provenance_errors)}")
            for err in provenance_errors[:3]:
                print(f"  - {err.error_type}: {err.message}")
            print()
        
        # 3. Check representation validity
        representation_errors.extend(
            self._check_representations(
                represented_doc,
                assembled_doc
            )
        )
        
        if self.verbose and representation_errors:
            print(f"REPRESENTATION ERRORS: {len(representation_errors)}")
            for err in representation_errors[:3]:
                print(f"  - {err.error_type}: {err.message}")
            print()
        
        # 4. Check content integrity
        content_warnings.extend(
            self._check_content_integrity(
                extracted_ids,
                assembled_ids,
                rendered_ids,
                render_manifest
            )
        )
        
        if self.verbose and content_warnings:
            print(f"CONTENT WARNINGS: {len(content_warnings)}")
            for warn in content_warnings[:3]:
                print(f"  - {warn.warning_type}: {warn.message}")
            print()
        
        # 5. Build per-item findings
        item_findings = self._build_item_findings(
            knowledge_doc,
            analyzed_doc,
            represented_doc,
            assembled_doc,
            render_manifest,
            extracted_ids,
            analyzed_ids,
            represented_ids,
            assembled_ids,
            rendered_ids,
            provenance_errors,
            representation_errors,
            content_warnings
        )
        
        # 6. Generate recommendations
        recommendations = self._generate_recommendations(
            coverage,
            provenance_errors,
            representation_errors,
            content_warnings
        )
        
        # 7. Determine overall status
        status = self._determine_status(
            coverage,
            provenance_errors,
            representation_errors,
            content_warnings
        )
        
        if self.verbose:
            print("=" * 80)
            print(f"EVALUATION STATUS: {status.status.upper()}")
            print(f"  Errors: {status.total_errors}")
            print(f"  Warnings: {status.total_warnings}")
            print("=" * 80)
            print()
        
        return EvaluationResult(
            evaluation_timestamp=datetime.now().isoformat(),
            document_id=source_doc.document_id,
            source_filename=source_doc.filename,
            status=status,
            coverage=coverage,
            provenance_errors=provenance_errors,
            representation_errors=representation_errors,
            content_warnings=content_warnings,
            item_findings=item_findings,
            recommendations=recommendations
        )
    
    def _get_extracted_knowledge_ids(self, knowledge_doc: KnowledgeDocument) -> Set[str]:
        """Extract all knowledge IDs from knowledge document."""
        ids = set()
        for attr in ['concepts', 'definitions', 'explanations', 'examples', 
                     'facts', 'formulas', 'procedures', 'relationships']:
            items = getattr(knowledge_doc, attr, [])
            for item in items:
                ids.add(item.knowledge_id)
        return ids
    
    def _get_analyzed_knowledge_ids(self, analyzed_doc: AnalyzedKnowledgeDocument) -> Set[str]:
        """Extract all knowledge IDs from analyzed document."""
        ids = set()
        for item in analyzed_doc.analyzed_items:
            ids.add(item.knowledge_id)
        return ids
    
    def _get_represented_knowledge_ids(self, represented_doc: RepresentationDocument) -> Set[str]:
        """Extract all knowledge IDs from represented document."""
        ids = set()
        for item in represented_doc.representations:
            ids.add(item.knowledge_id)
        return ids
    
    def _get_assembled_knowledge_ids(self, assembled_doc: AssembledNotesDocument) -> Set[str]:
        """Extract all knowledge IDs from assembled document."""
        ids = set()
        for section in assembled_doc.sections:
            for item in section.items:
                ids.add(item.knowledge_id)
        return ids
    
    def _get_rendered_knowledge_ids(self, render_manifest: RenderManifest) -> Set[str]:
        """Extract all knowledge IDs from render manifest."""
        return {item.knowledge_id for item in render_manifest.items}
    
    def _calculate_coverage(
        self,
        source_doc: SourceDocument,
        knowledge_doc: KnowledgeDocument,
        analyzed_doc: AnalyzedKnowledgeDocument,
        assembled_doc: AssembledNotesDocument,
        render_manifest: RenderManifest,
        extracted_ids: Set[str],
        analyzed_ids: Set[str],
        assembled_ids: Set[str],
        rendered_ids: Set[str]
    ) -> CoverageMetrics:
        """Calculate coverage metrics with explicit denominators."""
        
        # Source units with text content
        source_units_with_text = sum(
            1 for unit in source_doc.source_units 
            if unit.text and len(unit.text.strip()) > 0
        )
        
        # Count by type
        knowledge_by_type = {}
        for attr in ['concepts', 'definitions', 'explanations', 'examples',
                     'facts', 'formulas', 'procedures', 'relationships']:
            items = getattr(knowledge_doc, attr, [])
            if items:
                knowledge_by_type[attr] = len(items)
        
        # Count analyzed by confidence
        analyzed_by_confidence = {}
        for item in analyzed_doc.analyzed_items:
            conf = item.analysis_confidence
            analyzed_by_confidence[conf] = analyzed_by_confidence.get(conf, 0) + 1
        
        # Count assembled by format
        assembled_by_format = {}
        for section in assembled_doc.sections:
            for item in section.items:
                fmt = str(item.primary_format.value)
                assembled_by_format[fmt] = assembled_by_format.get(fmt, 0) + 1
        
        # Count rendered by format and status
        rendered_by_format = {}
        rendered_by_status = {}
        for item in render_manifest.items:
            fmt = str(item.format_used.value)
            rendered_by_format[fmt] = rendered_by_format.get(fmt, 0) + 1
            rendered_by_status[item.status] = rendered_by_status.get(item.status, 0) + 1
        
        # Calculate ratios with explicit denominators
        total_extracted = len(extracted_ids)
        total_analyzed = len(analyzed_ids)
        total_assembled = len(assembled_ids)
        total_rendered = len(rendered_ids)
        
        extraction_coverage = total_extracted / source_units_with_text if source_units_with_text > 0 else 0.0
        analysis_coverage = total_analyzed / total_extracted if total_extracted > 0 else 0.0
        
        # Assembly can work from analyzed or extracted
        assembly_denominator = total_analyzed if total_analyzed > 0 else total_extracted
        assembly_coverage = total_assembled / assembly_denominator if assembly_denominator > 0 else 0.0
        
        rendering_coverage = total_rendered / total_assembled if total_assembled > 0 else 0.0
        end_to_end_coverage = total_rendered / total_extracted if total_extracted > 0 else 0.0
        
        # Find missing items
        not_analyzed = list(extracted_ids - analyzed_ids)
        not_assembled = list(analyzed_ids - assembled_ids) if analyzed_ids else list(extracted_ids - assembled_ids)
        not_rendered = list(assembled_ids - rendered_ids)
        
        return CoverageMetrics(
            total_source_units=len(source_doc.source_units),
            source_units_with_text=source_units_with_text,
            total_knowledge_items_extracted=total_extracted,
            knowledge_items_by_type=knowledge_by_type,
            total_items_analyzed=total_analyzed,
            items_analyzed_by_confidence=analyzed_by_confidence,
            total_items_assembled=total_assembled,
            items_assembled_by_format=assembled_by_format,
            total_items_rendered=total_rendered,
            items_rendered_by_format=rendered_by_format,
            items_rendered_by_status=rendered_by_status,
            extraction_coverage_ratio=extraction_coverage,
            analysis_coverage_ratio=analysis_coverage,
            assembly_coverage_ratio=assembly_coverage,
            rendering_coverage_ratio=rendering_coverage,
            end_to_end_coverage_ratio=end_to_end_coverage,
            knowledge_ids_not_analyzed=not_analyzed,
            knowledge_ids_not_assembled=not_assembled,
            knowledge_ids_not_rendered=not_rendered
        )
    
    def _check_provenance(
        self,
        knowledge_doc: KnowledgeDocument,
        assembled_doc: AssembledNotesDocument,
        render_manifest: RenderManifest,
        valid_source_ids: Set[str],
        extracted_ids: Set[str]
    ) -> List[ProvenanceError]:
        """Check provenance integrity."""
        errors = []
        
        # Check assembled items
        for section in assembled_doc.sections:
            for item in section.items:
                # Check knowledge ID exists
                if item.knowledge_id not in extracted_ids:
                    errors.append(ProvenanceError(
                        error_type="unknown_knowledge_id",
                        knowledge_id=item.knowledge_id,
                        message=f"Knowledge ID {item.knowledge_id} in assembly not found in extracted knowledge",
                        location="assembly"
                    ))
                
                # Check source unit IDs
                if not item.source_unit_ids:
                    errors.append(ProvenanceError(
                        error_type="missing_source_units",
                        knowledge_id=item.knowledge_id,
                        message=f"Knowledge ID {item.knowledge_id} has no source unit references",
                        location="assembly"
                    ))
                else:
                    for source_id in item.source_unit_ids:
                        if source_id not in valid_source_ids:
                            errors.append(ProvenanceError(
                                error_type="unknown_source_unit_id",
                                knowledge_id=item.knowledge_id,
                                source_unit_ids=[source_id],
                                message=f"Source unit ID {source_id} not found in source document",
                                location="assembly"
                            ))
        
        # Check rendered items
        for item in render_manifest.items:
            # Check knowledge ID exists
            if item.knowledge_id not in extracted_ids:
                errors.append(ProvenanceError(
                    error_type="unknown_knowledge_id",
                    knowledge_id=item.knowledge_id,
                    message=f"Knowledge ID {item.knowledge_id} in render manifest not found in extracted knowledge",
                    location="rendering"
                ))
            
            # Check source unit IDs
            if not item.source_unit_ids:
                errors.append(ProvenanceError(
                    error_type="missing_source_units",
                    knowledge_id=item.knowledge_id,
                    message=f"Knowledge ID {item.knowledge_id} has no source unit references in manifest",
                    location="rendering"
                ))
            else:
                for source_id in item.source_unit_ids:
                    if source_id not in valid_source_ids:
                        errors.append(ProvenanceError(
                            error_type="unknown_source_unit_id",
                            knowledge_id=item.knowledge_id,
                            source_unit_ids=[source_id],
                            message=f"Source unit ID {source_id} in manifest not found in source document",
                            location="rendering"
                        ))
        
        # Check for duplicate knowledge IDs in assembly
        assembly_ids = []
        for section in assembled_doc.sections:
            for item in section.items:
                assembly_ids.append(item.knowledge_id)
        
        id_counts = Counter(assembly_ids)
        for kid, count in id_counts.items():
            if count > 1:
                errors.append(ProvenanceError(
                    error_type="duplicate_knowledge_id",
                    knowledge_id=kid,
                    message=f"Knowledge ID {kid} appears {count} times in assembled document",
                    location="assembly"
                ))
        
        return errors
    
    def _check_pipeline_consistency(
        self,
        source_doc: SourceDocument,
        knowledge_doc: KnowledgeDocument,
        analyzed_doc: AnalyzedKnowledgeDocument,
        represented_doc: RepresentationDocument,
        assembled_doc: AssembledNotesDocument,
        extracted_ids: Set[str],
        analyzed_ids: Set[str],
        represented_ids: Set[str],
        assembled_ids: Set[str]
    ) -> List[ProvenanceError]:
        """
        Check pipeline stage consistency.
        
        Validates that:
        1. Extracted items are analyzed
        2. No unexpected analyzed IDs
        3. Document IDs match across stages
        4. No missing stage data (unless legitimately empty)
        """
        errors = []
        
        # Check document ID consistency
        doc_ids = {
            "source": source_doc.document_id,
            "knowledge": knowledge_doc.document_id,
            "analyzed": analyzed_doc.document_id,
            "represented": represented_doc.document_id,
            "assembled": assembled_doc.document_id
        }
        
        # All should match
        unique_doc_ids = set(doc_ids.values())
        if len(unique_doc_ids) > 1:
            errors.append(ProvenanceError(
                error_type="document_id_mismatch",
                knowledge_id="PIPELINE",
                message=f"Document IDs do not match across pipeline stages: {doc_ids}",
                location="pipeline"
            ))
        
        # Check extracted → analyzed consistency
        if extracted_ids:  # Only check if extraction produced items
            missing_analyzed = extracted_ids - analyzed_ids
            
            if missing_analyzed:
                for kid in missing_analyzed:
                    errors.append(ProvenanceError(
                        error_type="missing_analyzed_item",
                        knowledge_id=kid,
                        message=f"Knowledge ID {kid} was extracted but not analyzed",
                        location="analysis"
                    ))
            
            # Check for unexpected analyzed IDs
            unexpected_analyzed = analyzed_ids - extracted_ids
            
            if unexpected_analyzed:
                for kid in unexpected_analyzed:
                    errors.append(ProvenanceError(
                        error_type="unexpected_analyzed_id",
                        knowledge_id=kid,
                        message=f"Knowledge ID {kid} appears in analysis but was not extracted",
                        location="analysis"
                    ))
        
        return errors
    
    def _check_representations(
        self,
        represented_doc: RepresentationDocument,
        assembled_doc: AssembledNotesDocument
    ) -> List[RepresentationError]:
        """Check representation format validity."""
        errors = []
        
        # Build map of representations
        repr_map = {item.knowledge_id: item for item in represented_doc.representations}
        
        # Check assembled items have valid representations
        for section in assembled_doc.sections:
            for item in section.items:
                format_content = item.format_content
                rep_format = item.primary_format
                
                # Check required fields for each format
                missing_fields = self._check_format_fields(rep_format, format_content)
                
                if missing_fields:
                    errors.append(RepresentationError(
                        error_type="missing_required_field",
                        knowledge_id=item.knowledge_id,
                        representation_format=str(rep_format.value),
                        missing_fields=missing_fields,
                        message=f"Missing required fields for {rep_format.value}: {', '.join(missing_fields)}"
                    ))
                
                # Check for empty collections in specific formats
                if rep_format == RepresentationFormat.FLOWCHART:
                    steps = format_content.get('steps', [])
                    if not steps or len(steps) < 2:
                        errors.append(RepresentationError(
                            error_type="empty_collection",
                            knowledge_id=item.knowledge_id,
                            representation_format=str(rep_format.value),
                            message=f"Flowchart has insufficient steps ({len(steps)})"
                        ))
                
                elif rep_format == RepresentationFormat.TIMELINE:
                    events = format_content.get('events', [])
                    if not events:
                        errors.append(RepresentationError(
                            error_type="empty_collection",
                            knowledge_id=item.knowledge_id,
                            representation_format=str(rep_format.value),
                            message="Timeline has no events"
                        ))
                
                elif rep_format == RepresentationFormat.HIERARCHY_TREE:
                    children = format_content.get('children', [])
                    if not children:
                        errors.append(RepresentationError(
                            error_type="empty_collection",
                            knowledge_id=item.knowledge_id,
                            representation_format=str(rep_format.value),
                            message="Hierarchy tree has no children"
                        ))
        
        return errors
    
    def _check_format_fields(
        self,
        rep_format: RepresentationFormat,
        format_content: dict
    ) -> List[str]:
        """Check if format_content has required fields for the given format."""
        missing = []
        
        required_fields = {
            RepresentationFormat.STANDARD_TEXT: ['content'],
            RepresentationFormat.DEFINITION_BOX: ['term', 'definition'],
            RepresentationFormat.EXAMPLE_CALLOUT: ['exemplifies', 'example_text'],
            RepresentationFormat.FLOWCHART: ['steps'],
            RepresentationFormat.TIMELINE: ['events'],
            RepresentationFormat.CAUSE_EFFECT_DIAGRAM: ['cause', 'effect'],
            RepresentationFormat.HIERARCHY_TREE: ['root'],
            RepresentationFormat.COMPARISON_TABLE: ['items', 'dimensions', 'values'],
            RepresentationFormat.FORMULA_DISPLAY: ['formula']
        }
        
        required = required_fields.get(rep_format, [])
        for field in required:
            if field not in format_content:
                missing.append(field)
        
        return missing
    
    def _check_content_integrity(
        self,
        extracted_ids: Set[str],
        assembled_ids: Set[str],
        rendered_ids: Set[str],
        render_manifest: RenderManifest
    ) -> List[ContentWarning]:
        """Check content integrity."""
        warnings = []
        
        # Check for missing rendered items
        for kid in assembled_ids - rendered_ids:
            warnings.append(ContentWarning(
                warning_type="missing_rendered_item",
                knowledge_id=kid,
                message=f"Knowledge ID {kid} was assembled but not rendered"
            ))
        
        # Check for duplicate IDs in rendering
        rendered_id_counts = Counter(item.knowledge_id for item in render_manifest.items)
        for kid, count in rendered_id_counts.items():
            if count > 1:
                warnings.append(ContentWarning(
                    warning_type="duplicated_knowledge_id",
                    knowledge_id=kid,
                    message=f"Knowledge ID {kid} appears {count} times in render manifest"
                ))
        
        # Note: We do NOT check semantic faithfulness here
        # That would require comparing extracted content to source text
        # using semantic similarity or fact-checking, which is out of scope
        
        return warnings
    
    def _build_item_findings(
        self,
        knowledge_doc: KnowledgeDocument,
        analyzed_doc: AnalyzedKnowledgeDocument,
        represented_doc: RepresentationDocument,
        assembled_doc: AssembledNotesDocument,
        render_manifest: RenderManifest,
        extracted_ids: Set[str],
        analyzed_ids: Set[str],
        represented_ids: Set[str],
        assembled_ids: Set[str],
        rendered_ids: Set[str],
        provenance_errors: List[ProvenanceError],
        representation_errors: List[RepresentationError],
        content_warnings: List[ContentWarning]
    ) -> List[ItemFinding]:
        """Build per-item findings."""
        
        findings = []
        
        # Get all knowledge items
        all_items = []
        for attr in ['concepts', 'definitions', 'explanations', 'examples',
                     'facts', 'formulas', 'procedures', 'relationships']:
            items = getattr(knowledge_doc, attr, [])
            all_items.extend(items)
        
        # Build error/warning maps
        prov_errors_by_id = {}
        for err in provenance_errors:
            if err.knowledge_id not in prov_errors_by_id:
                prov_errors_by_id[err.knowledge_id] = []
            prov_errors_by_id[err.knowledge_id].append(err.message)
        
        repr_errors_by_id = {}
        for err in representation_errors:
            if err.knowledge_id not in repr_errors_by_id:
                repr_errors_by_id[err.knowledge_id] = []
            repr_errors_by_id[err.knowledge_id].append(err.message)
        
        content_warnings_by_id = {}
        for warn in content_warnings:
            if warn.knowledge_id not in content_warnings_by_id:
                content_warnings_by_id[warn.knowledge_id] = []
            content_warnings_by_id[warn.knowledge_id].append(warn.message)
        
        # Get format info
        format_map = {}
        status_map = {}
        for section in assembled_doc.sections:
            for item in section.items:
                format_map[item.knowledge_id] = str(item.primary_format.value)
        
        for item in render_manifest.items:
            status_map[item.knowledge_id] = item.status
        
        # Create findings
        for item in all_items:
            kid = item.knowledge_id
            
            finding = ItemFinding(
                knowledge_id=kid,
                knowledge_type=item.knowledge_type,
                source_unit_ids=item.source_unit_ids.copy(),
                extracted=True,
                analyzed=kid in analyzed_ids,
                represented=kid in represented_ids,
                assembled=kid in assembled_ids,
                rendered=kid in rendered_ids,
                provenance_errors=prov_errors_by_id.get(kid, []),
                representation_errors=repr_errors_by_id.get(kid, []),
                content_warnings=content_warnings_by_id.get(kid, []),
                representation_format=format_map.get(kid),
                rendering_status=status_map.get(kid)
            )
            
            findings.append(finding)
        
        return findings
    
    def _generate_recommendations(
        self,
        coverage: CoverageMetrics,
        provenance_errors: List[ProvenanceError],
        representation_errors: List[RepresentationError],
        content_warnings: List[ContentWarning]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Coverage recommendations
        if coverage.knowledge_ids_not_analyzed:
            missing_count = len(coverage.knowledge_ids_not_analyzed)
            recommendations.append(
                f"Investigate why {missing_count} extracted knowledge items were not analyzed. "
                f"Check analysis layer logic."
            )
        
        if coverage.knowledge_ids_not_assembled:
            missing_count = len(coverage.knowledge_ids_not_assembled)
            recommendations.append(
                f"Investigate why {missing_count} items were not assembled. "
                f"Check assembly logic and ordering rules."
            )
        
        if coverage.knowledge_ids_not_rendered:
            missing_count = len(coverage.knowledge_ids_not_rendered)
            recommendations.append(
                f"Investigate why {missing_count} assembled items were not rendered. "
                f"Check renderer fallback logic."
            )
        
        # Provenance recommendations
        unknown_kid_count = sum(1 for e in provenance_errors if e.error_type == "unknown_knowledge_id")
        if unknown_kid_count > 0:
            recommendations.append(
                f"Fix {unknown_kid_count} unknown knowledge ID references in assembly or rendering layers."
            )
        
        unknown_source_count = sum(1 for e in provenance_errors if e.error_type == "unknown_source_unit_id")
        if unknown_source_count > 0:
            recommendations.append(
                f"Fix {unknown_source_count} invalid source unit ID references. "
                f"Verify extraction layer is using correct source IDs."
            )
        
        duplicate_count = sum(1 for e in provenance_errors if e.error_type == "duplicate_knowledge_id")
        if duplicate_count > 0:
            recommendations.append(
                f"Fix {duplicate_count} duplicate knowledge IDs in pipeline. "
                f"Ensure knowledge IDs are unique."
            )
        
        # Representation recommendations
        missing_field_count = sum(1 for e in representation_errors if e.error_type == "missing_required_field")
        if missing_field_count > 0:
            recommendations.append(
                f"Fix {missing_field_count} representations with missing required fields. "
                f"Check representation selector logic."
            )
        
        empty_collection_count = sum(1 for e in representation_errors if e.error_type == "empty_collection")
        if empty_collection_count > 0:
            recommendations.append(
                f"Review {empty_collection_count} representations with empty collections. "
                f"Consider using fallback formats."
            )
        
        # Content recommendations
        if content_warnings:
            recommendations.append(
                f"Review {len(content_warnings)} content warnings for potential data loss or duplication."
            )
        
        # Semantic faithfulness note
        recommendations.append(
            "IMPORTANT: This evaluation did NOT verify semantic faithfulness (factual correctness). "
            "Implement a semantic faithfulness module to verify that extracted claims accurately "
            "represent the source content."
        )
        
        if not recommendations:
            recommendations.append("No issues found. Pipeline output appears valid.")
        
        return recommendations
    
    def _determine_status(
        self,
        coverage: CoverageMetrics,
        provenance_errors: List[ProvenanceError],
        representation_errors: List[RepresentationError],
        content_warnings: List[ContentWarning]
    ) -> EvaluationStatus:
        """Determine overall evaluation status."""
        
        total_errors = len(provenance_errors) + len(representation_errors)
        total_warnings = len(content_warnings)
        
        # Check if pipeline is complete
        pipeline_complete = True
        incomplete_reasons = []
        
        # Check for missing analyzed items
        if any(e.error_type == "missing_analyzed_item" for e in provenance_errors):
            pipeline_complete = False
            incomplete_reasons.append("extracted items not analyzed")
        
        # Check for unexpected IDs
        if any(e.error_type == "unexpected_analyzed_id" for e in provenance_errors):
            pipeline_complete = False
            incomplete_reasons.append("unexpected analyzed IDs")
        
        # Check for document ID mismatches
        if any(e.error_type == "document_id_mismatch" for e in provenance_errors):
            pipeline_complete = False
            incomplete_reasons.append("document ID mismatch")
        
        # Check for zero extraction with extractable content
        # This is a functional failure, not just a structural validation
        has_extractable_content = coverage.source_units_with_text > 0
        has_extraction_output = coverage.total_knowledge_items_extracted > 0
        
        if has_extractable_content and not has_extraction_output:
            pipeline_complete = False
            incomplete_reasons.append(
                f"zero items extracted from {coverage.source_units_with_text} "
                f"source units with text (extraction failure)"
            )
        
        # Determine pass criteria
        # Coverage is only meaningful if extraction succeeded
        if has_extraction_output:
            coverage_acceptable = (
                coverage.assembly_coverage_ratio >= 0.95 and
                coverage.rendering_coverage_ratio >= 0.95
            )
        else:
            # No extraction output = coverage not acceptable
            coverage_acceptable = False
        
        provenance_valid = len(provenance_errors) == 0
        representations_valid = len(representation_errors) == 0
        
        # Determine status
        if not pipeline_complete:
            status = "incomplete"
            message = f"Pipeline incomplete: {', '.join(incomplete_reasons)}"
        elif total_errors > 0:
            status = "fail"
            message = f"Evaluation failed with {total_errors} errors"
        elif not coverage_acceptable and has_extractable_content:
            # Coverage failure is a warning if extraction succeeded but coverage is low
            status = "warning"
            message = f"Evaluation passed with low coverage warnings"
        elif total_warnings > 0:
            status = "warning"
            message = f"Evaluation passed with {total_warnings} warnings"
        else:
            status = "pass"
            message = "Evaluation passed with no errors or warnings"
        
        return EvaluationStatus(
            status=status,
            total_errors=total_errors,
            total_warnings=total_warnings,
            provenance_errors=len(provenance_errors),
            representation_errors=len(representation_errors),
            content_warnings=len(content_warnings),
            coverage_acceptable=coverage_acceptable,
            provenance_valid=provenance_valid,
            representations_valid=representations_valid,
            pipeline_complete=pipeline_complete,
            summary_message=message
        )
