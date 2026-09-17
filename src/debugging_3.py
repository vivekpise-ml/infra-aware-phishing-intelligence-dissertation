import whois
from datetime import datetime, timezone

w = whois.whois("google.com")

creation = w.creation_date
print("RAW:", creation)

if isinstance(creation, list):
    creation = creation[0]

print("FINAL:", creation)

if isinstance(creation, datetime):
    age = (datetime.now(timezone.utc) - creation).days
    print("AGE:", age)