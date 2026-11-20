"""
Semantic Verification Benchmark.

A controlled synthetic benchmark for evaluating the deterministic semantic verifier.
Contains clearly labeled test cases with known ground truth labels.

Categories:
- SUPPORTED: Claims directly or closely supported by source
- CONTRADICTED: Claims that conflict with source facts
- UNSUPPORTED: Claims adding unsupported facts
- INCONCLUSIVE: Valid paraphrases/abstractions with low keyword overlap

This is a SYNTHETIC benchmark using hand-crafted examples.
Results do NOT represent real-world performance on actual extracted knowledge.
"""

import pytest
from datetime import datetime
from typing import List, Tuple
from collections import Counter

from app.evaluation.semantic_verifier import (
    DeterministicSemanticVerifier,
    SemanticVerificationReport
)
from app.models.source import SourceDocument, SourceUnit
from app.models.knowledge import (
    KnowledgeDocument,
    Definition,
    Explanation,
    Fact,
    Concept
)


# ============================================================================
# Benchmark Data
# ============================================================================

def create_benchmark_case(
    case_id: str,
    source_text: str,
    claim_text: str,
    claim_type: str,
    expected_status: str,
    description: str
) -> Tuple[SourceDocument, KnowledgeDocument, str, str]:
    """
    Create a single benchmark test case.
    
    Returns:
        (source_doc, knowledge_doc, expected_status, description)
    """
    
    source_doc = SourceDocument(
        document_id=f"BENCH_{case_id}",
        filename="benchmark.pdf",
        page_count=1,
        source_units=[
            SourceUnit(
                source_id=f"S{case_id}",
                document_id=f"BENCH_{case_id}",
                page=1,
                type="text",
                content_role="content",
                text=source_text,
                position=1
            )
        ]
    )
    
    # Create appropriate knowledge item based on type
    if claim_type == "definition":
        items = {
            "definitions": [
                Definition(
                    knowledge_id=f"BENCH_{case_id}",
                    knowledge_type="definition",
                    source_unit_ids=[f"S{case_id}"],
                    document_id=f"BENCH_{case_id}",
                    content=claim_text,
                    term="test term",
                    definition_text=claim_text
                )
            ]
        }
    elif claim_type == "fact":
        items = {
            "facts": [
                Fact(
                    knowledge_id=f"BENCH_{case_id}",
                    knowledge_type="fact",
                    source_unit_ids=[f"S{case_id}"],
                    document_id=f"BENCH_{case_id}",
                    content=claim_text,
                    fact_text=claim_text
                )
            ]
        }
    elif claim_type == "explanation":
        items = {
            "explanations": [
                Explanation(
                    knowledge_id=f"BENCH_{case_id}",
                    knowledge_type="explanation",
                    source_unit_ids=[f"S{case_id}"],
                    document_id=f"BENCH_{case_id}",
                    content=claim_text,
                    topic="test topic",
                    explanation_text=claim_text
                )
            ]
        }
    else:  # concept
        items = {
            "concepts": [
                Concept(
                    knowledge_id=f"BENCH_{case_id}",
                    knowledge_type="concept",
                    source_unit_ids=[f"S{case_id}"],
                    document_id=f"BENCH_{case_id}",
                    content=claim_text,
                    concept_name="test concept",
                    aliases=[]
                )
            ]
        }
    
    knowledge_doc = KnowledgeDocument(
        document_id=f"BENCH_{case_id}",
        source_filename="benchmark.pdf",
        extraction_timestamp=datetime.now().isoformat(),
        **items
    )
    
    return source_doc, knowledge_doc, expected_status, description


# ============================================================================
# Benchmark Test Cases
# ============================================================================

BENCHMARK_CASES = [
    # CATEGORY 1: SUPPORTED (Direct matches, high keyword overlap)
    create_benchmark_case(
        "001",
        "Photosynthesis is the process by which plants convert sunlight into chemical energy.",
        "Photosynthesis is the process by which plants convert sunlight into chemical energy.",
        "definition",
        "SUPPORTED",
        "Exact match - identical text"
    ),
    
    create_benchmark_case(
        "002",
        "The French Revolution began in 1789 and lasted until 1799.",
        "The French Revolution began in 1789.",
        "fact",
        "SUPPORTED",
        "Partial match - subset of source facts"
    ),
    
    create_benchmark_case(
        "003",
        "Albert Einstein developed the theory of relativity in the early 20th century.",
        "Einstein developed the theory of relativity.",
        "fact",
        "SUPPORTED",
        "High keyword overlap - minor paraphrase"
    ),
    
    create_benchmark_case(
        "004",
        "DNA carries genetic information. It consists of nucleotides arranged in a double helix structure.",
        "DNA carries genetic information and consists of nucleotides.",
        "explanation",
        "SUPPORTED",
        "Combined facts from source"
    ),
    
    # CATEGORY 2: CONTRADICTED (Factual conflicts, numeric/entity mismatches)
    create_benchmark_case(
        "101",
        "The experiment involved 500 participants over 3 years.",
        "The experiment involved 300 participants.",
        "fact",
        "CONTRADICTED",
        "Numeric contradiction - wrong number"
    ),
    
    create_benchmark_case(
        "102",
        "Shakespeare was born in Stratford-upon-Avon in 1564.",
        "Shakespeare was born in Stratford-upon-Avon in 1654.",
        "fact",
        "CONTRADICTED",
        "Date contradiction - wrong year"
    ),
    
    create_benchmark_case(
        "103",
        "Marie Curie won the Nobel Prize in Physics in 1903.",
        "Marie Curie won the Nobel Prize in Chemistry in 1903.",
        "fact",
        "CONTRADICTED",
        "Entity contradiction - wrong field"
    ),
    
    create_benchmark_case(
        "104",
        "Water boils at 100 degrees Celsius at sea level.",
        "Water boils at 90 degrees Celsius at sea level.",
        "fact",
        "CONTRADICTED",
        "Numeric contradiction - wrong temperature"
    ),
    
    # CATEGORY 3: UNSUPPORTED (Added facts not in source)
    create_benchmark_case(
        "201",
        "The protagonist was a teacher.",
        "The protagonist was a mathematics teacher with 20 years of experience.",
        "fact",
        "UNSUPPORTED",
        "Added specific details not in source"
    ),
    
    create_benchmark_case(
        "202",
        "The city experienced rapid growth.",
        "The city's population increased by 45% due to industrial development and immigration.",
        "explanation",
        "UNSUPPORTED",
        "Added statistics and causes not in source"
    ),
    
    create_benchmark_case(
        "203",
        "The meeting was scheduled for Monday.",
        "The meeting was scheduled for Monday at 3 PM in Conference Room B.",
        "fact",
        "UNSUPPORTED",
        "Added time and location not in source"
    ),
    
    # CATEGORY 4: FAITHFUL PARAPHRASES (Valid but low keyword overlap)
    create_benchmark_case(
        "301",
        "Mitochondria are the powerhouses of the cell.",
        "Mitochondria generate cellular energy.",
        "definition",
        "INCONCLUSIVE",  # Verifier expected to struggle with paraphrase
        "Valid paraphrase - powerhouse to generate energy"
    ),
    
    create_benchmark_case(
        "302",
        "The character underwent a significant transformation.",
        "The character experienced profound personal change.",
        "explanation",
        "INCONCLUSIVE",
        "Valid paraphrase - transformation to personal change"
    ),
    
    create_benchmark_case(
        "303",
        "Climate change poses serious environmental threats.",
        "Global warming represents significant ecological risks.",
        "fact",
        "INCONCLUSIVE",
        "Valid paraphrase - synonyms with low overlap"
    ),
    
    # CATEGORY 5: VALID ABSTRACTIONS (Generalizations from specific)
    create_benchmark_case(
        "401",
        "The apple fell from the tree branch and landed on the ground with a soft thud.",
        "The apple fell from the tree.",
        "fact",
        "SUPPORTED",  # Should support abstractions that preserve facts
        "Valid abstraction - removed descriptive details"
    ),
    
    create_benchmark_case(
        "402",
        "She visited Paris, London, and Rome during her three-week European vacation.",
        "She traveled to multiple European cities.",
        "fact",
        "INCONCLUSIVE",  # Low keyword overlap but valid abstraction
        "Valid abstraction - generalized specifics"
    ),
    
    create_benchmark_case(
        "403",
        "The temperature rose from 20°C to 35°C between 8 AM and 2 PM.",
        "The temperature increased significantly during the day.",
        "fact",
        "INCONCLUSIVE",  # Numbers removed, qualitative abstraction
        "Valid abstraction - quantitative to qualitative"
    ),
    
    # CATEGORY 6: MULTI-SOURCE SUPPORT (Claims spanning multiple sources)
    # Note: This benchmark uses single sources, so these test source unit splitting
    create_benchmark_case(
        "501",
        "Sentence one contains information. Sentence two contains more information.",
        "Information is contained in the text.",
        "fact",
        "SUPPORTED",
        "Supported by combined sentences"
    ),
    
    # CATEGORY 7: AMBIGUOUS EVIDENCE (Genuinely unclear)
    create_benchmark_case(
        "601",
        "The results were inconclusive.",
        "The experiment failed to produce clear outcomes.",
        "fact",
        "INCONCLUSIVE",
        "Ambiguous - 'inconclusive' interpreted as 'failed'"
    ),
    
    create_benchmark_case(
        "602",
        "Some scholars believe this theory.",
        "The theory is widely accepted.",
        "fact",
        "INCONCLUSIVE",  # 'some' vs 'widely' - quantifier ambiguity
        "Ambiguous - quantifier mismatch"
    ),
]


# ============================================================================
# Benchmark Tests
# ============================================================================

class TestSemanticVerificationBenchmark:
    """
    Controlled benchmark for semantic verification.
    
    Tests the verifier on synthetic examples with known ground truth.
    Results indicate verifier behavior on controlled cases, NOT real-world performance.
    """
    
    @pytest.fixture
    def verifier(self):
        """Create verifier instance."""
        return DeterministicSemanticVerifier(verbose=False)
    
    def test_benchmark_individual_cases(self, verifier):
        """Test each benchmark case individually with detailed output."""
        
        print("\n" + "=" * 80)
        print("SEMANTIC VERIFICATION BENCHMARK - Individual Cases")
        print("=" * 80)
        print(f"Total cases: {len(BENCHMARK_CASES)}")
        print()
        
        results = []
        
        for i, (source_doc, knowledge_doc, expected, description) in enumerate(BENCHMARK_CASES, 1):
            # Run verification
            report = verifier.verify(knowledge_doc, source_doc)
            
            # Get actual status
            claim = report.claim_verifications[0]
            actual = claim.verification_status.status
            
            # Check if matches expected
            match = "PASS" if actual == expected else "FAIL"
            
            # Store result
            results.append({
                "case_id": source_doc.document_id,
                "description": description,
                "expected": expected,
                "actual": actual,
                "match": match,
                "confidence": claim.verification_status.confidence
            })
            
            # Print result
            print(f"{match} Case {i:03d} ({source_doc.document_id}): {description}")
            print(f"    Expected: {expected:20s} | Actual: {actual:20s} | Conf: {claim.verification_status.confidence:.2f}")
            if match == "✗":
                print(f"    Reason: {claim.verification_status.reason[:80]}...")
        
        # Print summary
        correct = sum(1 for r in results if r["match"] == "PASS")
        total = len(results)
        accuracy = correct / total if total > 0 else 0.0
        
        print()
        print("=" * 80)
        print(f"BENCHMARK ACCURACY: {correct}/{total} ({accuracy:.1%})")
        print("=" * 80)
        
        # Note: We don't assert 100% accuracy because some cases are designed
        # to test verifier limitations (e.g., paraphrases marked INCONCLUSIVE)
    
    def test_benchmark_confusion_matrix(self, verifier):
        """
        Generate confusion matrix for benchmark.
        
        Shows where verifier agrees/disagrees with ground truth labels.
        """
        
        print("\n" + "=" * 80)
        print("CONFUSION MATRIX")
        print("=" * 80)
        
        # Run all cases
        confusion = Counter()
        
        for source_doc, knowledge_doc, expected, _ in BENCHMARK_CASES:
            report = verifier.verify(knowledge_doc, source_doc)
            actual = report.claim_verifications[0].verification_status.status
            confusion[(expected, actual)] += 1
        
        # Define status order
        statuses = ["SUPPORTED", "CONTRADICTED", "UNSUPPORTED", "INCONCLUSIVE"]
        
        # Print matrix
        print(f"\n{'Actual >':20s}", end="")
        for status in statuses:
            print(f"{status:18s}", end="")
        print()
        print("Expected v" + " " * 10 + "-" * (18 * len(statuses)))
        
        for expected in statuses:
            print(f"{expected:20s}", end="")
            for actual in statuses:
                count = confusion.get((expected, actual), 0)
                print(f"{count:18d}", end="")
            print()
        
        print()
    
    def test_benchmark_category_performance(self, verifier):
        """
        Test performance by category.
        
        Shows how verifier performs on different types of claims.
        """
        
        print("\n" + "=" * 80)
        print("CATEGORY PERFORMANCE")
        print("=" * 80)
        
        categories = {
            "Direct Matches (001-004)": BENCHMARK_CASES[0:4],
            "Contradictions (101-104)": BENCHMARK_CASES[4:8],
            "Unsupported (201-203)": BENCHMARK_CASES[8:11],
            "Paraphrases (301-303)": BENCHMARK_CASES[11:14],
            "Abstractions (401-403)": BENCHMARK_CASES[14:17],
            "Multi-source (501)": BENCHMARK_CASES[17:18],
            "Ambiguous (601-602)": BENCHMARK_CASES[18:20],
        }
        
        for category, cases in categories.items():
            correct = 0
            total = len(cases)
            
            for source_doc, knowledge_doc, expected, _ in cases:
                report = verifier.verify(knowledge_doc, source_doc)
                actual = report.claim_verifications[0].verification_status.status
                if actual == expected:
                    correct += 1
            
            accuracy = correct / total if total > 0 else 0.0
            print(f"{category:30s}: {correct:2d}/{total:2d} ({accuracy:5.1%})")
        
        print()
    
    def test_benchmark_precision_recall(self, verifier):
        """
        Calculate precision and recall for SUPPORTED status.
        
        Precision: Of all claims marked SUPPORTED, how many actually are?
        Recall: Of all truly SUPPORTED claims, how many were detected?
        
        Note: These metrics are meaningful because benchmark has ground truth labels.
        They do NOT represent real-world performance.
        """
        
        print("\n" + "=" * 80)
        print("PRECISION AND RECALL (SUPPORTED Status)")
        print("=" * 80)
        
        true_positives = 0  # Correctly marked SUPPORTED
        false_positives = 0  # Incorrectly marked SUPPORTED (actually not)
        false_negatives = 0  # Missed SUPPORTED (marked as something else)
        true_negatives = 0  # Correctly marked as NOT SUPPORTED
        
        for source_doc, knowledge_doc, expected, _ in BENCHMARK_CASES:
            report = verifier.verify(knowledge_doc, source_doc)
            actual = report.claim_verifications[0].verification_status.status
            
            if expected == "SUPPORTED" and actual == "SUPPORTED":
                true_positives += 1
            elif expected != "SUPPORTED" and actual == "SUPPORTED":
                false_positives += 1
            elif expected == "SUPPORTED" and actual != "SUPPORTED":
                false_negatives += 1
            elif expected != "SUPPORTED" and actual != "SUPPORTED":
                true_negatives += 1
        
        # Calculate metrics
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        print(f"True Positives:  {true_positives:3d} (Correctly marked SUPPORTED)")
        print(f"False Positives: {false_positives:3d} (Incorrectly marked SUPPORTED)")
        print(f"False Negatives: {false_negatives:3d} (Missed SUPPORTED)")
        print(f"True Negatives:  {true_negatives:3d} (Correctly marked NOT SUPPORTED)")
        print()
        print(f"Precision: {precision:.1%} (Of predicted SUPPORTED, how many are correct?)")
        print(f"Recall:    {recall:.1%} (Of actual SUPPORTED, how many detected?)")
        print(f"F1 Score:  {f1:.1%}")
        print()
        print("NOTE: These metrics are for the SYNTHETIC benchmark only.")
        print("      They do NOT represent real-world performance on actual extractions.")
        print()
    
    def test_paraphrase_detection_limitation(self, verifier):
        """
        Demonstrate paraphrase detection limitation.
        
        Shows that deterministic verifier cannot detect valid paraphrases.
        """
        
        # Get paraphrase cases
        paraphrase_cases = [
            ("mitochondria powerhouse", "mitochondria generate energy"),
            ("transformation", "personal change"),
            ("climate change", "global warming"),
        ]
        
        print("\n" + "=" * 80)
        print("PARAPHRASE DETECTION LIMITATION")
        print("=" * 80)
        print("Demonstrating that deterministic verifier cannot detect paraphrases.")
        print()
        
        for source_phrase, claim_phrase in paraphrase_cases:
            source_doc = SourceDocument(
                document_id="PARA_TEST",
                filename="test.pdf",
                page_count=1,
                source_units=[
                    SourceUnit(
                        source_id="S001",
                        document_id="PARA_TEST",
                        page=1,
                        type="text",
                        content_role="content",
                        text=f"The concept involves {source_phrase}.",
                        position=1
                    )
                ]
            )
            
            knowledge_doc = KnowledgeDocument(
                document_id="PARA_TEST",
                source_filename="test.pdf",
                extraction_timestamp=datetime.now().isoformat(),
                facts=[
                    Fact(
                        knowledge_id="PARA_001",
                        knowledge_type="fact",
                        source_unit_ids=["S001"],
                        document_id="PARA_TEST",
                        content=f"The concept involves {claim_phrase}.",
                        fact_text=f"The concept involves {claim_phrase}."
                    )
                ]
            )
            
            report = verifier.verify(knowledge_doc, source_doc)
            status = report.claim_verifications[0].verification_status.status
            
            print(f"Source:  '{source_phrase}'")
            print(f"Claim:   '{claim_phrase}'")
            print(f"Status:  {status}")
            print(f"Note:    This is a valid paraphrase but marked {status}")
            print()
        
        print("CONCLUSION: Deterministic verifier requires LLM assistance or")
        print("            embedding-based similarity for paraphrase detection.")
        print()


# ============================================================================
# Summary Test
# ============================================================================

def test_benchmark_summary():
    """
    Print benchmark summary.
    
    This test always passes - it just provides documentation.
    """
    
    print("\n" + "=" * 80)
    print("SEMANTIC VERIFICATION BENCHMARK SUMMARY")
    print("=" * 80)
    print()
    print(f"Total test cases: {len(BENCHMARK_CASES)}")
    print()
    print("Categories:")
    print("  - Direct matches (4 cases): Exact or high-overlap text")
    print("  - Contradictions (4 cases): Numeric, date, entity mismatches")
    print("  - Unsupported (3 cases): Added facts not in source")
    print("  - Paraphrases (3 cases): Valid but low keyword overlap")
    print("  - Abstractions (3 cases): Generalizations from specific")
    print("  - Multi-source (1 case): Combined information")
    print("  - Ambiguous (2 cases): Genuinely unclear evidence")
    print()
    print("Purpose:")
    print("  - Test verifier behavior on controlled examples")
    print("  - Measure precision, recall, confusion matrix")
    print("  - Document limitations (paraphrase detection)")
    print()
    print("IMPORTANT:")
    print("  This is a SYNTHETIC benchmark with hand-crafted examples.")
    print("  Results do NOT represent real-world performance.")
    print("  Use for development and tuning, not production claims.")
    print()
