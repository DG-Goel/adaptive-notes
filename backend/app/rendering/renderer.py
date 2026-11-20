"""
Markdown renderer - converts assembled notes to readable Markdown.

Implements deterministic, format-preserving rendering with full provenance tracking.
"""

import re
from datetime import datetime
from typing import List, Tuple, Optional

from app.assembly.models import AssembledNotesDocument, AssembledItem, AssembledSection
from app.representation.formats import RepresentationFormat
from app.rendering.models import (
    RenderedDocument,
    RenderManifest,
    RenderedItem,
    RenderWarning
)


class MarkdownRenderer:
    """
    Renders assembled notes to Markdown with provenance tracking.
    
    Supports all defined representation formats with safe fallbacks.
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize markdown renderer.
        
        Args:
            verbose: Print rendering progress
        """
        self.verbose = verbose
        self.warnings: List[RenderWarning] = []
        self.current_line: int = 1  # Track line number for provenance
    
    def render(self, assembled_doc: AssembledNotesDocument) -> RenderedDocument:
        """
        Render assembled notes to Markdown.
        
        Args:
            assembled_doc: Document with organized sections and items
            
        Returns:
            RenderedDocument with markdown and manifest
        """
        
        if self.verbose:
            print("\n" + "=" * 80)
            print("MARKDOWN RENDERING")
            print("=" * 80)
            print(f"Document: {assembled_doc.source_filename}")
            print(f"Items to render: {assembled_doc.statistics.total_items}")
            print()
        
        # Reset state
        self.warnings = []
        self.current_line = 1
        
        # Render document
        markdown_lines = []
        rendered_items = []
        
        # Document header
        header_lines = self._render_header(assembled_doc)
        markdown_lines.extend(header_lines)
        self.current_line += len(header_lines)
        
        # Render sections
        if len(assembled_doc.sections) == 0:
            # Empty document
            markdown_lines.append("*No content available*")
            markdown_lines.append("")
            self.current_line += 2
        else:
            for section in assembled_doc.sections:
                section_lines, section_items = self._render_section(section)
                markdown_lines.extend(section_lines)
                rendered_items.extend(section_items)
                self.current_line += len(section_lines)
        
        # Document footer
        footer_lines = self._render_footer(assembled_doc)
        markdown_lines.extend(footer_lines)
        
        # Combine into markdown string
        markdown = "\n".join(markdown_lines)
        
        # Create manifest
        manifest = RenderManifest(
            document_id=assembled_doc.document_id,
            source_filename=assembled_doc.source_filename,
            render_timestamp=datetime.now().isoformat(),
            assembly_timestamp=assembled_doc.assembly_timestamp,
            representation_timestamp=assembled_doc.representation_timestamp,
            analysis_timestamp=assembled_doc.analysis_timestamp,
            extraction_timestamp=assembled_doc.extraction_timestamp,
            markdown_length=len(markdown),
            total_lines=len(markdown_lines),
            items=rendered_items,
            warnings=self.warnings,
            total_items=len(rendered_items)
        )
        
        # Calculate statistics
        manifest.items_complete = sum(1 for item in rendered_items if item.status == "complete")
        manifest.items_partial = sum(1 for item in rendered_items if item.status == "partial")
        manifest.items_fallback = sum(1 for item in rendered_items if item.status == "fallback")
        
        if self.verbose:
            print("=" * 80)
            print("RENDERING COMPLETE")
            print("=" * 80)
            self._print_summary(manifest)
        
        return RenderedDocument(content=markdown, manifest=manifest)
    
    def _render_header(self, doc: AssembledNotesDocument) -> List[str]:
        """Render document header"""
        lines = []
        lines.append(f"# {doc.source_filename}")
        lines.append("")
        lines.append("*Generated from assembled notes*")
        lines.append("")
        lines.append("---")
        lines.append("")
        return lines
    
    def _render_footer(self, doc: AssembledNotesDocument) -> List[str]:
        """Render document footer"""
        lines = []
        lines.append("---")
        lines.append("")
        lines.append(f"*Render complete: {doc.statistics.total_items} items from {doc.statistics.total_sections} sections*")
        lines.append("")
        return lines
    
    def _render_section(
        self, 
        section: AssembledSection
    ) -> Tuple[List[str], List[RenderedItem]]:
        """
        Render a section with all its items.
        
        Returns:
            (markdown_lines, rendered_items)
        """
        lines = []
        rendered_items = []
        
        # Section heading
        lines.append(f"## {self._escape_markdown(section.section_name)}")
        lines.append("")
        
        if len(section.items) == 0:
            lines.append("*No items in this section*")
            lines.append("")
        else:
            for item in section.items:
                item_start_line = self.current_line + len(lines)
                item_lines, render_status, fallback_reason = self._render_item(item)
                lines.extend(item_lines)
                item_end_line = self.current_line + len(lines) - 1
                
                # Track rendered item
                rendered_item = RenderedItem(
                    knowledge_id=item.knowledge_id,
                    source_unit_ids=item.source_unit_ids.copy(),
                    format_used=item.primary_format,
                    start_line=item_start_line,
                    end_line=item_end_line,
                    status=render_status,
                    used_fallback=(render_status == "fallback"),
                    fallback_reason=fallback_reason
                )
                rendered_items.append(rendered_item)
        
        return lines, rendered_items
    
    def _render_item(
        self, 
        item: AssembledItem
    ) -> Tuple[List[str], str, Optional[str]]:
        """
        Render a single item based on its format.
        
        Returns:
            (markdown_lines, rendering_status, fallback_reason)
        """
        
        if item.educational_context:
            bare=item.model_copy(update={'educational_context':{}})
            lines,status,reason=self._render_item(bare)
            if item.educational_context.get('student_view') and 'Original presentation data (fallback):' in lines:
                lines=lines[:lines.index('Original presentation data (fallback):')]
            notices=['> '+self._escape_markdown(n) for n in item.educational_context.get('notices',[])]
            return notices+([''] if notices else [])+lines,status,reason

        format_handlers = {
            RepresentationFormat.STANDARD_TEXT: self._render_standard_text,
            RepresentationFormat.DEFINITION_BOX: self._render_definition_box,
            RepresentationFormat.EXAMPLE_CALLOUT: self._render_example_callout,
            RepresentationFormat.FLOWCHART: self._render_flowchart,
            RepresentationFormat.TIMELINE: self._render_timeline,
            RepresentationFormat.CAUSE_EFFECT_DIAGRAM: self._render_cause_effect,
            RepresentationFormat.HIERARCHY_TREE: self._render_hierarchy_tree,
            RepresentationFormat.COMPARISON_TABLE: self._render_comparison_table,
            RepresentationFormat.FORMULA_DISPLAY: self._render_formula_display
        }
        
        handler = format_handlers.get(item.primary_format)
        
        if handler is None:
            # Unsupported format - fallback
            self._add_warning(
                item.knowledge_id,
                "unsupported_format",
                f"Unsupported format: {item.primary_format}"
            )
            lines = [
                f"*[Unsupported format: {item.primary_format}]*",
                "",
                self._format_provenance(item),
                ""
            ]
            return lines, "fallback", f"Unsupported format: {item.primary_format}"
        
        # Render using appropriate handler
        try:
            lines, status, fallback_reason = handler(item)
            lines.append("")  # Add spacing between items
            if status != "complete":
                lines.extend(self._literal_payload(item))
            return lines, status, fallback_reason
        except Exception as e:
            # Rendering error - fallback to safe display
            self._add_warning(
                item.knowledge_id,
                "malformed_payload",
                f"Rendering error: {str(e)}"
            )
            lines = [
                f"*[Rendering error for {item.primary_format}]*",
                "",
                self._format_provenance(item),
                ""
            ]
            lines.extend(self._literal_payload(item))
            return lines, "fallback", f"Rendering error: {str(e)}"
    
    def _literal_payload(self,item):
        import json,re
        text=json.dumps(item.format_content,ensure_ascii=False,indent=2)
        fence='`'*max(3,1+max((len(m.group()) for m in re.finditer(r'`+',text)),default=0))
        return ['Original presentation data (fallback):',fence+'json',text,fence,'']

    def _render_standard_text(self, item: AssembledItem) -> Tuple[List[str], str, Optional[str]]:
        """Render STANDARD_TEXT format"""
        content = item.format_content.get("content", "")
        
        if not content:
            self._add_warning(item.knowledge_id, "empty_content", "Empty content field")
            return [
                "*[No content available]*",
                "",
                self._format_provenance(item)
            ], "partial", "Empty content"
        
        # Escape markdown (preserve basic structure)
        escaped_content = self._escape_markdown(content, preserve_basic=True)
        
        lines = [
            escaped_content,
            "",
            self._format_provenance(item)
        ]
        
        return lines, "complete", None
    
    def _render_definition_box(self, item: AssembledItem) -> Tuple[List[str], str, Optional[str]]:
        """Render DEFINITION_BOX format"""
        term = item.format_content.get("term", "")
        definition = item.format_content.get("definition", "")
        context = item.format_content.get("context")
        
        if not term or not definition:
            self._add_warning(item.knowledge_id, "missing_field", "Missing term or definition")
            # Fallback to text
            text = f"{term}: {definition}" if term and definition else term or definition or "No definition"
            return [
                text,
                "",
                self._format_provenance(item)
            ], "partial", "Missing term or definition"
        
        lines = [
            f"### {self._escape_markdown(term)}",
            "",
            self._escape_markdown(definition, preserve_basic=True)
        ]
        
        if context:
            lines.append("")
            lines.append(f"*Context: {self._escape_markdown(context)}*")
        
        lines.append("")
        lines.append(self._format_provenance(item))
        
        return lines, "complete", None
    
    def _render_example_callout(self, item: AssembledItem) -> Tuple[List[str], str, Optional[str]]:
        """Render EXAMPLE_CALLOUT format"""
        exemplifies = item.format_content.get("exemplifies", "")
        example_text = item.format_content.get("example_text", "")
        
        if not exemplifies or not example_text:
            self._add_warning(item.knowledge_id, "missing_field", "Missing exemplifies or example_text")
            text = example_text or exemplifies or "No example available"
            return [
                text,
                "",
                self._format_provenance(item)
            ], "partial", "Missing required fields"
        
        lines = [
            f"> **Example: {self._escape_markdown(exemplifies)}**",
            "> ",
            f"> {self._escape_markdown(example_text, preserve_basic=True)}",
            "",
            self._format_provenance(item)
        ]
        
        return lines, "complete", None
    
    def _render_flowchart(self, item: AssembledItem) -> Tuple[List[str], str, Optional[str]]:
        """Render FLOWCHART format using Mermaid"""
        steps = item.format_content.get("steps", [])
        procedure_name = item.format_content.get("procedure_name")
        
        if not steps or len(steps) == 0:
            self._add_warning(item.knowledge_id, "missing_field", "No steps for flowchart")
            return [
                "*[Flowchart: insufficient data]*",
                "",
                self._format_provenance(item)
            ], "fallback", "No steps"
        
        if len(steps) == 1:
            # Single step - render as text
            return [
                f"**{procedure_name or 'Procedure'}:**",
                "",
                f"- {self._escape_markdown(steps[0])}",
                "",
                self._format_provenance(item)
            ], "partial", "Single step (text fallback)"
        
        # Generate Mermaid flowchart
        lines = []
        if procedure_name:
            lines.append(f"#### Flowchart: {self._escape_markdown(procedure_name)}")
            lines.append("")
        else:
            lines.append("#### Flowchart")
            lines.append("")
        
        lines.append("```mermaid")
        lines.append("flowchart TD")
        
        # Generate nodes
        for i, step in enumerate(steps):
            node_id = f"    N{i}"  # A, B, C, ...
            # Clean step text for mermaid (remove special chars)
            clean_step = self._clean_for_mermaid(step)
            lines.append(f"{node_id}[{clean_step}]")
        
        # Generate edges
        for i in range(len(steps) - 1):
            lines.append(f"    N{i} --> N{i+1}")
        
        lines.append("```")
        lines.append("")
        lines.append(self._format_provenance(item))
        
        return lines, "complete", None
    
    def _render_timeline(self, item: AssembledItem) -> Tuple[List[str], str, Optional[str]]:
        """Render TIMELINE format"""
        events = item.format_content.get("events", [])
        title = item.format_content.get("title")
        
        if not events or len(events) == 0:
            self._add_warning(item.knowledge_id, "missing_field", "No events for timeline")
            return [
                "*[Timeline: no events]*",
                "",
                self._format_provenance(item)
            ], "fallback", "No events"
        
        lines = []
        if title:
            lines.append(f"#### Timeline: {self._escape_markdown(title)}")
        else:
            lines.append("#### Timeline")
        lines.append("")
        
        # Render events as ordered list
        for i, event in enumerate(events, 1):
            if isinstance(event, dict):
                time = event.get("time", f"Event {i}")
                event_text = event.get("event", "")
            else:
                time = f"Event {i}"
                event_text = str(event)
            
            lines.append(f"{i}. **{self._escape_markdown(time)}**: {self._escape_markdown(event_text, preserve_basic=True)}")
        
        lines.append("")
        lines.append(self._format_provenance(item))
        
        return lines, "complete", None
    
    def _render_cause_effect(self, item: AssembledItem) -> Tuple[List[str], str, Optional[str]]:
        """Render CAUSE_EFFECT_DIAGRAM format using Mermaid"""
        cause = item.format_content.get("cause", "")
        effect = item.format_content.get("effect", "")
        mechanism = item.format_content.get("mechanism", "")
        
        if not cause and not effect:
            self._add_warning(item.knowledge_id, "missing_field", "Missing cause and effect")
            # Fallback to mechanism text
            if mechanism:
                return [
                    self._escape_markdown(mechanism, preserve_basic=True),
                    "",
                    self._format_provenance(item)
                ], "partial", "Missing cause/effect"
            else:
                return [
                    "*[Cause-effect: insufficient data]*",
                    "",
                    self._format_provenance(item)
                ], "fallback", "Missing all fields"
        
        lines = [
            "#### Cause and Effect",
            "",
            "```mermaid",
            "flowchart LR"
        ]
        
        # Clean text for mermaid
        clean_cause = self._clean_for_mermaid(cause) if cause else "Unknown cause"
        clean_effect = self._clean_for_mermaid(effect) if effect else "Unknown effect"
        
        if mechanism and mechanism != cause and mechanism != effect:
            clean_mechanism = self._clean_for_mermaid(mechanism[:30] + "..." if len(mechanism) > 30 else mechanism)
            lines.append(f"    A[{clean_cause}] -->|{clean_mechanism}| B[{clean_effect}]")
        else:
            lines.append(f"    A[{clean_cause}] --> B[{clean_effect}]")
        
        lines.append("```")
        lines.append("")
        lines.append(self._format_provenance(item))
        
        return lines, "complete", None
    
    def _render_hierarchy_tree(self, item: AssembledItem) -> Tuple[List[str], str, Optional[str]]:
        """Render HIERARCHY_TREE format"""
        root = item.format_content.get("root", "")
        children = item.format_content.get("children", [])
        
        if not root:
            self._add_warning(item.knowledge_id, "missing_field", "Missing root node")
            return [
                "*[Hierarchy: no root node]*",
                "",
                self._format_provenance(item)
            ], "fallback", "Missing root"
        
        lines = [
            f"#### Hierarchy: {self._escape_markdown(root)}",
            "",
            f"- {self._escape_markdown(root)}"
        ]
        
        # Render children recursively
        if children and len(children) > 0:
            for child in children:
                child_lines = self._render_hierarchy_node(child, indent=1)
                lines.extend(child_lines)
        
        lines.append("")
        lines.append(self._format_provenance(item))
        
        return lines, "complete", None
    
    def _render_hierarchy_node(self, node, indent: int) -> List[str]:
        """Render a hierarchy node recursively"""
        lines = []
        indent_str = "  " * indent
        
        if isinstance(node, dict):
            name = node.get("name", "")
            children = node.get("children", [])
            
            if name:
                lines.append(f"{indent_str}- {self._escape_markdown(name)}")
                
                for child in children:
                    child_lines = self._render_hierarchy_node(child, indent + 1)
                    lines.extend(child_lines)
        else:
            lines.append(f"{indent_str}- {self._escape_markdown(str(node))}")
        
        return lines
    
    def _render_comparison_table(self, item: AssembledItem) -> Tuple[List[str], str, Optional[str]]:
        """Render COMPARISON_TABLE format"""
        items = item.format_content.get("items", [])
        dimensions = item.format_content.get("dimensions", [])
        values = item.format_content.get("values", {})
        
        if not items or not dimensions or len(items) < 2:
            self._add_warning(item.knowledge_id, "missing_field", "Insufficient comparison data")
            # Fallback to text list
            lines = ["**Comparison:**", ""]
            if items:
                for comp_item in items:
                    lines.append(f"- {self._escape_markdown(str(comp_item))}")
            else:
                lines.append("*[No comparison data]*")
            lines.append("")
            lines.append(self._format_provenance(item))
            return lines, "partial", "Insufficient comparison data"
        
        lines = [
            "#### Comparison",
            ""
        ]
        
        # Build table header
        header = "| Dimension | " + " | ".join(self._escape_markdown(str(i)) for i in items) + " |"
        separator = "|" + "---|" * (len(items) + 1)
        
        lines.append(header)
        lines.append(separator)
        
        # Build table rows
        for dim in dimensions:
            row = f"| {self._escape_markdown(str(dim))} |"
            for comp_item in items:
                value = values.get(str(comp_item), {}).get(str(dim), "")
                row += f" {self._escape_markdown(str(value))} |"
            lines.append(row)
        
        lines.append("")
        lines.append(self._format_provenance(item))
        
        return lines, "complete", None
    
    def _render_formula_display(self, item: AssembledItem) -> Tuple[List[str], str, Optional[str]]:
        """Render FORMULA_DISPLAY format"""
        formula = item.format_content.get("formula", "")
        variables = item.format_content.get("variables")
        conditions = item.format_content.get("conditions")
        
        if not formula:
            self._add_warning(item.knowledge_id, "missing_field", "Missing formula")
            return [
                "*[Formula: no formula provided]*",
                "",
                self._format_provenance(item)
            ], "fallback", "Missing formula"
        
        lines = [
            "#### Formula",
            "",
            '`'*max(3,1+max((len(m.group()) for m in __import__('re').finditer(r'`+',formula)),default=0)),
            formula,
            '`'*max(3,1+max((len(m.group()) for m in __import__('re').finditer(r'`+',formula)),default=0))
        ]
        
        if variables:
            lines.append("")
            lines.append("**Symbols and operands:**")
            for var, desc in variables.items():
                lines.append(f"- `{var}`: {self._escape_markdown(desc)}")
        
        if conditions:
            lines.append("")
            lines.append(f"*Conditions: {self._escape_markdown(conditions)}*")
        
        lines.append("")
        lines.append(self._format_provenance(item))
        
        return lines, "complete", None
    
    def _format_provenance(self, item: AssembledItem) -> str:
        """Format provenance information"""
        sources = ", ".join(item.source_unit_ids) if item.source_unit_ids else "No sources"
        return f"*[Knowledge ID: {item.knowledge_id} | Sources: {sources}]*"
    
    def _escape_markdown(self, text: str, preserve_basic: bool = False) -> str:
        """
        Escape markdown special characters.
        
        Args:
            text: Text to escape
            preserve_basic: If True, only escape brackets (for preserving readability)
        """
        if not text:
            return ""
        
        import html
        text=html.escape(text,quote=False)
        text=text.replace('```', '\\`\\`\\`')
        if preserve_basic:
            # Only escape brackets to prevent link/reference breaking
            return text.replace('[', '\\[').replace(']', '\\]')
        else:
            # Full escape
            text = text.replace('\\', '\\\\')
            text = text.replace('*', '\\*')
            text = text.replace('_', '\\_')
            text = text.replace('[', '\\[')
            text = text.replace(']', '\\]')
            text = text.replace('#', '\\#')
            text = text.replace('|', '\\|').replace('\n',' ')
            return text
    
    def _clean_for_mermaid(self, text: str) -> str:
        """Clean text for use in Mermaid diagrams"""
        if not text:
            return ""
        
        # Quoted labels with numeric entities preserve characters without allowing
        # source text to terminate nodes, insert edges or close a Markdown fence.
        encoded=''.join(ch if ch.isalnum() or ch in ' .,:;+-=_' else f'#{ord(ch)};' for ch in text)
        return '"'+encoded+'"'

    def _add_warning(self, knowledge_id: str, warning_type: str, message: str):
        """Add a rendering warning"""
        warning = RenderWarning(
            item_id=knowledge_id,
            warning_type=warning_type,
            message=message
        )
        self.warnings.append(warning)
    
    def _print_summary(self, manifest: RenderManifest):
        """Print rendering summary"""
        print(f"Markdown length: {manifest.markdown_length} characters")
        print(f"Total lines: {manifest.total_lines}")
        print(f"Items rendered: {manifest.total_items}")
        print(f"  Complete: {manifest.items_complete}")
        print(f"  Partial: {manifest.items_partial}")
        print(f"  Fallback: {manifest.items_fallback}")
        print(f"Warnings: {len(manifest.warnings)}")
