"""Configurable, deterministic engineering heuristics; no model calls."""
from dataclasses import dataclass
import math
import re


def words(text):
    return len(re.findall(r'\w+',text,flags=re.UNICODE))


@dataclass(frozen=True)
class VisualizationBudgetConfig:
    anchors: tuple = ((1000,2,3,5),(2500,3,5,7),(5000,5,8,10),(10000,8,12,15),
                      (15000,10,15,20),(20000,12,18,24),(30000,15,25,35))
    complexity_weight: float = 0.15
    max_adjustment: float = 0.30
    interpolation: str = 'linear'

    def __post_init__(self):
        previous=0
        for size,low,high,soft in self.anchors:
            if not all(type(v) is int for v in (size,low,high,soft)) or not previous<size or not 1<=low<=high<=soft:
                raise ValueError('Invalid visualization budget anchors')
            previous=size
        if not self.anchors or self.interpolation not in {'linear','step'}:
            raise ValueError('Invalid budget interpolation')
        if not 0<=self.complexity_weight<=1 or not 0<=self.max_adjustment<=1:
            raise ValueError('Invalid complexity adjustment')


def recommendation(index,config=VisualizationBudgetConfig()):
    from .educational_content import educational_text
    count=words(educational_text(index))
    types=[b.type for b in index.blocks]
    n=max(1,len(types))
    indicators={kind:types.count(kind)/n for kind in ('heading','math','code','table')}
    chapters=len({b.section_path[:1] for b in index.blocks if b.section_path})
    diversity=len(set(types))/max(1,min(n,10))
    complexity=sum(indicators.values())+diversity+min(chapters/10,1)
    factor=1+min(config.max_adjustment,config.complexity_weight*complexity)
    anchors=config.anchors
    if count<=anchors[0][0]:
        values=[max(1,v*count/anchors[0][0]) for v in anchors[0][1:]]
    elif count>=anchors[-1][0]:
        values=[v*count/anchors[-1][0] for v in anchors[-1][1:]]
    else:
        for left,right in zip(anchors,anchors[1:]):
            if left[0]<=count<=right[0]:
                ratio=(count-left[0])/(right[0]-left[0]) if config.interpolation=='linear' else 0
                values=[a+(b-a)*ratio for a,b in zip(left[1:],right[1:])]
                break
    targets=[math.ceil(v*factor) if count else 0 for v in values]
    return dict(source_words=count,target_min=targets[0],target_max=targets[1],soft_upper_limit=targets[2],
                structural_indicators=indicators,major_chapters=chapters,structural_diversity=diversity,
                heuristic=True)


DEFAULT_CAPACITY = (
    ('A','Prefer 2-7 major branches, about 20 conceptual nodes, 3-8 independent groups, or 3-6 conceptual levels.'),
    ('B','Prefer 3-10 steps, 3-6 cyclic stages, 2-8 chronological events, about 15 relationship nodes, or 2-5 actors.'),
    ('C','Prefer two compared entities, four analytical groups, 2-10 numerical values, 2-15 ordered observations, or 2-7 proportions.'),
)
