import whois
from datetime import datetime

w = whois.whois("google.com")
print(w.creation_date)