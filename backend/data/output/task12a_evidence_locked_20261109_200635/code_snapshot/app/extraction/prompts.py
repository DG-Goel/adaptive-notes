"""Source-only extraction prompts. JSON object mode; schemas are validated locally."""
import json
from typing import List, Optional

SOURCE_GROUNDING_RULES = """You extract educational knowledge from the supplied source only. Return one valid JSON object, no prose or fences.

AUTHORITATIVE SOURCE-GROUNDING CONTRACT
- No invented information or external subject knowledge. Mentioning a decrement operator does not support explaining decrement or any other unstated behavior.
- Distinguish spoken explanation from literal code. Never reconstruct code or formulas, declarations, comments, casts, outputs, aliases, or relationships.
- Do not compute results unless explicitly stated. Preserve conditions, alternatives and scope, including "in this example" and "float or double"; never turn a demonstration into a universal rule or required prerequisite.
- Preserve uncertainty and transcription ambiguity; never complete a missing sentence. Omission is preferable to invention for the missing portion; keep independently supported explanations and definitions. Faithful paraphrasing and simpler wording are permitted; unsupported facts are not.
- Empty categories are normal. Populate only supported categories; the item limit is a ceiling, not a target.
- Omit unsupported optional fields entirely. Do not fill them with placeholders, null or empty strings. Empty category arrays [] are different from omitted optional fields.
- Every populated substantive field needs exact supporting excerpts, including names, content, aliases, classifications, formula keys/descriptions/conditions, procedure steps/prerequisites/outcomes and relationship subjects/objects.
- Each source_evidence entry has source_id, quote and fields. Quotes must be exact source substrings. Use canonical source-unit IDs from source markers only; scheduling/chunk IDs are never provenance.
- fields lists only JSON Pointer paths to populated substantive fields. Cover all such fields; never reference omitted fields, empty containers, source IDs or generated metadata. Array indexes start at 0. List individual paths for every populated alias, step, prerequisite and nested array element, e.g. /steps/0, /steps/1, /steps/2; a parent collection path such as /steps never substitutes for its elements. Escape ~ as ~0 and / as ~1 in keys (RFC 6901), e.g. key a/b~ becomes /variables/a~1b~0. Populated dictionary keys require evidence even when values are empty; nested keys and their substantive descendants each need paths.
- Mechanical quotation matching is not semantic entailment verification. An excerpt must actually support its associated claim; no matching-word shortcut. Match the whole claim, not just its subject; use additional exact excerpts for separately stated details or omit those details. Do not add textbook definitions, operator symbols or lifecycle qualifications not stated in the source.
- Before returning, check explicit teaching facts: demonstrated initial/final values, error and repair, alternatives and naming corrections. Preserve each once with its source scope. Consolidate only related facts rather than duplicating them; avoid redundant term-only items when a supported item explains the term. Do not fill gaps or force a category. Aliases require source-stated synonyms, not instance names.

CONTRASTS
Mention-only: "We have a decrement operator" does not explain its effect or syntax; omit that explanation.
Spoken arithmetic: "ten plus three gives thirteen" stays prose; do not invent "int result = 10 + 3; // result is 13". Without the stated result, do not calculate it.
Literal code: if source contains "int result = 10 + 3;", retain that exact snippet only; add no comment, cast, output or declaration.
Alternatives: preserve "in this example, float or double", not "one operand must be cast to double".
Truncated: "apply this as a prefix and then..." supplies no remaining outcome or steps.
Scope: "here the division of two whole numbers is a whole number" supports that result, not an added "truncates fractional part" explanation.
Association: exact quote "modulus which is the remainder of a division" supports the remainder description, not an unstated % symbol.
Arrays: three steps require /steps/0, /steps/1, /steps/2, not /steps; two prerequisites require /prerequisites/0 and /prerequisites/1; two aliases require /aliases/0 and /aliases/1. Omitted arrays have no paths.
Coverage: if stated, retain x starting at 1 and printing 2; the final-variable pi assignment error; the separate integer-declaration/double-expression error and its declaration repair; float-or-double alternatives; and the pi-to-PI correction (naming, never an alias). Keep the two errors separate: declaration repair does not fix final-variable assignment. Never infer them from a partial passage.
"""
EXTRACTION_SYSTEM_PROMPT = SOURCE_GROUNDING_RULES
from app.extraction.no_invention import PRINCIPLES
EXTRACTION_SYSTEM_PROMPT+='\n'+PRINCIPLES+'''
Use the existing evidenced fields, not claims/abstention objects in this legacy wire.
Represent missing source information in a source-supported explanation when possible;
otherwise leave the category empty. No placeholder code, formulas, dates or diagrams.
Preserve deliberately wrong examples with their stated teaching purpose and correction.
'''
SOURCE_GROUNDING_RULES=EXTRACTION_SYSTEM_PROMPT

CATEGORY_FIELDS = {
    "concepts": {
        "required": [
            "concept_name"
        ],
        "optional": [
            "aliases"
        ]
    },
    "definitions": {
        "required": [
            "term",
            "definition_text"
        ],
        "optional": [
            "context"
        ]
    },
    "explanations": {
        "required": [
            "topic",
            "explanation_text"
        ],
        "optional": [
            "explanation_type"
        ]
    },
    "examples": {
        "required": [
            "exemplifies",
            "example_text"
        ],
        "optional": [
            "example_type"
        ]
    },
    "facts": {
        "required": [
            "fact_text"
        ],
        "optional": [
            "fact_type"
        ]
    },
    "formulas": {
        "required": [
            "formula_text"
        ],
        "optional": [
            "variables",
            "conditions",
            "derivation"
        ]
    },
    "procedures": {
        "required": [
            "procedure_name",
            "steps"
        ],
        "optional": [
            "prerequisites",
            "outcomes"
        ]
    },
    "relationships": {
        "required": [
            "relationship_type",
            "subject",
            "object"
        ],
        "optional": [
            "description"
        ]
    }
}

RESPONSE_SKELETON = {category: [] for category in CATEGORY_FIELDS}
EVIDENCE_EXAMPLE = {
    "concept_name": "expression",
    "content": "A piece of code that produces a value.",
    "source_unit_ids": [
        "EXAMPLE_ONLY"
    ],
    "source_evidence": [
        {
            "source_id": "EXAMPLE_ONLY",
            "quote": "An expression is a piece of code that produces a value.",
            "fields": [
                "/concept_name",
                "/content"
            ]
        }
    ]
}


def build_extraction_prompt(
    chunk_text: str, chunk_id: str, max_items_hint: int = 50,
    allowed_source_ids: Optional[List[str]] = None,
) -> str:
    """Keep source intact; category contracts are not an API JSON Schema."""
    source_ids = (json.dumps(list(dict.fromkeys(allowed_source_ids)), ensure_ascii=False)
                  if allowed_source_ids is not None else "canonical IDs in the source markers below")
    contracts = "\n".join(
        f"- {category}: required COMMON + {', '.join(fields['required'])}; "
        f"optional {', '.join(fields['optional'])}."
        for category, fields in CATEGORY_FIELDS.items()
    )
    return f"""Extract up to ~{max_items_hint} supported items, at most 200 words per item.
SCHEDULING ID (never cite): {chunk_id}
ALLOWED CANONICAL SOURCE IDs: {source_ids}
Apply the system grounding contract. Do not fill categories to meet a quota.

CATEGORY/FIELD CONTRACTS
COMMON REQUIRED on every item: content (string), source_unit_ids (nonempty string array),
source_evidence (nonempty array of source_id/quote/fields objects).
Category requirements add to COMMON; they never replace it.
{contracts}
Text/name/classification fields are strings; aliases, steps and prerequisites are
string arrays; variables maps source-stated symbols to source-stated descriptions.
For definitions, explanations, examples, facts and formulas, content repeats the
corresponding main text. Procedure content summarizes only the supplied steps.
Omit unsupported optional fields and their evidence paths. Do not send knowledge_id,
document_id or verification flags; the application supplies metadata.

RESPONSE SKELETON (empty arrays are valid; replace only supported categories)
{json.dumps(RESPONSE_SKELETON, ensure_ascii=False, separators=(',', ':'))}

ONE EVIDENCE EXAMPLE (instruction only; never extract or cite this example)
Example scheduling ID EXAMPLE_CHUNK is not a source ID.
Example source [EXAMPLE_ONLY]: An expression is a piece of code that produces a value.
{json.dumps(EVIDENCE_EXAMPLE, ensure_ascii=False, separators=(',', ':'))}
This example omits aliases and therefore has no /aliases/0 path.
Use actual source IDs and exact excerpts from the content below.

BEGIN SOURCE
{chunk_text}
END SOURCE
Return only the JSON object."""
    

def build_validation_prompt(knowledge_json: str, source_text: str) -> str:
    """
    Build prompt to validate extracted knowledge against source.
    
    Args:
        knowledge_json: Extracted knowledge in JSON format
        source_text: Original source text
        
    Returns:
        Validation prompt
    """
    
    return f"""Validate that the following extracted knowledge is accurately represented from the source text.

EXTRACTED KNOWLEDGE:
{knowledge_json}

SOURCE TEXT:
{source_text}

For each knowledge item, check:
1. Is it actually present in the source?
2. Is the wording accurate (not oversimplified or distorted)?
3. Are important qualifications or context preserved?
4. Are the source_unit_ids correct?

Respond with JSON:
{{
  "valid": true/false,
  "issues": [
    {{
      "knowledge_id": "...",
      "issue": "description of problem",
      "severity": "critical|warning|minor"
    }}
  ]
}}"""
