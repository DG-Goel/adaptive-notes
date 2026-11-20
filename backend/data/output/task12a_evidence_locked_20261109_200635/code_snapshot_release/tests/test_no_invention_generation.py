"""Source-only generation contracts; mocks are not live quality measurements."""
import copy,json
from pathlib import Path
import pytest
from app.models.source import SourceDocument,SourceUnit
from app.models.knowledge import Fact,Formula,Example,KnowledgeDocument,Procedure
from app.extraction.no_invention import assess_claim,VERSION
from app.extraction.canonical_grounding import resolve_response,response_format
from app.extraction.context_grounding import chunk_prompt
from app.extraction.source_context import bind_context
from app.extraction.chunker import ContentChunker
from app.extraction.prompts import CATEGORY_FIELDS
from app.extraction.extractor import KnowledgeExtractor
from app.extraction.llm_provider import MockLLMProvider
from app.evaluation.notes_pipeline import build_preview

ROOT=Path(__file__).resolve().parents[1]


def source(texts):
    return SourceDocument(document_id='D',filename='controlled.txt',page_count=0,
        source_units=[SourceUnit(source_id=f'S{i}',document_id='D',position=i,type='paragraph',text=t)
                      for i,t in enumerate(texts)])


def response(**updates):
    return {**{c:[] for c in CATEGORY_FIELDS},'excluded':[],**updates}


def atomic(text,refs,**kw):
    return {'text':text,'refs':refs,'basis':'explicit','availability':'SOURCE_SUPPORTED','literal_kind':None,
            'instructional_role':None,'related_refs':[],**kw}


def value(claims):
    return {'text':' '.join(c['text'] for c in claims),
        'refs':list(dict.fromkeys(r for c in claims for r in c['refs']+c['related_refs'])),'claims':claims}


def extract(raw,s):
    chunk=bind_context(ContentChunker().chunk(s.source_units,s.document_id)[0],s.source_units)
    extractor=KnowledgeExtractor(MockLLMProvider(responses={},default_response=json.dumps(raw)),strict_evidence=True,verbose=False)
    extractor.valid_source_ids={u.source_id for u in s.source_units}
    extractor._evidence_sources={u.source_id:u.text for u in s.source_units}
    def transform(text):
        resolved,audit=resolve_response(text,chunk);extractor.generation_wire_audit=audit;return resolved
    extractor.response_transform=transform
    items=extractor._extract_from_chunk(chunk,s.document_id)
    groups={c:[] for c in CATEGORY_FIELDS}
    names={'fact':'facts','definition':'definitions','explanation':'explanations','example':'examples',
        'formula':'formulas','concept':'concepts','procedure':'procedures','relationship':'relationships'}
    for i in items:groups[names[i.knowledge_type]].append(i)
    knowledge=KnowledgeDocument(document_id='D',source_filename=s.filename,extraction_timestamp='offline-mock',**groups)
    return knowledge,extractor.generation_wire_audit


def preview(k,s):
    return build_preview(k,s,required_chunks=['offline'],completed_chunks=['offline'])


@pytest.mark.parametrize('original,paraphrase',[
    ('Cells divide to reproduce.','Cells reproduce through division.'),
    ('The sample may react under dry conditions.','Under dry conditions, a reaction is possible.'),
    ('The treaty was signed in 1918.','In 1918, the treaty was signed.'),
    ('The method must be called after the connection opens.','Call the method after opening the connection.'),
    ('Area equals pi times radius squared.','The area is pi multiplied by the square of the radius.')])
def test_faithful_paraphrases_stay_available_without_fake_approval(original,paraphrase):
    s=source([original]);v=value([atomic(paraphrase,['Q0000'],basis='direct_entailment')])
    k,_=extract(response(facts=[{'fact_text':v,'fact_type':None}]),s)
    result=preview(k,s)
    assert paraphrase in result['markdown']
    policy=k.facts[0].extraction_metadata['source_grounding']['generation_policy']
    assert not policy['semantic_entailment_verified']
    assert k.facts[0].educational_review is None
    assert all(c['semantic_review_status']=='NOT_REVIEWED' for f in policy['fields'] for c in f['claims'])


def test_mixed_field_preserves_supported_claim_and_withholds_invented_date():
    s=source(['Cells divide to reproduce.'])
    v=value([atomic('Cells reproduce through division.',['Q0000'],basis='direct_entailment'),
        atomic('This process was discovered in 2027.',['Q0000'])])
    k,audit=extract(response(facts=[{'fact_text':v,'fact_type':None}]),s)
    result=preview(k,s)
    assert 'Cells reproduce through division.' in result['markdown']
    assert '2027' not in result['markdown']
    assert '2027' in k.facts[0].fact_text  # Candidate retained in audit, not rewritten.
    assert any(r.get('policy')==VERSION for r in audit)
    assert result['report']['coverage_dimensions']['student_fields_withheld_for_review']


@pytest.mark.parametrize('state',['SOURCE_MISSING','VISUAL_CONTEXT_REQUIRED','AMBIGUOUS_SOURCE',
    'CONTRADICTORY_SOURCE','INCOMPLETE_LITERAL','REVIEW_REQUIRED','PARTIALLY_SUPPORTED'])
def test_abstention_keeps_independent_definitions_and_unresolved_coverage(state):
    s=source(['Principal P is the amount borrowed.','The complete expression is not provided.'])
    v={'text':'Principal P is the amount borrowed.','refs':['Q0000']}
    raw=response(facts=[{'fact_text':v,'fact_type':None}],formulas=[{'availability':state,
        'source_ids':['S1'],'reason':'Complete expression is unavailable'}])
    k,audit=extract(raw,s)
    assert k.facts and not k.formulas
    assert 'Principal P is the amount borrowed.' in preview(k,s)['markdown']
    record=next(a for a in audit if a.get('policy')==VERSION)['abstentions'][0]
    assert record['availability']==state and record['counts_as_completed'] is False
    assert state in preview(k,s)['markdown']


@pytest.mark.parametrize('problem',['unknown_ref','neighbor','uncovered_text','support_without_evidence','extra_property'])
def test_atomic_permissions_and_raw_schema_stay_strict(problem):
    s=source(['A cell divides.']);claim=atomic('A cell divides.',['Q0000']);v=value([claim])
    if problem=='unknown_ref':claim['refs']=['Q9999'];v=value([claim])
    elif problem=='neighbor':claim['related_refs']=['Q9999'];v=value([claim])
    elif problem=='uncovered_text':v['text']+=' Extra unsupported claim.'
    elif problem=='support_without_evidence':claim['refs']=[]
    else:v['claims'][0]['verified']=True
    chunk=ContentChunker().chunk(s.source_units,s.document_id)[0]
    with pytest.raises(ValueError):resolve_response(json.dumps(response(facts=[{'fact_text':v,'fact_type':None}])),chunk)


def test_context_cannot_be_abstained_or_extracted_as_primary():
    s=source(['A cell divides.','An unrelated observation.'])
    chunk=bind_context(ContentChunker()._create_chunk('one',[s.source_units[0]],None),s.source_units)
    with pytest.raises(ValueError):resolve_response(json.dumps(response(formulas=[
        {'availability':'SOURCE_MISSING','source_ids':['S1'],'reason':'missing'}])),chunk)


@pytest.mark.parametrize('code',['String path = "C:\\\\Windows\\\\";', 'x = inventedCall();','    if ready:\n        run()'])
def test_spoken_code_is_not_promoted_but_behavior_remains(code):
    s=source(['An escape sequence represents a special character.'])
    plain={'text':s.source_units[0].text,'refs':['Q0000']}
    example={'exemplifies':plain,'example_text':value([atomic(code,['Q0000'],literal_kind='literal_code')]),'example_type':None}
    k,_=extract(response(facts=[{'fact_text':plain,'fact_type':None}],examples=[example]),s)
    result=preview(k,s)
    assert code not in result['markdown']
    assert s.source_units[0].text in result['markdown']
    assert k.examples[0].example_text==code


def test_actual_literal_indentation_remains_exact():
    code='    if ready:\n        measure()\n';s=source([code])
    s.source_units[0].type='code'
    v=value([atomic(code,['Q0000'],literal_kind='literal_code')])
    k,_=extract(response(facts=[{'fact_text':v,'fact_type':None}]),s)
    assert k.facts[0].fact_text==code
    assert k.facts[0].extraction_metadata['source_grounding']['generation_policy']['fields'][0]['claims'][0]['eligible_for_preview']


def test_missing_mortgage_formula_keeps_supported_variable_definitions():
    s=source(['Principal P is the amount borrowed.','R is the monthly interest rate.',
              'The expression begins with P times R; additional expressions and division are not provided.'])
    def v(text,ref):return {'text':text,'refs':[ref]}
    raw=response(formulas=[{'formula_text':v('mortgage = P * R','Q0002'),
        'variables':[{'symbol':v('P','Q0000'),'description':v('Principal P is the amount borrowed.','Q0000')},
                     {'symbol':v('R','Q0001'),'description':v('R is the monthly interest rate.','Q0001')}],
        'conditions':None,'derivation':None}])
    k,_=extract(raw,s);result=preview(k,s)
    assert result['representations'].representations[0].primary_format=='standard_text'
    assert 'Principal P is the amount borrowed.' in result['markdown'] and 'monthly interest rate' in result['markdown']
    assert 'mortgage = P * R' not in result['markdown']
    states={c['availability'] for f in result['representations'].representations[0].educational_context['generation_policy']['fields'] for c in f['claims']}
    assert states & {'INCOMPLETE_LITERAL','VISUAL_CONTEXT_REQUIRED'}


def test_wrong_demonstration_and_correction_context_stay_linked():
    s=source(['The incorrect demonstration checks the general condition first.',
              'The correction checks the combined specific condition first.'])
    wrong=atomic(s.source_units[0].text,['Q0000'],instructional_role='deliberately_incorrect_demonstration',related_refs=['Q0001'])
    corrected=atomic(s.source_units[1].text,['Q0001'],instructional_role='corrected_approach',related_refs=['Q0000'])
    k,_=extract(response(facts=[{'fact_text':value([wrong]),'fact_type':None},
                               {'fact_text':value([corrected]),'fact_type':None}]),s)
    result=preview(k,s)
    assert 'INCORRECT DEMONSTRATION' in result['markdown'] and s.source_units[1].text in result['markdown']
    assert all(i.educational_review is None for i in k.facts)
    assert len(result['knowledge'].facts)==2


@pytest.mark.parametrize('claim',['The sample always reacts.','The sample reacts in 2027.'])
def test_qualification_loss_and_unsupported_expansion_use_source_not_invention(claim):
    s=source(['The sample may react under dry conditions.'])
    k,_=extract(response(facts=[{'fact_text':{'text':claim,'refs':['Q0000']},'fact_type':None}]),s)
    result=preview(k,s)
    assert claim not in result['markdown']
    assert s.source_units[0].text in result['markdown']
    assert not result['report']['publication_eligible']


def test_consolidation_does_not_merge_distinct_instructional_dispositions():
    from app.extraction.consolidation import consolidate
    s=source(['Check the condition.'])
    k,_=extract(response(facts=[{'fact_text':value([atomic('Check the condition.',['Q0000'],instructional_role='corrected_approach')]),'fact_type':None},
        {'fact_text':value([atomic('Check the condition.',['Q0000'],instructional_role='deliberately_incorrect_demonstration')]),'fact_type':None}]),s)
    result,_=consolidate(k)
    assert len(result.facts)==2


def test_task11_prepared_payloads_need_new_hashes():
    from app.extraction.organization_scheduler import ExtractionConfiguration,digest
    from app.extraction.organization_extraction import prepare_request
    from app.models.knowledge import ExtractionChunk
    p=ROOT/'data/output/task11_structured_ingestion_20261109_193204/controlled_txt/manifest.unapproved.json'
    old=json.loads(p.read_text(encoding='utf-8'));entry=old['requests'][0]
    config=ExtractionConfiguration.model_validate_json(json.dumps(old['configuration']))
    new,_=prepare_request(ExtractionChunk.model_validate(entry['chunk']),config)
    assert digest(new)!=entry['request_sha256']


def test_historical_windows_path_and_mortgage_are_not_complete_source_literals():
    from app.extraction.no_invention import assess_claim
    raw=json.loads((ROOT/'data/output/task8_semantic_readiness_20261109/knowledge_v8.json').read_text(encoding='utf-8'))
    s=json.loads((ROOT/'data/output/java_live_java-20261109_022409_842270/source_document.json').read_text(encoding='utf-8'))
    units={u['source_id']:u['text'] for u in s['source_units']}
    example=next(i for i in raw['examples'] if i['knowledge_id']=='EXM_0003')
    formula=next(i for i in raw['formulas'] if i['knowledge_id']=='FRM_0007')
    assert not assess_claim(example['example_text'],[units[s] for s in example['source_unit_ids']])['eligible_for_preview']
    assert not assess_claim(formula['formula_text'],[units[s] for s in formula['source_unit_ids']],formula=True)['eligible_for_preview']
    assert 'escape' in units['T0018'].lower()
    assert 'most specific conditions' in units['T0042']


def test_no_placeholder_comparisons_or_hierarchy_and_no_invented_dates():
    from app.representation.selector import RepresentationSelector
    from app.analysis.characteristics import AnalyzedKnowledge,ContentCharacteristic as C
    item=Fact(knowledge_id='F',document_id='D',source_unit_ids=['S0'],content='A sample was observed.',fact_text='A sample was observed.')
    analyzed=AnalyzedKnowledge(knowledge_item=item,characteristics=[C.HIERARCHY,C.COMPARISON,C.SEQUENCE],analysis_confidence='high',analysis_reasoning='controlled')
    selected=RepresentationSelector()._select_representation(analyzed)
    assert selected.primary_format=='standard_text'
    assert not any(s in str(selected.format_content) for s in ['Unknown','Property','Subject','Object','Root','Event'])


def test_no_semantic_claim_from_deterministic_screen():
    report=assess_claim('Leaves produce oxygen.',['Plants have leaves.'])
    assert report['availability']=='REVIEW_REQUIRED'
    assert report['semantic_verified'] is False
    assert report['semantic_review_status']=='NOT_REVIEWED'


def test_claim_level_source_ids_and_character_spans_are_preserved():
    s=source(['A cell divides.'])
    k,_=extract(response(facts=[{'fact_text':value([atomic('A cell divides.',['Q0000'])]),'fact_type':None}]),s)
    claim=k.facts[0].extraction_metadata['source_grounding']['generation_policy']['fields'][0]['claims'][0]
    assert claim['source_evidence'][0]['source_id']=='S0'
    assert claim['source_evidence'][0]['start_char']==0
    assert claim['source_evidence'][0]['end_char']==len(s.source_units[0].text)


def test_direct_assembly_route_cannot_leak_quarantined_code():
    from app.analysis.analyzer import ContentAnalyzer
    from app.representation.selector import RepresentationSelector
    from app.assembly.assembler import NoteAssembler
    from app.rendering.renderer import MarkdownRenderer
    s=source(['A special character can be represented by an escape sequence.'])
    v=value([atomic('String path = "invented";',['Q0000'],literal_kind='literal_code')])
    k,_=extract(response(facts=[{'fact_text':v,'fact_type':None}]),s)
    selected=RepresentationSelector().select(ContentAnalyzer().analyze(k))
    rendered=MarkdownRenderer().render(NoteAssembler().assemble(selected))
    assert 'String path' not in rendered.content
    assert s.source_units[0].text in rendered.content


def test_unsourced_placeholder_is_not_used_to_fill_required_content():
    record=assess_claim('Unknown',['A definition begins here but is incomplete.'])
    assert record['availability']=='SOURCE_MISSING' and not record['eligible_for_preview']
    assert assess_claim('Unknown',['The result is Unknown.'])['eligible_for_preview']


def test_separately_literal_code_fragments_cannot_be_spliced_into_source_code():
    s=source(['int first = 1;','int second = 2;'])
    for u in s.source_units:u.type='code'
    v=value([atomic('int first = 1;',['Q0000'],literal_kind='code_fragment'),
             atomic('int second = 2;',['Q0001'],literal_kind='code_fragment')])
    k,_=extract(response(facts=[{'fact_text':v,'fact_type':None}]),s)
    p=k.facts[0].extraction_metadata['source_grounding']['generation_policy']
    assert all(not c['eligible_for_preview'] for f in p['fields'] for c in f['claims'])
    text=preview(k,s)['markdown']
    assert 'int first = 1; int second = 2;' not in text
    assert 'int first = 1;' in text and 'int second = 2;' in text
