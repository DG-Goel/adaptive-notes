
const W=JSON.parse(document.getElementById('data').textContent), drafts=[], forms=new Map();
const el=id=>document.getElementById(id), rows=new Map(W.inventory.map(r=>[r.key,r]));
const statuses=['SUPPORTED','PARTIALLY_SUPPORTED','UNSUPPORTED','CONTRADICTED','INCONCLUSIVE','NOT_REVIEWED'];
for(const s of statuses){el('filter').add(new Option(s,s));el('decision').add(new Option(s,s))}el('decision').value='NOT_REVIEWED';
for(let n=0;n<=8;n++)el('risk').add(new Option(String(n),String(n)));
el('counts').textContent=`${W.inventory.length} fields · ${W.packets.length} exact-evidence bundles · atomic claim count not established`;
if(W.review_session){el('desk-heading').textContent=W.review_session.title;el('session-notice').textContent=W.review_session.status+' — '+W.review_session.notice}
let selected=null, matches=[];
function addButton(target,label,action){const b=document.createElement('button');b.textContent=label;b.onclick=action;target.append(b);return b}
function formState(){return {status:el('decision').value,rationale:el('rationale').value,quals:el('quals').checked,quotes:el('quotes').checked}}
function navigation(){const n=selected?matches.findIndex(p=>p.packet_id===selected.packet_id):-1;el('previous').disabled=n<=0;el('next').disabled=!matches.length||n===matches.length-1;el('filter-note').textContent=selected&&n<0?'Selected bundle is outside the current filter. Its exact identity remains shown above.':''}
function show(p){
 if(selected)forms.set(selected.packet_id,formState());selected=p;
 const rs=p.members.map(k=>rows.get(k)),scope=p.source_scope;
 el('title').textContent=p.packet_id;el('members').textContent=p.members.join(' | ');el('claim').textContent=p.claim;
 el('status').textContent=rs.map(r=>`${r.key}: ${r.semantic_status}`).join(' | ');
 const warnings=[];
 if(rs.some(r=>r.knowledge_type==='formula'&&r.formula_status!=='COMPLETE'))warnings.push('Incomplete formula / visual-context warning: the complete equation is not approved. Review components separately.');
 if(rs.some(r=>r.literal_code_form&&!r.literal_substring))warnings.push('Literal source fidelity is not established. Reconstructed code must remain withheld.');
 if(rs.some(r=>['UNSUPPORTED','CONTRADICTED'].includes(r.semantic_status)))warnings.push('Existing adverse disposition: this material is not approved for release. Check the rationale; literal-fidelity failure is separate from algorithm correctness.');
 if(rs.some(r=>!r.mechanical_validation.active_field_evidence_valid))warnings.push('Missing or invalid field evidence association: affirmative review import will be rejected.');
 if(rs.some(r=>['PARTIALLY_SUPPORTED','INCONCLUSIVE'].includes(r.semantic_status)))warnings.push('Partial or inconclusive support does not approve the entire field bundle.');
 if(scope.role==='deliberately_incorrect_demonstration')warnings.push('Deliberately incorrect demonstration: do not present this as the correct worked result.');
 el('warnings').replaceChildren();el('warnings').hidden=!warnings.length;el('warnings').className=warnings.length?'warning':'';
 for(const text of warnings){const line=document.createElement('p');line.textContent=text;el('warnings').append(line)}
 el('item-nav').replaceChildren();for(const id of [...new Set(rs.map(r=>r.item_id))])addButton(el('item-nav'),'View item '+id,()=>{el('item-details').open=true;el('item-content').textContent=JSON.stringify({item_id:id,fields:scope.qualification_context,instructional_role:scope.role,relationships:rs.flatMap(r=>r.relationships),notice:'Other item fields are context, not approved by this bundle decision.'},null,2);el('item-details').scrollIntoView()});
 el('source-nav').replaceChildren();el('evidence').replaceChildren();
 const seen=new Set();let sourceNumber=0;
 for(const e of p.evidence){const key=JSON.stringify([e.source_id,e.quote]);if(seen.has(key))continue;seen.add(key);
  const card=document.createElement('section');card.className='source-card';card.id='source-card-'+sourceNumber++;
  const label=document.createElement('p');label.className='source-tag';label.textContent=e.source_id+' · '+(scope.primary.includes(e.source_id)?'primary source':'contextual evidence');
  const quote=document.createElement('blockquote');quote.textContent=e.quote;card.append(label,quote);el('evidence').append(card);
  addButton(el('source-nav'),'Source '+e.source_id,()=>card.scrollIntoView());
 }
 if(!p.evidence.length){const note=document.createElement('p');note.textContent='No field-specific evidence supplied. Missing support cannot be inferred from neighboring context.';el('evidence').append(note)}
 el('scope-summary').textContent='Primary: '+scope.primary.join(', ')+'. Context: '+(scope.contextual.join(', ')||'none')+'. Repeated identical quotations are displayed once; original records are retained below.';
 el('mechanical').textContent=JSON.stringify({source_version:p.source_version,mechanical:rs.map(r=>r.mechanical_validation)},null,2);
 el('original').textContent=JSON.stringify({original_citations:rs.map(r=>r.original_evidence),scope},null,2);
 el('neighbors').textContent=JSON.stringify(p.neighbor_context,null,2);
 el('related').textContent=JSON.stringify(rs.map(r=>({related:r.relationships,risks:r.risk_reasons,suggested_defects:r.suggested_defect_categories})),null,2);
 el('history').textContent=JSON.stringify(rs.map(r=>({legacy:r.legacy_review,active:r.review_provenance,history:r.decision_history})),null,2);
 const state=forms.get(p.packet_id)||{status:'NOT_REVIEWED',rationale:'',quals:false,quotes:false};el('decision').value=state.status;el('rationale').value=state.rationale;el('quals').checked=state.quals;el('quotes').checked=state.quotes;el('message').textContent='';navigation();
}
function render(){const q=el('search').value.toLowerCase(),f=el('filter').value,priority=el('risk').value;
 matches=W.packets.filter(p=>p.members.some(k=>{const r=rows.get(k);return (!f||r.semantic_status===f)&&(!priority||String(r.risk_priority)===priority)&&(r.claim+' '+k+' '+r.source_ids.join(' ')+' '+r.evidence.map(e=>e.quote).join(' ')).toLowerCase().includes(q)}));
 matches.sort((a,b)=>Math.min(...a.members.map(k=>rows.get(k).risk_priority))-Math.min(...b.members.map(k=>rows.get(k).risk_priority))||a.packet_id.localeCompare(b.packet_id));
 el('list').replaceChildren();for(const p of matches.slice(0,120))addButton(el('list'),p.members.join(' | ')+' — '+p.claim.slice(0,100),()=>show(p));
 const note=document.createElement('small');note.textContent=`${matches.length} matches; first 120 shown. Search to narrow.`;el('list').append(note);navigation();
}
for(const id of ['search','filter','risk'])el(id).addEventListener('input',render);
el('previous').onclick=()=>{const n=matches.findIndex(p=>p.packet_id===selected?.packet_id);if(n>0)show(matches[n-1])};
el('next').onclick=()=>{const n=matches.findIndex(p=>p.packet_id===selected?.packet_id);if(n+1<matches.length)show(matches[n+1])};
el('save').onclick=()=>{
 if(!selected||!el('reviewer').value.trim()||!el('kind').value||!el('rationale').value.trim()){el('message').textContent='Choose a packet and provide reviewer type, identity and explanation.';return}
 const status=el('decision').value,rs=selected.members.map(k=>rows.get(k));
 if(['SUPPORTED','PARTIALLY_SUPPORTED'].includes(status)&&(!el('quals').checked||!el('quotes').checked)){el('message').textContent='Affirmative decisions require evidence and qualification checks.';return}
 if(['SUPPORTED','PARTIALLY_SUPPORTED'].includes(status)&&rs.some(r=>!r.mechanical_validation.active_field_evidence_valid)){el('message').textContent='Valid field-specific evidence is required before affirmative review.';return}
 if(status==='SUPPORTED'&&rs.some(r=>r.literal_code_form&&!r.literal_substring||r.knowledge_type==='formula'&&['/content','/formula_text'].includes(r.path)&&r.formula_status!=='COMPLETE')){el('message').textContent='Unverified literal code or an incomplete equation cannot be approved. Repair and review the source binding first.';return}
 drafts.push({packet_id:selected.packet_id,binding:selected.binding,source_version:W.source_version,members:selected.members,status,reviewer:el('reviewer').value.trim(),reviewer_kind:el('kind').value,reviewed_at:new Date().toISOString(),rationale:el('rationale').value.trim(),review_scope:'entire_field_bundle',qualifications_checked:el('quals').checked,evidence_checked:el('quotes').checked,factual_verification:'source_comparison_only'});
 el('session-log').textContent=JSON.stringify(drafts,null,2);el('export').disabled=false;el('message').textContent=`${drafts.length} draft decisions. Not accepted until version validation on import.`;
};
el('export').onclick=()=>{if(!drafts.length)return;const u=URL.createObjectURL(new Blob([JSON.stringify(drafts,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=u;a.download='semantic-review-drafts.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)};render();
