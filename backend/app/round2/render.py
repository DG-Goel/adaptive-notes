"""Export structured note visuals to Markdown-compatible artifacts."""
import asyncio
from base64 import b64decode
from shutil import copyfile
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import tempfile
from threading import Thread
import time
from urllib.request import urlopen

from websockets.asyncio.client import connect

from app.round2.pipeline import EXTRA_VISUAL_TYPES
from app.round2.visual_cards import visual_card


class LocalAssets(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


@contextmanager
def browser(renderer, executable):
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(LocalAssets, directory=renderer))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with tempfile.TemporaryDirectory(prefix='round2-browser-', ignore_cleanup_errors=True) as profile:
            process = subprocess.Popen([str(executable), '--headless=new', '--disable-background-networking',
                '--no-first-run', '--remote-debugging-port=0', '--remote-debugging-address=127.0.0.1',
                f'--user-data-dir={profile}', '--window-size=1500,1000',
                f'http://127.0.0.1:{server.server_port}/round2.html'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                port_file = Path(profile) / 'DevToolsActivePort'
                deadline = time.monotonic() + 15
                while not port_file.exists() and time.monotonic() < deadline and process.poll() is None:
                    time.sleep(.1)
                if not port_file.exists():
                    raise RuntimeError('Headless renderer did not start')
                port = int(port_file.read_text().splitlines()[0])
                with urlopen(f'http://127.0.0.1:{port}/json/list', timeout=5) as response:
                    targets = json.load(response)
                page = next(target for target in targets if target['type'] == 'page')
                yield page['webSocketDebuggerUrl']
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


async def export_visuals(endpoint, visuals, output):
    async with connect(endpoint, max_size=32 * 1024 * 1024) as socket:
        counter = 0

        async def command(method, **params):
            nonlocal counter
            counter += 1
            await socket.send(json.dumps(dict(id=counter, method=method, params=params)))
            while True:
                message = json.loads(await asyncio.wait_for(socket.recv(), timeout=20))
                if message.get('id') == counter:
                    if 'error' in message:
                        raise RuntimeError('Browser command failed: ' + method)
                    return message['result']

        async def evaluate(expression):
            result = await command('Runtime.evaluate', expression=expression, returnByValue=True)
            if result.get('exceptionDetails'):
                raise RuntimeError('Existing renderer rejected this payload')
            return result['result'].get('value')

        await command('Network.enable')
        await command('Network.setBlockedURLs', urls=['https://*'])
        for _ in range(100):
            if await evaluate("typeof window.renderRound2 === 'function'"):
                break
            await asyncio.sleep(.1)
        else:
            raise RuntimeError('Renderer bundle failed to load')

        for visual in visuals:
            try:
                if visual['payload']['type'] in EXTRA_VISUAL_TYPES:
                    image = Path('visuals') / (visual['id'] + '.png')
                    markup = json.dumps(visual_card(visual['payload']), ensure_ascii=True)
                    clip = await evaluate(f"""(() => {{
                      const layer = document.createElement('div');
                      layer.id = 'round2-overlay';
                      layer.style.cssText = 'position:absolute;top:0;left:0;z-index:9999';
                      document.body.appendChild(layer);
                      const shadow = layer.attachShadow({{mode:'open'}});
                      shadow.innerHTML = {markup};
                      const rect = shadow.querySelector('article').getBoundingClientRect();
                      return {{x:0,y:0,width:Math.ceil(rect.width),height:Math.ceil(rect.height),scale:1}};
                    }})()""")
                    try:
                        capture = await command('Page.captureScreenshot', format='png', clip=clip,
                                                captureBeyondViewport=True)
                        (output / image).write_bytes(b64decode(capture['data']))
                    finally:
                        await evaluate("document.getElementById('round2-overlay').remove()")
                    visual.update(render_status='rendered', image=image.as_posix(),
                                  export_method='browser_screenshot')
                    continue
                arguments = json.dumps([visual['payload'], visual['id']], ensure_ascii=True)
                await evaluate('window.renderRound2(...' + arguments + ')')
                selector = {
                    'table': 'table tbody tr',
                    'flowchart': '.react-flow__edge-path',
                    'architecture': '.react-flow__edge-path',
                    'data_structure': 'svg text',
                    'sequence': 'svg[id^=sequence], svg .messageText',
                }[visual['payload']['type']]
                for _ in range(120):
                    ready = await evaluate(f"""(() => {{
                      const el = document.querySelector('#visual');
                      return el?.dataset.renderId === {json.dumps(visual['id'])}
                          && Boolean(el.querySelector({json.dumps(selector)}));
                    }})()""")
                    if ready:
                        break
                    await asyncio.sleep(.1)
                else:
                    raise RuntimeError('No rendered visual appeared')
                if visual['payload']['type'] == 'table':
                    visual.update(render_status='rendered', export_method='native_table')
                    continue
                image = Path('visuals') / (visual['id'] + '.png')
                with tempfile.TemporaryDirectory(prefix='round2-download-') as folder:
                    await command('Page.setDownloadBehavior', behavior='allow', downloadPath=folder)
                    clicked = await evaluate("""(() => {
                      const button = [...document.querySelectorAll('#visual button')].find(
                        item => !item.disabled && item.textContent.trim().startsWith('Download PNG'));
                      if (!button) return false;
                      button.click();
                      return true;
                    })()""")
                    if not clicked:
                        raise RuntimeError('Download PNG button unavailable')
                    for _ in range(200):
                        files = list(Path(folder).glob('*.png'))
                        if len(files) == 1 and files[0].read_bytes().endswith(b'IEND\xaeB\x60\x82'):
                            copyfile(files[0], output / image)
                            break
                        await asyncio.sleep(.1)
                    else:
                        raise RuntimeError('Download PNG did not complete')
                visual.update(render_status='rendered', image=image.as_posix(), export_method='download_png_button')
            except (RuntimeError, TimeoutError, ValueError) as error:
                visual.update(render_status='failed', render_error=str(error))


def render_visuals(visuals, output, renderer, executable):
    if not visuals:
        return
    (output / 'visuals').mkdir(exist_ok=True)
    with browser(renderer, executable) as endpoint:
        asyncio.run(export_visuals(endpoint, visuals, output))
