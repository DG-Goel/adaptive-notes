# Proposed intermediate contract

Stage A model output, illustrative fragment using a contiguous excerpt from T0022:

```json
{"facts":[{"claim":"In this example, the constant should be named PI under the capital-letter convention.","source_id":"T0022","quote":"by convention we use all capital letters to name constants so this should be PI"}]}
```

Require exactly one top-level facts array and explicit nonblank claim, source_id and quote strings on every row. Reject unknown keys, malformed containers and source IDs outside the supplied chunk. Match quote case and spacing literally. Use one contiguous quote per row. A literal ellipsis present in the source can match, while a fabricated join fails. Reject an empty array for this T0022 acceptance fixture, where supported facts are known to exist. Keep actual no-content cases a distinct, explicit outcome. A stage item remains a claim plus evidence, without category metadata or semantic certification.

After A validation, assign local fact IDs such as f001 and freeze a manifest containing ordered facts, source hash and chunk identity. Include no model-generated offsets. Exact quote occurrence metadata may be derived locally. B can reference only that manifest.

Proposed B fragment:

```json
{"facts":[{"fact_text":"The example's constant should be named PI under the capital-letter convention.","content":"The example's constant should be named PI under the capital-letter convention.","evidence_refs":{"/fact_text":["f001"],"/content":["f001"]}}]}
```

B keeps the eight existing category names and their common content and subtype fields. Its wire contract replaces copied quotes and model-supplied source IDs with a path-to-fact-ID map. Reject empty mappings, unknown IDs, omitted populated paths, references to absent optional fields, and parent paths used for leaves. Use existing RFC 6901 path semantics. Derive source_unit_ids and source_evidence from immutable facts and validate the expanded result with the existing strict contract. For one fact cited at several paths, emit one evidence record listing those independent paths. A B fact reference proves lineage only. The resolver cannot determine that a new paraphrase is entailed.
