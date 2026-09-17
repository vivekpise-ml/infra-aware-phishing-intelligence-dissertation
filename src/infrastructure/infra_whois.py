"""
Infrastructure WHOIS Intelligence

Collects WHOIS/RDAP intelligence and exposes two independent outputs:

1. Prediction Features
2. Campaign Metadata

Public API
----------
collect_whois(domain)

Returns
-------
{
    "features": {...},
    "metadata": {...}
}
"""

import time
from datetime import datetime, timezone

import whois


###########################################################################
# PRIVATE HELPERS
###########################################################################

def _extract_single(value):
    """
    WHOIS libraries often return a list instead of a single value.
    Always normalize to a single object.
    """

    if isinstance(value, list):

        if len(value) == 0:
            return None

        return value[0]

    return value


def _safe_datetime(value):
    """
    Normalize datetime objects returned by WHOIS.

    Returns
    -------
    datetime | None
    """

    value = _extract_single(value)

    if value is None:
        return None

    if not isinstance(value, datetime):
        return None

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value


def _load_whois(domain):
    """
    Perform WHOIS / RDAP lookup.

    Returns
    -------
    whois object | None
    """

    try:

        start = time.time()

        record = whois.whois(domain)

        print(
            f"WHOIS {domain} took "
            f"{time.time() - start:.2f}s"
        )

        return record

    except Exception as e:

        print(f"WHOIS ERROR ({domain}) : {e}")

        return None


###########################################################################
# COMMON DATE HELPERS
###########################################################################

def _domain_age_days(record):
    """
    Domain age in days.
    """

    if record is None:
        return None

    creation = _safe_datetime(
        record.creation_date
    )

    if creation is None:
        return None

    return (

        datetime.now(timezone.utc)

        - creation

    ).days


def _registration_lifetime_days(record):
    """
    Registration validity period.
    """

    if record is None:
        return None

    creation = _safe_datetime(
        record.creation_date
    )

    expiry = _safe_datetime(
        record.expiration_date
    )

    if creation is None or expiry is None:
        return None

    return (

        expiry

        - creation

    ).days


def _registration_remaining_days(record):
    """
    Remaining registration validity.
    """

    if record is None:
        return None

    expiry = _safe_datetime(
        record.expiration_date
    )

    if expiry is None:
        return None

    return (

        expiry

        - datetime.now(timezone.utc)

    ).days


###########################################################################
# COMMON UTILITIES
###########################################################################

def _domain_age_bucket(age):
    """
    Convert domain age into maturity bucket.

    -1 : Unknown
     0 : Today
     1 : <30 days
     2 : <180 days
     3 : <365 days
     4 : >=365 days
    """

    if age is None:
        return -1

    if age == 0:
        return 0

    if age < 30:
        return 1

    if age < 180:
        return 2

    if age < 365:
        return 3

    return 4

###########################################################################
# IDENTITY NORMALIZATION
###########################################################################

def _is_real_identity(value):
    """
    Determine whether a WHOIS identity value represents
    a real identity rather than a privacy-protection service.

    Returns
    -------
    bool
    """

    if value is None:
        return False

    value = str(value).strip()

    if value == "":
        return False

    lower = value.lower()

    privacy_keywords = [

        "privacy",

        "proxy",

        "whoisguard",

        "redacted",

        "withheld",

        "gdpr",

        "contact privacy",

        "domains by proxy",

        "privacy protect",

        "data protected",

        "private person",

        "identity protection"

    ]

    return not any(
        keyword in lower
        for keyword in privacy_keywords
    )


def _normalize_registrar(registrar):
    """
    Normalize registrar names so that equivalent
    registrar strings map to a common representation.
    """

    if registrar is None:
        return None

    registrar = str(registrar).lower().strip()

    replacements = {

        "godaddy.com llc": "godaddy",
        "godaddy llc": "godaddy",

        "namecheap inc": "namecheap",
        "namecheap, inc.": "namecheap",

        "amazon registrar, inc.": "amazon",

        "markmonitor inc.": "markmonitor",

        "cloudflare, inc.": "cloudflare",

        "tucows domains inc.": "tucows",

        "network solutions, llc": "networksolutions"

    }

    return replacements.get(
        registrar,
        registrar
    )



###########################################################################
# PREDICTION FEATURE EXTRACTION
###########################################################################

def _prediction_features(record):
    """
    Extract numerical WHOIS features used by the
    phishing prediction pipeline.

    Returns
    -------
    dict
    """

    age = _domain_age_days(record)

    if age is None:

        age_value = 0

        has_age = 0

    else:

        age_value = age

        has_age = 1

    lifetime = _registration_lifetime_days(record)

    if lifetime is None:
        lifetime = 0

    remaining = _registration_remaining_days(record)

    if remaining is None:
        remaining = 0

    # ---------------------------------------------------------
    # Domain Status Count
    # ---------------------------------------------------------

    try:

        status = record.status if record else None

        if status is None:

            status_count = 0

        elif isinstance(status, list):

            status_count = len(status)

        else:

            status_count = 1

    except Exception:

        status_count = 0

    # ---------------------------------------------------------
    # Privacy Protection
    # ---------------------------------------------------------

    privacy_protected = 0

    try:

        values = [

            getattr(record, "registrant_name", None),

            getattr(record, "name", None),

            getattr(record, "org", None),

            getattr(record, "emails", None)

        ]

        text = " ".join(

            str(v).lower()

            for v in values

            if v is not None

        )

        privacy_keywords = [

            "privacy",

            "proxy",

            "redacted",

            "whoisguard",

            "withheld",

            "gdpr"

        ]

        privacy_protected = int(

            any(

                keyword in text

                for keyword in privacy_keywords

            )

        )

    except Exception:

        privacy_protected = 0

    # ---------------------------------------------------------
    # Prediction Features
    # ---------------------------------------------------------

    return {

        # ---------------------------------------------
        # Availability
        # ---------------------------------------------

        "has_domain_age":

            has_age,

        # ---------------------------------------------
        # Raw
        # ---------------------------------------------

        "domain_age_days":

            age_value,

        "registration_lifetime_days":

            lifetime,

        "registration_remaining_days":

            remaining,

        # ---------------------------------------------
        # Behaviour
        # ---------------------------------------------

        "domain_age_bucket":

            _domain_age_bucket(age),

        "is_new_domain":

            int(

                has_age == 1

                and

                age_value <= 3

            ),

        "privacy_protected":

            privacy_protected,

        "domain_status_count":

            status_count

    }

###########################################################################
# CAMPAIGN METADATA EXTRACTION
###########################################################################

def _campaign_metadata(record):
    """
    Extract WHOIS identity metadata used by the
    Campaign Analysis pipeline.

    Returns
    -------
    dict
    """

    metadata = {}

    # ---------------------------------------------------------
    # Registrar
    # ---------------------------------------------------------

    try:

        registrar = _normalize_registrar(
            getattr(record, "registrar", None)
        )

        metadata["registrar"] = registrar

        metadata["registrar_available"] = int(
            _is_real_identity(registrar)
        )

    except Exception:

        metadata["registrar"] = None
        metadata["registrar_available"] = 0

    # ---------------------------------------------------------
    # Registrant Name
    # ---------------------------------------------------------

    try:

        registrant = getattr(record, "name", None)

        metadata["registrant_name"] = registrant

        metadata["registrant_name_available"] = int(
            _is_real_identity(registrant)
        )

    except Exception:

        metadata["registrant_name"] = None
        metadata["registrant_name_available"] = 0

    # ---------------------------------------------------------
    # Organization
    # ---------------------------------------------------------

    try:

        organization = getattr(record, "org", None)

        metadata["organization"] = organization

        metadata["organization_available"] = int(
            _is_real_identity(organization)
        )

    except Exception:

        metadata["organization"] = None
        metadata["organization_available"] = 0

    # ---------------------------------------------------------
    # Email
    # ---------------------------------------------------------

    try:

        email = getattr(record, "emails", None)

        if isinstance(email, list):

            email = email[0] if len(email) > 0 else None

        metadata["email"] = email

        metadata["email_available"] = int(
            _is_real_identity(email)
        )

    except Exception:

        metadata["email"] = None
        metadata["email_available"] = 0

    # ---------------------------------------------------------
    # Name Servers
    # ---------------------------------------------------------

    try:

        nameservers = getattr(record, "name_servers", None)

        if nameservers is None:

            nameservers = []

        elif not isinstance(nameservers, list):

            nameservers = [nameservers]

        nameservers = sorted(

            list(

                set(

                    str(ns).lower()

                    for ns in nameservers

                )

            )

        )

        metadata["nameservers"] = nameservers

        metadata["nameserver_count"] = len(nameservers)

    except Exception:

        metadata["nameservers"] = []

        metadata["nameserver_count"] = 0

    # ---------------------------------------------------------
    # Domain Status
    # ---------------------------------------------------------

    try:

        status = getattr(record, "status", None)

        if status is None:

            status = []

        elif not isinstance(status, list):

            status = [status]

        metadata["domain_status"] = status

    except Exception:

        metadata["domain_status"] = []

    return metadata

###########################################################################
# PUBLIC API
###########################################################################

def collect_whois(domain):
    """
    Collect WHOIS / RDAP intelligence.

    Notes
    -----
    - 'features' are consumed by the Prediction pipeline.
    - 'metadata' are consumed by the Campaign pipeline.
    - This function performs no caching.
    - Cache ownership belongs to the caller.
    """

    domain = domain.lower().replace("www.", "").strip()

    record = _load_whois(domain)

    return {

        "features": _prediction_features(record),

        "metadata": _campaign_metadata(record)

    }


###########################################################################
# DEBUG
###########################################################################

if __name__ == "__main__":

    domains = [

        "google.com",

        "amazon.com",

        "paypal.com",

        "github.com"

    ]

    for domain in domains:

        print("\n")

        print("=" * 80)

        print(domain)

        print("=" * 80)

        whois_data = collect_whois(domain)

        print("\nPrediction Features\n")

        for key, value in sorted(

            whois_data["features"].items()

        ):

            print(f"{key:35s}: {value}")

        print("\nCampaign Metadata\n")

        for key, value in sorted(

            whois_data["metadata"].items()

        ):

            print(f"{key:35s}: {value}")