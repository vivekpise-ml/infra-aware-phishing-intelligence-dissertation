from pathlib import Path
from datetime import datetime, timezone, timedelta

import pandas as pd

import src.infrastructure.infra_cache as cache
import src.infrastructure.infra_features as infra


# ============================================================
# CONFIGURATION
# ============================================================

CSV_PATH = Path("data/ind_strat_sample_campaign.csv")

# ------------------------------------------------------------
# Expected infrastructure collectors
# ------------------------------------------------------------

COLLECTORS = (
    "network",
    "whois",
    "ssl",
    "ct",
)


# ============================================================
# HELPER — NORMALIZE DOMAIN
# ============================================================

def normalize_domain(domain):
    """
    Normalize a domain for diagnostic comparison.

    This follows the same basic normalization expected by
    the cache layer without modifying the production cache.
    """
    return str(domain).strip().lower().rstrip(".")


# ============================================================
# HELPER — CHECK FEATURE CACHE
# ============================================================

def check_feature_cache(domain):
    """
    Inspect the Feature Cache entry for one domain.

    Returns
    -------
    dict
        Detailed diagnostic information.
    """

    domain = normalize_domain(domain)

    entry = cache.FEATURE_CACHE.get(domain)

    if entry is None:
        return {
            "status": "MISSING",
            "reason": "domain_not_in_feature_cache",
        }

    if not isinstance(entry, dict):
        return {
            "status": "INVALID",
            "reason": "feature_cache_entry_not_dict",
        }

    if entry.get("version") != cache.FEATURE_CACHE_VERSION:
        return {
            "status": "STALE",
            "reason": "feature_cache_version_mismatch",
            "version": entry.get("version"),
            "expected_version": cache.FEATURE_CACHE_VERSION,
        }

    section = entry.get(
        "campaign_metadata"
    )

    if not isinstance(section, dict):
        return {
            "status": "INVALID",
            "reason": "campaign_metadata_section_missing_or_not_dict",
        }

    if not section:
        return {
            "status": "EMPTY",
            "reason": "campaign_metadata_section_empty",
        }

    return {
        "status": "VALID",
        "reason": "feature_cache_valid",
    }


# ============================================================
# HELPER — CHECK ONE OBSERVATION
# ============================================================

def check_observation(domain, collector):
    """
    Reproduce the same validity criteria used by
    has_valid_cached_observation(), but report the
    exact failure reason instead of only True/False.

    This function is READ-ONLY.
    """

    domain = normalize_domain(domain)

    domain_entry = cache.OBSERVATION_CACHE.get(
        domain
    )

    if domain_entry is None:
        return {
            "status": "MISSING",
            "reason": "domain_not_in_observation_cache",
        }

    observation = domain_entry.get(
        collector
    )

    if observation is None:
        return {
            "status": "MISSING",
            "reason": "collector_entry_missing",
        }

    if not isinstance(observation, dict):
        return {
            "status": "INVALID",
            "reason": "collector_entry_not_dict",
        }

    # --------------------------------------------------------
    # Version
    # --------------------------------------------------------

    if observation.get(
        "version"
    ) != cache.OBSERVATION_CACHE_VERSION:

        return {
            "status": "STALE",
            "reason": "version_mismatch",
            "version": observation.get("version"),
            "expected_version": cache.OBSERVATION_CACHE_VERSION,
        }

    # --------------------------------------------------------
    # cached_at
    # --------------------------------------------------------

    cached_at_raw = observation.get(
        "cached_at"
    )

    if not cached_at_raw:
        return {
            "status": "STALE",
            "reason": "cached_at_missing",
        }

    try:

        cached_at = datetime.fromisoformat(
            cached_at_raw
        )

        # Handle timestamps without timezone information
        if cached_at.tzinfo is None:
            cached_at = cached_at.replace(
                tzinfo=timezone.utc
            )

    except Exception:

        return {
            "status": "STALE",
            "reason": "cached_at_invalid",
            "cached_at": cached_at_raw,
        }

    # --------------------------------------------------------
    # TTL
    # --------------------------------------------------------

    ttl_days = cache.OBSERVATION_TTL[
        collector
    ]

    now = datetime.now(
        timezone.utc
    )

    age = now - cached_at

    if age > timedelta(
        days=ttl_days
    ):

        return {
            "status": "STALE",
            "reason": "ttl_expired",
            "cached_at": cached_at_raw,
            "age_days": age.total_seconds()
            / 86400.0,
            "ttl_days": ttl_days,
        }

    # --------------------------------------------------------
    # Actual cached data
    # --------------------------------------------------------

    data = observation.get(
        "data"
    )

    if not isinstance(data, dict):
        return {
            "status": "EMPTY",
            "reason": "data_missing_or_not_dict",
        }

    features = data.get(
        "features"
    )

    if not isinstance(features, dict):
        return {
            "status": "EMPTY",
            "reason": "features_missing_or_not_dict",
        }

    if not features:
        return {
            "status": "EMPTY",
            "reason": "features_dict_empty",
        }

    # --------------------------------------------------------
    # VALID
    # --------------------------------------------------------

    return {
        "status": "VALID",
        "reason": "observation_valid",
        "cached_at": cached_at_raw,
        "age_days": age.total_seconds()
        / 86400.0,
        "ttl_days": ttl_days,
        "feature_count": len(features),
    }


# ============================================================
# LOAD URL SET
# ============================================================

df = pd.read_csv(
    CSV_PATH
)

print("=" * 80)
print("CAMPAIGN CACHE DIAGNOSTIC")
print("=" * 80)

print("CSV:", CSV_PATH)
print("Rows:", len(df))
print("Columns:", list(df.columns))

if "url" not in df.columns:
    raise ValueError(
        f"Expected 'url' column, found: {list(df.columns)}"
    )

urls = (
    df["url"]
    .dropna()
    .astype(str)
    .drop_duplicates()
    .tolist()
)

print("Unique URLs:", len(urls))
print()

# ============================================================
# RESET PRODUCTION CACHE STATISTICS
# ============================================================
#
# These counters are NOT used for the main diagnostic,
# because this diagnostic inspects the cache directly.
#
# We reset them so the final comparison is still clean.
# ============================================================

infra.reset_cache_statistics()


# ============================================================
# DIAGNOSTIC STORAGE
# ============================================================

results = []

feature_status_counts = {
    "VALID": 0,
    "MISSING": 0,
    "INVALID": 0,
    "STALE": 0,
    "EMPTY": 0,
}

observation_status_counts = {
    collector: {
        "VALID": 0,
        "MISSING": 0,
        "INVALID": 0,
        "STALE": 0,
        "EMPTY": 0,
    }
    for collector in COLLECTORS
}

observation_reason_counts = {
    collector: {}
    for collector in COLLECTORS
}


# ============================================================
# INSPECT ALL DOMAINS
# ============================================================

print(
    "Inspecting all URLs..."
)
print(
    "NO real collectors will be called."
)
print(
    "NO cache entries will be modified."
)
print()

for index, url in enumerate(
    urls,
    start=1
):

    domain = normalize_domain(url)

    # --------------------------------------------------------
    # Feature Cache
    # --------------------------------------------------------

    feature_result = check_feature_cache(
        domain
    )

    feature_status = feature_result[
        "status"
    ]

    feature_status_counts[
        feature_status
    ] += 1

    # --------------------------------------------------------
    # Observation Cache
    # --------------------------------------------------------

    observations = {}

    for collector in COLLECTORS:

        result = check_observation(
            domain,
            collector
        )

        observations[
            collector
        ] = result

        status = result[
            "status"
        ]

        reason = result[
            "reason"
        ]

        observation_status_counts[
            collector
        ][
            status
        ] += 1

        observation_reason_counts[
            collector
        ][
            reason
        ] = (
            observation_reason_counts[
                collector
            ].get(
                reason,
                0
            )
            + 1
        )

    # --------------------------------------------------------
    # Determine whether the complete infrastructure
    # cache state is reusable.
    # --------------------------------------------------------

    all_observations_valid = all(
        observations[
            collector
        ]["status"] == "VALID"
        for collector in COLLECTORS
    )

    complete_reuse = (
        feature_status == "VALID"
        and all_observations_valid
    )

    results.append(
        {
            "url": url,
            "domain": domain,
            "feature_status": feature_status,
            "feature_reason": feature_result[
                "reason"
            ],
            "network_status": observations[
                "network"
            ]["status"],
            "network_reason": observations[
                "network"
            ]["reason"],
            "whois_status": observations[
                "whois"
            ]["status"],
            "whois_reason": observations[
                "whois"
            ]["reason"],
            "ssl_status": observations[
                "ssl"
            ]["status"],
            "ssl_reason": observations[
                "ssl"
            ]["reason"],
            "ct_status": observations[
                "ct"
            ]["status"],
            "ct_reason": observations[
                "ct"
            ]["reason"],
            "complete_reuse": complete_reuse,
        }
    )

    # Progress every 50 URLs
    if index % 50 == 0:
        print(
            f"Inspected {index}/{len(urls)} URLs..."
        )


# ============================================================
# DATAFRAME
# ============================================================

diagnostic_df = pd.DataFrame(
    results
)


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 80)
print("FEATURE CACHE SUMMARY")
print("=" * 80)

for status, count in feature_status_counts.items():

    print(
        f"{status:10s}: {count}"
    )


# ============================================================
# OBSERVATION SUMMARY
# ============================================================

print()
print("=" * 80)
print("OBSERVATION CACHE SUMMARY")
print("=" * 80)

for collector in COLLECTORS:

    print()
    print(
        f"[{collector.upper()}]"
    )
    print(
        "-" * 50
    )

    for status, count in (
        observation_status_counts[
            collector
        ].items()
    ):

        print(
            f"{status:10s}: {count}"
        )


# ============================================================
# FAILURE REASONS
# ============================================================

print()
print("=" * 80)
print("OBSERVATION FAILURE REASONS")
print("=" * 80)

for collector in COLLECTORS:

    print()
    print(
        f"[{collector.upper()}]"
    )

    reasons = observation_reason_counts[
        collector
    ]

    if not reasons:

        print(
            "No failures."
        )

        continue

    for reason, count in sorted(
        reasons.items(),
        key=lambda x: (
            -x[1],
            x[0],
        ),
    ):

        print(
            f"{count:5d} : {reason}"
        )


# ============================================================
# COMPLETE REUSE
# ============================================================

complete_reuse_count = int(
    diagnostic_df[
        "complete_reuse"
    ].sum()
)

complete_reuse_failed = (
    len(diagnostic_df)
    - complete_reuse_count
)

print()
print("=" * 80)
print("COMPLETE CACHE REUSE")
print("=" * 80)

print(
    "Fully reusable:",
    complete_reuse_count,
)

print(
    "Not fully reusable:",
    complete_reuse_failed,
)

if len(diagnostic_df) > 0:

    reuse_rate = (
        complete_reuse_count
        / len(diagnostic_df)
    ) * 100

    print(
        "Reuse rate:",
        f"{reuse_rate:.2f}%",
    )


# ============================================================
# DOMAINS THAT CANNOT FULLY REUSE CACHE
# ============================================================

problem_df = diagnostic_df[
    ~diagnostic_df[
        "complete_reuse"
    ]
].copy()

print()
print("=" * 80)
print(
    "DOMAINS REQUIRING CACHE REFRESH / COLLECTOR PATH"
)
print("=" * 80)

print(
    "Count:",
    len(problem_df)
)

if len(problem_df) > 0:

    print()

    display_columns = [
        "domain",
        "feature_status",
        "feature_reason",
        "network_status",
        "network_reason",
        "whois_status",
        "whois_reason",
        "ssl_status",
        "ssl_reason",
        "ct_status",
        "ct_reason",
    ]

    print(
        problem_df[
            display_columns
        ].to_string(
            index=False
        )
    )


# ============================================================
# COLLECTOR CALL ESTIMATE
# ============================================================
#
# A collector is required whenever its observation is not
# valid. This does NOT actually call the collector.
#
# This gives us the exact number of collector executions
# that the production path would be expected to attempt
# if these cache states were encountered.
# ============================================================

print()
print("=" * 80)
print("EXPECTED COLLECTOR EXECUTION REQUIREMENTS")
print("=" * 80)

expected_total_collector_calls = 0

for collector in COLLECTORS:

    column = (
        f"{collector}_status"
    )

    required = int(
        (
            diagnostic_df[
                column
            ] != "VALID"
        ).sum()
    )

    expected_total_collector_calls += (
        required
    )

    print(
        f"{collector.upper():8s}: "
        f"{required}"
    )

print(
    "-" * 50
)

print(
    "TOTAL EXPECTED:",
    expected_total_collector_calls
)


# ============================================================
# FINAL RESULT
# ============================================================

print()
print("=" * 80)
print("DIAGNOSTIC RESULT")
print("=" * 80)

if (
    complete_reuse_failed == 0
    and expected_total_collector_calls == 0
):

    print(
        "RESULT: PASS"
    )

    print(
        "All URLs have a reusable Feature Cache entry"
        " and all four observations are valid."
    )

    print(
        "A subsequent campaign feature extraction"
        " should require zero collector executions."
    )

else:

    print(
        "RESULT: CACHE REUSE INCOMPLETE"
    )

    print(
        "One or more URLs would fall through to"
        " the collector path."
    )

print("=" * 80)