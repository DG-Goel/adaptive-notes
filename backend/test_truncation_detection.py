"""Test truncation detection for the failing request."""
import json
from pathlib import Path


def test_truncation_detection():
    """Test that truncation is detected for the failing request."""
    
    # Load the audit
    audit_path = Path(__file__).parent / "data/output/java_live_java-20261106_165352_030420/request_audit.json"
    audit = json.loads(audit_path.read_text(encoding='utf-8'))
    
    # Find the provider_error event
    error_event = next(e for e in audit['events'] if e['event'] == 'provider_error')
    error_details = json.loads(error_event['details'])
    
    message = error_details['message'].lower()
    print(f"Error code: {error_details.get('error_code')}")
    print(f"Message (first 200 chars): {error_details['message'][:200]}")
    
    # Check for truncation indicators
    is_json_validate = error_details.get('error_code') == 'json_validate_failed'
    print(f"\nIs json_validate_failed: {is_json_validate}")
    
    # Extract failed_generation
    failed_gen_start = message.find("'failed_generation': '")
    if failed_gen_start >= 0:
        json_start = failed_gen_start + len("'failed_generation': '")
        json_end = message.find("'", json_start)
        if json_end > json_start:
            json_part = message[json_start:json_end].rstrip()
            print(f"\nFailed generation (last 100 chars): ...{json_part[-100:]}")
            
            # Check backslash at end
            ends_with_backslash = json_part.endswith('\\')
            print(f"Ends with backslash (mid-escape): {ends_with_backslash}")
            
            # Try to parse
            try:
                json.loads(json_part)
                print("JSON parses successfully (not truncated)")
                truncated = False
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
                error_keywords = ['unterminated', 'eof', 'expecting']
                has_keyword = any(kw in str(e).lower() for kw in error_keywords)
                print(f"Error indicates truncation: {has_keyword}")
                truncated = has_keyword or ends_with_backslash
            
            if truncated:
                print("\n✓ TRUNCATION DETECTED - Recovery should be triggered")
                return True
    
    print("\n✗ TRUNCATION NOT DETECTED")
    return False


if __name__ == '__main__':
    success = test_truncation_detection()
    exit(0 if success else 1)
