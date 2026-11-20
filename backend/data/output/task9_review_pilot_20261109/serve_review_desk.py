"""Read-only loopback server for explicitly approved Task 9 browser validation.

No directory listing, POST, source tree, credentials, provider calls or remote bind.
"""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit,unquote
import json

ROOT=Path(__file__).resolve().parent
ALLOWED={'baseline_desk.html','pilot_desk.html','transport_fixture_desk.html'}
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        name=unquote(urlsplit(self.path).path).removeprefix('/')
        if name not in ALLOWED:self.send_error(404);return
        data=(ROOT/name).read_bytes()
        self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8')
        self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store')
        self.send_header('Content-Security-Policy',"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; base-uri 'none'; form-action 'none'")
        self.end_headers();self.wfile.write(data)
    def do_POST(self):self.send_error(405)

if __name__=='__main__':
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    print(json.dumps(dict(url=f'http://127.0.0.1:{server.server_port}/pilot_desk.html',
        fixture_url=f'http://127.0.0.1:{server.server_port}/transport_fixture_desk.html',read_only=True,bind='127.0.0.1')),flush=True)
    server.serve_forever()
