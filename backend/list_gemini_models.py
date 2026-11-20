"""List available Gemini models"""

import os
from dotenv import load_dotenv
load_dotenv()

try:
    from google import genai
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        exit(1)
    
    print(f"API Key length: {len(api_key)}")
    print()
    
    client = genai.Client(api_key=api_key)
    
    print("Listing available models...")
    print("=" * 80)
    
    # Try to list models
    try:
        models = client.models.list()
        for model in models:
            print(f"Model: {model.name}")
            if hasattr(model, 'supported_generation_methods'):
                print(f"  Supported methods: {model.supported_generation_methods}")
            print()
    except Exception as e:
        print(f"Error listing models: {e}")
        print()
        print("Trying to generate content with gemini-pro...")
        try:
            response = client.models.generate_content(
                model="gemini-pro",
                contents="Hello, can you respond with a simple greeting?",
                config=genai.types.GenerateContentConfig(
                    temperature=0.0,
                    max_output_tokens=50
                )
            )
            print("✓ gemini-pro works!")
            print(f"Response: {response.candidates[0].content.parts[0].text}")
        except Exception as e2:
            print(f"✗ gemini-pro failed: {e2}")
            
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
