"""Sequential range accounting; only explicit validated decisions advance source."""
from dataclasses import asdict, dataclass, replace
import json
import math

from .source_index import SourceIndex, digest, subdivide
from .token_budget import RequestParts, TokenBudgetManager, serialize_request


@dataclass(frozen=True)
class ReadingWindow:
    id: str
    previous: tuple
    source: tuple
    lookahead: tuple
    payload: str
    budget: object
    cursor: int
    end: int  # Exclusive commit-eligible range boundary.
    final_document_window: bool


@dataclass(frozen=True)
class WindowResult:
    status: str
    window: ReadingWindow | None = None
    block_ids: tuple[str, ...] = ()
    reason: str = ''


@dataclass(frozen=True)
class BoundaryDecision:
    window_id: str
    commit_through_id: str | None = None
    pending_from_id: str | None = None


@dataclass(frozen=True)
class ReadingState:
    cursor: int = 0
    committed_ranges: tuple[tuple[int,int], ...] = ()
    pending_range: tuple[int,int] | None = None
    no_progress: int = 0
    repeated_pending: int = 0
    last_pending_boundary: int | None = None
    target_source_tokens: int = 10000
    revision: int = 0
    status: str = 'ready'


class InvalidBoundary(ValueError):
    pass


def _groups(units, start):
    i = start
    while i < len(units):
        end = i+1
        while end < len(units) and units[end].cohesion_id == units[i].cohesion_id:
            end += 1
        yield units[i:end]
        i = end


class ReadingSession:
    def __init__(self,index: SourceIndex,budget: TokenBudgetManager,
                 parts: RequestParts | None = None,*,state: ReadingState | None = None):
        self.budget = budget
        self.parts = parts or RequestParts()
        capacity = budget.source_capacity(index,self.parts)
        self.index = subdivide(index,max(1,capacity))
        self.state = state or ReadingState(target_source_tokens=budget.config.target_source_tokens,
                                           status='complete' if not self.index.units else 'ready')
        self._active = None
        self._checkpoint_id = None
        self._validate_state(self.state)

    @property
    def configuration_hash(self):
        public = dict(budget=self.budget.public_config(),request_parts=asdict(self.parts))
        return digest(json.dumps(public,sort_keys=True,ensure_ascii=False).encode('utf-8'))

    def _validate_state(self,state):
        size = len(self.index.units)
        if type(state.cursor) is not int or not 0 <= state.cursor <= size:
            raise ValueError('Invalid processing cursor')
        end = 0
        for left,right in state.committed_ranges:
            if type(left) is not int or type(right) is not int or left != end or not left < right <= size:
                raise ValueError('Committed ranges overlap, skip content or are invalid')
            end = right
        if end != state.cursor:
            raise ValueError('Cursor is not backed by validated committed ranges')
        if state.pending_range is not None:
            left,right = state.pending_range
            if left != state.cursor or not left < right <= size:
                raise ValueError('Invalid pending source range')
        for value in (state.no_progress,state.repeated_pending,state.revision):
            if type(value) is not int or value < 0:
                raise ValueError('Invalid reading counter')
        if not self.budget.config.target_source_tokens <= state.target_source_tokens <= self.budget.config.max_source_tokens:
            raise ValueError('Checkpoint source target is outside configured bounds')
        if state.last_pending_boundary is not None and state.last_pending_boundary != state.cursor:
            raise ValueError('Invalid last pending boundary')
        statuses = {'ready','pending','forced_boundary_required','oversized_concept','complete'}
        if state.status not in statuses or (state.status == 'complete') != (state.cursor == size):
            raise ValueError('Reading completion status does not match source coverage')

    def _construct(self,target):
        index,parts,budget = self.index,self.parts,self.budget
        units = index.units
        cursor = self.state.cursor
        if cursor == len(units):
            return WindowResult('complete')
        if budget.count(parts.previous_summary).value > budget.config.previous_context_tokens:
            return WindowResult('context_budget_exceeded',reason='Previous summary exceeds its explicit budget')
        previous = ()
        if not parts.previous_summary:
            for block in reversed(units[:cursor]):
                candidate = (block,)+previous
                if budget.count(''.join(b.text for b in candidate)).value > budget.config.previous_context_tokens:
                    break
                previous = candidate
        maximum = min(budget.config.max_source_tokens,budget.source_capacity(index,parts))
        source = ()
        for group in _groups(units,cursor):
            candidate = source+tuple(group)
            cost = budget.count(''.join(b.text for b in candidate)).value
            # One cohesive unit may grow beyond the initial target, up to the
            # verified ceiling. Later units wait for the next sequential window.
            if cost > maximum or (source and cost > target):
                if source:
                    break
                return WindowResult('oversized_concept' if len(group)>1 else 'unsupported_atomic_block',
                    block_ids=tuple(b.id for b in group),reason='A complete structural group exceeds the usable source budget')
            report = budget.check(index,parts,previous,candidate)
            if not report.fits and not source:
                # Read-only context yields priority to source; never truncate it.
                previous = ()
                report = budget.check(index,parts,previous,candidate)
            if not report.fits:
                if source:
                    break
                return WindowResult('oversized_concept' if len(group)>1 else 'unsupported_atomic_block',
                    block_ids=tuple(b.id for b in group),reason='Source plus serialization/framing exceeds effective request limits')
            source = candidate
        if not source:
            return WindowResult('budget_exhausted',reason='No commit-eligible content fits')
        end = cursor+len(source)
        lookahead = ()
        for group in _groups(units,end):
            candidate = lookahead+tuple(group)
            if budget.count(''.join(b.text for b in candidate)).value > budget.config.lookahead_tokens:
                break
            if not budget.check(index,parts,previous,source,candidate).fits:
                break
            lookahead = candidate
        if not lookahead and end < len(units) and budget.config.lookahead_tokens:
            # When full serialization leaves no room for C, demote the last
            # complete B group into C if possible. It remains uncommitted.
            tail_start = len(source)-1
            while tail_start > 0 and source[tail_start-1].cohesion_id == source[-1].cohesion_id:
                tail_start -= 1
            tail = source[tail_start:]
            if (tail_start > 0 and budget.count(''.join(b.text for b in tail)).value <= budget.config.lookahead_tokens
                    and budget.check(index,parts,previous,source[:tail_start],tail).fits):
                source,lookahead = source[:tail_start],tail
                end = cursor+len(source)
        payload = serialize_request(index,parts,previous,source,lookahead)
        report = budget.check(index,parts,previous,source,lookahead,payload=payload)
        identity = json.dumps([index.fingerprint,self.configuration_hash,asdict(self.state),payload],sort_keys=True,ensure_ascii=False)
        window = ReadingWindow('W'+digest(identity.encode('utf-8')),
            previous,source,lookahead,payload,report,cursor,end,end==len(units))
        reason = 'forward_lookahead_unavailable_within_budget' if end < len(units) and not lookahead and budget.config.lookahead_tokens else ''
        return WindowResult('ready',window,reason=reason)

    def next_window(self,*,allow_forced_boundary=False):
        if self.state.status in {'forced_boundary_required','oversized_concept'} and not allow_forced_boundary:
            return WindowResult(self.state.status,reason='Explicit boundary decision or changed configuration required; source retained')
        result = self._construct(self.state.target_source_tokens)
        self._active = result.window
        return result

    def apply(self,decision: BoundaryDecision):
        active = self._active
        if active is None or decision.window_id != active.id:
            raise InvalidBoundary('No matching active reading window')
        ids = [b.id for b in active.source]
        if decision.commit_through_id is None:
            end = self.state.cursor
        elif decision.commit_through_id in ids:
            end = self.state.cursor+ids.index(decision.commit_through_id)+1
        else:
            raise InvalidBoundary('Commit boundary must be in commit-eligible Region B')
        if decision.pending_from_id is not None:
            if end >= active.end or self.index.units[end].id != decision.pending_from_id:
                raise InvalidBoundary('Pending boundary must be the first uncommitted block in Region B')
        old = self.state
        if end > old.cursor:
            ranges = old.committed_ranges+((old.cursor,end),)
            candidate = ReadingState(end,ranges,(end,active.end) if end<active.end else None,
                target_source_tokens=self.budget.config.target_source_tokens,revision=old.revision+1,
                status='complete' if end==len(self.index.units) else 'pending' if end<active.end else 'ready')
        else:
            count = old.no_progress+1
            repeated = old.repeated_pending+1 if old.last_pending_boundary==old.cursor else 1
            target = min(self.budget.config.max_source_tokens,
                         max(old.target_source_tokens+1,math.ceil(old.target_source_tokens*self.budget.config.expansion_factor)))
            expanded = self._construct(target)
            can_expand = expanded.window is not None and expanded.window.end > active.end
            status = 'pending'
            if count >= self.budget.config.max_no_progress or not can_expand:
                status = 'forced_boundary_required' if active.final_document_window else 'oversized_concept'
            candidate = replace(old,pending_range=(old.cursor,active.end),no_progress=count,
                repeated_pending=repeated,last_pending_boundary=old.cursor,target_source_tokens=target,
                revision=old.revision+1,status=status)
        self._validate_state(candidate)
        self.state = candidate
        self._active = None
        return candidate

    def ledger(self):
        """Range coverage only; makes no semantic fact-coverage claim."""
        self._validate_state(self.state)
        units = self.index.units
        cursor = self.state.cursor
        active = self._active
        committed = units[:cursor]
        uncommitted = units[cursor:]
        root_status = []
        unit_cursor = 0
        for block in self.index.blocks:
            start = unit_cursor
            while unit_cursor < len(units) and units[unit_cursor].source_end <= block.source_end:
                unit_cursor += 1
            done = max(0,min(cursor,unit_cursor)-start)
            root_status.append((block.id,'committed' if done==unit_cursor-start else 'uncommitted' if done==0 else 'partially_committed'))
        uncommitted_ids = {b.id for b in uncommitted}
        return dict(total_original_blocks=len(self.index.blocks),total_reading_units=len(units),
            committed_source_blocks=tuple(b.id for b in committed),
            uncommitted_source_blocks=tuple(b.id for b in uncommitted),
            read_only_context_blocks=tuple(b.id for b in active.previous) if active else (),
            lookahead_blocks=tuple(b.id for b in active.lookahead) if active else (),
            cursor=cursor,committed_ranges=self.state.committed_ranges,pending_range=self.state.pending_range,
            original_block_status=tuple(root_status),safely_subdivided_blocks=self.index.subdivisions,
            unresolved_oversized_blocks=tuple(b for b in self.index.oversized
                if b.block_id in uncommitted_ids),complete=cursor==len(units))

    def preflight(self,*,final_payload=None,provider_metadata=None):
        if self._active is None:
            raise ValueError('Build a window before checking a final request')
        window = self._active
        return self.budget.preflight(self.index,self.parts,window.previous,window.source,window.lookahead,
            final_payload=window.payload if final_payload is None else final_payload,
            provider_metadata=provider_metadata)

    def restart(self):
        """Explicit fresh reading state; leaves the old session/checkpoints untouched."""
        return ReadingSession(self.index,self.budget,self.parts)

    def checkpoint_payload(self):
        self._validate_state(self.state)
        return dict(source_artifact_id=self.index.snapshot.source_id,source_sha256=self.index.snapshot.sha256,
                    source_index_version=self.index.version,index_fingerprint=self.index.fingerprint,
                    window_configuration=asdict(self.budget.config),
                    token_budget_configuration=self.budget.public_config(),
                    configuration_sha256=self.configuration_hash,state=asdict(self.state))

    def save(self,store,run_id):
        from .checkpoints import ReadingCheckpoint
        payload = json.dumps(self.checkpoint_payload(),sort_keys=True,ensure_ascii=False,separators=(',',':'))
        checkpoint = ReadingCheckpoint(1,run_id,'source_reading',
            ((self.index.snapshot.source_id,self.index.snapshot.sha256),),self.configuration_hash,(),payload,
            self._checkpoint_id)
        identifier = store.append(checkpoint)
        self._checkpoint_id = identifier
        return identifier

    @classmethod
    def resume(cls,store,run_id,reader,source_id,budget,parts=None):
        from .checkpoints import ReadingCheckpoint
        record = store.latest(run_id)
        if (not isinstance(record,ReadingCheckpoint) or record.stage != 'source_reading'
                or record.schema_version != 1 or record.run_id != run_id):
            raise ValueError('No compatible source-reading checkpoint')
        payload = json.loads(record.state_json)
        snapshot = reader.snapshot(source_id)  # Always reread, never trust saved source bytes.
        if snapshot.source_id != payload['source_artifact_id'] or snapshot.sha256 != payload['source_sha256']:
            raise ValueError('Source changed; checkpoint is incompatible')
        from .source_index import build_index
        session = cls(build_index(snapshot),budget,parts)
        expected = session.checkpoint_payload()
        for key in ('source_index_version','index_fingerprint','window_configuration',
                    'token_budget_configuration','configuration_sha256'):
            if payload.get(key) != expected[key]:
                raise ValueError('Source index or reading configuration changed; checkpoint is incompatible')
        if record.source_hashes != ((source_id,snapshot.sha256),) or record.config_sha256 != session.configuration_hash:
            raise ValueError('Checkpoint envelope mismatch')
        values = dict(payload['state'])
        values['committed_ranges'] = tuple(tuple(r) for r in values['committed_ranges'])
        if values['pending_range'] is not None:
            values['pending_range'] = tuple(values['pending_range'])
        state = ReadingState(**values)
        session._validate_state(state)
        session.state = state
        session._checkpoint_id = record.checkpoint_id
        return session
