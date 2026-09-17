"""
Infrastructure Certificate Transparency Intelligence

Collects Certificate Transparency (CT) intelligence
using crt.sh JSON API.

Public API
----------
collect_ct(domain)

Returns
-------
{
    "features": {...},
    "metadata": {...}
}
"""

import requests
from datetime import datetime, timezone

###########################################################################
# CONFIGURATION
###########################################################################

CT_TIMEOUT = 10 #5

CT_URL = "https://crt.sh/"

CT_MAX_RECORDS = 5000


###########################################################################
# PRIVATE HELPERS
###########################################################################

def _normalize_domain(domain):
    """
    Normalize domain.
    """

    return (

        domain.lower()

              .replace("www.", "")

              .strip()

    )


def _parse_datetime(value):
    """
    Parse crt.sh timestamp.

    Supports ISO-8601 timestamps including:
    - fractional seconds
    - timezone suffixes
    - timestamps without timezone information

    Returns
    -------
    datetime | None
    """

    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    # -------------------------------------------------------------
    # Primary parser: ISO-8601
    # -------------------------------------------------------------

    try:

        normalized = value

        # Handle UTC "Z" suffix
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"

        dt = datetime.fromisoformat(
            normalized
        )

        # If timezone is absent, assume UTC
        if dt.tzinfo is None:

            dt = dt.replace(
                tzinfo=timezone.utc
            )

        else:

            dt = dt.astimezone(
                timezone.utc
            )

        return dt

    except Exception:
        pass

    # -------------------------------------------------------------
    # Legacy fallback formats
    # -------------------------------------------------------------

    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S"
    ]

    for fmt in formats:

        try:

            dt = datetime.strptime(
                value,
                fmt
            )

            return dt.replace(
                tzinfo=timezone.utc
            )

        except Exception:
            pass

    return None

###########################################################################
# CT COLLECTION
###########################################################################

def _load_ct_history(domain):
    """
    Retrieve Certificate Transparency history
    from crt.sh.

    Returns
    -------
    dict

    {

        "success": bool,

        "records": list,

        "error": str | None

    }

    """

    try:

        response = requests.get(

            CT_URL,

            params={

                "q": f"%.{domain}",

                "output": "json"

            },

            timeout=CT_TIMEOUT

        )

        response.raise_for_status()

        records = response.json()

        if not isinstance(records, list):

            records = []

        records = records[:CT_MAX_RECORDS]

        return {

            "success": True,

            "records": records,

            "error": None

        }

    except Exception as e:

        return {

            "success": False,

            "records": [],

            "error": str(e)

        }


###########################################################################
# COMMON HELPERS
###########################################################################

def _records(result):

    return result["records"]


def _has_history(result):

    return int(

        len(

            result["records"]

        ) > 0

    )

def _record_count(result):
    """
    Number of CT records.
    """

    return len(result["records"])

def _issuer_frequency(result):
    """
    Historical issuer frequency.

    Returns
    -------
    dict
    """

    issuers = {}

    for record in result["records"]:

        issuer = record.get("issuer_name")

        if not issuer:

            continue

        issuer = issuer.strip()

        issuers[issuer] = (

            issuers.get(issuer, 0)

            + 1

        )

    return issuers

def _san_frequency(result):
    """
    Historical SAN frequency.

    Returns
    -------
    dict
    """

    sans = {}

    for record in result["records"]:

        value = record.get("name_value")

        if not value:

            continue

        for san in value.split("\n"):

            san = san.strip()

            if not san:

                continue

            sans[san] = (

                sans.get(san, 0)

                + 1

            )

    return sans

def _record_timestamp(record):
    """
    Extract the best available timestamp from a CT record.

    Primary source
    --------------
    entry_timestamp
        Actual Certificate Transparency log entry time.

    Fallback
    --------
    not_before
        Certificate validity start time.

    The fallback is used only when entry_timestamp is missing
    or cannot be parsed.
    """

    # -------------------------------------------------------------
    # Primary source: CT log entry timestamp
    # -------------------------------------------------------------

    entry_timestamp = record.get(
        "entry_timestamp"
    )

    dt = _parse_datetime(
        entry_timestamp
    )

    if dt is not None:
        return dt

    # -------------------------------------------------------------
    # Fallback: certificate validity start
    # -------------------------------------------------------------

    not_before = record.get(
        "not_before"
    )

    dt = _parse_datetime(
        not_before
    )

    if dt is not None:
        return dt

    return None

def _timestamp_source(result):
    """
    Determine which timestamp source was successfully used.

    Returns
    -------
    str
        "entry_timestamp"
        "not_before"
        "none"
    """

    entry_count = 0
    not_before_count = 0

    for record in result["records"]:

        if _parse_datetime(
            record.get("entry_timestamp")
        ) is not None:

            entry_count += 1

        elif _parse_datetime(
            record.get("not_before")
        ) is not None:

            not_before_count += 1

    if entry_count > 0:
        return "entry_timestamp"

    if not_before_count > 0:
        return "not_before"

    return "none"

def _first_seen(result):
    """
    Return the earliest available CT/certificate timestamp.
    """

    timestamps = []

    for record in result["records"]:

        dt = _record_timestamp(
            record
        )

        if dt is not None:
            timestamps.append(
                dt
            )

    if not timestamps:
        return None

    return min(
        timestamps
    )

def _last_seen(result):
    """
    Return the latest available CT/certificate timestamp.
    """

    timestamps = []

    for record in result["records"]:

        dt = _record_timestamp(
            record
        )

        if dt is not None:
            timestamps.append(
                dt
            )

    if not timestamps:
        return None

    return max(
        timestamps
    )

###########################################################################
# PUBLIC API
###########################################################################

def collect_ct(domain):
    """
    Collect and normalize Certificate Transparency intelligence.

    Parameters
    ----------
    domain : str

    Returns
    -------
    dict
        {
            "features": {...},
            "metadata": {...}
        }

    Important
    ---------
    Raw CT records are NOT returned or persisted.

    The historical certificate observations are normalized into
    compact reusable intelligence such as:

    - record count
    - history presence
    - issuer frequency
    - SAN frequency
    - first seen
    - last seen
    """

    domain = _normalize_domain(domain)

    result = _load_ct_history(domain)

    if not result["success"]:

        return {
            "features": {
                "ct_has_history": 0,
                "ct_record_count": 0
            },

            "metadata": {
                "issuer_frequency": {},
                "san_frequency": {},
                "first_seen": None,
                "last_seen": None,

                # Collection diagnostics
                "ct_query_success": False,
                "ct_error": result["error"]
            }
        }

    first_seen = _first_seen(result)

    last_seen = _last_seen(result)

    return {
        "features": {
            "ct_has_history":
                _has_history(result),
            "ct_record_count":
                _record_count(result)
        },
        "metadata": {
            "issuer_frequency":
                _issuer_frequency(result),
            "san_frequency":
                _san_frequency(result),
            "first_seen":
                first_seen.isoformat()
                if first_seen
                else None,
            "last_seen":
                last_seen.isoformat()
                if last_seen
                else None,

            # Collection diagnostics
            "ct_query_success": True,
            "ct_error": None,

            "timestamp_source":
                _timestamp_source(result)
        }
    }
