"""Synthetic transport and review-desk regressions, not real semantic judgments."""
import json
from copy import deepcopy
from datetime import datetime,timezone,timedelta
import pytest
from tests.test_semantic_review_workflow import fixture,decision
from app.evaluation.semantic_review import build_review_inventory,append_decision,resolve_reviews,verify_history
from app.evaluation.review_outputs import evidence_desk_html
from import_semantic_reviews import import_reviews


def test_reimport_cannot_resurrect_a_withdrawn_approval():
    k,s=fixture();w=build_review_inventory(k,s)
    original=decision(w)
    h=append_decision(w,[],original)
    reset=deepcopy(original);reset.update(status='NOT_REVIEWED',rationale='Synthetic withdrawal of the original fixture decision.')
    h=append_decision(w,h,reset)
    repeated=append_decision(w,h,original)
    assert len(repeated)==2
    assert all(r['semantic_status']=='NOT_REVIEWED' for r in resolve_reviews(w,repeated)['inventory'])


def test_a_genuine_new_follow_up_is_preserved():
    k,s=fixture();w=build_review_inventory(k,s);first=decision(w)
    h=append_decision(w,[],first)
    follow=deepcopy(first);follow.update(rationale='A separate synthetic follow-up with a new recorded rationale.',reviewed_at=datetime.now(timezone.utc).isoformat())
    h=append_decision(w,h,follow)
    assert len(h)==2 and h[0]['decision']['rationale']==first['rationale']
    verify_history(h)


def test_member_order_and_timestamp_format_do_not_restore_old_approval():
    k,s=fixture();w=build_review_inventory(k,s);original=decision(w)
    history=append_decision(w,[],original)
    withdrawal=deepcopy(original);withdrawal.update(status='NOT_REVIEWED',rationale='Synthetic withdrawal before a formatting-only replay.')
    history=append_decision(w,history,withdrawal)
    replay=deepcopy(original);replay['members'].reverse()
    from datetime import timezone
    replay['reviewed_at']=datetime.fromisoformat(original['reviewed_at']).astimezone(timezone(timedelta(hours=5,minutes=30))).isoformat()
    result=append_decision(w,history,replay)
    assert result==history and resolve_reviews(w,result)['inventory'][0]['semantic_status']=='NOT_REVIEWED'


@pytest.mark.parametrize('bad',['not_list','unknown_status','stale_source','partial_members','missing_identity','naive_time'])
def test_invalid_batch_is_rejected_before_output(tmp_path,bad):
    k,s=fixture();w=build_review_inventory(k,s)
    kp=tmp_path/'k.json';sp=tmp_path/'s.json';dp=tmp_path/'d.json';out=tmp_path/'out'
    kp.write_text(k.model_dump_json(),encoding='utf-8');sp.write_text(s.model_dump_json(),encoding='utf-8')
    d=decision(w)
    if bad=='unknown_status':d['status']='VERIFIED'
    if bad=='stale_source':d['source_version']='changed'
    if bad=='partial_members':d['members']=d['members'][:1]
    if bad=='missing_identity':d['reviewer']=' '
    if bad=='naive_time':d['reviewed_at']='2026-11-09T00:00:00'
    payload={'decisions':[d]} if bad=='not_list' else [decision(w),d]
    dp.write_text(json.dumps(payload),encoding='utf-8')
    with pytest.raises(ValueError):import_reviews(kp,sp,dp,out)
    assert not out.exists()


def test_missing_and_contradictory_evidence_do_not_auto_approve():
    k,s=fixture();k.facts[0].content=k.facts[0].fact_text='The sample always reacts, including when wet.'
    w=build_review_inventory(k,s)
    assert all(r['semantic_status']=='NOT_REVIEWED' for r in w['inventory'])
    k.facts[0].extraction_metadata['source_grounding']['evidence']=[]
    w=build_review_inventory(k,s)
    with pytest.raises(ValueError,match='valid evidence'):append_decision(w,[],decision(w))


def test_review_desk_contains_navigation_warning_and_session_controls():
    k,s=fixture();w=resolve_reviews(build_review_inventory(k,s),[]);html=evidence_desk_html(w)
    for marker in ('id="warnings"','id="previous"','id="next"','id="source-nav"','id="item-nav"','id="session-log"',
                   'Incomplete formula / visual-context warning','Valid field-specific evidence is required',
                   'forms.set(selected.packet_id,formState())','No review is saved to the server.'):
        assert marker in html
    assert 'connect-src' not in html  # Deployment policy belongs to the test server, not model/source text.


def test_source_change_invalidates_history_without_changing_it():
    k,s=fixture();w=build_review_inventory(k,s);h=append_decision(w,[],decision(w));before=deepcopy(h)
    s.source_units[1].text+=' The example was withdrawn.'
    resolved=resolve_reviews(build_review_inventory(k,s),h)
    assert h==before and len(resolved['invalidated_decisions'])==1
    assert not any(r['semantic_status']=='SUPPORTED' for r in resolved['inventory'])
