"""
Infrastructure Cache Manager

Centralized cache management for the Infrastructure package.

The framework maintains two independent persistent caches.

1. Feature Cache
----------------

Stores outputs consumed by downstream pipelines.

    data
        Owned by Prediction.

    campaign_metadata
        Owned by Campaign.

2. Observation Cache
--------------------

Stores normalized infrastructure observations collected from
external services.

Examples

    WHOIS
    SSL
    Certificate Transparency
    Network Intelligence

Collectors never directly manage persistent caches.

The Infrastructure Orchestrator (infra_features.py) is responsible
for deciding when cache lookups and updates are performed.

--------------------------------------------------------------------

Public API

Feature Cache
-------------

get_feature_entry()

update_prediction_features()

update_campaign_metadata()

delete_feature_entry()


Observation Cache
-----------------

get_observation()

update_observation()

delete_observation()

has_valid_cached_observation()

cache_statistics()

"""

import json
import os
import tempfile

from copy import deepcopy
from datetime import datetime
from datetime import timedelta
from datetime import timezone


###########################################################################
# CONFIGURATION
###########################################################################

FEATURE_CACHE_PATH = "data/cache/infra_cache.json"

OBSERVATION_CACHE_PATH = (
    "data/cache/infra_observation_cache.json"
)

FEATURE_CACHE_VERSION = "v4"

OBSERVATION_CACHE_VERSION = "v1"

# Collector-specific observation schema versions.
#
# The global cache version tracks the Observation Cache envelope.
# These versions track the structure of each collector's normalized
# observation payload.
OBSERVATION_SCHEMA_VERSION = {
    "network": "v1",
    "whois": "v1",
    "ssl": "v2",
    "ct": "v1",
}

CACHE_SESSION_ACTIVE = False

###########################################################################
# OBSERVATION COLLECTORS
###########################################################################

OBSERVATION_COLLECTORS = (

    "network",

    "whois",

    "ssl",

    "ct"

)


###########################################################################
# CACHE TTL POLICY (Days)
###########################################################################

OBSERVATION_TTL = {

    "network": 1,

    "whois": 30,

    "ssl": 7,

    "ct": 30

}


def begin_cache_session():

    global CACHE_SESSION_ACTIVE
    global FEATURE_CACHE
    global OBSERVATION_CACHE

    CACHE_SESSION_ACTIVE = True

    FEATURE_CACHE = load_feature_cache()

    OBSERVATION_CACHE = load_observation_cache()

def end_cache_session():

    global CACHE_SESSION_ACTIVE

    save_feature_cache(FEATURE_CACHE)

    save_observation_cache(OBSERVATION_CACHE)

    CACHE_SESSION_ACTIVE = False

###########################################################################
# INTERNAL HELPERS
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


def _utc_now():
    """
    Current UTC timestamp.
    """

    return datetime.now(

        timezone.utc

    )


def _utc_now_iso():
    """
    Current UTC timestamp in ISO-8601 format.
    """

    return _utc_now().isoformat()


###########################################################################
# GENERIC JSON HELPERS
###########################################################################

def _load_json(path):
    """
    Generic JSON loader.
    """

    if not os.path.exists(path):

        return {}

    try:

        with open(path, "r") as f:

            return json.load(f)

    except json.JSONDecodeError:

        print(

            f"WARNING: Corrupted cache detected: {path}"

        )

        return {}


def _save_json(path, data):
    """
    Generic JSON writer using atomic file replacement.
    """

    directory = os.path.dirname(path)

    os.makedirs(
        directory,
        exist_ok=True
    )

    fd, temp_path = tempfile.mkstemp(
        dir=directory,
        prefix=".cache_",
        suffix=".tmp"
    )

    try:

        with os.fdopen(
            fd,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                indent=2
            )

            f.flush()

            os.fsync(
                f.fileno()
            )

        os.replace(
            temp_path,
            path
        )

    finally:

        if os.path.exists(temp_path):
            os.remove(temp_path)

###########################################################################
# LOAD / SAVE FEATURE CACHE
###########################################################################

def load_feature_cache():

    return _load_json(

        FEATURE_CACHE_PATH

    )


def save_feature_cache(cache):

    _save_json(

        FEATURE_CACHE_PATH,

        cache

    )


###########################################################################
# LOAD / SAVE OBSERVATION CACHE
###########################################################################

def load_observation_cache():

    return _load_json(

        OBSERVATION_CACHE_PATH

    )


def save_observation_cache(cache):

    _save_json(

        OBSERVATION_CACHE_PATH,

        cache

    )


###########################################################################
# GLOBAL CACHES
###########################################################################

FEATURE_CACHE = load_feature_cache()

OBSERVATION_CACHE = load_observation_cache()


###########################################################################
# CACHE STATISTICS
###########################################################################

#
# Feature Cache
#

FEATURE_CACHE_HITS = 0

FEATURE_CACHE_MISSES = 0


#
# Observation Cache
#
# HIT
#     Entry exists and is fresh.
#
# MISS
#     Entry does not exist.
#
# STALE
#     Entry exists but exceeded TTL.
#

OBSERVATION_CACHE_HITS = {

    collector: 0

    for collector in OBSERVATION_COLLECTORS

}


OBSERVATION_CACHE_MISSES = {

    collector: 0

    for collector in OBSERVATION_COLLECTORS

}


OBSERVATION_CACHE_STALE = {

    collector: 0

    for collector in OBSERVATION_COLLECTORS

}

###########################################################################
# FEATURE CACHE HELPERS
###########################################################################

def _create_empty_feature_entry():
    """
    Create an empty feature cache entry.

    Returns
    -------
    dict
    """

    return {

        "version": FEATURE_CACHE_VERSION,

        "data": {},

        "campaign_metadata": {}

    }

FEATURE_CACHE_SECTIONS = (

    "data",

    "campaign_metadata"

)

###########################################################################
# FEATURE CACHE API
###########################################################################

def get_feature_entry(domain):
    """
    Retrieve one feature cache entry.

    If the entry does not exist or has an older cache
    version, an empty entry is returned.

    Parameters
    ----------
    domain : str

    Returns
    -------
    dict
    """

    global FEATURE_CACHE
    global FEATURE_CACHE_HITS
    global FEATURE_CACHE_MISSES

    domain = _normalize_domain(domain)

    entry = FEATURE_CACHE.get(domain)

    if entry is None:

        FEATURE_CACHE_MISSES += 1

        return _create_empty_feature_entry()

    if (
        not isinstance(entry, dict)
        or
        entry.get("version") != FEATURE_CACHE_VERSION
    ):

        FEATURE_CACHE_MISSES += 1

        return _create_empty_feature_entry()

    FEATURE_CACHE_HITS += 1

    return deepcopy(entry)


def update_feature_entry(
    domain,
    entry,
    save=True
):
    """
    Replace an entire feature cache entry.

    This function reloads the latest cache before writing
    in order to minimise stale in-memory updates.
    """

    global FEATURE_CACHE

    domain = _normalize_domain(domain)

    if not CACHE_SESSION_ACTIVE:
        FEATURE_CACHE = load_feature_cache()

    FEATURE_CACHE[domain] = deepcopy(entry)

    if save and not CACHE_SESSION_ACTIVE:
        save_feature_cache(FEATURE_CACHE)


def update_feature_section(
    domain,
    section,
    section_data,
    save=True
):
    """
    Update one Feature Cache section.

    Existing sections are preserved.

    Parameters
    ----------
    domain : str

    section : str

    section_data : dict
    """

    if section not in FEATURE_CACHE_SECTIONS:

        raise ValueError(

            f"Unknown Feature Cache section: {section}"

        )

    entry = get_feature_entry(domain)

    entry["version"] = FEATURE_CACHE_VERSION

    entry[section] = deepcopy(section_data)

    update_feature_entry(

        domain,

        entry,

        save

    )


def delete_feature_entry(domain):
    """
    Delete one feature cache entry.
    """

    global FEATURE_CACHE

    domain = _normalize_domain(domain)

    if not CACHE_SESSION_ACTIVE:
        FEATURE_CACHE = load_feature_cache()

    if domain not in FEATURE_CACHE:

        return

    del FEATURE_CACHE[domain]

    if not CACHE_SESSION_ACTIVE:
        save_feature_cache(FEATURE_CACHE)

###########################################################################
# OBSERVATION CACHE HELPERS
###########################################################################

def _create_observation_entry(observation,collector):
    """
    Create one observation cache entry.

    Parameters
    ----------
    observation : dict

    Returns
    -------
    dict
    """

    return {

        "version": OBSERVATION_CACHE_VERSION,

        "schema_version": OBSERVATION_SCHEMA_VERSION[collector],

        "cached_at": _utc_now_iso(),

        "data": deepcopy(observation)

    }


###########################################################################
# OBSERVATION CACHE API
###########################################################################

def get_observation(
    domain,
    collector
):
    """
    Retrieve one collector observation.

    Statistics are intentionally NOT updated here.
    Statistics are maintained only by
    has_valid_cached_observation().

    Parameters
    ----------
    domain : str

    collector : str

    Returns
    -------
    dict | None
    """

    global OBSERVATION_CACHE

    domain = _normalize_domain(domain)

    collector = collector.lower()

    if collector not in OBSERVATION_COLLECTORS:

        raise ValueError(

            f"Unknown collector: {collector}"

        )

    domain_entry = OBSERVATION_CACHE.get(domain)

    if domain_entry is None:

        return None

    observation = domain_entry.get(collector)

    if observation is None:

        return None

    if (
        observation.get("version")
        !=
        OBSERVATION_CACHE_VERSION
    ):

        return None

    # The persisted observation entry has the structure:
    #
    # {
    #     "version": "...",
    #     "cached_at": "...",
    #     "data": {
    #         "features": {...},
    #         "metadata": {...}
    #     }
    # }
    #
    # Callers of get_observation() expect the normalized
    # observation itself, not the persistence wrapper.

    return deepcopy(observation.get("data"))


def get_observation_cached_at(
    domain,
    collector
):
    """
    Retrieve the cached_at timestamp of one observation.

    This is a read-only Cache Manager API used by derived
    Feature Cache validation.

    Parameters
    ----------
    domain : str

    collector : str

    Returns
    -------
    str | None
        ISO-8601 cached_at timestamp, or None if unavailable.
    """

    domain = _normalize_domain(domain)
    collector = collector.lower()

    if collector not in OBSERVATION_COLLECTORS:
        raise ValueError(
            f"Unknown collector: {collector}"
        )

    domain_entry = OBSERVATION_CACHE.get(
        domain
    )

    if not isinstance(domain_entry, dict):
        return None

    observation = domain_entry.get(
        collector
    )

    if not isinstance(observation, dict):
        return None

    if (
        observation.get("version")
        !=
        OBSERVATION_CACHE_VERSION
    ):
        return None

    return observation.get(
        "cached_at"
    )

def update_observation(
    domain,
    collector,
    observation,
    save=True
):
    """
    Update one collector observation.
    """

    global OBSERVATION_CACHE

    domain = _normalize_domain(domain)

    collector = collector.lower()

    if collector not in OBSERVATION_COLLECTORS:

        raise ValueError(

            f"Unknown collector: {collector}"

        )

    if not CACHE_SESSION_ACTIVE:
        OBSERVATION_CACHE = load_observation_cache()

    domain_entry = OBSERVATION_CACHE.get(

        domain,

        {}

    )

    domain_entry[collector] = (

        _create_observation_entry(

            observation,
            collector

        )

    )

    OBSERVATION_CACHE[domain] = domain_entry

    if save and not CACHE_SESSION_ACTIVE:
        save_observation_cache(OBSERVATION_CACHE)


def delete_observation(
    domain,
    collector
):
    """
    Delete one collector observation.
    """

    global OBSERVATION_CACHE

    domain = _normalize_domain(domain)

    collector = collector.lower()

    if not CACHE_SESSION_ACTIVE:
        OBSERVATION_CACHE = load_observation_cache()

    domain_entry = OBSERVATION_CACHE.get(domain)

    if domain_entry is None:

        return

    if collector not in domain_entry:

        return

    del domain_entry[collector]

    if not domain_entry:

        del OBSERVATION_CACHE[domain]

    else:

        OBSERVATION_CACHE[domain] = domain_entry

    if not CACHE_SESSION_ACTIVE:
        save_observation_cache(OBSERVATION_CACHE)


def has_valid_cached_observation(
    domain,
    collector
):
    """
    Determine whether a valid cached observation exists.

    IMPORTANT:
    The Observation Cache stores an envelope:

        {
            "version": ...,
            "cached_at": ...,
            "data": {
                "features": ...,
                "metadata": ...
            }
        }

    Cache validity therefore checks:

        1. Entry exists
        2. Cache version is current
        3. cached_at is valid
        4. Entry is within TTL
        5. Actual feature data is present

    An entry with an empty "features" dictionary is NOT
    considered reusable, even if its version and TTL are valid.
    """

    global OBSERVATION_CACHE_HITS
    global OBSERVATION_CACHE_MISSES
    global OBSERVATION_CACHE_STALE

    domain = _normalize_domain(domain)
    collector = collector.lower()

    if collector not in OBSERVATION_COLLECTORS:
        raise ValueError(
            f"Unknown collector: {collector}"
        )

    # ---------------------------------------------------------
    # Retrieve raw observation envelope
    # ---------------------------------------------------------

    domain_entry = OBSERVATION_CACHE.get(
        domain
    )

    if domain_entry is None:

        OBSERVATION_CACHE_MISSES[collector] += 1

        return False

    observation = domain_entry.get(
        collector
    )

    if observation is None:

        OBSERVATION_CACHE_MISSES[collector] += 1

        return False

    # ---------------------------------------------------------
    # Validate cache version
    # ---------------------------------------------------------

    if (
        observation.get("version")
        != OBSERVATION_CACHE_VERSION
    ):

        OBSERVATION_CACHE_STALE[collector] += 1

        return False

    # ---------------------------------------------------------
    # Validate collector-specific observation schema
    # ---------------------------------------------------------

    cached_schema_version = observation.get(
        "schema_version",
        "v1"
    )

    if (
        cached_schema_version
        != OBSERVATION_SCHEMA_VERSION[collector]
    ):

        OBSERVATION_CACHE_STALE[collector] += 1

        return False
    
    # ---------------------------------------------------------
    # Validate cached_at
    # ---------------------------------------------------------

    try:

        cached_at = datetime.fromisoformat(
            observation["cached_at"]
        )

    except Exception:

        OBSERVATION_CACHE_STALE[collector] += 1

        return False

    # ---------------------------------------------------------
    # TTL validation
    # ---------------------------------------------------------

    ttl = OBSERVATION_TTL[collector]

    age = (
        _utc_now()
        - cached_at
    )

    if age > timedelta(days=ttl):

        OBSERVATION_CACHE_STALE[collector] += 1

        return False

    # ---------------------------------------------------------
    # Validate actual cached observation data
    # ---------------------------------------------------------
    #
    # A cache entry can have:
    #
    #   - correct version
    #   - valid cached_at
    #   - valid TTL
    #
    # but still contain no usable observation.
    #
    # Example:
    #
    #     "data": {
    #         "features": {},
    #         "metadata": {}
    #     }
    #
    # Such an entry must NOT be treated as a cache hit.
    #
    # It must fall through to the collector path.
    # ---------------------------------------------------------

    data = observation.get(
        "data"
    )

    if not isinstance(data, dict):

        OBSERVATION_CACHE_MISSES[collector] += 1

        return False

    cached_features = data.get(
        "features"
    )

    if not isinstance(cached_features, dict):

        OBSERVATION_CACHE_MISSES[collector] += 1

        return False

    if not cached_features:

        OBSERVATION_CACHE_MISSES[collector] += 1

        return False

    # ---------------------------------------------------------
    # Valid reusable observation
    # ---------------------------------------------------------

    OBSERVATION_CACHE_HITS[collector] += 1

    return True

###########################################################################
# CACHE STATISTICS
###########################################################################

def cache_statistics():
    """
    Return cache statistics for both Feature Cache and
    Observation Cache.

    Returns
    -------
    dict
    """

    feature_total = (

        FEATURE_CACHE_HITS

        +

        FEATURE_CACHE_MISSES

    )

    if feature_total == 0:

        feature_hit_rate = 0.0

    else:

        feature_hit_rate = (

            FEATURE_CACHE_HITS

            /

            feature_total

        )

    observation_stats = {}

    for collector in OBSERVATION_COLLECTORS:

        hits = OBSERVATION_CACHE_HITS[collector]

        misses = OBSERVATION_CACHE_MISSES[collector]

        stale = OBSERVATION_CACHE_STALE[collector]

        total = hits + misses + stale

        if total == 0:

            hit_rate = 0.0

        else:

            hit_rate = hits / total

        observation_stats[collector] = {

            "hits": hits,

            "misses": misses,

            "stale": stale,

            "total": total,

            "effective_hit_rate": hit_rate

        }

    return {

        "feature_cache": {

            "hits": FEATURE_CACHE_HITS,

            "misses": FEATURE_CACHE_MISSES,

            "total": feature_total,

            "hit_rate": feature_hit_rate

        },

        "observation_cache": observation_stats

    }


###########################################################################
# CACHE FLUSH
###########################################################################

def flush_feature_cache():
    """
    Persist the current feature cache to disk.
    """

    save_feature_cache(

        FEATURE_CACHE

    )


def flush_observation_cache():
    """
    Persist the current observation cache to disk.
    """

    save_observation_cache(

        OBSERVATION_CACHE

    )


###########################################################################
# DEBUG
###########################################################################

if __name__ == "__main__":

    import pprint

    pprint.pprint(

        cache_statistics(),

        sort_dicts=False

    )