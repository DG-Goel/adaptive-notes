"""Conservative review signals, never an entailment certificate."""
import re


def review_claim(claim, excerpts):
    source=' '.join(excerpts)
    missing_numbers=sorted(set(re.findall(r'\b\d+(?:\.\d+)?\b',claim))-set(re.findall(r'\b\d+(?:\.\d+)?\b',source)))
    families={'may':r'may|might|could|can|possible|possibly|potential',
              'under':r'under|when|if|conditions?', 'only':r'only|restricted|limited|exclusively',
              'if':r'if|when|provided|conditional', 'approximately':r'approximately|about|roughly|around|estimated'}
    qualifiers=[q for q,alternatives in families.items() if re.search(r'\b'+q+r'\b',source.lower())
                and not re.search(r'\b(?:'+alternatives+r')\b',claim.lower())]
    negation=bool(re.search(r'\b(?:not|never|no)\b',source.lower())) != bool(re.search(r'\b(?:not|never|no)\b',claim.lower()))
    return {'status':'unverified','semantic_verified':False,'review_required':True,
            'signals':{'unsupported_numbers':missing_numbers,'possibly_lost_qualifiers':qualifiers,
                       'possible_contradiction':negation},
            'limitation':'Signals can have false positives; partial support, contradiction and entailment require claim-level review.'}
