"""Lossless structural indexing of existing Markdown and JSON note artifacts."""
from dataclasses import dataclass, replace
from bisect import bisect_right
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Mapping

from .contracts import Evidence, KnowledgeItem, SourceSnapshot

INDEX_VERSION = 'noetra-source-index-v1'
ESTIMATOR = 'utf8-bytes-upper-bound-v1'


def digest(content: bytes) -> str:
    return sha256(content).hexdigest()


@dataclass(frozen=True)
class SourceBlock:
    id: str
    position: int
    text: str
    source_artifact_id: str
    source_start: int
    source_end: int
    section_path: tuple[str, ...]
    type: str
    parent_id: str | None
    token_count: int
    content_hash: str
    token_count_kind: str = 'estimated'
    token_estimator: str = ESTIMATOR
    references: tuple[str, ...] = ()
    timestamps: tuple[str, ...] = ()  # Exact textual/JSON evidence, no inferred times.
    locator: str = ''
    cohesion_id: str = ''
    split_boundaries: tuple[int, ...] = ()  # Absolute source character positions.


@dataclass(frozen=True)
class OversizedBlock:
    block_id: str
    token_estimate: int
    budget: int
    status: str = 'unsupported_atomic_block'


@dataclass(frozen=True)
class SourceIndex:
    snapshot: SourceSnapshot
    text: str
    blocks: tuple[SourceBlock, ...]  # Original structural blocks.
    units: tuple[SourceBlock, ...]   # Original blocks or lossless subdivision leaves.
    subdivisions: tuple[tuple[str, tuple[str, ...]], ...] = ()
    oversized: tuple[OversizedBlock, ...] = ()
    version: str = INDEX_VERSION

    @property
    def fingerprint(self):
        data = [self.version, self.snapshot.source_id, self.snapshot.sha256,
                [(b.id, b.source_start, b.source_end) for b in self.units]]
        return digest(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def reconstruct(self):
        return ''.join(b.text for b in self.units)

    def validate(self):
        if digest(self.snapshot.content) != self.snapshot.sha256:
            raise ValueError('Source snapshot hash mismatch')
        if self.text.encode('utf-8') != self.snapshot.content:
            raise ValueError('Source encoding mismatch')
        for sequence in (self.blocks, self.units):
            cursor = 0
            identifiers = set()
            for position, block in enumerate(sequence):
                if block.position != position or block.source_start != cursor or block.id in identifiers:
                    raise ValueError('Source index order or coverage mismatch')
                if block.source_end <= cursor or block.text != self.text[cursor:block.source_end]:
                    raise ValueError('Source index offset mismatch')
                if block.content_hash != digest(block.text.encode('utf-8')):
                    raise ValueError('Source block hash mismatch')
                if block.token_count != len(block.text.encode('utf-8')) or block.source_artifact_id != self.snapshot.source_id:
                    raise ValueError('Source block metadata mismatch')
                identifiers.add(block.id)
                cursor = block.source_end
            if cursor != len(self.text):
                raise ValueError('Source index has missing content')
        starts = [b.source_start for b in self.blocks]
        children = {}
        for unit in self.units:
            parent = self.blocks[bisect_right(starts,unit.source_start)-1]
            if unit.source_end > parent.source_end:
                raise ValueError('Reading unit crosses original block boundaries')
            if unit.id != parent.id:
                if unit.parent_id != parent.id:
                    raise ValueError('Subdivision lost original parent relationship')
                children.setdefault(parent.id,[]).append(unit.id)
            elif (unit.source_start,unit.source_end) != (parent.source_start,parent.source_end):
                raise ValueError('Original source block range changed')
        if {key:tuple(value) for key,value in children.items()} != dict(self.subdivisions):
            raise ValueError('Subdivision ledger does not match reading units')
        return self


class FileSourceReader:
    """Explicitly allowlisted, read-only SourceReader implementation."""
    def __init__(self, artifacts: Mapping[str, Path]):
        self._artifacts = {key: Path(path).resolve() for key, path in artifacts.items()}

    def snapshot(self, source_id: str) -> SourceSnapshot:
        path = self._artifacts[source_id]
        if path.suffix.lower() not in {'.md','.markdown','.txt','.json'}:
            raise ValueError('Unsupported note artifact extension; expected Markdown, text or JSON')
        content = path.read_bytes()
        media = 'application/json' if path.suffix.lower() == '.json' else 'text/markdown'
        return SourceSnapshot(source_id, digest(content), content, media)


def _block(snapshot, text, start, end, position, kind, sections=(), parent=None,
           references=(), timestamps=(), locator='', boundaries=()):
    content = text[start:end]
    identity = f'{INDEX_VERSION}\0{snapshot.source_id}\0{snapshot.sha256}\0{start}:{end}'
    identifier = 'B' + digest(identity.encode('utf-8'))[:24]
    return SourceBlock(identifier, position, content, snapshot.source_id, start, end,
                       tuple(sections), kind, parent, len(content.encode('utf-8')),
                       digest(content.encode('utf-8')), references=tuple(references),
                       timestamps=tuple(timestamps), locator=locator,
                       split_boundaries=tuple(boundaries))


HEADING = re.compile(r'^ {0,3}(#{1,6})\s+(.+?)\s*#*\s*$')
FENCE = re.compile(r'^ {0,3}(`{3,}|~{3,})(.*)$')
LIST = re.compile(r'^( *)(?:[-+*]|\d+[.)])\s+')
ANCHOR = re.compile(r'\*\[Knowledge ID:\s*([^|\]]+)\|\s*Sources:\s*([^\]]+)\]\*')
TIME = re.compile(r'(?<!\w)(?:\d+:)?\d{1,2}:\d{2}(?:\.\d+)?(?:\s*[–-]\s*(?:\d+:)?\d{1,2}:\d{2}(?:\.\d+)?)?|\b\d+(?:\.\d+)?[–-]\d+(?:\.\d+)?s\b')


def _kind(line):
    clean = line.strip()
    if HEADING.match(line):
        return 'heading'
    if FENCE.match(line):
        language = FENCE.match(line)[2].strip().lower()
        return 'diagram' if language in {'mermaid', 'dot', 'graphviz'} else 'code'
    if clean.startswith(('$$', r'\[',r'\begin{equation}',r'\begin{align}',r'\begin{aligned}')):
        return 'math'
    if LIST.match(line):
        return 'numbered_list' if re.match(r'^\s*\d+[.)]', line) else 'bullet_list'
    if clean.startswith('|') or clean.lower().startswith('<table'):
        return 'table'
    if clean.startswith(('![', '<svg', '<img')):
        return 'diagram'
    if re.match(r'^(?:\*\*|__)?(?:Definition|定义|परिभाषा)\b', clean, re.I):
        return 'definition'
    if re.match(r'^(?:\*\*|__)?(?:Example|उदाहरण|例子)\b', clean, re.I):
        return 'example'
    if ANCHOR.search(line) or clean.startswith('*Source:'):
        return 'source_reference'
    return 'paragraph'


def _markdown(snapshot, text):
    lines = text.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    blocks = []
    headings = []  # (level, title, block ID).
    i = 0
    while i < len(lines):
        start = i
        kind = _kind(lines[i])
        setext = (i+1 < len(lines) and lines[i].strip() and kind=='paragraph'
                  and re.fullmatch(r' {0,3}(?:=+|-+)\s*',lines[i+1]))
        if setext:
            kind = 'heading'
        if kind == 'paragraph' and i+1 < len(lines) and '|' in lines[i] and re.fullmatch(
                r'\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*',lines[i+1]):
            kind = 'table'
        if not lines[i].strip():
            kind = 'whitespace'
            i += 1
        elif kind in {'code', 'diagram'} and FENCE.match(lines[i]):
            fence = FENCE.match(lines[i])[1]
            i += 1
            while i < len(lines):
                closing = re.match(r'^ {0,3}(' + re.escape(fence[0]) + r'{'+str(len(fence))+r',})\s*$', lines[i])
                i += 1
                if closing:
                    break
        elif kind in {'table','diagram'} and re.match(r'^\s*<(?:table|svg)\b',lines[i],re.I):
            tag = 'table' if kind=='table' else 'svg'
            while i < len(lines):
                found = '</'+tag+'>' in lines[i].lower()
                i += 1
                if found:
                    break
        elif kind == 'math':
            environment = re.match(r'\s*\\begin\{([^}]+)\}',lines[i])
            closing = (r'\end{'+environment[1]+'}') if environment else '$$' if lines[i].strip().startswith('$$') else r'\]'
            inline_closed = closing == '$$' and lines[i].strip().count('$$') >= 2
            inline_closed |= closing != '$$' and closing in lines[i]
            i += 1
            while not inline_closed and i < len(lines):
                found = closing in lines[i]
                i += 1
                if found:
                    break
        elif kind in {'bullet_list', 'numbered_list'}:
            i += 1
            while i < len(lines):
                line = lines[i]
                if not line.strip():
                    next_i = i + 1
                    while next_i < len(lines) and not lines[next_i].strip():
                        next_i += 1
                    if next_i < len(lines) and (LIST.match(lines[next_i]) or lines[next_i].startswith(('  ', '\t'))):
                        i = next_i
                        continue
                    break
                if LIST.match(line) or line.startswith(('  ', '\t')) or _kind(line) in {'paragraph','definition','example'}:
                    i += 1
                else:
                    break
        elif kind == 'heading':
            i += 2 if setext else 1
        else:
            i += 1
            while i < len(lines) and lines[i].strip():
                next_kind = _kind(lines[i])
                if kind == 'table' and '|' not in lines[i]:
                    break
                if kind != 'table' and next_kind in {'heading','code','math','table','bullet_list','numbered_list','source_reference','diagram'}:
                    break
                i += 1
        while i < len(lines) and not lines[i].strip():
            i += 1
        if kind == 'heading':
            match = HEADING.match(lines[start])
            level, title = (len(match[1]), match[2]) if match else (1 if lines[start+1].strip().startswith('=') else 2,lines[start].strip())
            while headings and headings[-1][0] >= level:
                headings.pop()
            path = tuple(h[1] for h in headings) + (title,)
        else:
            path = tuple(h[1] for h in headings)
        content = text[offsets[start]:offsets[i]]
        anchors = list(ANCHOR.finditer(content))
        refs = [v.strip() for m in anchors for v in (m[1].strip(), *m[2].split(','))]
        if kind == 'source_reference' and not refs:
            refs = [content.strip()]
        boundaries = ()
        if kind in {'bullet_list','numbered_list'}:
            items = [(j, LIST.match(lines[j])) for j in range(start, i) if LIST.match(lines[j])]
            indent = min(len(m[1]) for _, m in items)
            boundaries = tuple(offsets[j] for j,m in items[1:] if len(m[1]) == indent)
        block = _block(snapshot, text, offsets[start], offsets[i], len(blocks), kind,
                       path, headings[-1][2] if headings else None, refs,
                       TIME.findall(content), boundaries=boundaries)
        blocks.append(block)
        if kind == 'heading':
            headings.append((level, title, block.id))
    # Explicit syntax/adjacency cohesion only; no semantic interpretation.
    groups = list(range(len(blocks)))
    for j, b in enumerate(blocks):
        if j == 0:
            continue
        previous = blocks[j-1]
        join = previous.type == 'heading' or b.type == 'source_reference'
        join |= b.type in {'code','math','example'} and previous.type in {'paragraph','definition'}
        join |= previous.type in {'code','math'} and b.type == 'paragraph'
        join |= b.type == 'paragraph' and bool(re.match(r'^\s*(?:Where\b|Let\b|Unless\b|Except\b|However\b|If\b|Note:)', b.text, re.I))
        if join:
            groups[j] = groups[j-1]
    result = [replace(b,cohesion_id=blocks[groups[j]].id) for j,b in enumerate(blocks)]
    # A trailing NOETRA provenance anchor describes the preceding cohesive unit.
    # Copy only explicit metadata; retain original content and offsets verbatim.
    for j,b in enumerate(result):
        if b.type == 'source_reference':
            k = j-1
            while k >= 0 and result[k].cohesion_id == b.cohesion_id:
                prior = result[k]
                if prior.type != 'source_reference':
                    result[k] = replace(prior,references=tuple(dict.fromkeys(prior.references+b.references)),
                                       timestamps=tuple(dict.fromkeys(prior.timestamps+b.timestamps)))
                k -= 1
    return tuple(result)


def _json_spans(text):
    """Parse JSON with exact value spans; retain every envelope/unknown field."""
    decoder = json.JSONDecoder()
    nodes = {}
    def whitespace(i):
        while i < len(text) and text[i] in ' \t\r\n':
            i += 1
        return i
    def parse(i, path):
        i = whitespace(i)
        start = i
        if text[i] == '{':
            value = {}
            i = whitespace(i+1)
            while text[i] != '}':
                key, i = decoder.raw_decode(text, i)
                if key in value:
                    raise ValueError('Duplicate JSON keys are unsupported')
                i = whitespace(i)
                if text[i] != ':':
                    raise ValueError('Invalid JSON object')
                child, i = parse(i+1, path + (key,))
                value[key] = child
                i = whitespace(i)
                if text[i] != ',':
                    break
                i = whitespace(i+1)
            if text[i] != '}':
                raise ValueError('Invalid JSON object ending')
            i += 1
        elif text[i] == '[':
            value = []
            i = whitespace(i+1)
            while text[i] != ']':
                child, i = parse(i, path + (len(value),))
                value.append(child)
                i = whitespace(i)
                if text[i] != ',':
                    break
                i = whitespace(i+1)
            if text[i] != ']':
                raise ValueError('Invalid JSON array ending')
            i += 1
        else:
            value, i = decoder.raw_decode(text, i)
        nodes[path] = (start, i, value)
        return value, i
    # Validate strict syntax first (including trailing commas); then obtain spans.
    json.loads(text)
    try:
        value, end = parse(0, ())
    except (IndexError, RecursionError):
        raise ValueError('Unsupported JSON nesting or incomplete structure') from None
    if whitespace(end) != len(text):
        raise ValueError('Trailing JSON content')
    return value, nodes


def _json_blocks(snapshot, text):
    if not text.strip():
        raise ValueError('Empty JSON artifact; use Markdown for empty text')
    value, nodes = _json_spans(text)
    targets = []
    if isinstance(value, list) and all(isinstance(row, dict) and 'note_id' in row and 'text' in row for row in value):
        targets = [((i,), (), 'ordered_note') for i in range(len(value))]
    elif isinstance(value, dict) and isinstance(value.get('sections'), list):
        stack = []
        for i, section in enumerate(value['sections']):
            if not isinstance(section, dict) or not isinstance(section.get('blocks'), list):
                raise ValueError('Unsupported NoteDocument section')
            level = section.get('level', 1)
            if type(level) is not int or level < 1:
                raise ValueError('Invalid NoteDocument section level')
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, str(section.get('title', ''))))
            path = tuple(title for _, title in stack)
            targets += [(('sections',i,'blocks',j), path, 'structured_block') for j in range(len(section['blocks']))]
    else:
        raise ValueError('Unsupported JSON notes format: expected ordered_notes or NoteDocument sections')
    blocks = []
    cursor = 0
    for pointer, path, fallback in targets:
        start, end, item = nodes[pointer]
        if not isinstance(item, dict):
            raise ValueError('Structured note blocks must be objects')
        if start > cursor:
            envelope = _block(snapshot,text,cursor,start,len(blocks),'json_structure',path,
                              locator='/'+'/'.join(map(str,pointer)))
            blocks.append(envelope)
        references = [str(item[k]) for k in ('note_id','id','sourceBlockId') if k in item]
        for key in ('source_segment_ids','source_ids'):
            if key in item:
                references.append(json.dumps(item[key],ensure_ascii=False))
        timestamps = [json.dumps(item[k], ensure_ascii=False) for k in ('timing','startSeconds','endSeconds') if k in item]
        if pointer and pointer[0] == 'sections':
            section = value['sections'][pointer[1]]
            timestamps += [json.dumps({k: section[k]},ensure_ascii=False) for k in ('startSeconds','endSeconds') if k in section]
        block = _block(snapshot,text,start,end,len(blocks),str(item.get('type',fallback)),path,
                       parent=blocks[-1].id if pointer and pointer[0]=='sections' and blocks else None,
                       references=references,timestamps=timestamps,
                       locator='/'+'/'.join(map(str,pointer)))
        blocks.append(block)
        cursor = end
    if cursor < len(text):
        blocks.append(_block(snapshot,text,cursor,len(text),len(blocks),'json_structure'))
    # Associate structural prefix/suffix with adjacent content for window admission.
    for j, b in enumerate(blocks):
        group = blocks[j-1].cohesion_id if j and b.type == 'json_structure' and j == len(blocks)-1 else b.id
        if j and blocks[j-1].type == 'json_structure':
            group = blocks[j-1].cohesion_id
        blocks[j] = replace(b, cohesion_id=group or b.id)
    return tuple(blocks)


def build_index(snapshot: SourceSnapshot) -> SourceIndex:
    if digest(snapshot.content) != snapshot.sha256:
        raise ValueError('Source snapshot hash mismatch')
    try:
        text = snapshot.content.decode('utf-8')
    except UnicodeDecodeError:
        raise ValueError('Only lossless UTF-8 note artifacts are supported') from None
    if snapshot.media_type in {'text/markdown','text/plain'}:
        blocks = _markdown(snapshot, text)
    elif snapshot.media_type == 'application/json':
        blocks = _json_blocks(snapshot,text)
    else:
        raise ValueError('Unsupported source media type')
    return SourceIndex(snapshot,text,blocks,blocks).validate()


def subdivide(index: SourceIndex, max_tokens: int) -> SourceIndex:
    """Split oversized lists at complete top-level items; other atoms fail closed."""
    if type(max_tokens) is not int or max_tokens <= 0:
        raise ValueError('Subdivision budget must be positive')
    units, subdivisions, oversized = [], [], []
    for parent in index.blocks:
        children = []
        if parent.token_count > max_tokens and parent.split_boundaries:
            boundaries = [parent.source_start, *parent.split_boundaries, parent.source_end]
            start = boundaries[0]
            for left, right in zip(boundaries, boundaries[1:]):
                if len(index.text[start:right].encode('utf-8')) > max_tokens and left > start:
                    children.append(_block(index.snapshot,index.text,start,left,0,parent.type,
                        parent.section_path,parent.id,parent.references,parent.timestamps,parent.locator))
                    start = left
            children.append(_block(index.snapshot,index.text,start,parent.source_end,0,parent.type,
                parent.section_path,parent.id,parent.references,parent.timestamps,parent.locator))
        if len(children) > 1:
            subdivisions.append((parent.id, tuple(c.id for c in children)))
        else:
            children = [parent]
        for child_number,child in enumerate(children):
            # Subdivision is an explicit structural boundary, never a semantic decision.
            cohesion = (parent.cohesion_id if child_number==0 else child.id) if len(children)>1 else child.cohesion_id
            child = replace(child,position=len(units),cohesion_id=cohesion)
            units.append(child)
            if child.token_count > max_tokens:
                oversized.append(OversizedBlock(child.id,child.token_count,max_tokens))
    return replace(index,units=tuple(units),subdivisions=tuple(subdivisions),oversized=tuple(oversized)).validate()


class StructuralSourceIndexer:
    """Phase 1 SourceIndexer-compatible adapter; richer metadata lives in build_index."""
    def index(self, sources: tuple[SourceSnapshot, ...]) -> tuple[KnowledgeItem, ...]:
        return tuple(KnowledgeItem(b.id,b.text,(Evidence(source.source_id,source.sha256,
                     b.source_start,b.source_end,b.text),))
                     for source in sources for b in build_index(source).blocks)
