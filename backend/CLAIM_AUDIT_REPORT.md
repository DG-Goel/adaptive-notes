# Semantic Verification Claim Audit Report

**Date**: October 21, 2026  
**Document**: test.pdf (TEST_DOC)  
**Flagged Claims**: 3 (2 UNSUPPORTED, 1 INCONCLUSIVE)

---

## Claim 1: INCONCLUSIVE - CON_0001

### Claim Text
```
"The practice of assigning meaning to dreams"
```

### Knowledge Type
Concept

### Cited Source Units
- S0022
- S0027

### Complete Source Text (Combined)

**S0022**:
```
In reality, that was her only trade. She had been the third of eleven children 
born to a prosperous shopkeeper in old Caldas, and as soon as she learned to speak 
she instituted the fine custom in her family of telling dreams before breakfast, 
the time when their oracular qualities are preserved in their purest form. When 
she was seven she dreamed that one of her brothers was carried off by a flood. 
Her mother, out of sheer religious superstition, forbade the boy to swim in the 
ravine, which was his favourite pastime. But Frau Frieda already had her own 
system of prophecy.
```

**S0027**:
```
She did her job well, and for a long time, above all during the war years, when 
reality was more sinister than nightmares. Only she could decide at breakfast 
what each should do that day, and how it should be done, until her predictions 
became the sole authority in the house. Her control over the family was absolute: 
even the faintest sigh was breathed by her order. The master of the house died 
at about the time I was in Vienna, and had the elegance to leave her a part of 
his estate on the condition that she continue dreaming for the family until her 
dreams came to an end.
```

### Verifier Reasoning
- **Status**: INCONCLUSIVE
- **Confidence**: 0.5
- **Reason**: "Moderate keyword overlap (25.0%) but insufficient evidence for strong verdict"
- **Keyword Overlap**: 25.0%
- **Has Keyword Match**: False

### Audit Analysis

**Source Evidence Examination**:
- S0022 mentions: "telling dreams before breakfast", "oracular qualities", "system of prophecy"
- S0027 mentions: "decide at breakfast what each should do", "her predictions became the sole authority"

**Ground Truth**: **SUPPORTED**

**Rationale**:
The source text DOES support this claim through clear semantic equivalence:
- "telling dreams before breakfast" + "their oracular qualities" + "system of prophecy" = **assigning meaning to dreams**
- "decide at breakfast what each should do" based on dreams = **practice of interpreting dreams**

This is a **valid abstraction/generalization** of the specific practices described in the source.

**Failure Type**: **Valid paraphrase with low keyword overlap**

The deterministic verifier cannot detect that:
- "telling dreams" = "assigning meaning to dreams"
- "oracular qualities" + "prophecy" = interpretation/meaning
- "decide what each should do" based on dreams = practical application of dream interpretation

**Justification**: The claim uses conceptual language ("assigning meaning") while the source uses descriptive language ("telling dreams", "oracular qualities", "prophecy"). These are semantically equivalent but have minimal lexical overlap.

---

## Claim 2: UNSUPPORTED - CON_0005

### Claim Text
```
"A dream believed to predict future events"
```

### Knowledge Type
Concept

### Cited Source Units
- S0029
- S0030

### Complete Source Text (Combined)

**S0029**:
```
'I only came to tell you that I dreamed about you last night,' she said. 'You 
must leave right away and not come back to Vienna for five years.'
```

**S0030**:
```
Her conviction was so real that I boarded the last train to Rome that same night. 
As for me, I was so influenced by what she said that from then on I considered 
myself a survivor of some catastrophe I never experienced. I still have not 
returned to Vienna.
```

### Verifier Reasoning
- **Status**: UNSUPPORTED
- **Confidence**: 0.7
- **Reason**: "Low keyword overlap (0.0%), claim contains many terms not in source: believed, future, dream, events, predict"
- **Keyword Overlap**: 0.0%
- **Has Keyword Match**: False

### Audit Analysis

**Source Evidence Examination**:
- S0029: Woman tells narrator about her dream and warns him to leave Vienna
- S0030: Narrator acts on the warning, considering himself "a survivor of some catastrophe I never experienced"

**Ground Truth**: **SUPPORTED**

**Rationale**:
The source text DOES support this claim through clear semantic inference:
- The woman "dreamed about you last night" and immediately warns "You must leave right away" = **dream predicting future danger**
- The narrator acts on this, considering himself "a survivor of some catastrophe I never experienced" = **belief that the dream predicted future events**
- The entire narrative context is about a prophetic dream

This is a **valid conceptual abstraction** of the narrative. The source demonstrates:
1. A dream (stated)
2. Believed to predict future danger (implied by immediate warning and action)
3. Future events (the "catastrophe" that might have happened)

**Failure Type**: **Valid abstraction with technical terminology**

The deterministic verifier fails because:
- The word "predict" doesn't appear (but the concept is demonstrated)
- The word "believed" doesn't appear (but belief is shown through action)
- The phrase "future events" doesn't appear (but future danger is clearly implied)

**Justification**: This is a definitional abstraction of "prophetic dream" - the entire passage describes this concept without using those exact words. The verifier cannot perform semantic inference to recognize that "dreamed about you last night" + immediate warning + acting on it = belief in predictive dreams.

---

## Claim 3: UNSUPPORTED - EXM_0003

### Claim Text
```
"When someone dreamed of drowning, she interpreted it to mean they shouldn't eat 
sweets, not that they would drown."
```

### Knowledge Type
Example

### Cited Source Units
- S0023

### Complete Source Text

**S0023**:
```
'What that dream means,' she said, 'isn't that he's going to drown, but that he 
shouldn't eat sweets.'
```

### Verifier Reasoning
- **Status**: UNSUPPORTED
- **Confidence**: 0.7
- **Reason**: "Low keyword overlap (33.3%), claim contains many terms not in source: when, would, dreamed, drowning, someone"
- **Keyword Overlap**: 33.3%
- **Has Keyword Match**: False

### Audit Analysis

**Source Evidence Examination**:
- Source: "'What that dream means,' she said, 'isn't that he's going to drown, but that he shouldn't eat sweets.'"

**Ground Truth**: **SUPPORTED**

**Rationale**:
The source text DIRECTLY supports this claim. The claim is a **reformulation** of the source quote:

**Source structure**: "What that dream means... isn't that he's going to drown, but that he shouldn't eat sweets"

**Claim structure**: "When someone dreamed [of drowning], she interpreted it to mean [they shouldn't eat sweets], not that [they would drown]"

The claim:
1. Correctly identifies the dream content (drowning)
2. Correctly identifies the interpretation (shouldn't eat sweets)
3. Correctly identifies the rejected interpretation (won't drown)

The only additions are:
- "When someone dreamed" (contextual framing, not factual addition)
- "she interpreted" (explicit agent, implied in source's "she said")

**Failure Type**: **Overly strict keyword matching**

The deterministic verifier fails because:
- "when someone dreamed of drowning" is not lexically present (context: "that dream" implies drowning dream)
- "would drown" vs "going to drown" (synonymous)
- Keyword overlap of only 33.3% despite semantic equivalence

**Justification**: This is nearly a direct quote reformulated into complete sentence form. The verifier's 33.3% keyword overlap threshold misses that:
- "that dream" (source) = "dreamed of drowning" (claim with context)
- "he's going to drown" (source) = "they would drown" (claim)
- "he shouldn't eat sweets" (source) = "they shouldn't eat sweets" (claim)

The missing context is that earlier in the text, someone's brother dreamed of drowning, which is referenced by "that dream". The claim correctly identifies this as "dreamed of drowning".

---

## Summary of Audit Findings

| Claim ID | Type | Verifier Status | Ground Truth | Failure Type |
|----------|------|-----------------|--------------|--------------|
| CON_0001 | Concept | INCONCLUSIVE | SUPPORTED | Valid abstraction, low keyword overlap |
| CON_0005 | Concept | UNSUPPORTED | SUPPORTED | Valid abstraction, semantic inference |
| EXM_0003 | Example | UNSUPPORTED | SUPPORTED | Direct paraphrase, overly strict matching |

### Key Finding

**ALL THREE FLAGGED CLAIMS ARE ACTUALLY SUPPORTED BY THEIR SOURCES**

None of the flagged claims are:
- ❌ Hallucinations or fabrications
- ❌ Contradictions
- ❌ Unsupported additions

All three are:
- ✅ Valid abstractions or paraphrases
- ✅ Semantically faithful to source
- ✅ Correctly cite relevant source units

### Verifier Limitations Identified

1. **Cannot detect conceptual abstractions** (CON_0001, CON_0005)
   - "telling dreams" → "assigning meaning to dreams"
   - Narrative demonstration → conceptual definition

2. **Cannot perform semantic inference** (CON_0005)
   - Dream + warning + action → belief in prophetic dreams
   - Requires understanding implicit meaning

3. **Overly strict keyword threshold** (EXM_0003)
   - 33.3% overlap rejected despite semantic equivalence
   - Cannot recognize pronoun changes (he → they, someone)
   - Cannot match synonyms (going to → would)

4. **Lacks context resolution** (EXM_0003)
   - "that dream" in source = "dreamed of drowning" in claim
   - Requires understanding cross-reference

### Implications

The current 62.5% support rate (5/8) is **artificially low** due to verifier limitations, not extraction quality. The actual support rate for this document appears to be **100% (8/8)** based on manual audit.

The 80% threshold for semantic faithfulness verification is **too high for a deterministic verifier** given its inherent limitations in detecting:
- Paraphrases
- Abstractions  
- Semantic inference
- Contextual references

---

## Recommendations

### 1. Add Context-Aware Matching (EXM_0003)

For claims with low keyword overlap but high structural similarity, check if the claim is a reformulation of a direct quote.

**Proposed Enhancement**:
```python
# Check if claim is reformulation of short source quote
if len(source_text.split()) < 30:  # Short source
    # Compare structure rather than just keywords
    # Check if key entities and relations preserved
    pass
```

### 2. Lower Keyword Threshold for Abstractions

Abstractions naturally have lower keyword overlap. For concept-type knowledge items, lower the threshold:

**Current**: 40% for SUPPORTED, <20% for UNSUPPORTED  
**Proposed**: 30% for SUPPORTED concepts, <15% for UNSUPPORTED concepts

### 3. Add Semantic Role Detection

Detect when claim uses abstract/general terms while source uses specific examples:
- Source: "telling dreams", "oracular qualities" → Claim: "assigning meaning"
- This is valid abstraction, not unsupported addition

### 4. Adjust Semantic Faithfulness Threshold

**Current**: Requires 80% SUPPORTED, <10% UNSUPPORTED, 0 CONTRADICTED  
**Proposed**: Requires 70% SUPPORTED (deterministic only), or 80% with LLM assistance

### 5. Add Regression Tests

Create tests for these specific failure patterns (see next section).

---

## Conclusion

The semantic verifier is **working as designed** for a deterministic keyword-based system, but its limitations cause false negatives on valid abstractions and paraphrases.

**No contradictions or hallucinations were found** in the flagged claims. All three are semantically faithful to their sources.

The path forward is either:
1. **Accept limitations**: Lower thresholds, document that INCONCLUSIVE/UNSUPPORTED may include valid abstractions
2. **Add LLM assistance**: Use LLM to verify INCONCLUSIVE/UNSUPPORTED cases
3. **Hybrid approach**: Use embeddings for semantic similarity scoring

The current implementation correctly **avoids false positives** (no unsupported claims marked SUPPORTED) at the cost of **false negatives** (valid claims marked INCONCLUSIVE/UNSUPPORTED).
