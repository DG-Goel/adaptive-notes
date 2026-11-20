"""Independent, append-only SQLite implementation of the Phase 1 checkpoint port."""
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import sqlite3

from .contracts import Checkpoint
from .source_index import digest

APPLICATION_ID = 0x4E494732
DEFAULT_NAMESPACE = Path(__file__).resolve().parents[2] / 'data' / 'infographics'


@dataclass(frozen=True)
class ReadingCheckpoint(Checkpoint):
    state_json: str
    parent_checkpoint_id: str | None = None
    checkpoint_id: str = ''


class CheckpointConflict(ValueError):
    pass


class SQLiteCheckpointStore:
    """Own database only; no connection to any existing NOETRA database.

    Construction is lazy. Transactions atomically append complete revisions;
    rollback/recovery is provided by SQLite, without updating older revisions.
    """
    def __init__(self,namespace=DEFAULT_NAMESPACE):
        self.namespace = Path(namespace).absolute()
        self.path = self.namespace / 'source-reading-checkpoints.sqlite3'

    def _validate_path(self):
        if self.namespace.resolve() != self.namespace or self.path.is_symlink():
            raise ValueError('Checkpoint namespace must not traverse symlinks or junctions')
        if self.path.resolve().parent != self.namespace:
            raise ValueError('Checkpoint path escaped independent namespace')

    def _connect(self):
        self._validate_path()
        self.namespace.mkdir(parents=True,exist_ok=True)
        self._validate_path()
        connection = sqlite3.connect(self.path,timeout=10)
        try:
            app = connection.execute('PRAGMA application_id').fetchone()[0]
            tables = connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            if app != APPLICATION_ID and (app != 0 or tables):
                raise ValueError('Refusing to use an unrelated checkpoint database')
            connection.execute('BEGIN IMMEDIATE')
            connection.execute(f'PRAGMA application_id={APPLICATION_ID}')
            connection.execute('CREATE TABLE IF NOT EXISTS checkpoints ('
                'run_id TEXT NOT NULL, revision INTEGER NOT NULL, checkpoint_id TEXT NOT NULL UNIQUE, '
                'body TEXT NOT NULL, checksum TEXT NOT NULL, PRIMARY KEY(run_id,revision))')
            connection.commit()
        except Exception:
            connection.close()
            raise
        return connection

    @staticmethod
    def _run_id(run_id):
        if not isinstance(run_id,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',run_id):
            raise ValueError('Invalid independent checkpoint run ID')

    @staticmethod
    def _body(checkpoint):
        values = asdict(checkpoint)
        values.pop('checkpoint_id',None)
        return json.dumps(values,sort_keys=True,ensure_ascii=False,separators=(',',':'))

    @staticmethod
    def _decode(row):
        if row is None:
            return None
        identifier,body,checksum = row
        if digest(body.encode('utf-8')) != checksum or identifier != 'CP'+checksum:
            raise ValueError('Checkpoint integrity mismatch')
        value = json.loads(body)
        value['source_hashes'] = tuple(tuple(pair) for pair in value['source_hashes'])
        value['artifact_ids'] = tuple(value['artifact_ids'])
        if 'state_json' in value:
            return ReadingCheckpoint(**value,checkpoint_id=identifier)
        return Checkpoint(**value)

    def append(self,checkpoint: Checkpoint) -> str:
        self._run_id(checkpoint.run_id)
        body = self._body(checkpoint)
        checksum = digest(body.encode('utf-8'))
        identifier = 'CP'+checksum
        connection = self._connect()
        try:
            with connection:
                connection.execute('BEGIN IMMEDIATE')
                row = connection.execute('SELECT checkpoint_id,body,checksum FROM checkpoints '
                    'WHERE run_id=? ORDER BY revision DESC LIMIT 1',(checkpoint.run_id,)).fetchone()
                previous = self._decode(row)
                if isinstance(checkpoint,ReadingCheckpoint):
                    if previous is not None:
                        if not isinstance(previous,ReadingCheckpoint):
                            raise CheckpointConflict('Run already contains another checkpoint type')
                        if (previous.source_hashes,previous.config_sha256) != (checkpoint.source_hashes,checkpoint.config_sha256):
                            raise CheckpointConflict('Run source/configuration changed; use a new run ID')
                        if previous.state_json == checkpoint.state_json:
                            return previous.checkpoint_id
                        if checkpoint.parent_checkpoint_id != previous.checkpoint_id:
                            raise CheckpointConflict('Stale checkpoint writer; resume latest revision')
                        old = json.loads(previous.state_json)['state']
                        new = json.loads(checkpoint.state_json)['state']
                        if new['cursor'] < old['cursor'] or new['revision'] <= old['revision']:
                            raise CheckpointConflict('Checkpoint cannot rewind source progress')
                        if new['committed_ranges'][:len(old['committed_ranges'])] != old['committed_ranges']:
                            raise CheckpointConflict('Checkpoint history diverged')
                    elif checkpoint.parent_checkpoint_id is not None:
                        raise CheckpointConflict('Missing checkpoint parent')
                if row and row[0] == identifier:
                    return identifier
                revision = connection.execute('SELECT COALESCE(MAX(revision),0)+1 FROM checkpoints WHERE run_id=?',
                                               (checkpoint.run_id,)).fetchone()[0]
                connection.execute('INSERT INTO checkpoints VALUES (?,?,?,?,?)',
                    (checkpoint.run_id,revision,identifier,body,checksum))
            return identifier
        finally:
            connection.close()

    def latest(self,run_id) -> Checkpoint | None:
        self._run_id(run_id)
        self._validate_path()
        if not self.path.exists():
            return None
        connection = self._connect()
        try:
            row = connection.execute('SELECT checkpoint_id,body,checksum FROM checkpoints '
                'WHERE run_id=? ORDER BY revision DESC LIMIT 1',(run_id,)).fetchone()
            return self._decode(row)
        finally:
            connection.close()
