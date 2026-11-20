"""
Exhaustive T0018 recovery with multiple progressive strategies
"""

import json
import os
from pathlib import Path
from datetime import datetime
from app.extraction.extractor import KnowledgeExtractor
from app.extraction.llm_provider import OpenAIProvider

def load_source_unit(source_id, source_units_path):
    """Load a specific source unit"""
    with open(source_units_path, encoding='utf-8') as f:
        data = json.load(f)
    units = data.get('source_units', [])
    unit = [u for u in units if u.get('source_id') == source_id]
    return unit[0] if unit else None

def save_attempt_result(attempt_num, strategy, result, output_dir):
    """Save attempt result"""
    filename = output_dir / f"t0018_attempt_{attempt_num}_{strategy}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    return filename

def attempt_recovery(unit, strategy_name, extractor, attempt_num, output_dir):
    """Single recovery attempt"""
    print(f"\nAttempt {attempt_num}: {strategy_name}")
    print(f"  Input length: {len(unit['text'])} chars")
    
    try:
        result = extractor.extract(
            text=unit['text'],
            source_id=unit['source_id'],
            document_id=unit['document_id']
        )
        
        total_items = (
            len(result.get('concepts', [])) +
            len(result.get('definitions', [])) +
            len(result.get('explanations', [])) +
            len(result.get('examples', [])) +
            len(result.get('facts', [])) +
            len(result.get('formulas', [])) +
            len(result.get('procedures', [])) +
            len(result.get('relationships', []))
        )
        
        print(f"  ✓ Success: {total_items} items extracted")
        
        result['attempt_metadata'] = {
            'attempt_num': attempt_num,
            'strategy': strategy_name,
            'success': True,
            'total_items': total_items
        }
        
        save_attempt_result(attempt_num, strategy_name.replace(' ', '_').lower(), result, output_dir)
        return result, total_items
        
    except Exception as e:
        print(f"  ✗ Failed: {str(e)}")
        result = {
            'attempt_metadata': {
                'attempt_num': attempt_num,
                'strategy': strategy_name,
                'success': False,
                'error': str(e)
            }
        }
        save_attempt_result(attempt_num, strategy_name.replace(' ', '_').lower(), result, output_dir)
        return None, 0

def main():
    print("=" * 80)
    print("EXHAUSTIVE T0018 RECOVERY")
    print("=" * 80)
    
    # Setup
    source_units_path = Path("data/output/complete_e2e_validation/validation_20261101_174430/source_units.json")
    output_dir = Path("data/output/t0018_recovery_attempts")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load T0018
    print("\nLoading T0018...")
    unit = load_source_unit('T0018', source_units_path)
    if not unit:
        print("ERROR: T0018 not found")
        return
    
    print(f"  Text length: {len(unit['text'])} chars")
    print(f"  Word count: {len(unit['text'].split())} words")
    
    # Initialize extractor
    print("\nInitializing OpenAI provider...")
    llm_provider = OpenAIProvider(
        api_key=os.getenv('OPENAI_API_KEY'),
        model_name='gpt-4-turbo-preview'
    )
    extractor = KnowledgeExtractor(llm_provider)
    
    # Track all attempts
    attempts_log = {
        'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S"),
        'source_id': 'T0018',
        'original_length': len(unit['text']),
        'original_word_count': len(unit['text'].split()),
        'attempts': []
    }
    
    successful_attempts = []
    
    # STRATEGY 1: Full text with default settings
    result, items = attempt_recovery(
        unit, 
        "Full Text Default Settings",
        extractor,
        1,
        output_dir
    )
    attempts_log['attempts'].append({
        'num': 1,
        'strategy': "Full Text Default Settings",
        'success': result is not None,
        'items': items
    })
    if result:
        successful_attempts.append((1, "Full Text Default Settings", items))
    
    # STRATEGY 2: First half only (1301 chars)
    half_point = len(unit['text']) // 2
    unit_half1 = unit.copy()
    unit_half1['text'] = unit['text'][:half_point]
    result, items = attempt_recovery(
        unit_half1,
        "First Half (1301 chars)",
        extractor,
        2,
        output_dir
    )
    attempts_log['attempts'].append({
        'num': 2,
        'strategy': "First Half (1301 chars)",
        'success': result is not None,
        'items': items
    })
    if result:
        successful_attempts.append((2, "First Half", items))
    
    # STRATEGY 3: Second half only
    unit_half2 = unit.copy()
    unit_half2['text'] = unit['text'][half_point:]
    result, items = attempt_recovery(
        unit_half2,
        "Second Half (1302 chars)",
        extractor,
        3,
        output_dir
    )
    attempts_log['attempts'].append({
        'num': 3,
        'strategy': "Second Half (1302 chars)",
        'success': result is not None,
        'items': items
    })
    if result:
        successful_attempts.append((3, "Second Half", items))
    
    # STRATEGY 4: Small chunks (400 chars each)
    chunk_size = 400
    chunks = []
    for i in range(0, len(unit['text']), chunk_size):
        chunks.append(unit['text'][i:i+chunk_size])
    
    print(f"\n  Breaking into {len(chunks)} chunks of ~{chunk_size} chars...")
    chunk_results = []
    for idx, chunk_text in enumerate(chunks):
        unit_chunk = unit.copy()
        unit_chunk['text'] = chunk_text
        result, items = attempt_recovery(
            unit_chunk,
            f"Chunk {idx+1}/{len(chunks)} ({len(chunk_text)} chars)",
            extractor,
            4 + idx,
            output_dir
        )
        chunk_results.append((result, items))
        attempts_log['attempts'].append({
            'num': 4 + idx,
            'strategy': f"Chunk {idx+1}/{len(chunks)}",
            'success': result is not None,
            'items': items
        })
        if result:
            successful_attempts.append((4 + idx, f"Chunk {idx+1}", items))
    
    # Save log
    log_path = output_dir / "recovery_attempts_log.json"
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(attempts_log, f, indent=2, ensure_ascii=False)
    
    # Summary
    print("\n" + "=" * 80)
    print("RECOVERY SUMMARY")
    print("=" * 80)
    print(f"Total attempts: {len(attempts_log['attempts'])}")
    print(f"Successful: {len(successful_attempts)}")
    print(f"Failed: {len(attempts_log['attempts']) - len(successful_attempts)}")
    
    if successful_attempts:
        print("\nSuccessful attempts:")
        for attempt_num, strategy, items in successful_attempts:
            print(f"  Attempt {attempt_num}: {strategy} → {items} items")
    else:
        print("\n⚠ NO SUCCESSFUL ATTEMPTS")
    
    print(f"\nResults saved to: {output_dir}")
    print(f"Log saved to: {log_path}")
    print("=" * 80)

if __name__ == "__main__":
    main()
