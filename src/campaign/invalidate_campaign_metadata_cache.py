import json
from pathlib import Path

CACHE_PATH = Path("data/cache/infra_cache.json")

with CACHE_PATH.open("r", encoding="utf-8") as f:
    cache = json.load(f)

count = 0

for domain, entry in cache.items():

    if not isinstance(entry, dict):
        continue

    campaign = entry.get("campaign_metadata")

    if isinstance(campaign, dict):
        # Make the existing Campaign Metadata entry stale.
        campaign["cached_at"] = "2000-01-01T00:00:00+00:00"
        count += 1

with CACHE_PATH.open("w", encoding="utf-8") as f:
    json.dump(cache, f, indent=2)

print(f"Invalidated Campaign Metadata entries: {count}")
print("Prediction 'data' sections were not modified.")