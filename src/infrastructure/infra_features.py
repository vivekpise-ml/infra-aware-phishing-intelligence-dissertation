"""
Infrastructure Feature Orchestrator

Coordinates infrastructure intelligence collection across
the independent infrastructure collectors.

Collectors
----------
- Network
- WHOIS
- SSL
- Certificate Transparency (CT)

Responsibilities
----------------
- Check the Feature Cache for an existing derived result.
- Validate the underlying infrastructure observations.
- Reuse valid observations from the Observation Cache.
- Invoke collectors when observations are missing or stale.
- Update the Observation Cache with normalized observations.
- Provide Prediction features and Campaign metadata.

The module does not implement:
- Network collection
- WHOIS parsing
- SSL parsing
- CT parsing
- Persistent cache management

Those responsibilities belong to the corresponding
collector and cache modules.

Public API
----------
collect_infrastructure_features(domain, feature_section)
"""

###########################################################################
# IMPORTS
###########################################################################

from copy import deepcopy
from datetime import datetime, timezone

###############################################################################
# CACHE STATISTICS
###############################################################################

_CACHE_STATISTICS = {
    "feature_cache_hits": 0,
    "feature_cache_misses": 0,
    "observation_cache_hits": 0,
    "observation_cache_misses": 0,
    "collector_calls": 0,
}

# ---------------------------------------------------------------------------
# Conference-era (where paper was submitted) infrastructure trust configuration
# ---------------------------------------------------------------------------

trusted_countries = [
    "India",
    "US",
    "Singapore",
    "Germany",
]


def get_asn_reputation(asn):
    """
    Conference-era ASN reputation signal.

    Returns:
        1 -> ASN belongs to a known trusted infrastructure provider
        0 -> otherwise / unknown
    """

    if asn is None:
        return 0

    trusted_asns = [
        "Google",
        "Amazon",
        "Microsoft",
        "Cloudflare",
        "Akamai",
    ]

    asn_string = str(asn).lower()

    for provider in trusted_asns:
        if provider.lower() in asn_string:
            return 1

    return 0


def domain_age_bucket(age):
    """
    Conference-era domain-age bucket.

    0 : created today
    1 : < 30 days
    2 : < 180 days
    3 : < 365 days
    4 : >= 365 days
   -1 : unknown
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

#### End conference - era global configuration

def reset_cache_statistics():
    """
    Reset infrastructure cache statistics.

    This affects only in-memory counters.
    It does not modify Feature Cache or Observation Cache.
    """

    for key in _CACHE_STATISTICS:
        _CACHE_STATISTICS[key] = 0


def get_cache_statistics():
    """
    Return a snapshot of infrastructure cache statistics.

    Returns
    -------
    dict
        Independent copy of the current statistics.
    """

    return deepcopy(_CACHE_STATISTICS)


def get_cache_statistics_summary():
    """
    Return cache statistics together with derived hit rates.

    This is an observability helper only.
    It does not affect cache validity or cache decisions.
    """

    stats = get_cache_statistics()

    feature_total = (
        stats["feature_cache_hits"]
        + stats["feature_cache_misses"]
    )

    observation_total = (
        stats["observation_cache_hits"]
        + stats["observation_cache_misses"]
    )

    stats["feature_cache_hit_rate"] = (
        stats["feature_cache_hits"] / feature_total
        if feature_total > 0
        else 0.0
    )

    stats["observation_cache_hit_rate"] = (
        stats["observation_cache_hits"] / observation_total
        if observation_total > 0
        else 0.0
    )

    return stats

###########################################################################
# FEATURE CACHE SECTIONS
###########################################################################

FEATURE_SECTION_DATA = "data"

FEATURE_SECTION_CAMPAIGN_METADATA = "campaign_metadata"

VALID_FEATURE_SECTIONS = (

    FEATURE_SECTION_DATA,

    FEATURE_SECTION_CAMPAIGN_METADATA,

)


###########################################################################
# INFRASTRUCTURE COLLECTORS
###########################################################################

COLLECTOR_NETWORK = "network"

COLLECTOR_WHOIS = "whois"

COLLECTOR_SSL = "ssl"

COLLECTOR_CT = "ct"

INFRASTRUCTURE_COLLECTORS = (

    COLLECTOR_NETWORK,

    COLLECTOR_WHOIS,

    COLLECTOR_SSL,

    COLLECTOR_CT,

)

###########################################################################
# FEATURE SECTION VALIDATION
###########################################################################

def _validate_feature_section(feature_section):
    """
    Validate the requested Feature Cache section.

    Parameters
    ----------
    feature_section : str

    Raises
    ------
    ValueError
        If the requested Feature Cache section is unsupported.
    """

    if feature_section not in VALID_FEATURE_SECTIONS:

        raise ValueError(

            f"Unsupported feature section: "
            f"{feature_section}"

        )


###########################################################################
# DOMAIN NORMALIZATION
###########################################################################

def _normalize_domain(domain):
    """
    Normalize a domain name for infrastructure processing.

    Parameters
    ----------
    domain : str

    Returns
    -------
    str
    """

    if domain is None:

        return ""

    return (

        str(domain)

        .lower()

        .replace("www.", "")

        .strip()

    )


###########################################################################
# RESULT HELPERS
###########################################################################

def _empty_result():
    """
    Create an empty infrastructure result.

    Returns
    -------
    dict
        Standard infrastructure result.
    """

    return {

        "features": {},

        "metadata": {},

    }


def _copy_dict(value):
    """
    Safely copy a dictionary.

    Parameters
    ----------
    value : dict

    Returns
    -------
    dict
    """

    if not isinstance(value, dict):

        return {}

    return deepcopy(value)


def _merge_features(
    target,
    source
):
    """
    Merge collector features into the
    aggregated feature dictionary.

    Parameters
    ----------
    target : dict

    source : dict
    """

    if not isinstance(source, dict):

        return

    target.update(

        deepcopy(source)

    )


def _merge_metadata(
    target,
    collector,
    source
):
    """
    Store collector metadata under its
    collector namespace.

    Parameters
    ----------
    target : dict

    collector : str

    source : dict
    """

    target[collector] = _copy_dict(

        source

    )

###########################################################################
# CACHE ACCESS
###########################################################################

from .infra_cache import (
    get_feature_entry,
    get_observation,
    get_observation_cached_at,
    has_valid_cached_observation,
    update_observation,
)

###########################################################################
# FEATURE CACHE HELPERS
###########################################################################

def _get_feature_cache_entry(domain):
    """
    Retrieve the Feature Cache entry for a domain.

    Returns
    -------
    dict | None
    """

    entry = get_feature_entry(

        domain

    )

    if not isinstance(entry, dict):

        return None

    return entry


def _get_cached_feature_section(
    domain,
    feature_section
):
    """
    Retrieve a requested Feature Cache section.

    Parameters
    ----------
    domain : str

    feature_section : str

    Returns
    -------
    dict | None
    """

    if feature_section not in VALID_FEATURE_SECTIONS:

        raise ValueError(

            f"Unsupported feature section: "
            f"{feature_section}"

        )

    entry = _get_feature_cache_entry(

        domain

    )

    if entry is None:

        return None

    section = entry.get(

        feature_section

    )

    if not isinstance(section, dict):

        return None

    if not section:

        return None

    return deepcopy(section)


###########################################################################
# OBSERVATION CACHE HELPERS
###########################################################################

def _get_valid_observation(
    domain,
    collector
):
    """
    Retrieve a valid cached observation.

    Cache statistics are recorded here.

    Returns
    -------
    dict | None

    Notes
    -----
    A valid observation is returned exactly as stored
    in the Observation Cache.

    No collector-specific interpretation is performed here.
    """

    if not has_valid_cached_observation(
        domain,
        collector
    ):

        _CACHE_STATISTICS[
            "observation_cache_misses"
        ] += 1

        return None

    observation = get_observation(
        domain,
        collector
    )

    if not isinstance(observation, dict):

        _CACHE_STATISTICS[
            "observation_cache_misses"
        ] += 1

        return None

    _CACHE_STATISTICS[
        "observation_cache_hits"
    ] += 1

    return deepcopy(observation)


def _store_observation(
    domain,
    collector,
    observation
):
    """
    Store a normalized infrastructure observation.

    Parameters
    ----------
    domain : str

    collector : str

    observation : dict
        Normalized collector observation containing
        features and metadata.

    Returns
    -------
    dict
        The normalized observation that was stored.
    """

    if not isinstance(observation, dict):

        observation = _empty_result()

    normalized = {

        "features": _copy_dict(

            observation.get("features")

        ),

        "metadata": _copy_dict(

            observation.get("metadata")

        ),

    }

    update_observation(

        domain,

        collector,

        normalized

    )

    return normalized


def _is_campaign_metadata_cache_fresh(cached_features):
    """
    Determine whether cached Campaign Metadata is still fresh.

    Campaign Metadata uses a 30-day cache lifetime.
    Missing or malformed timestamps are treated as stale.

    Returns
    -------
    bool
    """

    if not isinstance(cached_features, dict):
        return False

    timestamp = cached_features.get("cached_at")

    if not timestamp:
        return False

    try:
        cached_at = datetime.fromisoformat(timestamp)

        # Handle legacy naive timestamps defensively.
        if cached_at.tzinfo is None:
            cached_at = cached_at.replace(tzinfo=timezone.utc)

        age = datetime.now(timezone.utc) - cached_at

        return age.days < 30

    except Exception:
        return False


def _is_campaign_metadata_cache_current(
    domain,
    cached_features
):
    """
    Determine whether cached Campaign Metadata was
    generated after all underlying infrastructure
    observations it depends on.

    A derived Campaign Metadata cache is stale when
    any underlying observation has a newer cached_at
    timestamp than the derived Campaign Metadata.
    """

    if not isinstance(cached_features, dict):
        return False

    campaign_cached_at = cached_features.get(
        "cached_at"
    )

    if not campaign_cached_at:
        return False

    try:
        campaign_cached_at = datetime.fromisoformat(
            campaign_cached_at
        )

        if campaign_cached_at.tzinfo is None:
            campaign_cached_at = campaign_cached_at.replace(
                tzinfo=timezone.utc
            )

    except Exception:
        return False

    for collector in INFRASTRUCTURE_COLLECTORS:

        observation_cached_at = (
            get_observation_cached_at(
                domain,
                collector
            )
        )

        if not observation_cached_at:
            return False

        try:
            observation_cached_at = (
                datetime.fromisoformat(
                    observation_cached_at
                )
            )

            if observation_cached_at.tzinfo is None:
                observation_cached_at = (
                    observation_cached_at.replace(
                        tzinfo=timezone.utc
                    )
                )

        except Exception:
            return False

        if observation_cached_at > campaign_cached_at:
            return False

    return True


###########################################################################
# FEATURE CACHE VALIDATION
###########################################################################

def _has_valid_cached_features(
    domain,
    feature_section
):
    """
    Determine whether a cached derived result can be reused.

    A Feature Cache entry is reusable only when:

    1. The requested Feature Cache section exists.
    2. All infrastructure observations required to derive that
       section are still valid.

    Parameters
    ----------
    domain : str

    feature_section : str

    Returns
    -------
    bool
    """


    '''
    cached_features = _get_cached_feature_section(

        domain,

        feature_section

    )

    if cached_features is None:

        return False

    for collector in INFRASTRUCTURE_COLLECTORS:

        if not has_valid_cached_observation(

            domain,

            collector

        ):

            return False

    return True
    '''

    cached_features = _get_cached_feature_section(

        domain,

        feature_section

    )

    if cached_features is None:

        return False

    # ---------------------------------------------------------
    # Validate actual cached derived data
    # ---------------------------------------------------------
    #
    # A Feature Cache section must not be considered reusable
    # merely because the section exists and its underlying
    # observations are valid.
    #
    # The derived cache itself must contain meaningful data.
    #
    # This prevents an empty/failed derived result from being
    # reused when the underlying observations are available.
    # ---------------------------------------------------------

    if feature_section == FEATURE_SECTION_DATA:

        if not isinstance(cached_features, dict):

            return False

        if not cached_features:

            return False


    elif feature_section == FEATURE_SECTION_CAMPAIGN_METADATA:

        # ---------------------------------------------------------
        # Campaign Metadata requires meaningful data from the
        # underlying infrastructure collectors.
        #
        # A single populated field such as ssl_available=1 must
        # NOT make an otherwise incomplete derived metadata cache
        # reusable.
        # ---------------------------------------------------------

        has_network_metadata = any([
            cached_features.get("ip"),
            cached_features.get("as"),
            cached_features.get("organization"),
            cached_features.get("isp"),
            cached_features.get("country"),
        ])

        has_whois_metadata = any([
            cached_features.get("nameservers"),
            cached_features.get("nameserver_count", 0),
        ])

        has_ssl_metadata = (
            cached_features.get("ssl_available", 0) == 1
            or cached_features.get("ssl_days_remaining", 0) > 0
        )

        if not (
            has_network_metadata
            and has_whois_metadata
            and has_ssl_metadata
        ):

            return False

        # ---------------------------------------------------------
        # Validate Campaign Metadata freshness
        # ---------------------------------------------------------

        if not _is_campaign_metadata_cache_fresh(
            cached_features
        ):
            return False

        # ---------------------------------------------------------
        # Validate Campaign Metadata dependency timestamps
        # ---------------------------------------------------------

        if not _is_campaign_metadata_cache_current(
            domain,
            cached_features
        ):
            return False
        
    # ---------------------------------------------------------
    # Validate underlying infrastructure observations
    # ---------------------------------------------------------
    #
    # Existing observation-cache validation is preserved.
    # ---------------------------------------------------------

    for collector in INFRASTRUCTURE_COLLECTORS:

        if not has_valid_cached_observation(

            domain,

            collector

        ):

            return False

    return True


###########################################################################
# FEATURE CACHE RESULT
###########################################################################

def _get_reusable_feature_result(
    domain,
    feature_section
):
    """
    Return a reusable Feature Cache result when both the
    derived result and its underlying observations are valid.

    Cache statistics are recorded here.

    Returns
    -------
    dict | None
    """

    if not _has_valid_cached_features(
        domain,
        feature_section
    ):

        _CACHE_STATISTICS[
            "feature_cache_misses"
        ] += 1

        return None

    reusable = _get_cached_feature_section(
        domain,
        feature_section
    )

    if reusable is None:

        _CACHE_STATISTICS[
            "feature_cache_misses"
        ] += 1

        return None

    _CACHE_STATISTICS[
        "feature_cache_hits"
    ] += 1

    return reusable

###########################################################################
# COLLECTOR IMPORTS
###########################################################################

from .infra_network import collect_network
from .infra_whois import collect_whois
from .infra_ssl import collect_ssl
from .infra_ct import collect_ct


###########################################################################
# COLLECTOR EXECUTION
###########################################################################

def _collect_network_observation(domain):
    """
    Obtain Network observation.

    Uses a valid Observation Cache entry when available.
    Otherwise invokes the Network collector and stores the
    normalized observation.
    """

    cached = _get_valid_observation(

        domain,

        COLLECTOR_NETWORK

    )

    if cached is not None:

        return cached

    _CACHE_STATISTICS[
        "collector_calls"
    ] += 1

    result = collect_network(

        domain

    )

    print("\nDEBUG NETWORK COLLECTOR RESULT:")
    print(result)

    normalized = {

        "features": _copy_dict(

            result.get("features")

        ),

        "metadata": _copy_dict(

            result.get("metadata")

        ),

    }

    return _store_observation(

        domain,

        COLLECTOR_NETWORK,

        normalized

    )


def _collect_whois_observation(domain):
    """
    Obtain WHOIS observation.

    Uses a valid Observation Cache entry when available.
    Otherwise invokes the WHOIS collector and stores the
    normalized observation.
    """

    cached = _get_valid_observation(

        domain,

        COLLECTOR_WHOIS

    )

    if cached is not None:

        return cached

    _CACHE_STATISTICS[
        "collector_calls"
    ] += 1

    result = collect_whois(

        domain

    )

    print("\nDEBUG WHOIS COLLECTOR RESULT:")
    print(result)

    normalized = {

        "features": _copy_dict(

            result.get("features")

        ),

        "metadata": _copy_dict(

            result.get("metadata")

        ),

    }

    return _store_observation(

        domain,

        COLLECTOR_WHOIS,

        normalized

    )


def _collect_ssl_observation(domain):
    """
    Obtain SSL observation.

    Uses a valid Observation Cache entry when available.
    Otherwise invokes the SSL collector and stores the
    normalized observation.
    """

    cached = _get_valid_observation(

        domain,

        COLLECTOR_SSL

    )

    if cached is not None:

        return cached

    _CACHE_STATISTICS[
        "collector_calls"
    ] += 1

    result = collect_ssl(

        domain

    )

    print("\nDEBUG SSL COLLECTOR RESULT:")
    print(result)

    normalized = {

        "features": _copy_dict(

            result.get("features")

        ),

        "metadata": _copy_dict(

            result.get("metadata")

        ),

    }

    return _store_observation(

        domain,

        COLLECTOR_SSL,

        normalized

    )


def _collect_ct_observation(domain):
    """
    Obtain CT observation.

    Uses a valid Observation Cache entry when available.
    Otherwise invokes the CT collector and stores the
    normalized observation.
    """

    cached = _get_valid_observation(

        domain,

        COLLECTOR_CT

    )

    if cached is not None:

        return cached

    _CACHE_STATISTICS[
        "collector_calls"
    ] += 1

    result = collect_ct(

        domain

    )

    print("\nDEBUG CT COLLECTOR RESULT:")
    print(result)

    normalized = {

        "features": _copy_dict(

            result.get("features")

        ),

        "metadata": _copy_dict(

            result.get("metadata")

        ),

    }

    return _store_observation(

        domain,

        COLLECTOR_CT,

        normalized

    )


###########################################################################
# INFRASTRUCTURE OBSERVATION COLLECTION
###########################################################################

def _collect_all_observations(domain):
    """
    Obtain all required infrastructure observations.

    Each collector is handled independently.

    A valid observation is reused from the Observation Cache.
    Only missing or stale observations trigger network
    collection.

    Returns
    -------
    dict
        {
            "network": {...},
            "whois": {...},
            "ssl": {...},
            "ct": {...}
        }
    """

    return {

        COLLECTOR_NETWORK:
            _collect_network_observation(domain),

        COLLECTOR_WHOIS:
            _collect_whois_observation(domain),

        COLLECTOR_SSL:
            _collect_ssl_observation(domain),

        COLLECTOR_CT:
            _collect_ct_observation(domain),

    }

###########################################################################
# OBSERVATION → DERIVED OUTPUT
###########################################################################

def _build_features_from_observations(observations):
    """
    Derive the complete infrastructure feature set from normalized
    Observation Cache data.

    IMPORTANT
    ---------
    This function does NOT perform network/WHOIS/SSL/CT collection.

    The collection flow is:

        Feature Cache
              ↓
        Observation Cache
              ↓
        collectors (only when required)
              ↓
        this function
              ↓
        derived infrastructure features

    The conference-era trust/stability features are intentionally
    preserved because they are part of the training and inference
    feature contract.
    """

    # ------------------------------------------------------------------
    # Defensive extraction of observation sections
    # ------------------------------------------------------------------

    network = observations.get(
        "network",
        {}
    ) or {}

    whois_data = observations.get(
        "whois",
        {}
    ) or {}

    ssl = observations.get(
        "ssl",
        {}
    ) or {}

    ct = observations.get(
        "ct",
        {}
    ) or {}

    network_features = network.get(
        "features",
        {}
    ) or {}

    network_metadata = network.get(
        "metadata",
        {}
    ) or {}

    whois_features = whois_data.get(
        "features",
        {}
    ) or {}

    whois_metadata = whois_data.get(
        "metadata",
        {}
    ) or {}

    ssl_features = ssl.get(
        "features",
        {}
    ) or {}

    ct_features = ct.get(
        "features",
        {}
    ) or {}

    # ------------------------------------------------------------------
    # RAW infrastructure observations
    # ------------------------------------------------------------------

    has_ip = int(
        network_features.get(
            "has_ip",
            0
        )
    )

    has_asn = int(
        network_features.get(
            "has_asn",
            0
        )
    )

    asn_reputation = int(
        network_features.get(
            "asn_reputation",
            0
        )
    )

    is_foreign_hosting = int(
        network_features.get(
            "is_foreign_hosting",
            0
        )
    )

    # ------------------------------------------------------------------
    # WHOIS / domain age
    # ------------------------------------------------------------------

    has_domain_age = int(
        whois_features.get(
            "has_domain_age",
            0
        )
    )

    domain_age_days = whois_features.get(
        "domain_age_days"
    )

    # Preserve the conference-era availability semantics.
    #
    # Unknown age is represented as 0 for the numerical feature,
    # while has_domain_age explicitly tells the model whether that
    # value is actually known.

    if domain_age_days is None:
        age_value = 0
    else:
        age_value = domain_age_days

    # ------------------------------------------------------------------
    # Conference-era domain age bucket
    # ------------------------------------------------------------------

    domain_age_bucket_value = domain_age_bucket(
        domain_age_days
    )

    # ------------------------------------------------------------------
    # Conference-era ASN reputation
    #
    # Prefer the collector-produced feature because the new network
    # collector already derives it from the ASN.
    #
    # If it is unavailable, derive it from ASN metadata using the
    # conference-era get_asn_reputation() implementation.
    # ------------------------------------------------------------------

    if "asn_reputation" not in network_features:

        asn = network_metadata.get(
            "asn"
        )

        asn_reputation = get_asn_reputation(
            asn
        )

    # ------------------------------------------------------------------
    # Conference-era TRUST SCORE
    #
    # EXACT original semantics:
    #
    #   ASN reputation
    # + domain older than 365 days
    # + IP and ASN both available
    #
    # Maximum = 3
    # ------------------------------------------------------------------

    infra_trust_score = (
        asn_reputation
        + int(
            has_domain_age == 1
            and
            age_value > 365
        )
        + int(
            has_ip == 1
            and
            has_asn == 1
        )
    )

    # ------------------------------------------------------------------
    # Conference-era STABILITY SCORE
    #
    # Original semantics:
    #
    #   domain age > 180 days
    #   AND IP exists
    #   AND ASN exists
    # ------------------------------------------------------------------

    infra_stability_score = int(
        (
            domain_age_days is not None
            and
            domain_age_days > 180
        )
        and
        has_ip == 1
        and
        has_asn == 1
    )

    # ------------------------------------------------------------------
    # Complete infrastructure feature dictionary
    # ------------------------------------------------------------------

    features = {

        # ==============================================================
        # DOMAIN AGE / AVAILABILITY
        # ==============================================================

        "domain_age_days":
            age_value,

        "has_domain_age":
            has_domain_age,

        "is_new_domain":
            int(
                has_domain_age == 1
                and
                age_value <= 3
            ),

        "domain_age_bucket":
            domain_age_bucket_value,

        # ==============================================================
        # NETWORK AVAILABILITY
        # ==============================================================

        "has_ip":
            has_ip,

        "has_asn":
            has_asn,

        "is_foreign_hosting":
            is_foreign_hosting,

        # ==============================================================
        # ASN REPUTATION
        # ==============================================================

        "asn_reputation":
            asn_reputation,

        # ==============================================================
        # INFRASTRUCTURE STABILITY
        # ==============================================================

        "infra_stability_score":
            infra_stability_score,

        # ==============================================================
        # TRUST SCORE
        # ==============================================================

        "infra_trust_score":
            infra_trust_score,

        "infra_trust_score_scaled":
            infra_trust_score * 20,

        "trusted_infra_flag":
            int(
                infra_trust_score >= 3
            ),

        # ==============================================================
        # STRONG TRUSTED INFRASTRUCTURE
        # ==============================================================

        "strong_trusted_infra":
            int(
                (
                    infra_trust_score >= 3
                )
                and
                (
                    domain_age_days is not None
                    and
                    domain_age_days > 180
                )
                and
                (
                    has_ip == 1
                )
                and
                (
                    has_asn == 1
                )
            ),

        # ==============================================================
        # WEIGHTED STRONG TRUSTED INFRASTRUCTURE
        # ==============================================================

        "strong_trusted_infra_weighted":
            int(
                (
                    infra_trust_score >= 3
                )
                and
                (
                    domain_age_days is not None
                    and
                    domain_age_days > 180
                )
                and
                (
                    has_ip == 1
                )
                and
                (
                    has_asn == 1
                )
            ) * 50,

        # ==============================================================
        # EXISTING SSL FEATURES
        # ==============================================================

        **ssl_features,

        # ==============================================================
        # EXISTING CT FEATURES
        # ==============================================================

        **ct_features,

        # ==============================================================
        # EXISTING WHOIS FEATURES
        # ==============================================================
        #
        # This preserves the additional features introduced by the
        # newer WHOIS collector instead of throwing them away.
        #
        **{
            k: v
            for k, v in whois_features.items()
            if k not in {
                "domain_age_days",
                "has_domain_age",
                "domain_age_bucket",
                "is_new_domain",
            }
        },

        # ==============================================================
        # EXISTING NETWORK FEATURES
        # ==============================================================
        #
        # Preserve any additional network-derived numerical features.
        #
        **{
            k: v
            for k, v in network_features.items()
            if k not in {
                "has_ip",
                "has_asn",
                "asn_reputation",
                "is_foreign_hosting",
            }
        },
    }

    return features


def _build_metadata_from_observations(observations):
    """
    Build Campaign metadata from normalized
    infrastructure observations.

    Parameters
    ----------
    observations : dict

    Returns
    -------
    dict
    """

    metadata = {}

    for collector in INFRASTRUCTURE_COLLECTORS:

        observation = observations.get(

            collector,

            {}

        )

        if not isinstance(observation, dict):

            continue

        _merge_metadata(

            metadata,

            collector,

            observation.get("metadata")

        )

    return metadata


###########################################################################
# PUBLIC API
###########################################################################

def collect_infrastructure_features(
    domain,
    feature_section
):
    """
    Collect or retrieve infrastructure intelligence
    for a domain.

    Parameters
    ----------
    domain : str

    feature_section : str
        Requested derived output.

        Supported values:

        - "data"
        - "campaign_metadata"

    Returns
    -------
    dict
        {
            "features": {...},
            "metadata": {...}
        }

    Notes
    -----
    Feature Cache is checked first.

    If the cached derived result cannot be reused,
    the Observation Cache is consulted.

    Missing or stale observations are collected through
    the appropriate infrastructure collectors.

    The Observation Cache is updated with normalized
    observations.

    This function does NOT update the Feature Cache.

    The owning Prediction or Campaign pipeline is
    responsible for persisting its respective section.
    """

    domain = _normalize_domain(

        domain

    )

    if not domain:

        return _empty_result()

    _validate_feature_section(

        feature_section

    )

    #######################################################################
    # LEVEL 1 — FEATURE CACHE
    #######################################################################

    reusable = _get_reusable_feature_result(

        domain,

        feature_section

    )

    if reusable is not None:

        if feature_section == FEATURE_SECTION_DATA:

            return {

                "features": reusable,

                "metadata": {},

            }

        return {

            "features": {},

            "metadata": reusable,

        }

    #######################################################################
    # LEVEL 2 — OBSERVATION CACHE / COLLECTORS
    #######################################################################

    observations = _collect_all_observations(

        domain

    )

    #######################################################################
    # DERIVE REQUESTED OUTPUT
    #######################################################################

    features = _build_features_from_observations(

        observations

    )

    metadata = _build_metadata_from_observations(

        observations

    )

    #######################################################################
    # RETURN
    #######################################################################

    return {

        "features": features,

        "metadata": metadata,

    }
