"""Static HTML/JavaScript checks only; does not launch or control a browser."""
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import subprocess

P=Path('data/output/task8_semantic_readiness_20261109')
class Parser(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.scripts=[];self.current=None;self.external=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'id' in attrs:self.ids.append(attrs['id'])
        if tag in ('script','link','img','iframe'):
            for name in ('src','href'):
                if attrs.get(name,'').startswith(('http:','https:','//')):self.external.append(attrs[name])
        if tag=='script':self.current=dict(attrs=attrs,text='')
    def handle_data(self,data):
        if self.current is not None:self.current['text']+=data
    def handle_endtag(self,tag):
        if tag=='script' and self.current is not None:self.scripts.append(self.current);self.current=None

parser=Parser();html=(P/'evidence_desk.html').read_text(encoding='utf-8');parser.feed(html)
assert len(parser.ids)==len(set(parser.ids))
data=next(s for s in parser.scripts if s['attrs'].get('type')=='application/json')
workspace=json.loads(data['text'])
script='\n'.join(s['text'] for s in parser.scripts if s['attrs'].get('type')!='application/json')
assert all(name in parser.ids for name in re.findall(r"el\('([^']+)'\)",script))
assert not parser.external and not re.search(r'fetch\(|XMLHttpRequest',script)
(P/'review_desk_script.js').write_text(script,encoding='utf-8')
result=subprocess.run(['node','--check',str(P/'review_desk_script.js')],capture_output=True,text=True,timeout=20)
assert result.returncode==0,result.stderr
report=dict(html_ids_unique=True,referenced_controls_present=True,embedded_json_valid=True,
    javascript_syntax_valid=True,external_resources_or_requests=False,fields=len(workspace['inventory']),
    visual_browser_test='NOT_COMPLETED',
    reasons=['Automatic approval review rejected reading an existing Chrome window titled Project Status Summary because it could expose unrelated private content.',
             'Isolated in-app browser URL policy disallows file URLs. No workaround, alternate browser access or policy bypass attempted.'],
    static_checks_are_not_browser_usability_validation=True)
(P/'static_ui_checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
