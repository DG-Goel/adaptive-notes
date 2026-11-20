"""Audited downstream orchestration; unverified output is always a preview."""
from collections import Counter
import json
from app.extraction.consolidation import consolidate
from app.extraction.knowledge_merge import validate_provenance
from app.analysis.analyzer import ContentAnalyzer
from app.representation.selector import RepresentationSelector
from app.representation.formats import RepresentationFormat as F
from app.assembly.assembler import NoteAssembler
from app.rendering.renderer import MarkdownRenderer


def build_preview(knowledge, source, *, required_chunks, completed_chunks, topic_expectations=None):
    consolidated,audit=consolidate(knowledge)
    items={i.knowledge_id:i for i in consolidated.get_all_items()}
    representations=RepresentationSelector().select(ContentAnalyzer().analyze(consolidated))
    fallbacks=[]
    for rep in representations.representations:
        item=items[rep.knowledge_id]
        # Diagrams must have actual typed structure, not keyword-created placeholders.
        safe={F.STANDARD_TEXT:True,F.DEFINITION_BOX:item.knowledge_type=='definition',
              F.EXAMPLE_CALLOUT:item.knowledge_type=='example',F.FORMULA_DISPLAY:item.knowledge_type=='formula',
              F.FLOWCHART:item.knowledge_type=='procedure' and bool(getattr(item,'steps',[])),
              F.CAUSE_EFFECT_DIAGRAM:item.knowledge_type=='relationship' and getattr(item,'relationship_type','') in ('causal','causes','cause_effect'),
              F.HIERARCHY_TREE:item.knowledge_type=='relationship' and getattr(item,'relationship_type','') in ('is_a','part_of'),F.COMPARISON_TABLE:False,F.TIMELINE:False}
        if not safe.get(rep.primary_format,False):
            fallbacks.append(dict(id=rep.knowledge_id,reason='No explicit supported structure for selected representation'))
            rep.primary_format=F.STANDARD_TEXT;rep.format_content={'content':item.content}
            rep.confidence_label='fallback';rep.selection_reasoning=fallbacks[-1]['reason']
        rep.secondary_format=None;rep.secondary_content=None
    from app.evaluation.educational_safeguards import apply_safeguards
    educational=apply_safeguards(consolidated,source,representations)
    representations.update_statistics()
    assembled=NoteAssembler().assemble(representations)
    rendered=MarkdownRenderer().render(assembled)
    # Preserve details omitted by a format-specific presentation without inventing prose.
    details=[]
    for item in items.values():
        fields=item.model_dump(exclude={'knowledge_id','document_id','source_unit_ids','section','page_range','confidence','extraction_metadata','knowledge_type','educational_review'})
        details.append({'id':item.knowledge_id,'sources':item.source_unit_ids,'fields':fields,
                        'metadata':item.extraction_metadata,'suppressed_fields':next(r.educational_context.get('suppressed_fields',[]) for r in representations.representations if r.knowledge_id==item.knowledge_id),'original_ids':audit['original_ids'][item.knowledge_id]})
    rendered_ids={i.knowledge_id for i in rendered.manifest.items}
    sources={u.source_id:u for u in source.source_units}
    coverage={sid:[] for sid in sources}
    for item in items.values():
        metadata=item.extraction_metadata or {}
        for sid in metadata.get('primary_source_ids',item.source_unit_ids):
            if sid in coverage:coverage[sid].append(item.knowledge_id)
    gaps=[sid for sid,u in sources.items() if not u.educational_assessment.excluded and not coverage[sid]]
    provenance=validate_provenance(consolidated,source)
    gates={
        'extraction_completion':{'outcome':'PASS' if set(required_chunks)==set(completed_chunks) else 'FAIL','required':list(required_chunks),'completed':list(completed_chunks)},
        'structural_validity':{'outcome':'PASS' if rendered_ids==set(items) else 'FAIL','missing_items':sorted(set(items)-rendered_ids)},
        'semantic_faithfulness':{'outcome':'NEEDS_REVIEW' if provenance.valid else 'FAIL','mechanical_provenance':provenance.model_dump(),'semantic_entailment_verified':False},
        'educational_completeness':{'outcome':'NEEDS_REVIEW','source_units_without_primary_knowledge':gaps,'topic_coverage':'NOT_EVALUATED'},
        'notes_usability':{'outcome':'NEEDS_REVIEW','fallbacks':fallbacks,'render_warnings':[w.model_dump() for w in rendered.manifest.warnings]}}
    if any(i['severity']=='critical' for i in educational['issues']):
        gates['semantic_faithfulness']['outcome']='FAIL'
    topic_review=[]
    for topic in topic_expectations or []:
        valid=(topic['source_id'] in sources and topic['quote'] in (sources[topic['source_id']].text or ''))
        represented=bool(topic.get('represented_by')) and all(k in items for k in topic.get('represented_by',[]))
        topic_review.append({**topic,'source_evidence_valid':valid,'represented':represented})
    if topic_expectations is not None:
        gates['educational_completeness']['topic_coverage']=topic_review
        if any(not t['source_evidence_valid'] or not t['represented'] for t in topic_review):
            gates['educational_completeness']['outcome']='FAIL'
    report=dict(educational_review=educational,publication_eligible=False,status='UNVERIFIED_PREVIEW',gates=gates,source_coverage=coverage,
        before=len(knowledge.get_all_items()),after=len(items),consolidation=audit,
        representation_distribution=dict(Counter(r.primary_format.value for r in representations.representations)),
        knowledge_quality={'supported':None,'partially_supported':None,'unsupported':None,'contradicted':None,'inconclusive':len(items)},
        examples_preserved=sum(i.knowledge_type=='example' for i in items.values()),
        original_knowledge=details,manual_review_required=True)
    report['coverage_dimensions']={'primary_sources_with_items':sum(bool(v) for v in coverage.values()),
        'primary_sources_total':len(sources),'accepted_items_before_consolidation':len(knowledge.get_all_items()),
        'items_after_consolidation':len(items),'rendered_item_ids':len(rendered_ids),
        'knowledge_ids_missing_from_render':sorted(set(items)-rendered_ids),
        'examples_in_audit':sum(i.knowledge_type=='example' for i in items.values()),
        'procedures_in_audit':sum(i.knowledge_type=='procedure' for i in items.values()),
        'topic_coverage':'REVIEWED_INVENTORY_ONLY' if topic_expectations is not None else 'NOT_EVALUATED'}
    report['coverage_dimensions']['nonquotable_sources']=[{'source_id':u.source_id,
        'state':u.representation_status or 'awaiting_interpretation','limitations':u.interpretation_limitations,
        'counts_as_completed':False} for u in source.source_units if not u.text]
    report['ingestion']=source.ingestion
    withheld=[{'item_id':r.knowledge_id,'paths':r.educational_context['withheld_paths']} for r in representations.representations if r.educational_context.get('withheld_paths')]
    report['coverage_dimensions']['student_fields_withheld_for_review']=withheld
    if withheld:gates['educational_completeness']['outcome']='FAIL'
    # Append only substantive fields absent from the formatted body. Literal fences
    # retain mathematical/code notation and prevent source Markdown injection.
    supplemental=[]
    renderer=MarkdownRenderer()
    for detail in details:
        seen=set()
        missing={}
        for key,value in detail['fields'].items():
            if key in detail['suppressed_fields'] or not value or str(value) in rendered.content or str(value) in seen:continue
            seen.add(str(value));missing[key]=value
        if missing:
            supplemental.extend(['### Additional details: '+detail['id']])
            for key,value in missing.items():
                supplemental.append('**'+key.replace('_',' ').capitalize()+':**')
                if isinstance(value,list):supplemental.extend('- '+renderer._escape_markdown(str(v),True) for v in value)
                elif isinstance(value,dict):supplemental.extend('- '+renderer._escape_markdown(str(k))+': '+renderer._escape_markdown(str(v),True) for k,v in value.items())
                else:supplemental.append(renderer._escape_markdown(str(value),True))
            supplemental.extend(['Sources: '+', '.join(detail['sources']),''])
    from pathlib import Path
    body=rendered.content.replace('# '+source.filename,'# Study notes: '+renderer._escape_markdown(Path(source.filename).stem.replace('_',' ')),1)
    markdown='> UNVERIFIED PREVIEW — semantic and educational review required.\n\n'+body+'\n'+ '\n'.join(supplemental)
    return dict(markdown=markdown,report=report,knowledge=consolidated,representations=representations,
                assembled=assembled,rendered=rendered)
