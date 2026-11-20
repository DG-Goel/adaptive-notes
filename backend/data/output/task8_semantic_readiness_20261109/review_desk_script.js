
const W=JSON.parse(document.getElementById('data').textContent), drafts=[];
const el=id=>document.getElementById(id), rows=new Map(W.inventory.map(r=>[r.key,r]));
const statuses=['SUPPORTED','PARTIALLY_SUPPORTED','UNSUPPORTED','CONTRADICTED','INCONCLUSIVE','NOT_REVIEWED'];
for(const s of statuses){el('filter').add(new Option(s,s));el('decision').add(new Option(s,s))}el('decision').value='NOT_REVIEWED';
for(let n=0;n<=8;n++)el('risk').add(new Option(String(n),String(n)));
el('counts').textContent=`${W.inventory.length} fields · ${W.packets.length} exact-evidence bundles · atomic claim count not established`;
let selected=null;
function show(p){selected=p;const rs=p.members.map(k=>rows.get(k));el('title').textContent=p.packet_id;el('members').textContent=p.members.join(' | ');el('claim').textContent=p.claim;
el('status').textContent=rs.map(r=>`${r.key}: ${r.semantic_status}`).join(' | ');
el('evidence').textContent=JSON.stringify({source_version:p.source_version,source_scope:p.source_scope,evidence:p.evidence,mechanical:rs.map(r=>r.mechanical_validation)},null,2);
el('original').textContent=JSON.stringify(rs.map(r=>r.original_evidence),null,2);el('neighbors').textContent=JSON.stringify(p.neighbor_context,null,2);
el('related').textContent=JSON.stringify(rs.map(r=>({related:r.relationships,risks:r.risk_reasons,suggested_defects:r.suggested_defect_categories})),null,2);
el('history').textContent=JSON.stringify(rs.map(r=>({legacy:r.legacy_review,active:r.review_provenance,history:r.decision_history})),null,2);
el('decision').value='NOT_REVIEWED';el('rationale').value='';el('quals').checked=false;el('quotes').checked=false;el('message').textContent='';}
function render(){const q=el('search').value.toLowerCase(),f=el('filter').value,priority=el('risk').value;
const packets=W.packets.filter(p=>p.members.some(k=>{const r=rows.get(k);return (!f||r.semantic_status===f)&&(!priority||String(r.risk_priority)===priority)&&(r.claim+' '+k+' '+r.source_ids.join(' ')).toLowerCase().includes(q)}));
packets.sort((a,b)=>Math.min(...a.members.map(k=>rows.get(k).risk_priority))-Math.min(...b.members.map(k=>rows.get(k).risk_priority))||a.packet_id.localeCompare(b.packet_id));
el('list').replaceChildren();for(const p of packets.slice(0,120)){const b=document.createElement('button');b.textContent=p.members.join(' | ')+' — '+p.claim.slice(0,100);b.onclick=()=>show(p);el('list').append(b)}
const note=document.createElement('small');note.textContent=`${packets.length} matches; first 120 shown. Search to narrow.`;el('list').append(note);}
for(const id of ['search','filter','risk'])el(id).addEventListener('input',render);
el('save').onclick=()=>{if(!selected||!el('reviewer').value.trim()||!el('kind').value||!el('rationale').value.trim()){el('message').textContent='Choose a packet and provide reviewer type, identity and explanation.';return}
const status=el('decision').value;if(['SUPPORTED','PARTIALLY_SUPPORTED'].includes(status)&&(!el('quals').checked||!el('quotes').checked)){el('message').textContent='Affirmative decisions require evidence and qualification checks.';return}
drafts.push({packet_id:selected.packet_id,binding:selected.binding,source_version:W.source_version,members:selected.members,status,reviewer:el('reviewer').value.trim(),reviewer_kind:el('kind').value,reviewed_at:new Date().toISOString(),rationale:el('rationale').value.trim(),review_scope:'entire_field_bundle',qualifications_checked:el('quals').checked,evidence_checked:el('quotes').checked,factual_verification:'source_comparison_only'});
el('message').textContent=`${drafts.length} draft decisions. Not accepted until version validation on import.`;};
el('export').onclick=()=>{const u=URL.createObjectURL(new Blob([JSON.stringify(drafts,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=u;a.download='semantic-review-drafts.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)};render();
