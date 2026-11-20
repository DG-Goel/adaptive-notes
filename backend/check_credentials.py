"""
Check Groq credential configuration without exposing secrets.
"""
import os
from pathlib import Path

# Load .env file
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key.startswith("GROQ_API_KEY"):
                        os.environ[key] = value

# Check what's configured
credentials_found = []
for i in range(1, 6):
    key = os.getenv(f"GROQ_API_KEY_{i}")
    if key and key.strip():
        prefix = key[:4] if len(key) >= 4 else "???"
        suffix = key[-4:] if len(key) >= 8 else "???"
        credentials_found.append(f"key_{i}")
        print(f"✓ GROQ_API_KEY_{i}: {prefix}...{suffix} ({len(key)} chars)")
    else:
        print(f"✗ GROQ_API_KEY_{i}: NOT SET")

# Check backward compatible single key
single_key = os.getenv("GROQ_API_KEY")
if single_key and single_key.strip():
    prefix = single_key[:4] if len(single_key) >= 4 else "???"
    suffix = single_key[-4:] if len(single_key) >= 8 else "???"
    print(f"✓ GROQ_API_KEY (legacy): {prefix}...{suffix} ({len(single_key)} chars)")

print(f"\nTotal credentials configured: {len(credentials_found)}")
print(f"Credential IDs: {', '.join(credentials_found) if credentials_found else 'NONE'}")

# Verify they start with expected prefix
all_valid = True
for i in range(1, 6):
    key = os.getenv(f"GROQ_API_KEY_{i}")
    if key and key.strip():
        if not key.startswith("gsk_"):
            print(f"⚠ WARNING: GROQ_API_KEY_{i} doesn't start with 'gsk_'")
            all_valid = False

if all_valid and credentials_found:
    print("\n✅ All credentials have valid format (gsk_...)")
