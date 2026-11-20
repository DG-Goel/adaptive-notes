"""Render grounded hierarchies, timelines and charts as self-contained cards."""
from html import escape


STYLE = """
    width: 1000px; box-sizing: border-box; padding: 32px 40px;
    background: #fff; border: 1px solid #dce4e8; color: #193042;
    font: 18px/1.4 'Segoe UI', sans-serif; overflow-wrap: anywhere;
"""


def visual_card(payload):
    kind = payload['type']
    title = escape(payload['title'])
    if kind == 'concept_tree':
        children = {}
        for node in payload['nodes']:
            children.setdefault(node.get('parent'), []).append(node)

        def branch(node):
            nested = ''.join(branch(child) for child in children.get(node['id'], []))
            return f'<li>{node_text(node)}' + (f'<ul>{nested}</ul>' if nested else '') + '</li>'

        body = '<ul class="tree">' + branch(children[None][0]) + '</ul>'
    elif kind == 'mind_map':
        root, *branches = payload['nodes']
        items = ''.join(f'<li>{node_text(node)}</li>' for node in branches)
        body = f'<div class="map"><div class="hub">{node_text(root)}</div><ul>{items}</ul></div>'
    elif kind == 'timeline':
        items = ''.join(f'<li><strong>{escape(event["time"])}</strong> {escape(event["label"])}</li>'
                        for event in payload['events'])
        body = f'<ol class="timeline">{items}</ol>'
    else:
        body = chart(payload)

    return f"""<style>
        #round2-card h2 {{ margin: 0 0 20px; font-size: 26px; }}
        #round2-card ul, #round2-card ol {{ list-style: none; margin: 0; }}
        #round2-card .tree {{ padding: 0; }}
        #round2-card .tree ul {{ border-left: 2px solid #9db7c5; padding-left: 24px; margin-left: 12px; }}
        #round2-card .tree li {{ position: relative; padding-top: 8px; }}
        #round2-card .tree ul > li::before {{
            content: ''; position: absolute; left: -24px; top: 24px; width: 18px; border-top: 2px solid #9db7c5;
        }}
        #round2-card .node {{ display: inline-block; padding: 6px 12px; background: #edf4f7; border-radius: 6px; }}
        #round2-card .detail {{ display: block; }}
        #round2-card .map {{ display: grid; grid-template-columns: 1fr 2fr; align-items: center; }}
        #round2-card .hub {{ position: relative; padding-right: 30px; }}
        #round2-card .hub::after, #round2-card .map li::before {{
            content: ''; position: absolute; top: 50%; border-top: 2px solid #9db7c5;
        }}
        #round2-card .hub::after {{ right: 0; width: 30px; }}
        #round2-card .hub .node {{ box-sizing: border-box; width: 100%; background: #d8edf2; }}
        #round2-card .map ul {{ border-left: 2px solid #9db7c5; padding-left: 28px; }}
        #round2-card .map li {{ position: relative; margin: 8px 0; }}
        #round2-card .map li::before {{ left: -28px; width: 28px; }}
        #round2-card .timeline {{ border-left: 2px solid #9db7c5; margin-left: 6px; padding-left: 22px; }}
        #round2-card .timeline li {{ position: relative; margin: 14px 0; }}
        #round2-card .timeline li::before {{
            content: ''; position: absolute; top: 9px; left: -28px; width: 10px; height: 10px;
            border-radius: 50%; background: #23758a;
        }}
        #round2-card .timeline strong {{ display: block; color: #206678; }}
        #round2-card .chart {{ display: grid; grid-template-columns: 32% 1fr auto; gap: 10px 14px; align-items: center; }}
        #round2-card .track {{ position: relative; height: 24px; background: #edf4f7; }}
        #round2-card .zero {{ position: absolute; height: 100%; width: 1px; background: #607985; }}
        #round2-card .bar {{ position: absolute; top: 3px; bottom: 3px; background: #23758a; }}
        #round2-card .value {{ font-variant-numeric: tabular-nums; }}
    </style><article id="round2-card" style="{STYLE}"><h2>{title}</h2>{body}</article>"""


def node_text(node):
    description = node.get('description')
    detail = f'<span class="detail">{escape(description)}</span>' if description else ''
    return f'<span class="node"><strong>{escape(node["label"])}</strong>{detail}</span>'


def chart(payload):
    points = payload['points']
    values = [float(point['value']) for point in points]
    low, high = min(0, *values), max(0, *values)
    extent = high - low or 1
    zero = -100 * low / extent
    unit = ' ' + escape(payload['unit']) if payload.get('unit') else ''
    rows = []
    for point, value in zip(points, values):
        left = 100 * (min(0, value) - low) / extent
        width = 100 * abs(value) / extent
        rows.append(f'<span>{escape(point["label"])}</span><div class="track">'
                    f'<i class="zero" style="left:{zero:.8f}%"></i>'
                    f'<i class="bar" style="left:{left:.8f}%;width:{width:.8f}%"></i></div>'
                    f'<strong class="value">{escape(point["value"])}{unit}</strong>')
    return '<div class="chart">' + ''.join(rows) + '</div>'
