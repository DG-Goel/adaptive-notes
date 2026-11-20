"""
Rendering module for converting assembled notes to readable formats.

This module provides the Renderer v1 layer that converts AssembledNotesDocument
into Markdown with full provenance tracking.
"""

from app.rendering.models import (
    RenderedItem,
    RenderWarning,
    RenderManifest,
    RenderedDocument,
)
from app.rendering.renderer import MarkdownRenderer

__all__ = [
    "RenderedItem",
    "RenderWarning",
    "RenderManifest",
    "RenderedDocument",
    "MarkdownRenderer",
]
