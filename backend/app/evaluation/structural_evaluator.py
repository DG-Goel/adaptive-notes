"""
Structural evaluation module for validating representation, assembly, and rendering artifacts.

Validates structural integrity independently from semantic faithfulness.
"""

from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel, Field
from pathlib import Path
import json

from app.representation.models import RepresentationDocument, SelectedRepresentation
from app.assembly.models import AssembledNotesDocument, AssembledSection, AssembledItem
from app.models.knowledge import KnowledgeDocument


class StructuralIssue(BaseModel):
    """A structural validation issue"""
    severity: str  # ERROR, WARNING
    category: str  # missing_field, invalid_type, broken_reference, etc.
    artifact: str  # representation, assembly, markdown
    item_id: Optional[str] = None
    field_name: Optional[str] = None
    reason: str
    details: Optional[Dict] = None


class StructuralEvaluationReport(BaseModel):
    """Complete structural validation report"""
    evaluation_timestamp: str
    artifacts_evaluated: List[str]
    
    # Results
    passed: bool
    error_count: int = 0
    warning_count: int = 0
    
    # Issues by category
    issues: List[StructuralIssue] = Field(default_factory=list)
    
    # Summary by artifact
    representation_errors: int = 0
    assembly_errors: int = 0
    markdown_errors: int = 0
    
    representation_warnings: int = 0
    assembly_warnings: int = 0
    markdown_warnings: int = 0


class StructuralEvaluator:
    """
    Validates structural integrity of knowledge pipeline artifacts.
    
    Checks:
    - Required fields present
    - Valid data types
    - Reference integrity
    - Schema compliance
    - Content completeness
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def evaluate(
        self,
        knowledge_doc: Optional[KnowledgeDocument] = None,
        representation_doc: Optional[RepresentationDocument] = None,
        assembly_doc: Optional[AssembledNotesDocument] = None,
        markdown_output: Optional[str] = None
    ) -> StructuralEvaluationReport:
        """
        Evaluate structural integrity of pipeline artifacts.
        
        Args:
            knowledge_doc: Knowledge extraction output
            representation_doc: Representation selection output
            assembly_doc: Assembled notes output
            markdown_output: Rendered markdown string
            
        Returns:
            StructuralEvaluationReport with all issues found
        """
        from datetime import datetime
        
        issues = []
        artifacts_evaluated = []
        
        # Evaluate representations
        if representation_doc:
            artifacts_evaluated.append("representations")
            rep_issues = self._evaluate_representations(representation_doc, knowledge_doc)
            issues.extend(rep_issues)
        
        # Evaluate assembly
        if assembly_doc:
            artifacts_evaluated.append("assembly")
            asm_issues = self._evaluate_assembly(assembly_doc, representation_doc)
            issues.extend(asm_issues)
        
        # Evaluate markdown
        if markdown_output is not None:
            artifacts_evaluated.append("markdown")
            md_issues = self._evaluate_markdown(markdown_output, assembly_doc)
            issues.extend(md_issues)
        
        # Summarize
        error_count = sum(1 for i in issues if i.severity == "ERROR")
        warning_count = sum(1 for i in issues if i.severity == "WARNING")
        
        rep_errors = sum(1 for i in issues if i.artifact == "representation" and i.severity == "ERROR")
        rep_warnings = sum(1 for i in issues if i.artifact == "representation" and i.severity == "WARNING")
        
        asm_errors = sum(1 for i in issues if i.artifact == "assembly" and i.severity == "ERROR")
        asm_warnings = sum(1 for i in issues if i.artifact == "assembly" and i.severity == "WARNING")
        
        md_errors = sum(1 for i in issues if i.artifact == "markdown" and i.severity == "ERROR")
        md_warnings = sum(1 for i in issues if i.artifact == "markdown" and i.severity == "WARNING")
        
        return StructuralEvaluationReport(
            evaluation_timestamp=datetime.now().isoformat(),
            artifacts_evaluated=artifacts_evaluated,
            passed=(error_count == 0),
            error_count=error_count,
            warning_count=warning_count,
            issues=issues,
            representation_errors=rep_errors,
            representation_warnings=rep_warnings,
            assembly_errors=asm_errors,
            assembly_warnings=asm_warnings,
            markdown_errors=md_errors,
            markdown_warnings=md_warnings
        )
    
    def _evaluate_representations(
        self,
        representation_doc: RepresentationDocument,
        knowledge_doc: Optional[KnowledgeDocument]
    ) -> List[StructuralIssue]:
        """Validate representation document structure"""
        issues = []
        
        # Check required fields at document level
        if not representation_doc.representations:
            issues.append(StructuralIssue(
                severity="ERROR",
                category="empty_content",
                artifact="representation",
                reason="No representations found in document"
            ))
            return issues
        
        # Validate each representation
        for rep in representation_doc.representations:
            # Required fields
            if not rep.knowledge_id:
                issues.append(StructuralIssue(
                    severity="ERROR",
                    category="missing_field",
                    artifact="representation",
                    item_id=getattr(rep, 'knowledge_id', 'unknown'),
                    field_name="knowledge_id",
                    reason="Missing required field: knowledge_id"
                ))
            
            if not rep.source_unit_ids:
                issues.append(StructuralIssue(
                    severity="ERROR",
                    category="missing_field",
                    artifact="representation",
                    item_id=rep.knowledge_id,
                    field_name="source_unit_ids",
                    reason="Missing or empty source_unit_ids"
                ))
            
            if not rep.primary_format:
                issues.append(StructuralIssue(
                    severity="ERROR",
                    category="missing_field",
                    artifact="representation",
                    item_id=rep.knowledge_id,
                    field_name="primary_format",
                    reason="Missing required field: primary_format"
                ))
            
            # Check format content exists
            if not rep.format_content:
                issues.append(StructuralIssue(
                    severity="ERROR",
                    category="missing_content",
                    artifact="representation",
                    item_id=rep.knowledge_id,
                    field_name="format_content",
                    reason="Missing or empty format_content"
                ))
            
            # Type-specific validation based on primary_format
            from app.representation.formats import RepresentationFormat
            if rep.primary_format == RepresentationFormat.COMPARISON_TABLE:
                table_issues = self._validate_table_content(rep)
                issues.extend(table_issues)
            
            elif rep.primary_format == RepresentationFormat.FLOWCHART:
                flow_issues = self._validate_flowchart_content(rep)
                issues.extend(flow_issues)
            
            elif rep.primary_format == RepresentationFormat.FORMULA_DISPLAY:
                formula_issues = self._validate_formula_content(rep)
                issues.extend(formula_issues)
            
            # Reference integrity
            if knowledge_doc:
                ref_issues = self._validate_knowledge_reference(rep, knowledge_doc)
                issues.extend(ref_issues)
        
        return issues
    
    def _validate_table_content(self, rep: SelectedRepresentation) -> List[StructuralIssue]:
        """Validate table format content"""
        issues = []
        
        if not rep.format_content:
            return issues  # Already flagged in main validation
        
        content = rep.format_content
        
        # Check for required table structure
        if 'headers' not in content and 'rows' not in content:
            issues.append(StructuralIssue(
                severity="WARNING",
                category="missing_structure",
                artifact="representation",
                item_id=rep.knowledge_id,
                reason="Table format_content missing headers/rows structure"
            ))
        
        # Check rows exist
        if 'rows' in content and not content['rows']:
            issues.append(StructuralIssue(
                severity="WARNING",
                category="empty_content",
                artifact="representation",
                item_id=rep.knowledge_id,
                reason="Table has no rows"
            ))
        
        return issues
    
    def _validate_flowchart_content(self, rep: SelectedRepresentation) -> List[StructuralIssue]:
        """Validate flowchart format content"""
        issues = []
        
        if not rep.format_content:
            return issues  # Already flagged in main validation
        
        content = rep.format_content
        
        # Flowcharts may have either nodes/edges structure OR steps structure
        has_nodes_edges = 'nodes' in content or 'edges' in content
        has_steps = 'steps' in content
        
        if not has_nodes_edges and not has_steps:
            issues.append(StructuralIssue(
                severity="WARNING",
                category="missing_structure",
                artifact="representation",
                item_id=rep.knowledge_id,
                reason="Flowchart format_content missing both nodes/edges and steps structure"
            ))
        
        # If using nodes/edges structure, validate it
        if has_nodes_edges:
            if 'nodes' not in content or not content['nodes']:
                issues.append(StructuralIssue(
                    severity="ERROR",
                    category="missing_content",
                    artifact="representation",
                    item_id=rep.knowledge_id,
                    reason="Flowchart has no nodes"
                ))
        
        # If using steps structure, validate it
        if has_steps:
            if not content['steps']:
                issues.append(StructuralIssue(
                    severity="WARNING",
                    category="empty_content",
                    artifact="representation",
                    item_id=rep.knowledge_id,
                    reason="Flowchart has no steps"
                ))
        
        return issues
    
    def _validate_formula_content(self, rep: SelectedRepresentation) -> List[StructuralIssue]:
        """Validate formula format content"""
        issues = []
        
        if not rep.format_content:
            return issues  # Already flagged in main validation
        
        content = rep.format_content
        
        # Check for formula text
        if 'formula' not in content or not content['formula']:
            issues.append(StructuralIssue(
                severity="ERROR",
                category="missing_content",
                artifact="representation",
                item_id=rep.knowledge_id,
                reason="Formula format_content missing formula text"
            ))
        
        return issues
    
    def _validate_table(self, rep: SelectedRepresentation) -> List[StructuralIssue]:
        """Validate table structure"""
        issues = []
        
        if not hasattr(rep, 'table_data') or not rep.table_data:
            issues.append(StructuralIssue(
                severity="ERROR",
                category="missing_content",
                artifact="representation",
                item_id=rep.knowledge_id,
                reason="Table representation missing table_data"
            ))
            return issues
        
        # Check headers
        if 'headers' not in rep.table_data:
            issues.append(StructuralIssue(
                severity="WARNING",
                category="missing_field",
                artifact="representation",
                item_id=rep.knowledge_id,
                field_name="table_data.headers",
                reason="Table missing headers"
            ))
        
        # Check rows
        if 'rows' not in rep.table_data:
            issues.append(StructuralIssue(
                severity="ERROR",
                category="missing_field",
                artifact="representation",
                item_id=rep.knowledge_id,
                field_name="table_data.rows",
                reason="Table missing rows"
            ))
        elif not rep.table_data['rows']:
            issues.append(StructuralIssue(
                severity="WARNING",
                category="empty_content",
                artifact="representation",
                item_id=rep.knowledge_id,
                reason="Table has no rows"
            ))
        
        return issues
    
    def _validate_flowchart(self, rep: SelectedRepresentation) -> List[StructuralIssue]:
        """Validate flowchart structure"""
        issues = []
        
        if not hasattr(rep, 'flowchart_structure') or not rep.flowchart_structure:
            issues.append(StructuralIssue(
                severity="ERROR",
                category="missing_content",
                artifact="representation",
                item_id=rep.knowledge_id,
                reason="Flowchart representation missing flowchart_structure"
            ))
            return issues
        
        # Check nodes
        if 'nodes' not in rep.flowchart_structure or not rep.flowchart_structure['nodes']:
            issues.append(StructuralIssue(
                severity="ERROR",
                category="missing_content",
                artifact="representation",
                item_id=rep.knowledge_id,
                reason="Flowchart has no nodes"
            ))
        
        # Check edges
        if 'edges' not in rep.flowchart_structure:
            issues.append(StructuralIssue(
                severity="WARNING",
                category="missing_field",
                artifact="representation",
                item_id=rep.knowledge_id,
                field_name="flowchart_structure.edges",
                reason="Flowchart missing edges (may be intentional for single-node)"
            ))
        
        return issues
    
    def _validate_formula(self, rep: SelectedRepresentation) -> List[StructuralIssue]:
        """Validate formula structure"""
        issues = []
        
        if not hasattr(rep, 'formula_notation') or not rep.formula_notation:
            issues.append(StructuralIssue(
                severity="ERROR",
                category="missing_content",
                artifact="representation",
                item_id=rep.knowledge_id,
                reason="Formula representation missing formula_notation"
            ))
        
        return issues
    
    def _validate_knowledge_reference(
        self,
        rep: SelectedRepresentation,
        knowledge_doc: KnowledgeDocument
    ) -> List[StructuralIssue]:
        """Validate that representation references exist in knowledge document"""
        issues = []
        
        # Get all knowledge IDs
        all_knowledge_ids = {item.knowledge_id for item in knowledge_doc.get_all_items()}
        
        if rep.knowledge_id not in all_knowledge_ids:
            issues.append(StructuralIssue(
                severity="ERROR",
                category="broken_reference",
                artifact="representation",
                item_id=rep.knowledge_id,
                reason=f"Representation references non-existent knowledge_id: {rep.knowledge_id}"
            ))
        
        return issues
    
    def _evaluate_assembly(
        self,
        assembly_doc: AssembledNotesDocument,
        representation_doc: Optional[RepresentationDocument]
    ) -> List[StructuralIssue]:
        """Validate assembly document structure"""
        issues = []
        
        # Check sections exist
        if not assembly_doc.sections:
            issues.append(StructuralIssue(
                severity="ERROR",
                category="empty_content",
                artifact="assembly",
                reason="No sections found in assembled notes"
            ))
            return issues
        
        # Validate each section
        for section in assembly_doc.sections:
            if not section.section_name:
                issues.append(StructuralIssue(
                    severity="WARNING",
                    category="missing_field",
                    artifact="assembly",
                    field_name="section_name",
                    reason="Section missing name"
                ))
            
            if not section.items:
                issues.append(StructuralIssue(
                    severity="WARNING",
                    category="empty_content",
                    artifact="assembly",
                    item_id=section.section_name or "unnamed",
                    reason="Section has no items"
                ))
            
            # Check item references
            if representation_doc:
                rep_ids = {r.knowledge_id for r in representation_doc.representations}
                for item in section.items:
                    if item.knowledge_id not in rep_ids:
                        issues.append(StructuralIssue(
                            severity="ERROR",
                            category="broken_reference",
                            artifact="assembly",
                            item_id=item.knowledge_id,
                            reason=f"Assembled item references non-existent representation: {item.knowledge_id}"
                        ))
        
        return issues
    
    def _evaluate_markdown(
        self,
        markdown: str,
        assembly_doc: Optional[AssembledNotesDocument]
    ) -> List[StructuralIssue]:
        """Validate markdown output structure"""
        issues = []
        
        # Check not empty
        if not markdown or not markdown.strip():
            issues.append(StructuralIssue(
                severity="ERROR",
                category="empty_content",
                artifact="markdown",
                reason="Markdown output is empty"
            ))
            return issues
        
        # Check for basic structure
        lines = markdown.split('\n')
        has_headers = any(line.startswith('#') for line in lines)
        
        if not has_headers:
            issues.append(StructuralIssue(
                severity="WARNING",
                category="missing_structure",
                artifact="markdown",
                reason="Markdown has no headers (may be intentional for simple notes)"
            ))
        
        # Check for malformed markdown patterns
        # Unclosed code blocks
        code_fence_count = sum(1 for line in lines if line.strip().startswith('```'))
        if code_fence_count % 2 != 0:
            issues.append(StructuralIssue(
                severity="ERROR",
                category="malformed_structure",
                artifact="markdown",
                reason=f"Unmatched code fences: {code_fence_count} found (should be even)"
            ))
        
        # Check content length is reasonable
        if len(markdown) < 100:
            issues.append(StructuralIssue(
                severity="WARNING",
                category="insufficient_content",
                artifact="markdown",
                reason=f"Markdown very short ({len(markdown)} chars) - may indicate incomplete rendering"
            ))
        
        return issues
