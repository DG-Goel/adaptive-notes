"""Hand-authored reference annotations and scripted mock outputs, never model output."""
import json
from pathlib import Path

from app.extraction.prompts import CATEGORY_FIELDS
from prototype import AtomicFact, MockResponse


BACKEND = Path(__file__).resolve().parents[3]
SMOKE = BACKEND / "data/output/groq_strict_t0022_20261103_8daaab0610db4f2f"
source = json.loads((SMOKE / "source_units.json").read_text(encoding="utf-8"))
SOURCES = {unit["source_id"]: unit["text"] for unit in source["source_units"]}
CHUNK = "JAVA_CHUNK_000"


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


REFERENCE = [
    ("f001", "In the example, assigning to final variable pi causes a compilation error.",
     "we have a compilation error and it says cannot assign a value to final variable pi", "final pi example"),
    ("f002", "The example's constant pi should be named PI under the capital-letter convention.",
     "so pi is a final variable or a constant now by convention we use all capital letters to name constants so this should be PI", "constant naming example"),
    ("f003", "In the division example, the integer declaration conflicts with the double expression result.",
     "now we have a compilation error because on the left side we declared an integer but here the result of this expression is a double", "division example"),
    ("f004", "In the division example, changing the declaration to double repairs the mismatch.",
     "so to fix this problem we need to change this to double", "division example"),
    ("f005", "In this division example, float or double are conversion alternatives for a floating-point result.",
     "if you want to get a floating-point number here you need to convert these numbers to a float or a double", "division example"),
    ("f006", "In the increment example, x starts at 1 and prints 2 after incrementing.",
     "declare a new variable int X we set it to 1 now if you want to increase the value of x by 1 we use the increment operator now let's print this on a terminal so we get 2", "increment example"),
    ("f007", "Modulus is the remainder of a division.", "modulus which is the remainder of a division", "arithmetic introduction"),
    ("f008", "In Java, division of two whole numbers yields a whole number.",
     "in Java the division of two whole numbers is a whole number", "Java arithmetic"),
    ("f009", "An expression is a piece of code that produces a value.",
     "an expression is a piece of code that produces a value", "expression definition"),
    ("f010", "In the addition example, printing the result of 10 plus 3 gives 13.",
     "declare an integer called result and here we can type 10 plus 3 now when we print result it's gonna be 13", "addition example"),
]
FACTS = {}
for fid, claim, quote, scope in REFERENCE:
    links = [{"relation": "repairs", "target_id": "f003"}] if fid == "f004" else []
    FACTS[fid] = AtomicFact.model_validate_json(compact(dict(
        fact_id=fid, source_id="T0022", claim=claim, quote=quote, scope=scope,
        relationships=links)))
A = {"facts": [f.model_dump(mode="json", exclude_defaults=True) for f in FACTS.values()]}


def review_fact(fact):
    return FACTS.get(fact.fact_id) == fact


# Manually scoped structuring decisions and field support annotations.
ANNOTATIONS = {category: [] for category in CATEGORY_FIELDS}


def annotate(category, fields, ids, paths=None):
    refs = {path: ids for path in (paths or [f"/{key}" for key in fields])}
    ANNOTATIONS[category].append({**fields, "evidence_refs": refs})


for fid in ("f001", "f002", "f005", "f008"):
    claim = FACTS[fid].claim
    annotate("facts", {"content": claim, "fact_text": claim}, [fid])
repair = FACTS["f004"].claim
annotate("procedures", {
    "procedure_name": "Repair the declaration mismatch in the division example",
    "steps": [repair],
    "content": FACTS["f003"].claim + " " + repair,
}, ["f003", "f004"], ["/procedure_name", "/steps/0", "/content"])
ANNOTATIONS["procedures"][0]["evidence_refs"]["/steps/0"] = ["f004"]
for fid, term in (("f007", "modulus"), ("f009", "expression")):
    claim = FACTS[fid].claim
    annotate("definitions", {"term": term, "content": claim, "definition_text": claim}, [fid])
for fid, topic in (("f006", "increment operator"), ("f010", "addition")):
    claim = FACTS[fid].claim
    annotate("examples", {"exemplifies": topic, "content": claim, "example_text": claim}, [fid])


def approved_fields():
    for category, rows in ANNOTATIONS.items():
        for row in rows:
            for path, ids in row["evidence_refs"].items():
                value = row
                for part in path[1:].split("/"):
                    value = value[int(part)] if isinstance(value, list) else value[part]
                yield category, path, value, frozenset(ids)


APPROVED = tuple(approved_fields())
B = json.loads(compact(ANNOTATIONS))


def review_field(category, path, value, facts):
    return (category, path, value, frozenset(f.fact_id for f in facts)) in APPROVED


def mock_a(sources):
    assert sources == SOURCES
    return MockResponse(compact(A))


def mock_b(facts):
    assert all(review_fact(fact) for fact in facts.values())
    return MockResponse(compact(B))
