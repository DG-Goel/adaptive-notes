"""Local video library and durable notes jobs. Run from the backend directory."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
import re
import subprocess
import sys
import time
from types import SimpleNamespace

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock
from types import SimpleNamespace as Payload
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import unquote
from uuid import uuid4
from dotenv import dotenv_values

from run_authorized_java import save
from run_video3_notes import ROOT, read, run_workflow

JOBS = ROOT / 'data/output/video_jobs'
VIDEO_DIR = ROOT / 'video'
worker = ThreadPoolExecutor(max_workers=1)
ASR = ROOT / '.venv-transcription/Scripts/python.exe'
WINDOWS_PROCESS_TERMINATED = 0x40010004
OCR_RETRIES = 3
lock = Lock()
active_jobs = set()
index_lock = Lock()


def rag_post(endpoint, payload):
    request = Request('http://127.0.0.1:8000/api/v1/' + endpoint,
                      data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
    try:
        with urlopen(request, timeout=180) as response:
            return json.load(response)
    except HTTPError as error:
        raise HTTPException(502, f'Tutor service rejected {endpoint} (HTTP {error.code}).') from error
    except (URLError, TimeoutError) as error:
        raise HTTPException(503, 'Start Universal-AI-Tutor on port 8000 and check its model and vector store.') from error


def ask_tutor(payload):
    question = payload.get('question')
    if not isinstance(question, str) or not 0 < len(question.strip()) <= 1000:
        raise HTTPException(400, 'Enter a question of up to 1,000 characters.')
    job_id = payload.get('job_id')
    video_name = payload.get('video')
    if video_name is not None:
        if not isinstance(video_name, str) or video_name not in videos():
            raise HTTPException(404, 'This video is no longer in the library.')
        current_id = latest_video_job_id(VIDEO_DIR / video_name)
        if not (JOBS / current_id / 'status.json').is_file():
            raise HTTPException(409, 'Generate notes in this video’s AI Notes tab first.')
        job_id = current_id
    request = dict(question=question, mode='strict', top_k=4)
    if job_id is not None:
        if not isinstance(job_id, str):
            raise HTTPException(400, 'Invalid notes job.')
        folder = job_path(job_id)
        notes = folder / 'polished_combined/polished_notes.md'
        if progress(job_id)['state'] not in ('complete', 'partial') or not notes.is_file():
            raise HTTPException(409, 'Generate notes for this video first.')
        content = notes.read_bytes()
        filename = f'video-notes-{job_id}-{sha256(content).hexdigest()[:16]}.md'
        tutor = ROOT / 'Universal-AI-Tutor'
        configured_dir = os.environ.get('ALLOWED_NOTES_DIR') or dotenv_values(tutor / '.env').get('ALLOWED_NOTES_DIR')
        directory = Path(configured_dir or 'notes')
        if not directory.is_absolute():
            directory = tutor / directory
        document = directory.resolve() / filename
        marker = folder / 'tutor-index.json'
        with index_lock:
            if not marker.exists() or read(marker).get('document') != str(document):
                directory.mkdir(parents=True, exist_ok=True)
                document.write_bytes(content)
                indexed = rag_post('ingest', {'file_paths': [str(document)], 'overwrite': False})
                if indexed.get('status') != 'success' or not indexed.get('successful'):
                    raise HTTPException(502, 'The tutor could not index these notes.')
                save(marker, {'document': str(document)})
        request['notes_file'] = filename
    result = rag_post('ask', request)
    if job_id is not None:
        for citation in result.get('citations', []):
            if Path(citation.get('doc_path') or '').resolve() != document:
                raise HTTPException(502, 'The tutor returned a source outside this lecture. Restart the tutor service with lecture filtering enabled.')
    return result


class HTTPException(Exception):
    def __init__(self, status, detail='Not found'):
        self.status = status
        self.detail = detail


def job_path(job_id):
    if not re.fullmatch(r'[a-f0-9]{24}', job_id):
        raise HTTPException(404)
    path = JOBS / job_id
    if not (path / 'status.json').is_file():
        raise HTTPException(404)
    return path


def process(path, video):
    stage = 'transcription'

    def status(state, **fields):
        with lock:
            save(path / 'status.json', dict(video=video.name, state=state, stage=stage, **fields))
        print(f'{path.name} {video.name}: {stage} [{state}]', flush=True)

    def command(*args, interruption_retries=0):
        with (path / 'worker.log').open('a', encoding='utf-8') as log:
            for attempt in range(interruption_retries + 1):
                result = subprocess.run([str(arg) for arg in args], cwd=ROOT, stdout=log,
                                        stderr=subprocess.STDOUT)
                if result.returncode == 0:
                    return
                if result.returncode != WINDOWS_PROCESS_TERMINATED:
                    raise RuntimeError(f'{stage} failed with exit code {result.returncode}. See worker.log.')
                if attempt == interruption_retries:
                    raise RuntimeError(
                        f'{stage} was terminated by Windows (0x40010004). '
                        'Generate AI notes again to resume from saved progress. See worker.log.')
                log.write(f'\n{stage} process terminated (0x40010004). '
                          f'Resuming from checkpoints, retry {attempt + 1}/{interruption_retries}.\n')
                log.flush()
                time.sleep(1)

    try:
        status('running')
        data = path / 'source'
        transcript = data / 'speech/transcript.json'
        if not transcript.exists():
            model = next((ROOT / 'data/transcriptions/model-cache').glob('**/model.bin')).parent
            command(ASR, 'transcribe_video.py', '--input', video, '--model', model,
                    '--output', transcript.parent)
        if read(transcript).get('status') != 'complete':
            raise RuntimeError('Transcription did not finish successfully')
        stage = 'risk detection'
        status('running')
        risks = data / 'risks/risk_intervals.json'
        if not risks.exists():
            command(sys.executable, 'detect_transcription_risks.py', '--input', transcript,
                    '--output', risks.parent)
        stage = 'OCR'
        status('running')
        # The integrated source binds the exact OCR files used by Round 1.
        if (data / 'multimodal/multimodal_transcript.json').is_file():
            pass
        elif any(event['priority'] == 'HIGH' for event in read(risks)['events']):
            command(ASR, 'visual_recovery.py', '--video', video, '--transcript', transcript,
                        '--risks', risks, '--output', data / 'ocr', '--chronological',
                        interruption_retries=OCR_RETRIES)
        else:
            from multimodal_transcript import digest
            (data / 'ocr').mkdir(exist_ok=True)
            save(data / 'ocr/frame_manifest.json', {'events': []})
            save(data / 'ocr/visual_ocr_results.json', dict(records=[], identity=dict(
                transcript_sha256=digest(transcript.read_bytes()), risks_sha256=digest(risks.read_bytes()))))
        stage = 'notes extraction and refinement'
        status('running')
        def update_stage(next_stage):
            nonlocal stage
            stage = next_stage
            status('running')

        run_workflow(SimpleNamespace(legacy_category_passes=False), data=data, output=path,
                     progress=update_stage)
        polish = path / 'polished_combined/report.json'
        if not polish.exists():
            raise RuntimeError('Notes processing stopped. Check the stage reports.')
        stage = 'PDF export'
        status('running')
        command(sys.executable, 'export_video3_notes.py', '--output-root', path)
        first = read(path / 'round1_combined/run_summary.json')
        second = read(path / 'round2_combined/report.json')
        text = read(polish)
        complete = (first['classification'] == 'Full live extraction completed'
                    and second['analyzed_note_count'] == second['note_count']
                    and not second['render_errors'] and not text['errors'])
        status('complete' if complete else 'partial', visuals=second['visuals_rendered'])
    except Exception as error:
        import traceback
        with (path / 'worker.log').open('a', encoding='utf-8') as log:
            traceback.print_exc(file=log)
        status('failed', error=str(error)[:300])
    finally:
        with lock:
            active_jobs.discard(path.name)


def videos():
    return sorted(path.name for path in VIDEO_DIR.iterdir()
                  if path.suffix.lower() == '.mp4' and path.is_file()
                  and path.resolve().parent == VIDEO_DIR.resolve()) if VIDEO_DIR.is_dir() else []


def video_job_id(video):
    stat = video.stat()
    return sha256(f'{video}:{stat.st_size}:{stat.st_mtime_ns}'.encode()).hexdigest()[:24]


def latest_video_job_id(video):
    original_id = video_job_id(video)
    pointer = JOBS / original_id / 'latest_run.json'
    return read(pointer)['job_id'] if pointer.is_file() else original_id


def start(payload, origin):
    if origin not in (None, 'http://127.0.0.1:8765', 'http://localhost:8765',
                      'http://127.0.0.1:5173', 'http://localhost:5173'):
        raise HTTPException(403, 'Use the local notes page')
    if not payload.allow_groq:
        raise HTTPException(400, 'Authorize sending transcript and notes text to Groq')
    if payload.video not in videos():
        raise HTTPException(404, 'Video is outside the local library')
    video = VIDEO_DIR / payload.video
    job_id = latest_video_job_id(video)
    if job_id in active_jobs:
        return {'job_id': job_id}
    regenerate = getattr(payload, 'regenerate', False)
    if type(regenerate) is not bool:
        raise HTTPException(400, 'regenerate must be a boolean')
    previous = JOBS / job_id
    status_file = previous / 'status.json'
    if not regenerate and status_file.is_file():
        status = read(status_file)
        if status['state'] == 'failed':
            manifest = previous / 'round1_combined/manifest.json'
            old_quiz = manifest.is_file() and read(manifest)['configuration'].get('wire_format') in (
                'compact_field_rows_quiz_v1', 'compact_field_rows_quiz_v2')
            stale_source = status.get('error', '').startswith('Historical source hash mismatch:')
            regenerate = old_quiz or stale_source
    if regenerate:
        job_id = uuid4().hex[:24]
    path = JOBS / job_id
    try:
        path.mkdir(parents=True)
    except FileExistsError:
        if job_id in active_jobs or (
                (path / 'status.json').exists() and read(path / 'status.json')['state'] in ('complete', 'partial')):
            return {'job_id': job_id}
    save(path / 'status.json', dict(video=video.name, state='queued', stage='queued'))
    if regenerate:
        original = JOBS / video_job_id(video)
        original.mkdir(parents=True, exist_ok=True)
        save(original / 'latest_run.json', {'job_id': job_id})
    active_jobs.add(job_id)
    worker.submit(process, path, video)
    return {'job_id': job_id}


def progress(job_id: str):
    with lock:
        result = read(job_path(job_id) / 'status.json')
        quiz_path = job_path(job_id) / 'round1_combined/quiz.json'
        if quiz_path.is_file():
            quiz = read(quiz_path)
            result = {**result, 'quiz_available': True, 'quiz_count': quiz['question_count'],
                      'quiz_status': quiz['status']}
        if result['state'] in ('running', 'queued') and job_id not in active_jobs:
            return {**result, 'state': 'interrupted',
                    'error': 'The previous notes run was interrupted. Click Generate AI notes to resume.'}
        return result


def download(job_id: str, edition: str):
    if edition in ('quiz', 'quiz-json'):
        path = job_path(job_id) / 'round1_combined' / ('quiz.md' if edition == 'quiz' else 'quiz.json')
        if not path.is_file():
            raise HTTPException(404)
        return path
    names = {'study': 'Video3-study-notes.pdf', 'reference': 'Video3-notes-with-evidence.pdf',
             'markdown': 'polished_notes.md'}
    folder = job_path(job_id) / 'polished_combined'
    path = folder / names.get(edition, 'missing')
    if not path.is_file():
        raise HTTPException(404)
    return path


def visual_asset(job_id, filename):
    if not re.fullmatch(r'visual-[a-f0-9]{20}\.png', filename):
        raise HTTPException(404)
    folder = job_path(job_id)
    for stage in ('polished_combined', 'round2_combined'):
        path = folder / stage / 'visuals' / filename
        if path.is_file():
            return path
    raise HTTPException(404)


def visual_gallery(job_id):
    folder = job_path(job_id)
    manifest = folder / 'round2_combined/ordered_notes.json'
    if not manifest.is_file():
        return []
    result = []
    for note in read(manifest):
        for visual in note['visuals']:
            if visual.get('render_status') != 'rendered':
                continue
            payload = visual['payload']
            if visual.get('export_method') == 'native_table':
                from app.round2.pipeline import table_markdown
                content = table_markdown(payload)
            else:
                image = Path(visual['image']).name
                try:
                    visual_asset(job_id, image)
                except HTTPException:
                    continue
                content = f'![Lecture diagram](/api/video-notes/{job_id}/visuals/{image})'
            result.append({'id': visual['id'], 'title': payload['title'], 'markdown': content})
    return result


def generated_quizzes():
    results = []
    for name in videos():
        job_id = latest_video_job_id(VIDEO_DIR / name)
        path = JOBS / job_id / 'round1_combined' / 'quiz.json'
        if path.is_file():
            quiz = read(path)
            if quiz['question_count']:
                results.append({'video': name, 'question_count': quiz['question_count'],
                                'status': quiz['status']})
    return results


def index():
    return (ROOT / 'video_notes.html').read_text(encoding='utf-8')
class Handler(BaseHTTPRequestHandler):
    def stream_video(self, name):
        if name not in videos():
            raise HTTPException(404, 'Video not found')
        with (VIDEO_DIR / name).open('rb') as source:
            size = os.fstat(source.fileno()).st_size
            start, end = 0, size - 1
            requested = self.headers.get('Range')
            if requested:
                match = re.fullmatch(r'bytes=(\d*)-(\d*)', requested)
                if match and match[1]:
                    start = int(match[1])
                    end = min(end, int(match[2])) if match[2] else end
                elif match and match[2]:
                    start = max(0, size - int(match[2]))
                if not match or not any(match.groups()) or start > end:
                    self.send_response(416)
                    self.send_header('Content-Range', f'bytes */{size}')
                    self.send_header('Content-Length', '0')
                    self.end_headers()
                    return
            self.send_response(206 if requested else 200)
            self.send_header('Content-Type', 'video/mp4')
            self.send_header('Accept-Ranges', 'bytes')
            if requested:
                self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
            remaining = end - start + 1
            self.send_header('Content-Length', str(remaining))
            self.end_headers()
            source.seek(start)
            try:
                while remaining and (chunk := source.read(min(remaining, 1024 * 1024))):
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass

    def send_body(self, data, mime, status=200):
        try:
            self.send_response(status)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            # The browser or proxy closed this request before the response arrived.
            return

    def route(self, post=False):
        if self.headers.get('Host') not in ('127.0.0.1:8765', 'localhost:8765'):
            return self.send_body(b'Invalid host', 'text/plain', 403)
        parts = self.path.split('?')[0].strip('/').split('/')
        try:
            if post:
                if parts not in (['api', 'video-notes'], ['api', 'video-notes', 'ask']):
                    raise HTTPException(404)
                size = int(self.headers.get('Content-Length', 0))
                if not 0 < size <= 4096:
                    raise HTTPException(400, 'Invalid request size')
                payload = json.loads(self.rfile.read(size))
                if not isinstance(payload, dict):
                    raise HTTPException(400, 'Expected a JSON object')
                if parts[-1] == 'ask':
                    if self.headers.get('Origin') not in (
                        None, 'http://localhost:5173', 'http://127.0.0.1:5173',
                        'http://localhost:8765', 'http://127.0.0.1:8765'):
                        raise HTTPException(403, 'Use the local tutor page.')
                    return self.send_body(json.dumps(ask_tutor(payload)).encode(), 'application/json')
                if not isinstance(payload.get('video'), str) or payload.get('allow_groq') is not True:
                    raise HTTPException(400, 'Choose a video and authorize Groq text processing')
                with lock:
                    result = start(Payload(**payload), self.headers.get('Origin'))
                code = 202
            elif parts == ['']:
                return self.send_body(index().encode(), 'text/html; charset=utf-8')
            elif parts == ['api', 'videos']:
                result, code = videos(), 200
            elif parts[:2] == ['api', 'videos'] and len(parts) == 4 and parts[3] in ('quiz', 'notes-job', 'overview', 'visuals'):
                name = unquote(parts[2])
                if name not in videos():
                    raise HTTPException(404, 'Video is outside the local library')
                job_id = latest_video_job_id(VIDEO_DIR / name)
                if parts[3] == 'visuals':
                    result = visual_gallery(job_id) if (JOBS / job_id / 'status.json').is_file() else []
                    return self.send_body(json.dumps(result).encode(), 'application/json')
                if parts[3] == 'notes-job':
                    job_exists = (JOBS / job_id / 'status.json').is_file()
                    return self.send_body(json.dumps({'job_id': job_id if job_exists else ''}).encode(),
                                          'application/json')
                path = JOBS / job_id / 'round1_combined' / 'quiz.json'
                if parts[3] == 'overview':
                    topics = {}
                    if path.is_file():
                        for question in read(path)['questions']:
                            topic = (question.get('topic') or '').strip()
                            if topic:
                                topics.setdefault(topic.casefold(), topic)
                    result = {'topics': list(topics.values())}
                    return self.send_body(json.dumps(result).encode(), 'application/json')
                if not path.is_file():
                    raise HTTPException(404, 'No generated quiz for this video yet')
                quiz = read(path)
                transcript = JOBS / job_id / 'source/speech/transcript.json'
                try:
                    duration = read(transcript).get('audio_duration')
                except (OSError, ValueError):
                    duration = None
                if isinstance(duration, (int, float)) and 0 < duration < float('inf'):
                    quiz['duration_seconds'] = duration
                return self.send_body(json.dumps(quiz).encode(), 'application/json')
            elif parts[:2] == ['api', 'videos'] and len(parts) == 3:
                return self.stream_video(unquote(parts[2]))
            elif parts == ['api', 'video-notes', 'quizzes']:
                result, code = generated_quizzes(), 200
            elif parts[:2] == ['api', 'video-notes'] and len(parts) == 3:
                result, code = progress(parts[2]), 200
            elif parts[:2] == ['api', 'video-notes'] and len(parts) == 5 and parts[3] == 'visuals':
                return self.send_body(visual_asset(parts[2], parts[4]).read_bytes(), 'image/png')
            elif parts[:2] == ['api', 'video-notes'] and len(parts) == 4:
                if parts[3] == 'markdown':
                    markdown = download(parts[2], 'markdown').read_text(encoding='utf-8')
                    markdown = re.sub(r'(?<=\]\()visuals/(visual-[a-f0-9]{20}\.png)(?=\))',
                                      lambda match: f'/api/video-notes/{parts[2]}/visuals/{match[1]}', markdown)
                    return self.send_body(markdown.encode('utf-8'), 'text/plain; charset=utf-8')
                mime = ('application/json' if parts[3] == 'quiz-json' else
                        'text/plain; charset=utf-8' if parts[3] in ('markdown', 'quiz') else 'application/pdf')
                return self.send_body(download(parts[2], parts[3]).read_bytes(), mime)
            else:
                raise HTTPException(404)
        except HTTPException as error:
            result, code = {'detail': error.detail}, error.status
        except (ValueError, TypeError, AttributeError):
            result, code = {'detail': 'Invalid request'}, 400
        self.send_body(json.dumps(result).encode(), 'application/json', code)

    def do_GET(self):
        self.route()

    def do_POST(self):
        self.route(post=True)


class NotesServer(ThreadingHTTPServer):
    allow_reuse_address = False
    allow_reuse_port = False

    def server_bind(self):
        import socket
        if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


if __name__ == '__main__':
    with NotesServer(('127.0.0.1', 8765), Handler) as server:
        print(f'Video notes: http://127.0.0.1:8765 (PID {os.getpid()})', flush=True)
        server.serve_forever()
