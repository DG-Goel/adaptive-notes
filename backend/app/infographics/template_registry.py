"""Exactly fifteen approved choices; native AntV 0.2.20 source-inspected contracts."""
from dataclasses import dataclass,asdict
from types import MappingProxyType

REGISTRY_VERSION='noetra-templates-v1'
ANTV_VERSION='0.2.20'


@dataclass(frozen=True)
class Template:
    code: str
    antv: str
    purpose: str
    family: str
    required: tuple
    optional: tuple=()
    recommended_items: tuple=(2,8)
    description_support: str='native desc; rendering behavior pending browser verification'
    limitation: str='No semantic suitability guarantee from structural validation.'
    native_mapping: str='items'
    antv_version: str=ANTV_VERSION
    documentation_status: str='package-source-verified'
    browser_status: str='not-tested-phase7'

    @property
    def category(self): return self.code[0]


_TEMPLATES=(
 Template('A1','hierarchy-mindmap-branch-gradient-capsule-item','Central concept and related branches','hierarchy',('root',),native_mapping='root'),
 Template('A2','hierarchy-tree-curved-line-rounded-rect-node','Strict taxonomy with parent-child classifications','hierarchy',('root',),native_mapping='root'),
 Template('A3','hierarchy-structure','Component layers, groups and subcomponents','grouped',('groups',),recommended_items=(2,7),description_support='structure consumes labels; adapter folds desc into labels',limitation='At most layer/group/component depth is mapped; deeper source requires support.',native_mapping='items[].children[].children'),
 Template('A4','list-grid-badge-card','Independent explained facts without invented hierarchy','list',('items',)),
 Template('A5','sequence-pyramid-simple','Meaningfully ordered conceptual levels','sequence',('items','order_basis'),recommended_items=(3,6),native_mapping='sequences; order asc'),
 Template('B1','sequence-snake-steps-compact-card','Ordered nonbranching procedure','sequence',('items','order_basis'),recommended_items=(3,10),native_mapping='sequences; order asc'),
 Template('B2','sequence-circular-simple','Source-supported repeating stages','sequence',('items','order_basis','cycle_refs'),recommended_items=(3,6),limitation='Closure requires explicit source refs; references alone do not prove a genuine cycle.',native_mapping='sequences; order asc'),
 Template('B3','sequence-timeline-rounded-rect-node','Chronology with literal dates or periods','sequence',('items','order_basis'),recommended_items=(2,8),native_mapping='sequences; order asc; time folded into label'),
 Template('B4','relation-dagre-flow-tb-badge-card','Directed dependencies and conditional relationships','graph',('nodes','relations'),recommended_items=(2,15),native_mapping='nodes; relations from/to/direction forward'),
 Template('B5','sequence-interaction-default-compact-card','Actor lanes and ordered uniquely identified actions','interaction',('actors','actions','relations'),recommended_items=(2,5),description_support='lane desc supported; action desc folded into label',native_mapping='items actor lanes with children action id/step; relations'),
 Template('C1','compare-binary-horizontal-simple-fold','Exactly two entities and comparable attributes','comparison',('groups',),recommended_items=(2,2),native_mapping='compares: two roots and child comparison points'),
 Template('C2','compare-quadrant-quarter-simple-card','Four groups justified by two analytical dimensions','comparison',('groups','dimensions'),recommended_items=(4,4),native_mapping='compares: four roots; dimensions in data desc'),
 Template('C3','chart-bar-plain-text','Comparable numerical categories and shared units','numeric',('values','unit'),recommended_items=(2,10),native_mapping='values; exact numeric text retained in labels'),
 Template('C4','chart-line-plain-text','Ordered numerical observations with meaningful progression','numeric',('values','unit','order_basis'),recommended_items=(2,15),limitation='Package places observations at equal index spacing, not a continuous numerical time axis.',native_mapping='values in input order; progression in data desc'),
 Template('C5','chart-pie-donut-plain-text','Nonnegative mutually exclusive parts of a named whole','numeric',('values','unit','whole','whole_refs','exclusive_refs'),recommended_items=(2,7),limitation='Whole/exclusivity refs require later semantic verification; negative/zero-total values rejected.',native_mapping='values; whole and unit in data desc'),
)
REGISTRY=MappingProxyType({t.code:t for t in _TEMPLATES})


def choices(category):
    return [dict(code=t.code,purpose=t.purpose,family=t.family,required=t.required,
                 optional=t.optional,recommended_items=t.recommended_items,limitations=t.limitation)
            for t in _TEMPLATES if t.category==category]


def registry_metadata(): return [asdict(t) for t in _TEMPLATES]
