"""Single authorized strict-evidence T0022 request. No retries or recovery."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd().resolve()))
import json,os,logging
from hashlib import sha256
import httpx
from dotenv import load_dotenv
from app.extraction.extractor import KnowledgeExtractor
from app.extraction.llm_provider import GroqProvider
from app.extraction.knowledge_merge import validate_provenance
from app.models.source import SourceDocument
from app.models.knowledge import KnowledgeDocument

out=Path(__file__).resolve().parent
root=Path.cwd().resolve()
assert Path(sys.prefix).resolve()==root/'.venv'
assert not (out/'request_started.json').exists(), 'Request already started; no second request allowed'
logging.disable(logging.CRITICAL)
load_dotenv(root/'.env',override=False)
assert os.getenv('GROQ_MODEL')=='openai/gpt-oss-120b'
pre=json.loads((out/'preflight.json').read_text(encoding='utf-8'))
messages=json.loads((out/'assembled_messages.json').read_text(encoding='utf-8'))
source=SourceDocument.model_validate_json((out/'source_units.json').read_text(encoding='utf-8'))
source_path=Path(pre['source_path'])
source_before=source_path.read_bytes()
keys=[os.getenv(f'GROQ_API_KEY_{i}') for i in range(1,6)]
keys=[key for key in keys if key] or [os.getenv('GROQ_API_KEY')]
assert keys and keys[0], 'No configured Groq credential'
secrets=keys+[value for name,value in os.environ.items()
              if value and any(word in name.upper() for word in ('API_KEY','TOKEN','SECRET','PASSWORD'))]
def save(name,value):
    with (out/name).open('x',encoding='utf-8') as f:
        json.dump(value,f,indent=2,ensure_ascii=False)
def safe(value):
    serialized=json.dumps(value,ensure_ascii=True)
    return not any(secret in serialized for secret in secrets if len(secret)>=8)
provider=GroqProvider(model='openai/gpt-oss-120b',api_key=keys[0],use_multi_key=False,max_retries=1)
network={'requests':0,'status_codes':[]}
def request_hook(request):
    assert network['requests']==0, 'Second provider request prohibited'
    payload=json.loads(request.content)
    assert payload['model']=='openai/gpt-oss-120b'
    assert payload['messages']==[
        {'role':'system','content':messages['system']},
        {'role':'user','content':messages['user']}]
    assert payload['max_tokens']==pre['budget']['max_output_tokens']
    assert extractor.strict_evidence is True
    assert payload['response_format']=={'type':'json_object'}
    assert payload['temperature']==0.0
    assert provider.key_pool is None
    assert provider.client.max_retries==0
    save('request_metadata.json',{'provider':'Groq','payload':payload,'authorization':'[REDACTED]','extractor_retries':0,'sdk_retries':0,'credential_rotation':False})
    network['requests']+=1
def response_hook(response):
    network['status_codes'].append(response.status_code)
    # Preserve only model output/usage, never HTTP request headers or credential metadata.
    response.read()
    try:
        body=response.json()
    except ValueError:
        body={'unparseable_body':provider._sanitize_error(response.text)}
    body={key:body[key] for key in ('choices','model','usage','error','object','created') if key in body}
    if safe(body):
        save('raw_model_response.json',body)
    else:
        save('raw_response_withheld.json',{'reason':'Potential credential match in response'})
client=httpx.Client(event_hooks={'request':[request_hook],'response':[response_hook]})
provider.client=provider.client.with_options(max_retries=0,timeout=90.0,http_client=client)
extractor=KnowledgeExtractor(provider,verbose=False,max_retries=0,max_split_depth=0,strict_evidence=True)
assert extractor.strict_evidence and extractor.max_retries==0
original_generate=provider.generate
def checked_generate(prompt,system=None,temperature=0.0,max_tokens=4000):
    assert prompt==messages['user'] and system==messages['system']
    assert max_tokens==pre['budget']['max_output_tokens']
    return original_generate(prompt=prompt,system=system,temperature=temperature,max_tokens=max_tokens)
provider.generate=checked_generate
def failed_response(response,chunk_id,error_msg):
    data={'chunk_id':chunk_id,'error':provider._sanitize_error(error_msg)}
    if safe(response):
        data['response']=response
    save('parse_failure.json',data)
extractor._save_failed_response=failed_response
save('request_started.json',{'maximum_requests':1,'command':'.\\.venv\\Scripts\\python.exe -B '+str(Path(__file__).resolve()),
                            'strict_evidence':extractor.strict_evidence,'input_sha256':sha256(source_before).hexdigest()})
result=None
error=None
try:
    result=extractor.extract(source)
except Exception as exception:
    error={'type':type(exception).__name__,'message':provider._sanitize_error(str(exception))}
finally:
    client.close()
raw_path=out/'raw_model_response.json'
raw=json.loads(raw_path.read_text(encoding='utf-8')) if raw_path.exists() else {}
content=None
if raw.get('choices'):
    content=raw['choices'][0].get('message',{}).get('content')
parsed=None
json_error=None
if isinstance(content,str):
    try:
        parsed=json.loads(content)
    except ValueError as exception:
        json_error=str(exception)
if parsed is not None and safe(parsed):
    save('parsed_response.json',parsed)
if result:
    save('knowledge.json',result.model_dump(mode='json'))
    save('source_grounding.json',{item.knowledge_id:item.extraction_metadata for item in result.get_all_items()})
provenance=validate_provenance(result,source) if result else None
metadata=getattr(provider,'last_response_metadata',{})
technical=bool(network['requests']==1 and network['status_codes']==[200] and parsed is not None
               and result and result.total_items>0 and provenance.valid
               and metadata.get('model')=='openai/gpt-oss-120b'
               and metadata.get('finish_reason')=='stop'
               and result.extraction_metadata.get('extraction_successful'))
save('technical_validation.json',{
    'status':'PENDING_MANUAL_REVIEW' if technical else 'FAILED',
    'provider':'Groq','model':'openai/gpt-oss-120b','network':network,
    'response_metadata':metadata,'json_valid':parsed is not None,'json_error':json_error,
    'strict_evidence':extractor.strict_evidence,'validated_item_count':result.total_items if result else 0,
    'provenance':provenance.model_dump() if provenance else None,
    'extraction_diagnostics':result.extraction_metadata if result else None,
    'provider_error':getattr(provider,'last_error_metadata',None),'unexpected_error':error,
    'semantic_entailment_verified':False,'release':'NO-GO'})
assert source_path.read_bytes()==source_before
print(json.dumps({'status':'PENDING_MANUAL_REVIEW' if technical else 'FAILED',
                  'network':network,'response_metadata':metadata,'json_valid':parsed is not None,
                  'validated_items':result.total_items if result else 0,'error':error},ensure_ascii=True))
