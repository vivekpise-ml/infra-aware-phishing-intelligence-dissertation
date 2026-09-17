"""
Infrastructure Package Integration Test

Validates the frozen Infrastructure Package architecture.

Tested here
-----------
1. Cold start
2. Feature Cache hit
3. Feature Cache present but observation stale
4. Feature Cache missing but Observation Cache valid
5. Only stale collector is invoked
6. Overlapping requests reuse cached observations
7. CT normalized observation structure
8. Observation Cache stores normalized observations
9. Feature Cache sections remain independent
10. Feature-cache reuse requires valid observations

NOT tested here
---------------
Prediction Pipeline integration
Campaign Package integration
Streamlit integration

Those are tested separately after the Infrastructure Package passes.
"""

from copy import deepcopy
from datetime import datetime, timezone

import src.infrastructure.infra_features as infra


# ============================================================================
# TEST DATA
# ============================================================================

DOMAIN = "example.com"


COLLECTOR_NETWORK = infra.COLLECTOR_NETWORK
COLLECTOR_WHOIS = infra.COLLECTOR_WHOIS
COLLECTOR_SSL = infra.COLLECTOR_SSL
COLLECTOR_CT = infra.COLLECTOR_CT

COLLECTORS = (
    COLLECTOR_NETWORK,
    COLLECTOR_WHOIS,
    COLLECTOR_SSL,
    COLLECTOR_CT,
)


# ============================================================================
# FAKE CACHE STATE
# ============================================================================

FEATURE_CACHE = {}

OBSERVATION_CACHE = {}

COLLECTOR_CALLS = {
    COLLECTOR_NETWORK: 0,
    COLLECTOR_WHOIS: 0,
    COLLECTOR_SSL: 0,
    COLLECTOR_CT: 0,
}


# ============================================================================
# FAKE COLLECTOR RESULTS
# ============================================================================

FAKE_RESULTS = {

    COLLECTOR_NETWORK: {
        "features": {
            "has_ip": 1,
            "has_asn": 1,
            "asn_reputation": 1,
            "is_foreign_hosting": 0,
        },
        "metadata": {
            "ip_address": "1.2.3.4",
            "asn": "AS15169 Google LLC",
            "hosting_country": "US",
        },
    },

    COLLECTOR_WHOIS: {
        "features": {
            "domain_age_days": 1000,
            "has_domain_age": 1,
            "domain_age_bucket": 4,
        },
        "metadata": {
            "creation_date": "2023-01-01T00:00:00+00:00",
            "registrar": "Test Registrar",
        },
    },

    COLLECTOR_SSL: {
        "features": {
            "ssl_available": 1,
            "ssl_validity_bucket": 4,
            "ssl_days_remaining": 300,
        },
        "metadata": {
            "issuer": "Test CA",
            "subject": "example.com",
        },
    },

    COLLECTOR_CT: {
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
        },
    },
}


# ============================================================================
# TEST HELPERS
# ============================================================================

def reset_state():
    """
    Reset all fake cache and collector state.
    """

    FEATURE_CACHE.clear()
    OBSERVATION_CACHE.clear()

    for collector in COLLECTOR_CALLS:
        COLLECTOR_CALLS[collector] = 0


def fake_get_feature_entry(domain):
    """
    Fake Feature Cache lookup.
    """

    return deepcopy(
        FEATURE_CACHE.get(domain)
    )


def fake_get_observation(domain, collector):
    """
    Fake Observation Cache lookup.
    """

    entry = OBSERVATION_CACHE.get(domain)

    if entry is None:
        return None

    observation = entry.get(collector)

    if observation is None:
        return None

    return deepcopy(observation["data"])


def fake_has_valid_cached_observation(
    domain,
    collector
):
    """
    Fake Observation Cache validity check.

    An observation is valid when:

    - it exists
    - its 'valid' flag is True
    """

    entry = OBSERVATION_CACHE.get(domain)

    if entry is None:
        return False

    observation = entry.get(collector)

    if observation is None:
        return False

    return observation.get(
        "valid",
        False
    )


def fake_update_observation(
    domain,
    collector,
    observation,
    save=True
):
    """
    Fake Observation Cache update.
    """

    domain_entry = OBSERVATION_CACHE.setdefault(
        domain,
        {}
    )

    domain_entry[collector] = {
        "version": "test-v1",
        "cached_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "valid": True,
        "data": deepcopy(observation),
    }


def make_feature_cache(
    domain,
    section,
    value
):
    """
    Create one Feature Cache section.
    """

    entry = FEATURE_CACHE.setdefault(
        domain,
        {}
    )

    entry[section] = deepcopy(value)


def make_observation(
    domain,
    collector,
    valid=True
):
    """
    Insert one normalized observation
    into the fake Observation Cache.
    """

    domain_entry = OBSERVATION_CACHE.setdefault(
        domain,
        {}
    )

    domain_entry[collector] = {
        "version": "test-v1",
        "cached_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "valid": valid,
        "data": deepcopy(
            FAKE_RESULTS[collector]
        ),
    }


def fake_collect(
    collector,
    domain
):
    """
    Fake network collector.

    No external network is used.
    """

    COLLECTOR_CALLS[collector] += 1

    return deepcopy(
        FAKE_RESULTS[collector]
    )


# ============================================================================
# PATCH INFRA_FEATURES BOUNDARIES
# ============================================================================

def install_test_doubles(monkeypatch):

    monkeypatch.setattr(
        infra,
        "get_feature_entry",
        fake_get_feature_entry
    )

    monkeypatch.setattr(
        infra,
        "get_observation",
        fake_get_observation
    )

    monkeypatch.setattr(
        infra,
        "has_valid_cached_observation",
        fake_has_valid_cached_observation
    )

    monkeypatch.setattr(
        infra,
        "update_observation",
        fake_update_observation
    )

    monkeypatch.setattr(
        infra,
        "collect_network",
        lambda domain:
            fake_collect(
                COLLECTOR_NETWORK,
                domain
            )
    )

    monkeypatch.setattr(
        infra,
        "collect_whois",
        lambda domain:
            fake_collect(
                COLLECTOR_WHOIS,
                domain
            )
    )

    monkeypatch.setattr(
        infra,
        "collect_ssl",
        lambda domain:
            fake_collect(
                COLLECTOR_SSL,
                domain
            )
    )

    monkeypatch.setattr(
        infra,
        "collect_ct",
        lambda domain:
            fake_collect(
                COLLECTOR_CT,
                domain
            )
    )


# ============================================================================
# TEST 1
# ============================================================================

def test_01_cold_start(monkeypatch):

    reset_state()

    install_test_doubles(
        monkeypatch
    )

    result = infra.collect_infrastructure_features(
        DOMAIN,
        infra.FEATURE_SECTION_DATA
    )

    assert result["features"]

    assert result["metadata"]

    assert "network" in result["metadata"]

    assert "whois" in result["metadata"]

    assert "ssl" in result["metadata"]

    assert "ct" in result["metadata"]

    for collector in COLLECTORS:
        assert (
            COLLECTOR_CALLS[collector]
            == 1
        )

    for collector in COLLECTORS:

        assert (
            collector
            in OBSERVATION_CACHE[DOMAIN]
        )

    print(
        "PASS 1: Cold start"
    )


# ============================================================================
# TEST 2
# ============================================================================

def test_02_feature_cache_hit(monkeypatch):

    reset_state()

    install_test_doubles(
        monkeypatch
    )

    # Valid observations must exist
    # because Feature Cache reuse is
    # intentionally dependent on them.

    for collector in COLLECTORS:
        make_observation(
            DOMAIN,
            collector,
            valid=True
        )

    cached_features = {
        "cached_marker": 123
    }

    make_feature_cache(
        DOMAIN,
        infra.FEATURE_SECTION_DATA,
        cached_features
    )

    result = infra.collect_infrastructure_features(
        DOMAIN,
        infra.FEATURE_SECTION_DATA
    )

    assert result["features"] == cached_features

    assert result["metadata"] == {}

    for collector in COLLECTORS:

        assert (
            COLLECTOR_CALLS[collector]
            == 0
        )

    print(
        "PASS 2: Feature Cache hit"
    )


# ============================================================================
# TEST 3
# ============================================================================

def test_03_feature_cache_present_but_observation_stale(
    monkeypatch
):

    reset_state()

    install_test_doubles(
        monkeypatch
    )

    for collector in COLLECTORS:

        make_observation(
            DOMAIN,
            collector,
            valid=True
        )

    make_feature_cache(
        DOMAIN,
        infra.FEATURE_SECTION_DATA,
        {
            "old_feature": 1
        }
    )

    # Make only SSL stale.
    OBSERVATION_CACHE[
        DOMAIN
    ][COLLECTOR_SSL]["valid"] = False

    result = infra.collect_infrastructure_features(
        DOMAIN,
        infra.FEATURE_SECTION_DATA
    )

    assert result["features"]

    assert (
        COLLECTOR_CALLS[
            COLLECTOR_SSL
        ]
        == 1
    )

    assert (
        COLLECTOR_CALLS[
            COLLECTOR_NETWORK
        ]
        == 0
    )

    assert (
        COLLECTOR_CALLS[
            COLLECTOR_WHOIS
        ]
        == 0
    )

    assert (
        COLLECTOR_CALLS[
            COLLECTOR_CT
        ]
        == 0
    )

    print(
        "PASS 3: Feature Cache invalidated by stale observation"
    )


# ============================================================================
# TEST 4
# ============================================================================

def test_04_feature_cache_missing_observation_cache_hit(
    monkeypatch
):

    reset_state()

    install_test_doubles(
        monkeypatch
    )

    for collector in COLLECTORS:

        make_observation(
            DOMAIN,
            collector,
            valid=True
        )

    result = infra.collect_infrastructure_features(
        DOMAIN,
        infra.FEATURE_SECTION_DATA
    )

    assert result["features"]

    for collector in COLLECTORS:

        assert (
            COLLECTOR_CALLS[collector]
            == 0
        )

    print(
        "PASS 4: Observation Cache reused when Feature Cache missing"
    )


# ============================================================================
# TEST 5
# ============================================================================

def test_05_only_stale_collector_invoked(
    monkeypatch
):

    reset_state()

    install_test_doubles(
        monkeypatch
    )

    for collector in COLLECTORS:

        make_observation(
            DOMAIN,
            collector,
            valid=True
        )

    # Make only WHOIS stale.
    OBSERVATION_CACHE[
        DOMAIN
    ][COLLECTOR_WHOIS]["valid"] = False

    result = infra.collect_infrastructure_features(
        DOMAIN,
        infra.FEATURE_SECTION_DATA
    )

    assert result["features"]

    assert (
        COLLECTOR_CALLS[
            COLLECTOR_WHOIS
        ]
        == 1
    )

    assert (
        COLLECTOR_CALLS[
            COLLECTOR_NETWORK
        ]
        == 0
    )

    assert (
        COLLECTOR_CALLS[
            COLLECTOR_SSL
        ]
        == 0
    )

    assert (
        COLLECTOR_CALLS[
            COLLECTOR_CT
        ]
        == 0
    )

    print(
        "PASS 5: Only stale collector invoked"
    )


# ============================================================================
# TEST 6
# ============================================================================

def test_06_overlapping_requests_reuse_observations(
    monkeypatch
):

    reset_state()

    install_test_doubles(
        monkeypatch
    )

    # First request.
    first = infra.collect_infrastructure_features(
        DOMAIN,
        infra.FEATURE_SECTION_DATA
    )

    first_calls = dict(
        COLLECTOR_CALLS
    )

    # Second request.
    second = infra.collect_infrastructure_features(
        DOMAIN,
        infra.FEATURE_SECTION_DATA
    )

    assert first["features"]

    assert second["features"]

    for collector in COLLECTORS:

        assert (
            COLLECTOR_CALLS[collector]
            == first_calls[collector]
        )

    print(
        "PASS 6: Overlapping requests reuse observations"
    )


# ============================================================================
# TEST 7
# ============================================================================

def test_07_ct_normalized_storage(
    monkeypatch
):

    reset_state()

    install_test_doubles(
        monkeypatch
    )

    result = infra.collect_infrastructure_features(
        DOMAIN,
        infra.FEATURE_SECTION_CAMPAIGN_METADATA
    )

    assert result["metadata"]

    ct_observation = OBSERVATION_CACHE[
        DOMAIN
    ][COLLECTOR_CT]["data"]

    ct_metadata = ct_observation[
        "metadata"
    ]

    assert (
        ct_metadata[
            "issuer_frequency"
        ][
            "Let's Encrypt"
        ]
        == 2
    )

    assert (
        ct_metadata[
            "issuer_frequency"
        ][
            "Google Trust"
        ]
        == 1
    )

    assert (
        ct_metadata[
            "san_frequency"
        ][
            "example.com"
        ]
        == 3
    )

    # Raw CT records must not be stored.
    assert "records" not in ct_observation

    print(
        "PASS 7: CT normalized storage"
    )


# ============================================================================
# TEST 8
# ============================================================================

def test_08_observation_cache_contains_normalized_entries(
    monkeypatch
):

    reset_state()

    install_test_doubles(
        monkeypatch
    )

    infra.collect_infrastructure_features(
        DOMAIN,
        infra.FEATURE_SECTION_DATA
    )

    for collector in COLLECTORS:

        entry = OBSERVATION_CACHE[
            DOMAIN
        ][collector]

        assert (
            "version"
            in entry
        )

        assert (
            "cached_at"
            in entry
        )

        assert (
            "data"
            in entry
        )

        assert isinstance(
            entry["data"],
            dict
        )

        assert "features" in entry["data"]

        assert "metadata" in entry["data"]

    print(
        "PASS 8: Observation Cache normalized structure"
    )


# ============================================================================
# TEST 9
# ============================================================================

def test_09_feature_cache_sections_are_independent(
    monkeypatch
):

    reset_state()

    install_test_doubles(
        monkeypatch
    )

    for collector in COLLECTORS:

        make_observation(
            DOMAIN,
            collector,
            valid=True
        )

    prediction_features = {
        "prediction_marker": 111
    }

    campaign_metadata = {
        "campaign_marker": 222
    }

    make_feature_cache(
        DOMAIN,
        infra.FEATURE_SECTION_DATA,
        prediction_features
    )

    make_feature_cache(
        DOMAIN,
        infra.FEATURE_SECTION_CAMPAIGN_METADATA,
        campaign_metadata
    )

    prediction_result = (
        infra.collect_infrastructure_features(
            DOMAIN,
            infra.FEATURE_SECTION_DATA
        )
    )

    campaign_result = (
        infra.collect_infrastructure_features(
            DOMAIN,
            infra.FEATURE_SECTION_CAMPAIGN_METADATA
        )
    )

    assert (
        prediction_result["features"]
        == prediction_features
    )

    assert (
        prediction_result["metadata"]
        == {}
    )

    assert (
        campaign_result["features"]
        == {}
    )

    assert (
        campaign_result["metadata"]
        == campaign_metadata
    )

    assert (
        FEATURE_CACHE[DOMAIN][
            infra.FEATURE_SECTION_DATA
        ]
        == prediction_features
    )

    assert (
        FEATURE_CACHE[DOMAIN][
            infra.FEATURE_SECTION_CAMPAIGN_METADATA
        ]
        == campaign_metadata
    )

    print(
        "PASS 9: Feature Cache sections remain independent"
    )


# ============================================================================
# TEST 10
# ============================================================================

def test_10_feature_cache_requires_all_valid_observations(
    monkeypatch
):

    reset_state()

    install_test_doubles(
        monkeypatch
    )

    cached_features = {
        "cached_marker": 999
    }

    make_feature_cache(
        DOMAIN,
        infra.FEATURE_SECTION_DATA,
        cached_features
    )

    # Deliberately create only three valid
    # observations. CT is missing.

    for collector in (
        COLLECTOR_NETWORK,
        COLLECTOR_WHOIS,
        COLLECTOR_SSL,
    ):

        make_observation(
            DOMAIN,
            collector,
            valid=True
        )

    result = infra.collect_infrastructure_features(
        DOMAIN,
        infra.FEATURE_SECTION_DATA
    )

    # Feature Cache must NOT be reused
    # because CT is missing.

    assert (
        result["features"]
        != cached_features
    )

    assert (
        COLLECTOR_CT
        in OBSERVATION_CACHE[DOMAIN]
    )

    assert (
        COLLECTOR_CT
        == COLLECTOR_CT
    )

    print(
        "PASS 10: Feature Cache requires valid underlying observations"
    )


# ============================================================================
# TEST RUNNER
# ============================================================================

if __name__ == "__main__":

    import pytest

    raise SystemExit(
        pytest.main(
            [
                __file__,
                "-v",
                "-s",
            ]
        )
    )