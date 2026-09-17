"""
Infrastructure Cache Statistics Test

Validates the cache statistics exposed by infra_features.py
while using the REAL two-cache architecture:

    infra_cache.json
            +
    infra_observation_cache.json

The actual cache implementation is used.

External collectors are replaced with deterministic test doubles,
so no real network traffic is generated.

Tests:
    1. Cold start
    2. Feature Cache hit
    3. One stale Observation Cache entry
    4. Statistics reset
"""

import src.infrastructure.infra_cache as cache
import src.infrastructure.infra_features as infra


DOMAIN = "example.com"


# ============================================================================
# TEST CACHE INITIALIZATION
# ============================================================================

def initialize_test_caches(tmp_path, monkeypatch):
    """
    Redirect the REAL infrastructure cache implementation to temporary
    cache files and initialise its in-memory cache globals.
    """

    feature_cache_path = (
        tmp_path / "infra_cache.json"
    )

    observation_cache_path = (
        tmp_path / "infra_observation_cache.json"
    )

    # ------------------------------------------------------------------
    # Redirect REAL cache paths
    # ------------------------------------------------------------------

    monkeypatch.setattr(
        cache,
        "FEATURE_CACHE_PATH",
        str(feature_cache_path)
    )

    monkeypatch.setattr(
        cache,
        "OBSERVATION_CACHE_PATH",
        str(observation_cache_path)
    )

    # ------------------------------------------------------------------
    # Reload the REAL cache globals from the temporary files.
    #
    # Since the files do not exist yet, both become empty dictionaries.
    # ------------------------------------------------------------------

    cache.FEATURE_CACHE = (
        cache.load_feature_cache()
    )

    cache.OBSERVATION_CACHE = (
        cache.load_observation_cache()
    )

    # ------------------------------------------------------------------
    # Reset cache session state if present.
    # ------------------------------------------------------------------

    if hasattr(cache, "CACHE_SESSION_ACTIVE"):
        cache.CACHE_SESSION_ACTIVE = False

    # ------------------------------------------------------------------
    # Reset statistics in infra_features.py.
    # ------------------------------------------------------------------

    infra.reset_cache_statistics()


# ============================================================================
# DETERMINISTIC COLLECTOR DOUBLES
# ============================================================================

def fake_network(domain):

    return {
        "features": {
            "has_ip": 1,
            "has_asn": 1,
            "asn_reputation": 1,
            "is_foreign_hosting": 0,
        },

        "metadata": {
            "ip_address": "192.0.2.10",
            "asn": "AS15169 Google LLC",
            "hosting_country": "US",
        }
    }


def fake_whois(domain):

    return {
        "features": {
            "domain_age_days": 3650,
            "has_domain_age": 1,
            "is_new_domain": 0,
            "domain_age_bucket": 4,
        },

        "metadata": {
            "registrar": "Test Registrar",
        }
    }


def fake_ssl(domain):

    return {
        "features": {
            "ssl_present": 1,
            "ssl_valid": 1,
        },

        "metadata": {
            "issuer": "Let's Encrypt",
            "subject": "example.com",
        }
    }


def fake_ct(domain):

    return {
        "features": {
            "ct_has_history": 1,
            "ct_record_count": 3,
        },

        "metadata": {
            "issuer_frequency": {
                "Let's Encrypt": 2,
                "Google Trust": 1,
            },

            "san_frequency": {
                "example.com": 3,
                "www.example.com": 2,
            },

            "first_seen": "2024-01-01T00:00:00+00:00",
        }
    }


# ============================================================================
# INSTALL COLLECTOR DOUBLES
# ============================================================================

def install_test_doubles(monkeypatch):

    monkeypatch.setattr(
        infra,
        "collect_network",
        fake_network
    )

    monkeypatch.setattr(
        infra,
        "collect_whois",
        fake_whois
    )

    monkeypatch.setattr(
        infra,
        "collect_ssl",
        fake_ssl
    )

    monkeypatch.setattr(
        infra,
        "collect_ct",
        fake_ct
    )


# ============================================================================
# TEST 1 — COLD START
# ============================================================================

def test_01_cold_start_statistics(
    tmp_path,
    monkeypatch
):

    initialize_test_caches(
        tmp_path,
        monkeypatch
    )

    install_test_doubles(
        monkeypatch
    )

    # -------------------------------------------------------------
    # Cold start:
    #
    # Feature Cache does not exist.
    # Observation Cache does not exist.
    # -------------------------------------------------------------

    result = infra.collect_infrastructure_features(
        DOMAIN,
        infra.FEATURE_SECTION_DATA
    )

    assert result["features"]

    stats = infra.get_cache_statistics()

    print(
        "\n\nCOLD START STATISTICS"
    )

    print(stats)

    # -------------------------------------------------------------
    # Feature Cache
    # -------------------------------------------------------------

    assert stats["feature_cache_hits"] == 0

    assert stats["feature_cache_misses"] == 1

    # -------------------------------------------------------------
    # Observation Cache
    #
    # Four observation types:
    #     network
    #     whois
    #     ssl
    #     ct
    # -------------------------------------------------------------

    assert stats["observation_cache_hits"] == 0

    assert stats["observation_cache_misses"] == 4

    # -------------------------------------------------------------
    # All four collectors must therefore execute.
    # -------------------------------------------------------------

    assert stats["collector_calls"] == 4


# ============================================================================
# TEST 2 — FEATURE CACHE HIT
# ============================================================================

def test_02_feature_cache_hit(
    tmp_path,
    monkeypatch
):

    initialize_test_caches(
        tmp_path,
        monkeypatch
    )

    install_test_doubles(
        monkeypatch
    )

    # -------------------------------------------------------------
    # First execution.
    #
    # This populates the Observation Cache.
    # -------------------------------------------------------------

    result1 = infra.collect_infrastructure_features(
        DOMAIN,
        infra.FEATURE_SECTION_DATA
    )

    assert result1["features"]

    # -------------------------------------------------------------
    # Feature Cache persistence is owned by infra_cache.py.
    # -------------------------------------------------------------

    cache.update_feature_section(
        DOMAIN,
        infra.FEATURE_SECTION_DATA,
        result1["features"]
    )

    # -------------------------------------------------------------
    # Reset statistics so only the second execution is measured.
    # -------------------------------------------------------------

    infra.reset_cache_statistics()

    # -------------------------------------------------------------
    # Second execution.
    # -------------------------------------------------------------

    result2 = infra.collect_infrastructure_features(
        DOMAIN,
        infra.FEATURE_SECTION_DATA
    )

    assert result2["features"]

    stats = infra.get_cache_statistics()

    print(
        "\n\nFEATURE CACHE HIT STATISTICS"
    )

    print(stats)

    # -------------------------------------------------------------
    # Feature Cache should be reused.
    # -------------------------------------------------------------

    assert stats["feature_cache_hits"] == 1

    assert stats["feature_cache_misses"] == 0

    # -------------------------------------------------------------
    # Because the Feature Cache is valid, no Observation Cache
    # lookup should be required by the feature retrieval path.
    # -------------------------------------------------------------

    assert stats["observation_cache_hits"] == 0

    assert stats["observation_cache_misses"] == 0

    # -------------------------------------------------------------
    # Therefore no collector should execute.
    # -------------------------------------------------------------

    assert stats["collector_calls"] == 0


# ============================================================================
# TEST 3 — ONE STALE OBSERVATION
# ============================================================================

def test_03_one_stale_observation(
    tmp_path,
    monkeypatch
):

    initialize_test_caches(
        tmp_path,
        monkeypatch
    )

    install_test_doubles(
        monkeypatch
    )

    # -------------------------------------------------------------
    # First execution.
    #
    # This creates all four observations.
    # -------------------------------------------------------------

    result = infra.collect_infrastructure_features(
        DOMAIN,
        infra.FEATURE_SECTION_DATA
    )

    assert result["features"]

    # -------------------------------------------------------------
    # Persist Feature Cache.
    # -------------------------------------------------------------

    cache.update_feature_section(
        DOMAIN,
        infra.FEATURE_SECTION_DATA,
        result["features"]
    )

    # -------------------------------------------------------------
    # Make ONLY WHOIS invalid/stale.
    #
    # The other three observations remain valid.
    # -------------------------------------------------------------

    original_validity = (
        infra.has_valid_cached_observation
    )

    def selective_validity(
        domain,
        collector
    ):

        if collector == "whois":
            return False

        return original_validity(
            domain,
            collector
        )

    monkeypatch.setattr(
        infra,
        "has_valid_cached_observation",
        selective_validity
    )

    # -------------------------------------------------------------
    # Reset statistics.
    # -------------------------------------------------------------

    infra.reset_cache_statistics()

    # -------------------------------------------------------------
    # Execute again.
    # -------------------------------------------------------------

    result2 = infra.collect_infrastructure_features(
        DOMAIN,
        infra.FEATURE_SECTION_DATA
    )

    assert result2["features"]

    stats = infra.get_cache_statistics()

    print(
        "\n\nONE STALE OBSERVATION STATISTICS"
    )

    print(stats)

    # -------------------------------------------------------------
    # Feature Cache must be considered invalid.
    # -------------------------------------------------------------

    assert stats["feature_cache_hits"] == 0

    assert stats["feature_cache_misses"] == 1

    # -------------------------------------------------------------
    # Three observations remain reusable.
    # -------------------------------------------------------------

    assert stats["observation_cache_hits"] == 3

    # -------------------------------------------------------------
    # Only WHOIS is stale.
    # -------------------------------------------------------------

    assert stats["observation_cache_misses"] == 1

    # -------------------------------------------------------------
    # Therefore exactly one collector should execute.
    # -------------------------------------------------------------

    assert stats["collector_calls"] == 1


# ============================================================================
# TEST 4 — STATISTICS RESET
# ============================================================================

def test_04_statistics_reset(
    tmp_path,
    monkeypatch
):

    initialize_test_caches(
        tmp_path,
        monkeypatch
    )

    install_test_doubles(
        monkeypatch
    )

    # -------------------------------------------------------------
    # Generate some statistics.
    # -------------------------------------------------------------

    infra.collect_infrastructure_features(
        DOMAIN,
        infra.FEATURE_SECTION_DATA
    )

    stats_before = (
        infra.get_cache_statistics()
    )

    print(
        "\n\nSTATISTICS BEFORE RESET"
    )

    print(stats_before)

    # There must have been some cache activity.
    assert (
        stats_before["feature_cache_misses"] > 0
        or
        stats_before["observation_cache_misses"] > 0
        or
        stats_before["collector_calls"] > 0
    )

    # -------------------------------------------------------------
    # Reset.
    # -------------------------------------------------------------

    infra.reset_cache_statistics()

    stats_after = (
        infra.get_cache_statistics()
    )

    print(
        "\n\nSTATISTICS AFTER RESET"
    )

    print(stats_after)

    # -------------------------------------------------------------
    # Every counter must be zero.
    # -------------------------------------------------------------

    assert stats_after == {
        "feature_cache_hits": 0,
        "feature_cache_misses": 0,
        "observation_cache_hits": 0,
        "observation_cache_misses": 0,
        "collector_calls": 0,
    }