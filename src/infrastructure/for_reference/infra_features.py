# src/infrastructure/infra_features.py

import whois
import socket
import requests
import json
import os
import ssl

from cryptography import x509

from datetime import datetime, timezone

import time


###########################################################################
# CONFIGURATION
###########################################################################

CACHE_PATH = "data/cache/infra_cache.json"

CACHE_VERSION = "v3"

print("LOADED infra_features.py VERSION 3")

CACHE_HITS = 0
CACHE_MISSES = 0

trusted_countries = [
    "India",
    "US",
    "Singapore",
    "Germany",
]

trusted_asns = [
    "Google",
    "Amazon",
    "Microsoft",
    "Cloudflare",
    "Akamai",
]

REQUEST_TIMEOUT = 3

###########################################################################
# EXISTING CONFERENCE HELPERS (UNCHANGED)
###########################################################################

def get_asn_reputation(asn):

    if asn is None:
        return 0

    for t in trusted_asns:

        if t.lower() in str(asn).lower():
            return 1

    return 0


def domain_age_bucket(age):

    if age is None:
        return -1

    elif age == 0:
        return 0

    elif age < 30:
        return 1

    elif age < 180:
        return 2

    elif age < 365:
        return 3

    else:
        return 4


###########################################################################
# CACHE
###########################################################################

def load_cache():

    if not os.path.exists(CACHE_PATH):
        return {}

    try:

        with open(CACHE_PATH, "r") as f:
            return json.load(f)

    except json.JSONDecodeError:

        print("WARNING: Corrupted infrastructure cache detected.")
        print("Creating a new cache.")

        return {}


def save_cache(cache):

    os.makedirs(
        os.path.dirname(CACHE_PATH),
        exist_ok=True,
    )

    with open(CACHE_PATH, "w") as f:

        json.dump(
            cache,
            f,
            indent=2,
        )


CACHE = load_cache()


###########################################################################
# NETWORK INTELLIGENCE
###########################################################################

def get_ip(domain):

    try:

        return socket.gethostbyname(domain)

    except Exception:

        return None


def get_ip_info(ip):

    if not ip:
        return None, None

    try:

        res = requests.get(
            f"http://ip-api.com/json/{ip}",
            timeout=REQUEST_TIMEOUT,
        ).json()

        asn = res.get("as", None)
        country = res.get("country", None)

        return asn, country

    except Exception:

        return None, None


###########################################################################
# WHOIS INTELLIGENCE
###########################################################################

def get_whois_record(domain):
    """
    Returns WHOIS object.

    Returns None if lookup fails.
    """

    try:

        start = time.time()

        record = whois.whois(domain)

        print(
            f"WHOIS {domain} took "
            f"{time.time()-start:.2f}s"
        )

        return record

    except Exception as e:

        print("WHOIS ERROR:", domain, e)

        return None


def _extract_single_date(value):
    """
    WHOIS libraries sometimes return lists.
    """

    if isinstance(value, list):

        if len(value) == 0:
            return None

        return value[0]

    return value


def get_domain_age_days(record):
    """
    Domain age in days.
    """

    if record is None:
        return None

    creation = _extract_single_date(
        record.creation_date
    )

    if creation is None:
        return None

    try:

        return (
            datetime.now(timezone.utc) -
            creation
        ).days

    except Exception:

        return None


def get_registration_lifetime_days(record):
    """
    Registration lifetime.

    Expiry - Creation
    """

    if record is None:
        return None

    creation = _extract_single_date(
        record.creation_date
    )

    expiry = _extract_single_date(
        record.expiration_date
    )

    if creation is None or expiry is None:
        return None

    try:

        return (
            expiry -
            creation
        ).days

    except Exception:

        return None


def get_remaining_registration_days(record):
    """
    Remaining registration validity.
    """

    if record is None:
        return None

    expiry = _extract_single_date(
        record.expiration_date
    )

    if expiry is None:
        return None

    try:

        return (
            expiry -
            datetime.now(timezone.utc)
        ).days

    except Exception:

        return None


def get_registrar(record):
    """
    Registrar name.
    """

    if record is None:
        return None

    try:

        registrar = record.registrar

        if registrar:

            return str(registrar)

    except Exception:

        pass

    return None


def is_privacy_protected(record):
    """
    Detect privacy protected WHOIS.
    """

    if record is None:
        return 0

    fields = [
        getattr(record, "registrant_name", None),
        getattr(record, "name", None),
        getattr(record, "org", None),
        getattr(record, "emails", None),
    ]

    text = " ".join(
        [
            str(x).lower()
            for x in fields
            if x is not None
        ]
    )

    privacy_keywords = [

        "privacy",

        "redacted",

        "whoisguard",

        "proxy",

        "withheld",

        "gdpr",

    ]

    return int(
        any(
            k in text
            for k in privacy_keywords
        )
    )


def get_domain_status_flags(record):
    """
    Number of WHOIS status flags.
    """

    if record is None:
        return 0

    try:

        status = record.status

        if status is None:
            return 0

        if isinstance(status, list):
            return len(status)

        return 1

    except Exception:

        return 0


def collect_whois_features(record):
    """
    Collect dissertation WHOIS intelligence.
    """

    age = get_domain_age_days(record)

    if age is None:

        age_value = 0
        has_age = 0

    else:

        age_value = age
        has_age = 1

    return {

        "domain_age_days": age_value,

        "has_domain_age": has_age,

        "domain_age_bucket":
            domain_age_bucket(age),

        "is_new_domain":
            int(has_age == 1 and age_value <= 3),

        "registration_lifetime_days":
            get_registration_lifetime_days(record) or 0,

        "registration_remaining_days":
            get_remaining_registration_days(record) or 0,

        "registrar":
            get_registrar(record),

        "privacy_protected":
            is_privacy_protected(record),

        "domain_status_count":
            get_domain_status_flags(record),

    }

###########################################################################
# SSL INTELLIGENCE
###########################################################################

def get_ssl_certificate(domain):
    """
    Retrieve leaf SSL certificate.

    Returns
    -------
    cryptography.x509.Certificate or None
    """

    try:

        context = ssl.create_default_context()

        with socket.create_connection(
            (domain, 443),
            timeout=REQUEST_TIMEOUT
        ) as sock:

            with context.wrap_socket(
                sock,
                server_hostname=domain
            ) as ssock:

                cert_bytes = ssock.getpeercert(
                    binary_form=True
                )

        certificate = x509.load_der_x509_certificate(
            cert_bytes
        )

        return certificate

    except Exception:

        return None


###########################################################################
# Certificate Dates
###########################################################################

def get_certificate_age_days(cert):
    """
    Age of certificate in days.
    """

    if cert is None:
        return None

    try:

        return (
            datetime.now(timezone.utc)
            - cert.not_valid_before
        ).days

    except Exception:

        return None


def get_certificate_lifetime_days(cert):
    """
    Certificate validity period.
    """

    if cert is None:
        return None

    try:

        return (
            cert.not_valid_after
            - cert.not_valid_before
        ).days

    except Exception:

        return None


def get_certificate_remaining_days(cert):
    """
    Remaining certificate validity.
    """

    if cert is None:
        return None

    try:

        return (
            cert.not_valid_after
            - datetime.now(timezone.utc)
        ).days

    except Exception:

        return None


###########################################################################
# Subject Alternative Names
###########################################################################

def get_san_count(cert):
    """
    Number of SAN entries.
    """

    if cert is None:
        return 0

    try:

        ext = cert.extensions.get_extension_for_class(
            x509.SubjectAlternativeName
        )

        return len(ext.value)

    except Exception:

        return 0


def has_wildcard_certificate(cert):
    """
    Detect wildcard certificate.
    """

    if cert is None:
        return 0

    try:

        ext = cert.extensions.get_extension_for_class(
            x509.SubjectAlternativeName
        )

        for name in ext.value:

            if name.value.startswith("*."):

                return 1

    except Exception:

        pass

    return 0

###########################################################################
# Certificate Identity
###########################################################################

def is_self_signed(cert):
    """
    Detect whether certificate is self-signed.

    Returns
    -------
    int
        1 -> Self-signed
        0 -> CA signed
    """

    if cert is None:
        return 0

    try:

        return int(
            cert.issuer == cert.subject
        )

    except Exception:

        return 0


def get_certificate_issuer(cert):
    """
    Return issuer common name.

    Returns
    -------
    str or None
    """

    if cert is None:
        return None

    try:

        attributes = cert.issuer.get_attributes_for_oid(
            x509.NameOID.COMMON_NAME
        )

        if attributes:

            return attributes[0].value

    except Exception:

        pass

    return None


###########################################################################
# Certificate Derived Intelligence
###########################################################################

def get_certificate_maturity_score(
    age_days,
    remaining_days
):
    """
    Simple certificate maturity score.

    Range
    -----
    0 - 3
    """

    score = 0

    if age_days is not None and age_days > 180:
        score += 1

    if remaining_days is not None and remaining_days > 90:
        score += 1

    if (
        age_days is not None and
        remaining_days is not None and
        age_days > 180 and
        remaining_days > 180
    ):
        score += 1

    return score


###########################################################################
# SSL Feature Collector
###########################################################################

def collect_ssl_features(domain):
    """
    Collect SSL certificate intelligence.

    Parameters
    ----------
    domain : str

    Returns
    -------
    dict
    """

    cert = get_ssl_certificate(domain)

    age = get_certificate_age_days(cert)

    lifetime = get_certificate_lifetime_days(cert)

    remaining = get_certificate_remaining_days(cert)

    maturity = get_certificate_maturity_score(
        age,
        remaining
    )

    return {

        # -------------------------------------------------
        # Raw
        # -------------------------------------------------

        "certificate_age_days":
            age if age is not None else 0,

        "certificate_lifetime_days":
            lifetime if lifetime is not None else 0,

        "certificate_remaining_days":
            remaining if remaining is not None else 0,

        # -------------------------------------------------
        # Identity
        # -------------------------------------------------

        "certificate_issuer":
            get_certificate_issuer(cert),

        "certificate_san_count":
            get_san_count(cert),

        "certificate_has_wildcard":
            has_wildcard_certificate(cert),

        # -------------------------------------------------
        # Behaviour
        # -------------------------------------------------

        "certificate_self_signed":
            is_self_signed(cert),

        # -------------------------------------------------
        # Derived
        # -------------------------------------------------

        "certificate_maturity_score":
            maturity,

        "certificate_is_recent":
            int(
                age is not None and
                age <= 30
            ),

        "certificate_long_validity":
            int(
                lifetime is not None and
                lifetime >= 365
            )
    }


###########################################################################
# CERTIFICATE TRANSPARENCY INTELLIGENCE
###########################################################################

def get_ct_information(domain):
    """
    Retrieve Certificate Transparency information from crt.sh.

    Parameters
    ----------
    domain : str

    Returns
    -------
    list
        JSON response from crt.sh.
    """

    try:

        response = requests.get(

            f"https://crt.sh/?q=%25.{domain}&output=json",

            timeout=REQUEST_TIMEOUT

        )

        if response.status_code != 200:

            return []

        data = response.json()

        if not isinstance(data, list):

            return []

        return data

    except Exception:

        return []


###########################################################################
# CT Identity Features
###########################################################################

def get_ct_certificate_count(ct_records):
    """
    Total certificates observed.
    """

    if not ct_records:

        return 0

    return len(ct_records)


def get_ct_unique_certificate_count(ct_records):
    """
    Unique certificate IDs.
    """

    if not ct_records:

        return 0

    ids = {

        record.get("id")

        for record in ct_records

        if record.get("id") is not None

    }

    return len(ids)


def get_ct_multi_domain_indicator(ct_records):
    """
    Whether certificates contain multiple domains.
    """

    if not ct_records:

        return 0

    for record in ct_records:

        names = record.get("name_value")

        if names is None:

            continue

        if "\n" in names:

            return 1

    return 0


###########################################################################
# CT Behaviour Features
###########################################################################

def get_latest_certificate_age_days(ct_records):
    """
    Age of most recently logged certificate.
    """

    if not ct_records:

        return None

    latest = None

    for record in ct_records:

        try:

            value = record.get("entry_timestamp")

            if value is None:

                continue

            timestamp = datetime.strptime(

                value,

                "%Y-%m-%dT%H:%M:%S.%f"

            )

            timestamp = timestamp.replace(

                tzinfo=timezone.utc

            )

            if latest is None or timestamp > latest:

                latest = timestamp

        except Exception:

            continue

    if latest is None:

        return None

    return (

        datetime.now(timezone.utc)

        - latest

    ).days


def has_recent_certificate(ct_records):
    """
    Certificate logged within last 30 days.
    """

    age = get_latest_certificate_age_days(

        ct_records

    )

    if age is None:

        return 0

    return int(age <= 30)

###########################################################################
# CT REUSE INTELLIGENCE
###########################################################################

def get_ct_certificate_reuse_count(ct_records):
    """
    Number of reused certificates.

    Reuse = Total Certificates - Unique Certificates
    """

    if not ct_records:
        return 0

    total = get_ct_certificate_count(ct_records)

    unique = get_ct_unique_certificate_count(ct_records)

    return max(0, total - unique)


def get_ct_reuse_ratio(ct_records):
    """
    Certificate reuse ratio.

    Returns
    -------
    float
    """

    total = get_ct_certificate_count(ct_records)

    if total == 0:
        return 0.0

    reuse = get_ct_certificate_reuse_count(
        ct_records
    )

    return reuse / total


###########################################################################
# CT DERIVED INTELLIGENCE
###########################################################################

def get_ct_reputation_score(ct_records):
    """
    Simple CT reputation score.

    Score Range
    -----------
    0 - 3
    """

    score = 0

    cert_count = get_ct_certificate_count(
        ct_records
    )

    latest_age = get_latest_certificate_age_days(
        ct_records
    )

    if cert_count >= 5:
        score += 1

    if latest_age is not None and latest_age > 180:
        score += 1

    if get_ct_multi_domain_indicator(ct_records):
        score += 1

    return score


###########################################################################
# CT FEATURE COLLECTOR
###########################################################################

def collect_ct_features(domain):
    """
    Collect Certificate Transparency intelligence.

    Parameters
    ----------
    domain : str

    Returns
    -------
    dict
    """

    ct_records = get_ct_information(
        domain
    )

    latest_age = get_latest_certificate_age_days(
        ct_records
    )

    return {

        # ---------------------------------------------
        # Identity
        # ---------------------------------------------

        "ct_certificate_count":
            get_ct_certificate_count(
                ct_records
            ),

        "ct_unique_certificate_count":
            get_ct_unique_certificate_count(
                ct_records
            ),

        "ct_certificate_reuse_count":
            get_ct_certificate_reuse_count(
                ct_records
            ),

        "ct_multi_domain_certificate":
            get_ct_multi_domain_indicator(
                ct_records
            ),

        # ---------------------------------------------
        # Behaviour
        # ---------------------------------------------

        "ct_latest_certificate_age_days":
            latest_age
            if latest_age is not None
            else 0,

        "ct_recent_certificate":
            has_recent_certificate(
                ct_records
            ),

        # ---------------------------------------------
        # Derived
        # ---------------------------------------------

        "ct_reuse_ratio":
            get_ct_reuse_ratio(
                ct_records
            ),

        "ct_reputation_score":
            get_ct_reputation_score(
                ct_records
            )

    }


###########################################################################
# DERIVED INFRASTRUCTURE INTELLIGENCE
###########################################################################

def get_domain_maturity_score(features):
    """
    Domain maturity score.

    Range
    -----
    0 - 3
    """

    score = 0

    if features.get("domain_age_days", 0) > 365:
        score += 1

    if features.get("registration_remaining_days", 0) > 180:
        score += 1

    if features.get("certificate_age_days", 0) > 180:
        score += 1

    return score


def get_infrastructure_confidence_score(features):
    """
    Infrastructure confidence.

    Uses multiple independent infrastructure
    observations.

    Range
    -----
    0 - 10
    """

    score = 0

    score += features.get("has_ip", 0)

    score += features.get("has_asn", 0)

    score += features.get("asn_reputation", 0)

    score += int(
        features.get("domain_age_days", 0) > 365
    )

    score += int(
        features.get("registration_remaining_days", 0) > 180
    )

    score += int(
        features.get("certificate_age_days", 0) > 180
    )

    score += int(
        features.get("certificate_remaining_days", 0) > 90
    )

    score += int(
        features.get("ct_certificate_count", 0) >= 5
    )

    score += int(
        features.get("ct_reputation_score", 0) >= 2
    )

    score += int(
        features.get("certificate_self_signed", 0) == 0
    )

    return score


def get_infrastructure_consistency_score(features):
    """
    Infrastructure consistency.

    Measures agreement between independent
    infrastructure observations.

    Range
    -----
    0 - 5
    """

    score = 0

    if (
        features.get("has_ip", 0) and
        features.get("has_asn", 0)
    ):
        score += 1

    if (
        features.get("domain_age_days", 0) > 365 and
        features.get("certificate_age_days", 0) > 180
    ):
        score += 1

    if (
        features.get("registration_remaining_days", 0) > 180 and
        features.get("certificate_remaining_days", 0) > 90
    ):
        score += 1

    if (
        features.get("asn_reputation", 0) == 1 and
        features.get("certificate_self_signed", 0) == 0
    ):
        score += 1

    if (
        features.get("ct_reputation_score", 0) >= 2
    ):
        score += 1

    return score


###########################################################################
# CONFERENCE TRUST SCORE (PRESERVED)
###########################################################################

def get_conference_trust_score(features):
    """
    Original conference trust score.

    Preserved for backward compatibility.
    """

    return (

        features.get("asn_reputation", 0)

        +

        int(
            features.get("has_domain_age", 0)
            and
            features.get("domain_age_days", 0) > 365
        )

        +

        int(
            features.get("has_ip", 0)
            and
            features.get("has_asn", 0)
        )

    )


def add_derived_features(features):
    """
    Adds all dissertation derived features.
    """

    features["domain_maturity_score"] = \
        get_domain_maturity_score(features)

    features["infrastructure_confidence_score"] = \
        get_infrastructure_confidence_score(features)

    features["infrastructure_consistency_score"] = \
        get_infrastructure_consistency_score(features)

    # ---------------------------------------
    # Preserve conference behaviour
    # ---------------------------------------

    features["infra_trust_score"] = \
        get_conference_trust_score(features)

    features["infra_trust_score_scaled"] = \
        features["infra_trust_score"] * 20

    features["trusted_infra_flag"] = int(
        features["infra_trust_score"] >= 3
    )

    features["infra_stability_score"] = int(

        features.get("domain_age_days", 0) > 180

        and

        features.get("has_ip", 0)

        and

        features.get("has_asn", 0)

    )

    features["strong_trusted_infra"] = int(

        features["trusted_infra_flag"]

        and

        features["infra_stability_score"]

    )

    features["strong_trusted_infra_weighted"] = (

        features["strong_trusted_infra"] * 50

    )

    return features


###########################################################################
# MAIN PUBLIC API
###########################################################################

def get_infra_features(domain):
    """
    Collect complete Infrastructure Intelligence.

    Parameters
    ----------
    domain : str

    Returns
    -------
    dict
        Infrastructure intelligence features.
    """

    global CACHE
    global CACHE_HITS
    global CACHE_MISSES

    domain = domain.replace("www.", "").lower().strip()

    # ---------------------------------------------------------
    # CACHE LOOKUP
    # ---------------------------------------------------------

    if domain in CACHE:

        CACHE_HITS += 1

        entry = CACHE[domain]

        if (
            isinstance(entry, dict)
            and
            entry.get("version") == CACHE_VERSION
        ):

            return entry["data"]

    CACHE_MISSES += 1

    # ---------------------------------------------------------
    # NETWORK
    # ---------------------------------------------------------

    ip = get_ip(domain)

    asn, country = get_ip_info(ip)

    network_features = {

        "has_ip": int(ip is not None),

        "has_asn": int(asn is not None),

        "asn_reputation": get_asn_reputation(asn),

        "is_foreign_hosting": int(

            country not in trusted_countries

            if country

            else 0

        ),

        # Identity Features
        "ip_address": ip,

        "asn": asn,

        "hosting_country": country

    }

    # ---------------------------------------------------------
    # WHOIS
    # ---------------------------------------------------------

    whois_record = get_whois_record(domain)

    whois_features = collect_whois_features(

        whois_record

    )

    # ---------------------------------------------------------
    # SSL
    # ---------------------------------------------------------

    ssl_features = collect_ssl_features(

        domain

    )

    # ---------------------------------------------------------
    # CERTIFICATE TRANSPARENCY
    # ---------------------------------------------------------

    ct_features = collect_ct_features(

        domain

    )

    # ---------------------------------------------------------
    # COMBINE EVERYTHING
    # ---------------------------------------------------------

    features = {}

    features.update(network_features)

    features.update(whois_features)

    features.update(ssl_features)

    features.update(ct_features)

    # ---------------------------------------------------------
    # DERIVED INTELLIGENCE
    # ---------------------------------------------------------

    features = add_derived_features(

        features

    )

    # ---------------------------------------------------------
    # CACHE
    # ---------------------------------------------------------

    CACHE[domain] = {

        "version": CACHE_VERSION,

        "data": features

    }

    if len(CACHE) % 20 == 0:

        save_cache(CACHE)

    return features


###########################################################################
# DEBUG
###########################################################################

if __name__ == "__main__":

    sample_domains = [

        "google.com",

        "amazon.com",

        "github.com",

        "paypal.com",

        "microsoft.com"

    ]

    for domain in sample_domains:

        print("\n" + "=" * 80)

        print(domain)

        print("=" * 80)

        features = get_infra_features(domain)

        for key in sorted(features):

            print(f"{key:40s} : {features[key]}")

    print("\n")

    print("=" * 80)

    print("CACHE STATISTICS")

    print("=" * 80)

    print(f"Cache Hits   : {CACHE_HITS}")

    print(f"Cache Misses : {CACHE_MISSES}")

    total = CACHE_HITS + CACHE_MISSES

    if total > 0:

        print(

            f"Hit Rate     : "

            f"{100 * CACHE_HITS / total:.2f}%"

        )