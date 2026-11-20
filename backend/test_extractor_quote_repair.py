"""Test extractor with quote repair integration using actual live response."""
import json
from pathlib import Path
from app.extraction.extractor import KnowledgeExtractor
from app.extraction.llm_provider import LLMProvider
from app.models.knowledge import ExtractionChunk


class MockLLMProvider(LLMProvider):
    """Mock LLM that returns the actual failing response."""
    
    def __init__(self, response_json: dict):
        self.response_json = response_json
        self.tokens_per_minute = 10000
    
    def generate(self, prompt: str, system: str = "", temperature: float = 0.0, 
                 max_tokens: int = 4000) -> str:
        """Return the stored response."""
        content = json.loads(self.response_json['choices'][0]['message']['content'])
        return json.dumps(content, ensure_ascii=False)


def test_extractor_repairs_quotes():
    """Test that the extractor automatically repairs the three failing quotes."""
    
    backend = Path(__file__).parent
    
    # Load actual response with failing quotes
    response_path = backend / "data/output/java_live_java-20261106_152613_552313/java-20261106_152613_552313-0000.response.json"
    response = json.loads(response_path.read_text(encoding='utf-8'))
    
    # Load source text
    source_file = backend.parent / "java.txt"
    source_text = source_file.read_text(encoding='utf-8')[:3000]
    
    # Create mock provider
    provider = MockLLMProvider(response)
    
    # Create extractor with strict evidence enabled
    extractor = KnowledgeExtractor(
        llm_provider=provider,
        strict_evidence=True,
        verbose=True
    )
    
    # Build extraction chunk
    chunk = ExtractionChunk(
        chunk_id="CHUNK_001",
        text_content=source_text,
        source_units=["T0001"],
        source_spans={"T0001": (0, len(source_text))},
        section="Introduction",
        page_range=None
    )
    
    # Set up evidence sources
    extractor._evidence_sources = {"T0001": source_text}
    extractor.valid_source_ids = {"T0001"}
    
    print("Testing extractor with quote repair...")
    print("=" * 60)
    
    # This should work now with quote repair
    try:
        items = extractor._parse_response(
            provider.generate("", ""),
            chunk,
            "DOC_001"
        )
        
        print(f"\n✓ Successfully extracted {len(items)} items")
        print(f"  Quotes repaired: {len(extractor.repaired_quotes)}")
        
        if extractor.repaired_quotes:
            print("\nRepaired quotes:")
            for repair in extractor.repaired_quotes:
                print(f"  - Source: {repair['source_id']}")
                print(f"    Original: '{repair['original_quote'][:60]}...'")
                print(f"    Repaired: '{repair['repaired_quote'][:60]}...'")
                print(f"    Similarity: {repair['similarity']:.3f}")
        
        # Verify all quotes now match
        all_exact = True
        for item in items:
            if not hasattr(item, 'extraction_metadata'):
                continue
            
            evidence = item.extraction_metadata.get('source_grounding', {}).get('evidence', [])
            for ev in evidence:
                quote = ev.get('quote')
                source_id = ev.get('source_id')
                if source_id == "T0001" and quote not in source_text:
                    all_exact = False
                    print(f"\n✗ Still inexact: '{quote[:60]}...'")
        
        if all_exact:
            print("\n" + "=" * 60)
            print("✓ ALL QUOTES NOW MATCH EXACTLY!")
            print("=" * 60)
            return True
        else:
            print("\n✗ Some quotes still don't match")
            return False
            
    except ValueError as e:
        print(f"\n✗ Extraction failed: {e}")
        return False


if __name__ == '__main__':
    success = test_extractor_repairs_quotes()
    exit(0 if success else 1)
