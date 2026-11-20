"""Optional source-backed instructional review; no inferred correctness defaults."""
from typing import Literal
from pydantic import BaseModel,Field,ConfigDict


class ReviewQuote(BaseModel):
    model_config=ConfigDict(extra='forbid')
    source_id:str
    quote:str=Field(min_length=1,pattern=r'\S')


class InstructionLink(BaseModel):
    kind:Literal['corrected_by','explained_by','alternative','prerequisite','continuation','qualified_by','counterexample','derivation','worked_example','warning','exception','experiment','conclusion']
    target_id:str
    evidence:list[ReviewQuote]=Field(min_length=1)


class FieldReview(BaseModel):
    model_config=ConfigDict(extra='forbid')
    path:str=Field(pattern=r'^/')
    mode:Literal['literal','faithful_paraphrase','source_supported_synthesis','incomplete','unsupported_reconstruction','contradicted','requires_review']
    status:Literal['SUPPORTED','PARTIALLY_SUPPORTED','UNSUPPORTED','CONTRADICTED','INCONCLUSIVE','NOT_REVIEWED']='NOT_REVIEWED'
    evidence:list[ReviewQuote]=Field(default_factory=list)
    reviewer:str|None=None
    rationale:str|None=None


class EducationalReview(BaseModel):
    model_config=ConfigDict(extra='forbid')
    role:Literal['correct_demonstration','deliberately_incorrect_demonstration','identified_mistake','explanation_of_mistake','corrected_approach','alternative_valid_approach','prerequisite','continuation','unresolved']='unresolved'
    links:list[InstructionLink]=Field(default_factory=list)
    field_reviews:list[FieldReview]=Field(default_factory=list)
    evidence:list[ReviewQuote]=Field(default_factory=list)
    formula_status:Literal['COMPLETE','INCOMPLETE','AMBIGUOUS','VISUAL_CONTEXT_REQUIRED','NEEDS_REVIEW']='NEEDS_REVIEW'
    code_kind:Literal['literal','verbal','partial','incorrect','corrected_literal','reconstructed','unclassified']='unclassified'
    status:Literal['SUPPORTED','PARTIALLY_SUPPORTED','UNSUPPORTED','CONTRADICTED','INCONCLUSIVE','NOT_REVIEWED']='NOT_REVIEWED'
    reviewer:str|None=None
    rationale:str|None=None
    severity:Literal['minor','major','critical']='major'
    unresolved:bool=True
    automated:bool=False
