"""
Note Assembler layer.

Organizes selected representations into coherent, readable sections.
"""

from app.assembly.models import (
    AssembledItem,
    AssembledSection,
    AssemblyMetadata,
    AssemblyStatistics,
    AssembledNotesDocument
)
from app.assembly.assembler import NoteAssembler

__all__ = [
    'AssembledItem',
    'AssembledSection',
    'AssemblyMetadata',
    'AssemblyStatistics',
    'AssembledNotesDocument',
    'NoteAssembler'
]
