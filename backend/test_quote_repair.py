"""Test quote repair with actual failing cases from Java live run."""
import json
from pathlib import Path
from app.extraction.quote_repair import QuoteRepair, repair_evidence_quotes


def test_real_failing_quotes():
    """Test repair of the three actual failing quotes from the live run."""
    
    # The actual source text from T0001 (first ~2000 chars)
    source_text = """Hi! My name is Mosh and I'm gonna be your instructor in this Java course. In this course, you're gonna learn everything you need to get started programming in Java. We'll start off by installing all the necessary tools to build Java applications then you're gonna learn about the basics of Java you'll learn how Java code gets executed you'll learn how to build simple algorithms and throughout this course I'm gonna share with you lots of tips and shortcuts from my years of experience I'll teach you how to write good code like a professional developer so we'll end up watching this course you will have a solid foundation in Java and be ready to learn about advanced Java features I've designed this course for anyone who wants to learn Java if you're a beginner don't worry I'll make Java super simple and hold your hands through this entire course you're not too old or too young you'll write your first Java program in minutes my name is mosh I'm a software engineer with two decades of experience and I've taught over 3 million people how to code and how to become professional software engineers I have a coding school at code with mass comm where you can find plenty of courses that help you take her coding skills to the next level I hope you'll stick around and learn this beautiful and powerful programming language and now award from this video sponsor as someone who runs an online business I cannot stress enough the importance of staying safe online which is why I was so excited when dashlane reached out to me if you don't know - Lane is the password manager and VPN recommended by Apple and Google and it's a fantastic safeguard for keeping your information secure it's completely free to use for your first device so head over to - Ling comm / marchÃ© - give it a go if you want to upgrade to the premium to get VPN or dark web monitoring you can use the promo code mosh to get 10% off sign up for - 9 today and keep yourself safe online now back to the course in this java tutorial we're going to download and install the necessary tools to build java applications so open up your browser and search for jdk download jdk is short for Java development kit and it's basically a software development environment for building Java applications it has a compiler it has a bunch of code that we can reuse it has a Java Runtime environment at a bunch of other stuff so over here you can see this page on Oracle com Java se which is short for Java standard edition click on this now over here click on this icon now on this page we can see Java development kit for various platforms like Linux Mac OS and Windows here I'm on a Mac so I'm gonna download this dmg file over here"""
    
    repairer = QuoteRepair(min_similarity=0.85)
    
    # Test case 1: Java SE (lowercase "se" in source)
    print("Test 1: Java SE case difference")
    print("-" * 60)
    inexact1 = "Java SE which is short for Java standard edition"
    result1 = repairer.repair_quote(inexact1, source_text, "T0001")
    if result1:
        print(f"Original:  '{result1['original_quote']}'")
        print(f"Repaired:  '{result1['repaired_quote']}'")
        print(f"Similarity: {result1['similarity']:.3f}")
        valid, reason = repairer.validate_semantic_equivalence(
            result1['original_quote'], result1['repaired_quote'], strict=True
        )
        print(f"Valid: {valid} - {reason}")
        assert result1['repaired_quote'] == "Java se which is short for Java standard edition"
        assert valid, "Should be semantically equivalent"
    else:
        print("FAILED: No match found")
        assert False, "Should have found a match"
    print()
    
    # Test case 2: you will vs you'll contraction
    print("Test 2: Contraction difference (you will -> you'll)")
    print("-" * 60)
    inexact2 = "you will write your first Java program in minutes"
    result2 = repairer.repair_quote(inexact2, source_text, "T0001")
    if result2:
        print(f"Original:  '{result2['original_quote']}'")
        print(f"Repaired:  '{result2['repaired_quote']}'")
        print(f"Similarity: {result2['similarity']:.3f}")
        valid, reason = repairer.validate_semantic_equivalence(
            result2['original_quote'], result2['repaired_quote'], strict=True
        )
        print(f"Valid: {valid} - {reason}")
        assert result2['repaired_quote'] == "you'll write your first Java program in minutes"
        assert valid, "Should be semantically equivalent"
    else:
        print("FAILED: No match found")
        assert False, "Should have found a match"
    print()
    
    # Test case 3: we vs you pronoun difference
    print("Test 3: Pronoun difference (you -> we)")
    print("-" * 60)
    inexact3 = "you can see Java development kit for various platforms like Linux Mac OS and Windows"
    print(f"Looking for quote in source...")
    print(f"Quote: '{inexact3}'")
    # Check if "we can see" is in source
    if "we can see Java" in source_text:
        print("+ 'we can see Java' found in source")
    else:
        print("- 'we can see Java' NOT in source") 
    result3 = repairer.repair_quote(inexact3, source_text, "T0001")
    if result3:
        print(f"Original:  '{result3['original_quote']}'")
        print(f"Repaired:  '{result3['repaired_quote']}'")
        print(f"Similarity: {result3['similarity']:.3f}")
        valid, reason = repairer.validate_semantic_equivalence(
            result3['original_quote'], result3['repaired_quote'], strict=True
        )
        print(f"Valid: {valid} - {reason}")
        assert result3['repaired_quote'] == "we can see Java development kit for various platforms like Linux Mac OS and Windows"
        assert valid, "Should be semantically equivalent"
    else:
        print("FAILED: No match found")
        assert False, "Should have found a match"
    print()
    
    print("=" * 60)
    print("All three real failing cases repaired successfully!")
    print("=" * 60)


def test_full_response_repair():
    """Test repairing the full response from the live run."""
    
    # Load actual response
    backend = Path(__file__).parent
    response_path = backend / "data/output/java_live_java-20261106_152613_552313/java-20261106_152613_552313-0000.response.json"
    
    if not response_path.exists():
        print(f"Response file not found: {response_path}")
        return
    
    response = json.loads(response_path.read_text(encoding='utf-8'))
    content = json.loads(response['choices'][0]['message']['content'])
    
    # Get source text
    source_file = backend.parent / "java.txt"
    source_text = source_file.read_text(encoding='utf-8')[:3000]  # First part for T0001, extended for full coverage
    
    sources = {"T0001": source_text}
    
    # Flatten all items with their categories
    all_items = []
    for category, items in content.items():
        for item in items:
            item_with_cat = dict(item)
            item_with_cat['_category'] = category
            all_items.append(item_with_cat)
    
    print(f"\nRepairing {len(all_items)} items...")
    repaired_items, repair_log = repair_evidence_quotes(all_items, sources)
    
    print(f"\nRepair Summary:")
    print(f"  Total items: {len(all_items)}")
    print(f"  Total evidence entries: {sum(len(item.get('source_evidence', [])) for item in all_items)}")
    print(f"  Repairs attempted: {len(repair_log)}")
    
    successful = [r for r in repair_log if not r.get('repair_failed')]
    failed = [r for r in repair_log if r.get('repair_failed')]
    
    print(f"  Successful repairs: {len(successful)}")
    print(f"  Failed repairs: {len(failed)}")
    
    if successful:
        print("\nSuccessful repairs:")
        for repair in successful:
            print(f"  - '{repair['original_quote'][:50]}...'")
            print(f"    -> '{repair['repaired_quote'][:50]}...'")
            print(f"    Similarity: {repair['similarity']:.3f}, {repair['validation']}")
    
    if failed:
        print("\nFailed repairs:")
        for repair in failed:
            print(f"  - '{repair['original_quote'][:50]}...'")
            print(f"    Reason: {repair['reason']}")
    
    # Verify all quotes now match
    all_exact = True
    for item in repaired_items:
        for evidence in item.get('source_evidence', []):
            quote = evidence.get('quote')
            source_id = evidence.get('source_id')
            if source_id in sources and quote not in sources[source_id]:
                all_exact = False
                print(f"\nStill inexact after repair: '{quote[:60]}...'")
    
    if all_exact:
        print("\n✓ All quotes now exactly match source text!")
    else:
        print("\n✗ Some quotes still don't match exactly")
    
    return repaired_items, repair_log


if __name__ == '__main__':
    print("Testing quote repair with actual failing cases\n")
    test_real_failing_quotes()
    print("\n" + "=" * 60)
    print("\nTesting full response repair\n")
    test_full_response_repair()
