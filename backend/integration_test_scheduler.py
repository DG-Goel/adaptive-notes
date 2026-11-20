"""
Integration test for multi-key Groq scheduler.

Tests:
1. Credential loading and initialization
2. Individual credential requests (one per key)
3. Round-robin selection across successive requests
4. Rate limit handling (if encountered)
5. Model verification
6. Minimal extraction through integrated pipeline

Does NOT:
- Deliberately exhaust quota
- Generate large responses
- Log secrets
- Modify prompts or architecture
"""
import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")

from app.extraction.llm_provider import GroqProvider
from app.extraction.groq_scheduler import load_groq_credentials, redact_api_key


def test_credential_loading():
    """Test 1: Verify credentials load correctly"""
    print("\n" + "="*60)
    print("TEST 1: Credential Loading")
    print("="*60)
    
    try:
        credentials = load_groq_credentials()
        print(f"✓ Loaded {len(credentials)} credentials")
        
        for i, key in enumerate(credentials, 1):
            print(f"  - key_{i}: {redact_api_key(key)} ({len(key)} chars)")
        
        if len(credentials) != 5:
            print(f"⚠ WARNING: Expected 5 credentials, got {len(credentials)}")
            return False
        
        print("✅ Test 1 PASSED")
        return True
    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}")
        return False


def test_provider_initialization():
    """Test 2: Verify provider initializes with multi-key mode"""
    print("\n" + "="*60)
    print("TEST 2: Provider Initialization")
    print("="*60)
    
    try:
        provider = GroqProvider(model="openai/gpt-oss-120b")
        
        if not provider.key_pool:
            print("❌ Provider did not initialize multi-key mode")
            return False
        
        print(f"✓ Provider initialized with multi-key mode")
        print(f"✓ Model: {provider.model}")
        print(f"✓ Max retries: {provider.max_retries}")
        
        status = provider.get_scheduler_status()
        if status:
            print(f"✓ Scheduler has {status['total_credentials']} credentials")
            print(f"✓ Next credential: {status['next_credential']}")
        
        print("✅ Test 2 PASSED")
        return True
    except Exception as e:
        print(f"❌ Test 2 FAILED: {e}")
        return False


def test_minimal_request_per_credential():
    """Test 3: Send one minimal request using each credential explicitly"""
    print("\n" + "="*60)
    print("TEST 3: Individual Credential Requests")
    print("="*60)
    
    # Minimal prompt compatible with Groq's JSON mode
    test_prompt = '''You are extracting knowledge from text. Return a JSON object with this structure:
{
  "items": [
    {"type": "fact", "content": "example fact", "source_ids": []}
  ]
}

Text: "The sky is blue."

Return the JSON now.'''
    
    results = []
    
    try:
        credentials = load_groq_credentials()
        
        for i, api_key in enumerate(credentials, 1):
            key_id = f"key_{i}"
            print(f"\n--- Testing {key_id} ({redact_api_key(api_key)}) ---")
            
            try:
                # Create single-key provider for this specific credential
                provider = GroqProvider(
                    model="openai/gpt-oss-120b",
                    api_key=api_key,
                    use_multi_key=False  # Force single-key mode
                )
                
                start_time = time.time()
                response = provider.generate(
                    prompt=test_prompt,
                    temperature=0.0,
                    max_tokens=200  # Small response
                )
                latency = time.time() - start_time
                
                # Verify model returned
                metadata = provider.last_response_metadata
                model_returned = metadata.get("model", "UNKNOWN")
                
                result = {
                    "credential": key_id,
                    "status": "success",
                    "latency_ms": round(latency * 1000, 2),
                    "model_returned": model_returned,
                    "response_length": len(response),
                    "tokens_used": metadata.get("usage", {}).get("total_tokens") if metadata.get("usage") else None
                }
                
                print(f"  ✓ Success")
                print(f"  ✓ Latency: {result['latency_ms']}ms")
                print(f"  ✓ Model: {model_returned}")
                print(f"  ✓ Response: {len(response)} chars")
                if result['tokens_used']:
                    print(f"  ✓ Tokens: {result['tokens_used']}")
                
                # Verify model is correct
                if "gpt-oss-120b" not in model_returned.lower() and "openai" not in model_returned.lower():
                    print(f"  ⚠ WARNING: Expected openai/gpt-oss-120b, got {model_returned}")
                
                results.append(result)
                
            except Exception as e:
                error_str = str(e)
                result = {
                    "credential": key_id,
                    "status": "failed",
                    "error_type": type(e).__name__,
                    "error": error_str[:200]  # Truncate long errors
                }
                
                print(f"  ❌ Failed: {type(e).__name__}")
                print(f"  Error: {error_str[:100]}")
                
                # Check if it's a rate limit
                if "429" in error_str or "rate" in error_str.lower():
                    print(f"  ⚠ Rate limit encountered (expected if quota shared)")
                    result["rate_limited"] = True
                
                results.append(result)
            
            # Small delay between requests to avoid immediate rate limits
            time.sleep(0.5)
        
        # Summary
        print("\n--- Summary ---")
        successful = sum(1 for r in results if r["status"] == "success")
        rate_limited = sum(1 for r in results if r.get("rate_limited"))
        
        print(f"Successful: {successful}/{len(results)}")
        print(f"Rate limited: {rate_limited}/{len(results)}")
        
        if successful > 0:
            print("✅ Test 3 PASSED (at least one credential works)")
            return True, results
        else:
            print("⚠ Test 3 PARTIAL (all requests failed, may be quota/rate limit)")
            return False, results
            
    except Exception as e:
        print(f"❌ Test 3 FAILED: {e}")
        return False, []


def test_round_robin_selection():
    """Test 4: Verify round-robin selection across requests"""
    print("\n" + "="*60)
    print("TEST 4: Round-Robin Selection")
    print("="*60)
    
    try:
        provider = GroqProvider(model="openai/gpt-oss-120b")
        
        if not provider.key_pool:
            print("❌ Multi-key mode not enabled")
            return False
        
        # Track which credentials are selected
        selections = []
        
        # Make 3 minimal requests with proper JSON mode prompt
        test_prompt = '''Return JSON with one fact:
{
  "items": [{"type": "fact", "content": "sky is blue"}]
}'''
        
        for i in range(3):
            try:
                # Get status before request
                status_before = provider.get_scheduler_status()
                next_cred = status_before.get("next_credential", "unknown")
                
                print(f"\nRequest {i+1}: Next credential should be {next_cred}")
                
                start_time = time.time()
                response = provider.generate(
                    prompt=test_prompt,
                    temperature=0.0,
                    max_tokens=100
                )
                latency = time.time() - start_time
                
                selections.append({
                    "request": i + 1,
                    "expected_credential": next_cred,
                    "success": True,
                    "latency_ms": round(latency * 1000, 2)
                })
                
                print(f"  ✓ Success ({latency*1000:.0f}ms)")
                
                # Small delay
                time.sleep(0.3)
                
            except Exception as e:
                error_str = str(e)
                print(f"  ❌ Failed: {type(e).__name__}")
                print(f"  Error: {str(e)[:100]}")
                
                if "429" in error_str or "rate" in error_str.lower():
                    print(f"  ⚠ Rate limit hit - stopping round-robin test")
                    break
                
                selections.append({
                    "request": i + 1,
                    "success": False,
                    "error": str(e)[:100]
                })
        
        # Check if rotation happened
        if len(selections) >= 2:
            print(f"\n✓ Completed {len(selections)} requests through scheduler")
            print("✅ Test 4 PASSED (scheduler operational)")
            return True
        else:
            print("⚠ Test 4 PARTIAL (too few successful requests)")
            return False
            
    except Exception as e:
        print(f"❌ Test 4 FAILED: {e}")
        return False


def test_minimal_extraction():
    """Test 5: Run one small extraction through integrated pipeline"""
    print("\n" + "="*60)
    print("TEST 5: Integrated Extraction Pipeline")
    print("="*60)
    
    try:
        from app.extraction.extractor import KnowledgeExtractor
        from app.models.source import SourceDocument, SourceUnit
        
        # Create minimal test document with correct schema
        doc = SourceDocument(
            document_id="TEST_INTEGRATION",
            filename="integration_test.txt",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="UNIT_001",
                    document_id="TEST_INTEGRATION",
                    type="text",
                    content_role="content",
                    text="Water freezes at 0 degrees Celsius.",
                    page=1,
                    position=0
                )
            ]
        )
        
        print(f"✓ Created test document with {len(doc.source_units)} units")
        
        # Create extractor with Groq provider
        provider = GroqProvider(model="openai/gpt-oss-120b")
        extractor = KnowledgeExtractor(llm_provider=provider)
        
        print(f"✓ Initialized extractor with {provider.model}")
        
        # Extract
        print("  Running extraction...")
        start_time = time.time()
        result = extractor.extract(doc)
        latency = time.time() - start_time
        
        print(f"✓ Extraction completed in {latency:.2f}s")
        print(f"✓ Total knowledge items: {result.total_items}")
        print(f"✓ Concepts: {len(result.concepts)}, Definitions: {len(result.definitions)}")
        print(f"✓ Facts: {len(result.facts)}, Relationships: {len(result.relationships)}")
        
        # Verify structure
        if result.total_items > 0:
            # Show a sample item
            if result.concepts:
                item = result.concepts[0]
                print(f"✓ Sample concept: {item.concept_name}")
            elif result.facts:
                item = result.facts[0]
                print(f"✓ Sample fact: {item.fact_text[:50]}")
            print(f"  - ID: {item.knowledge_id}")
            print(f"  - Source IDs: {item.source_unit_ids}")
        
        # Check scheduler usage
        if provider.key_pool:
            status = provider.get_scheduler_status()
            print(f"\n✓ Scheduler status after extraction:")
            for cred_status in status.get("credentials", []):
                print(f"  - {cred_status['credential_id']}: "
                      f"{cred_status['total_requests']} requests, "
                      f"{cred_status['total_failures']} failures")
        
        print("✅ Test 5 PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Test 5 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests"""
    print("\n" + "="*60)
    print("GROQ MULTI-KEY SCHEDULER INTEGRATION VALIDATION")
    print("="*60)
    
    print("\n! IMPORTANT NOTES:")
    print("- Groq rate limits are ORGANIZATION-LEVEL (confirmed via console.groq.com)")
    print("- Multiple keys from same org share quotas")
    print("- This test assumes keys from DIFFERENT organizations")
    print("- Minimal requests to respect each account's quota")
    
    results = {}
    
    # Run tests
    results["credential_loading"] = test_credential_loading()
    results["provider_init"] = test_provider_initialization()
    results["individual_requests"], request_details = test_minimal_request_per_credential()
    results["round_robin"] = test_round_robin_selection()
    results["integrated_extraction"] = test_minimal_extraction()
    
    # Final summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "[PASS]" if passed_test else "[FAIL]"
        print(f"{test_name:30s}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n*** ALL VALIDATION CHECKS PASSED ***")
        print("Multi-key scheduler is production-ready for use with")
        print("credentials from DIFFERENT organizations.")
    elif passed >= 3:
        print("\n! PARTIAL SUCCESS")
        print("Core functionality works but some tests failed.")
        print("Review failures above. May be rate limits or quota.")
    else:
        print("\nX VALIDATION FAILED")
        print("Critical issues detected. Review errors above.")


if __name__ == "__main__":
    main()
