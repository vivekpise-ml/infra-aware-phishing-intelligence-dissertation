import json

path = "data/cache/infra_observation_cache.json"

with open(path, "r", encoding="utf-8") as f:
    text = f.read()

print("File size:", len(text))
print("Line count:", len(text.splitlines()))

try:
    json.loads(text)
    print("JSON VALID")
    raise SystemExit

except json.JSONDecodeError as e:
    print("\nJSON INVALID")
    print("Line:", e.lineno)
    print("Column:", e.colno)
    print("Character:", e.pos)
    print("Message:", e.msg)

    lines = text.splitlines()

    start_line = max(1, e.lineno - 15)
    end_line = min(len(lines), e.lineno + 5)

    print("\nLines around parser error:")
    for number in range(start_line, end_line + 1):
        print(f"{number}: {lines[number - 1]}")

    print("\nLast 30 lines:")
    first = max(0, len(lines) - 30)
    for number in range(first, len(lines)):
        print(f"{number + 1}: {lines[number]}")

    # Show the final 500 characters with repr so invisible characters
    # and exact punctuation are visible.
    print("\nFinal 500 characters:")
    print(repr(text[-500:]))