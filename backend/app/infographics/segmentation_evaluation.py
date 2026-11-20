"""Independent fixture-based diagnostics; never a semantic-fact verifier."""
from collections import Counter
from .segmentation_budget import words


def evaluate(fixture,manifest,tolerance=0):
    if type(tolerance) is not int or tolerance<0: raise ValueError('Invalid boundary tolerance')
    n=len(fixture['blocks']); ownership=Counter(); invalid=0; ends=set(); confusion=Counter(); matches=0; total=0
    valid=[]
    for segment in manifest:
        left,right=segment.get('start_position'),segment.get('end_position')
        if type(left) is not int or type(right) is not int or not 0<=left<=right<n:
            invalid+=1; continue
        valid.append(segment); ownership.update(range(left,right+1))
        if right<n-1: ends.add(right)
        for i in range(left,right+1):
            allowed=fixture['acceptable_categories'][i]; actual=segment.get('category','?')
            total+=1; matches+=actual in allowed
            confusion[(allowed[0],actual)]+=1
    required=set(fixture['required_boundaries']); acceptable=set(fixture['acceptable_boundaries'])
    candidates=sorted((abs(a-b),a,b) for a in ends for b in acceptable if abs(a-b)<=tolerance)
    used_a=set();used_b=set()
    for _,a,b in candidates:
        if a not in used_a and b not in used_b: used_a.add(a);used_b.add(b)
    hit_required={b for b in required if any(abs(a-b)<=tolerance for a in ends)}
    precision=len(used_a)/len(ends) if ends else 1.
    recall=len(hit_required)/len(required) if required else 1.
    visuals=[s for s in valid if s.get('category')!='N']; count=len(visuals)
    low,high=fixture['visual_count_range']; unnecessary=len(ends-used_a)
    related=sum(any(min(group)<=e<max(group) for e in ends) for group in fixture['stay_together'])
    merged=sum(any(s['start_position']<=a<b<=s['end_position'] for s in valid) for a,b in fixture['independent_pairs'])
    complexity=sum(s.get('estimated_items',0)>fixture.get('max_items',20) for s in visuals)
    return dict(source_range_coverage=len(ownership)/max(1,n),missing_block_count=n-len(ownership),
        duplicate_ownership_count=sum(max(0,v-1) for v in ownership.values()),invalid_boundary_count=invalid,
        boundary_precision=precision,boundary_recall=recall,boundary_f1=2*precision*recall/(precision+recall) if precision+recall else 0,
        acceptable_boundary_match_rate=precision,missed_required_boundaries=sorted(required-hit_required),
        unnecessary_boundaries=unnecessary,generated_visual_count=count,annotated_visual_count=[low,high],
        unnecessary_splits=unnecessary,related_content_separated=related,
        source_words_per_visual=sum(words('\n'.join(fixture['blocks'][s['start_position']:s['end_position']+1])) for s in visuals)/max(1,count),
        fragmentation_severity=(unnecessary+related)/max(1,n-1),independent_concepts_merged=merged,
        required_boundaries_omitted=len(required-hit_required),segments_exceeding_complexity=complexity,
        excessive_conceptual_mixing=merged,master_category_accuracy=matches/max(1,total),acceptable_category_match_rate=matches/max(1,total),
        category_distribution=dict(Counter(s.get('category','?') for s in valid)),
        confusion_matrix={a+'->'+b:v for (a,b),v in confusion.items()},
        incorrect_nonvisual_classification=sum(s.get('category')=='N' and any('N' not in fixture['acceptable_categories'][i] for i in range(s['start_position'],s['end_position']+1)) for s in valid),
        target_visualization_count=[low,high],actual_visualization_count=count,
        soft_limit_adherence=count<=fixture['soft_limit'],budget_deviation=max(low-count,0,count-high),
        semantic_fact_coverage_verified=False)
