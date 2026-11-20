"""Export the saved video3 study and reference editions."""
import base64
import argparse
from html import escape
from pathlib import Path
import re
import subprocess
import tempfile

from markdown_it import MarkdownIt

from app.round2.pipeline import ANCHOR, load_notes, read_json
from render_java_round2_visuals import timestamp_label
from run_video3_notes import OUT

EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'


def export(markdown, folder, name, appendix=''):
    body = MarkdownIt('commonmark').enable('table').render(markdown)

    def embed(match):
        path = (folder / match[1]).resolve()
        if folder not in path.parents or not path.is_file():
            raise ValueError('Visual asset missing from this notes edition')
        return 'src="data:image/png;base64,' + base64.b64encode(path.read_bytes()).decode() + '"'

    body = re.sub(r'src="(visuals/[^"]+\.png)"', embed, body)
    page = folder / (name + '.html')
    page.write_text(f"""<!doctype html><html lang="en"><meta charset="utf-8">
<title>{name}</title><style>
@page {{margin:17mm}} body {{font:11pt/1.48 system-ui;color:#172438;max-width:980px;margin:auto}}
h1,h2,h3 {{color:#17447d;break-after:avoid}} h2 {{background:#edf5fa;padding:.4em}}
img {{max-width:100%;max-height:340px;object-fit:contain}} table {{border-collapse:collapse;width:100%}}
th,td {{border:1px solid #b7c5d6;padding:.45em}} th {{background:#edf5fa}}
img,table,li {{break-inside:avoid}} pre {{white-space:pre-wrap}}
.reference {{border-top:1px solid #b7c5d6;margin-top:1em}} blockquote {{color:#40546b}}
</style><main>{body}{appendix}</main></html>""", encoding='utf-8')
    pdf = folder / (name + '.pdf')
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
        subprocess.run([EDGE, '--headless=new', '--disable-background-networking',
                        '--no-first-run', '--no-pdf-header-footer', f'--user-data-dir={profile}',
                        f'--print-to-pdf={pdf}', page.as_uri()], timeout=90, check=True,
                       capture_output=True)
    if not pdf.read_bytes().startswith(b'%PDF'):
        raise ValueError('PDF export failed')
    print(pdf)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview', action='store_true')
    parser.add_argument('--output-root', type=Path)
    args = parser.parse_args()
    root = args.output_root or OUT
    study = (root / ('polished_combined' if args.output_root else 'polished_preview' if args.preview else 'polished')).resolve()
    reference = (root / ('round2_combined' if args.output_root else 'round2_preview' if args.preview else 'round2')).resolve()
    first = root / ('round1_combined' if args.output_root else 'round1')
    _, notes = load_notes(first)
    knowledge = read_json(first / 'extraction_results.json')
    items = {item['knowledge_id']: item for group in knowledge.values() if isinstance(group, list)
             for item in group if isinstance(item, dict) and 'knowledge_id' in item}
    sections = ['<h2>Source evidence and video timestamps</h2>']
    for key, note in notes.items():
        evidence = items[key].get('extraction_metadata', {}).get('source_grounding', {}).get('evidence', [])
        quotes = dict.fromkeys((row['source_id'], row['quote']) for row in evidence)
        excerpts = ''.join(f'<li><strong>{escape(source)}</strong> · {escape(quote)}</li>'
                           for source, quote in quotes)
        sections.append(f'<section class="reference"><h3>{escape(key)}</h3>'
                        f'<p>{escape(timestamp_label(note["timing"]))}</p><ul>{excerpts}</ul></section>')
    md = (reference / 'refined_notes.md').read_text(encoding='utf-8')
    md = ANCHOR.sub(lambda match: match[0][:-2] + ' | Video: '
                    + timestamp_label(notes[match[1]]['timing']) + ']*', md)
    polished = (study / 'polished_notes.md').read_text(encoding='utf-8')
    if args.preview:
        polished = '# Video3 study notes\n\n> Partial preview from the 69 saved Round 1 items. Extraction and visual review are incomplete.\n\n' + polished.removeprefix('# Study notes').lstrip()
    export(polished, study, 'Video3-study-notes')
    reference_body = (polished + '\n\n## Source-linked notes\n\n' + md)
    # The source-linked text and quotes use their original anchors. The polished
    # prose may combine claims and is only linked through that companion text.
    export(reference_body, study, 'Video3-notes-with-evidence', ''.join(sections))


if __name__ == '__main__':
    main()
