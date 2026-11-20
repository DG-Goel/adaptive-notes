"""Render source-reviewed Java examples into a separate, portable notes edition."""
import argparse
import base64
from html import escape
import json
import re
from pathlib import Path

from markdown_it import MarkdownIt

from app.round2.pipeline import ANCHOR, integrate, load_notes, read_json, require, table_markdown
from app.round2.render import render_visuals

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'data/output/multimodal_notes_category_full_20261110_135722_142723'
PRIOR = ROOT / 'data/output/round2_java_repaired'


def timestamp_label(spans):
    ranges = []
    for span in spans:
        start, end = span['start'], span['end']
        if start is None or end is None:
            continue
        resolution = span['resolution']
        if ranges and resolution == ranges[-1][2] and start <= ranges[-1][1]:
            ranges[-1][1] = max(end, ranges[-1][1])
        else:
            ranges.append([start, end, resolution])

    def clock(seconds):
        minutes, seconds = divmod(round(seconds * 100), 6000)
        hours, minutes = divmod(minutes, 60)
        whole_seconds, hundredths = divmod(seconds, 100)
        return f'{hours:02d}:{minutes:02d}:{whole_seconds:02d}.{hundredths:02d}'

    return ', '.join(
        f'{clock(start)}–{clock(end)}' + (' (passage)' if resolution != 'speech_segment' else '')
        for start, end, resolution in ranges
    ) or 'Unavailable'


def build_visuals(notes):
    def visual(identifier, ids, phrases, payload):
        evidence = []
        for note_id, phrase in zip(ids, phrases, strict=True):
            note = notes[note_id]
            require(not note['unresolved'] and phrase in note['text'], 'Reviewed note wording changed')
            evidence.append(dict(note_id=note_id, quote=phrase))
        spans = {(row['source_id'], row['segment_id']): row
                 for key in ids for row in notes[key]['timing']}
        require(bool(spans) and all(0 <= row['start'] <= row['end'] for row in spans.values()),
                'Reviewed example needs saved source timing')
        return dict(id=identifier, payload=payload, source_segment_ids=ids, evidence=evidence,
                    spans=sorted(spans.values(), key=lambda row: row['start']),
                    anchor_note_id=max(ids, key=lambda key: notes[key]['position']),
                    needs_timestamp_alignment=any(row['resolution'] != 'speech_segment' for row in spans.values()),
                    mode='text_and_visual', adaptation='Source-reviewed illustration of existing notes')

    prior = list(read_json(PRIOR / 'renderer_inputs.json').values())
    tables = {table['title']: table for table in prior if table['type'] == 'table'}
    return [
        visual('java-naming', ['FCT_0048', 'FCT_0049'],
               ['Java class names use PascalCase', 'Java method names use camelCase'],
               tables['Java Naming Conventions']),
        visual('java-runtime', ['FCT_0070'],
               ['The Java Runtime Environment includes the Java Virtual Machine (JVM)'],
               dict(type='architecture', title='Java runtime components', direction='RIGHT',
                    components=[dict(id='jre', label='Java Runtime Environment (JRE)'),
                                dict(id='jvm', label='Java Virtual Machine (JVM)')],
                    connections=[{'from': 'jre', 'to': 'jvm', 'label': 'includes'}])),
        visual('matrix-row', ['FCT_0177', 'FCT_0178', 'FCT_0179'],
               ['each row is an array', 'the second row, which is another array', '4, 5, and 6'],
               dict(type='data_structure', subtype='array', title='Second row of the matrix', values=[4, 5, 6])),
        visual('increment-forms', ['FCT_0202', 'FCT_0203'],
               ['the original value of x is used in the expression and then x is incremented',
                'x is incremented first and the new value is used in the expression'],
               dict(type='table', title='Prefix and postfix increment',
                    headers=['Form', 'Order of operations'],
                    rows=[['postfix (x++)', 'Use the original value of x in the expression, then increment x.'],
                          ['prefix (++x)', 'Increment x first, then use the new value in the expression.']])),
        visual('input-output', ['FCT_0260'],
               ['the user can type input (e.g., 20) and the program outputs the entered value'],
               dict(type='sequence', title='Entering a value and seeing it printed',
                    participants=[dict(id='User', label='User', kind='actor'),
                                  dict(id='Program', label='Program', kind='system')],
                    events=[{'kind': 'message', 'from': 'User', 'to': 'Program', 'text': 'Enter 20'},
                            {'kind': 'message', 'from': 'Program', 'to': 'User', 'text': 'Print 20', 'dashed': True}])),
        visual('for-loop', ['FCT_0387'],
               ['initialize the loop variable, evaluate the condition, execute the body if true, then increment the loop variable, and repeat'],
               dict(type='flowchart', title='For loop execution', direction='RIGHT',
                    nodes=[dict(id=key, kind=kind, label=label) for key, kind, label in [
                        ('init', 'start', 'Initialize the loop variable'),
                        ('condition', 'decision', 'Evaluate the condition'),
                        ('body', 'action', 'Execute the body'),
                        ('increment', 'action', 'Increment the loop variable'),
                        ('end', 'success', 'Exit the loop'),
                    ]],
                    edges=[{'from': source, 'to': target, 'label': label} for source, target, label in [
                        ('init', 'condition', ''), ('condition', 'body', 'True'),
                        ('body', 'increment', ''), ('increment', 'condition', 'Repeat'),
                        ('condition', 'end', 'False'),
                    ]])),
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    require(output not in (SOURCE, PRIOR) and SOURCE not in output.parents and PRIOR not in output.parents,
            'Use a separate visual edition output directory')
    output.mkdir(parents=True, exist_ok=True)
    markdown, notes = load_notes(SOURCE)
    visuals = build_visuals(notes)
    render_visuals(visuals, output, ROOT / 'data/round2-renderer',
                   Path('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'))
    require(all(row['render_status'] == 'rendered' for row in visuals), 'A renderer did not produce its image')
    # Replace only reviewed prose. Supporting notes can remain when they add context.
    replacements = {
        'java-naming': {'FCT_0048': None, 'FCT_0049': None},
        'java-runtime': {'FCT_0070': 'The JVM translates Java bytecode to native code for the underlying operating system.'},
        'matrix-row': {'FCT_0179': None},
        'increment-forms': {'FCT_0202': None, 'FCT_0203': None},
        'input-output': {'FCT_0260': None},
        'for-loop': {'FCT_0387': None},
    }
    edits = []
    for row in visuals:
        row['replaced_note_ids'] = list(replacements[row['id']])
        for note_id, remaining in replacements[row['id']].items():
            note = notes[note_id]
            start, end = note['body_start'], note['body_end']
            original = markdown[start:end]
            require(not note['unresolved'] and bool(original.strip()), 'Replacement target is unresolved')
            if remaining:
                warning = original.strip().split('\n\n', 1)[0]
                text = f'\n\n{warning}\n\n{remaining}\n\n'
            else:
                text = '\n\n'
            edits.append((start, end, text))
        row['replaced_text'] = {key: notes[key]['text'] for key in row['replaced_note_ids']}
    require(len({start for start, _, _ in edits}) == len(edits), 'Overlapping replacement targets')
    for start, end, text in sorted(edits, reverse=True):
        markdown = markdown[:start] + text + markdown[end:]
        for note in notes.values():
            if note['anchor'] >= end:
                note['anchor'] += len(text) - (end - start)
    refined = integrate(markdown, notes, visuals)
    for row in visuals:
        payload = row['payload']
        title = payload['title']
        section = table_markdown(payload) if payload['type'] == 'table' else f"![{title}]({row['image']})"
        require(refined.count(section) == 1, 'Visual insertion anchor did not resolve uniquely')
        heading = f"### {title}"
        refined = refined.replace(section, heading + '\n\n' + section
                                  + '\n\n*Based on Round 1 notes awaiting semantic review.*', 1)
        spans = ', '.join(f"{span['start']:.2f}–{span['end']:.2f}s" for span in row['spans'])
        caption = f"*Source: {', '.join(row['source_segment_ids'])} · {spans}"
        refined = refined.replace(caption, f"*Source: {', '.join(row['source_segment_ids'])} · "
                                  + timestamp_label(row['spans']), 1)
    refined = ANCHOR.sub(lambda match: match[0][:-2]
                         + ' | Video: ' + timestamp_label(notes[match[1]]['timing']) + ']*', refined)
    (output / 'refined_notes.md').write_text(refined, encoding='utf-8')
    html = MarkdownIt('commonmark').enable('table').render(refined)
    for row in visuals:
        title = row['payload']['title']
        html = html.replace(f'<h3>{escape(title)}</h3>', f'<h3 id="{row["id"]}">{escape(title)}</h3>', 1)
        if row['payload']['type'] != 'table':
            encoded = base64.b64encode((output / row['image']).read_bytes()).decode('ascii')
            html = html.replace(f'src="{row["image"]}"', f'src="data:image/png;base64,{encoded}"', 1)
    page = f"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Java notes with visuals</title>
<style>
body{{font:17px/1.55 system-ui,sans-serif;color:#182234;margin:2rem auto;max-width:1040px;padding:0 1rem}}
h3{{margin-top:2rem;color:#17447d}} img{{max-width:100%;height:auto;border:1px solid #cbd5e1}}
table{{border-collapse:collapse;width:100%}} th,td{{border:1px solid #b7c5d6;text-align:left;padding:.65rem}}
th{{background:#e9f1fa}} blockquote{{border-left:3px solid #cbd5e1;margin-left:0;padding-left:1rem;color:#46556a}}
@media print {{body{{font-size:10pt;margin:0}} h3{{break-after:avoid}}
table,img{{break-inside:avoid}} img{{max-height:340px;object-fit:contain}}}}
</style><main><h1>Java notes with visuals</h1>
{html}</main></html>"""
    (output / 'refined_notes.html').write_text(page, encoding='utf-8')
    (output / 'visual_mapping.json').write_text(json.dumps(visuals, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Saved two tables and four diagrams with source anchors and timestamps.')


if __name__ == '__main__':
    main()
