import json

path = "data/cache/infra_observation_cache.json"

with open(path, "r", encoding="utf-8") as f:
    text = f.read()

print("File size:", len(text))

try:
    json.loads(text)
    print("JSON VALID")

except json.JSONDecodeError as e:
    print("JSON INVALID")
    print("Line:", e.lineno)
    print("Column:", e.colno)
    print("Character:", e.pos)
    print("Message:", e.msg)

    start = max(0, e.pos - 300)
    end = min(len(text), e.pos + 300)

    print("\nText around error:")
    print(text[start:end])