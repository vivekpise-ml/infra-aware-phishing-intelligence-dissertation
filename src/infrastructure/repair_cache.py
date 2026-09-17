from pathlib import Path
import json

cache_path = Path("data/cache/infra_observation_cache.json")

# Read current cache
text = cache_path.read_text(encoding="utf-8")

# The parser showed that the file is missing the final
# closing brace for the root JSON object.
if not text.rstrip().endswith("}"):
    raise RuntimeError("Cache does not end with a closing brace.")

# Add the missing root closing brace.
repaired = text.rstrip() + "\n}\n"

cache_path.write_text(
    repaired,
    encoding="utf-8"
)

print("Added missing root JSON closing brace.")

# Validate
with open(cache_path, "r", encoding="utf-8") as f:
    cache = json.load(f)

print("JSON VALID")
print("Domains:", len(cache))