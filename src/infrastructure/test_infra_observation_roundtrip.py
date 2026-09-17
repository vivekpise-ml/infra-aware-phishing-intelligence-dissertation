"""
Regression test for Observation Cache persistence round-trip.

Purpose
-------
Verify that an observation written to the persistent Observation Cache
can be loaded in a new cache session and returned in the normalized
structure expected by infra_features.py.

This specifically protects against the bug where get_observation()
returned the persistence wrapper:

    {
        "version": ...,
        "cached_at": ...,
        "data": {
            "features": ...,
            "metadata": ...
        }
    }

instead of:

    {
        "features": ...,
        "metadata": ...
    }
"""

import json

from src.infrastructure import infra_cache as cache


DOMAIN = "roundtrip.example.com"

TEST_OBSERVATION = {
    "features": {
        "has_ip": 1,
        "has_asn": 1,
        "asn_reputation": 1,
        "domain_age_days": 3650,
        "has_domain_age": 1,
        "is_new_domain": 0,
        "domain_age_bucket": 4,
        "ssl_present": 1,
        "ssl_valid": 1,
        "ct_has_history": 1,
        "ct_record_count": 3,
    },
    "metadata": {
        "ip": "192.0.2.10",
        "ip_subnet24": "192.0.2.0/24",
        "hosting_provider": "TEST_PROVIDER",
        "nameservers": [
            "ns1.example.com",
            "ns2.example.com",
        ],
        "nameserver_count": 2,
    },
}


def test_observation_cache_roundtrip(monkeypatch, tmp_path):
    """
    Store an observation, persist it, start a new cache session,
    and verify that get_observation() returns the normalized
    observation rather than the persistence wrapper.
    """

    feature_cache_path = tmp_path / "infra_cache.json"
    observation_cache_path = (
        tmp_path / "infra_observation_cache.json"
    )

    # ---------------------------------------------------------
    # Use isolated temporary cache files.
    # ---------------------------------------------------------
    monkeypatch.setattr(
        cache,
        "FEATURE_CACHE_PATH",
        str(feature_cache_path),
    )

    monkeypatch.setattr(
        cache,
        "OBSERVATION_CACHE_PATH",
        str(observation_cache_path),
    )

    # ---------------------------------------------------------
    # Start a fresh cache session.
    # ---------------------------------------------------------
    cache.begin_cache_session()

    try:

        # -----------------------------------------------------
        # Store observation in RAM and persist at session end.
        # -----------------------------------------------------
        cache.update_observation(
            DOMAIN,
            "network",
            TEST_OBSERVATION,
            save=False,
        )

        # Verify that the in-memory representation contains
        # the expected normalized data.
        stored = cache.get_observation(
            DOMAIN,
            "network",
        )

        assert stored is not None
        assert stored["features"] == TEST_OBSERVATION["features"]
        assert stored["metadata"] == TEST_OBSERVATION["metadata"]

    finally:

        cache.end_cache_session()

    # ---------------------------------------------------------
    # Confirm the persistence wrapper exists on disk.
    # ---------------------------------------------------------
    with open(
        observation_cache_path,
        "r",
        encoding="utf-8",
    ) as f:
        persisted = json.load(f)

    persisted_entry = persisted[DOMAIN]["network"]

    assert "version" in persisted_entry
    assert "cached_at" in persisted_entry
    assert "data" in persisted_entry

    assert (
        persisted_entry["data"]["features"]
        ==
        TEST_OBSERVATION["features"]
    )

    assert (
        persisted_entry["data"]["metadata"]
        ==
        TEST_OBSERVATION["metadata"]
    )

    # ---------------------------------------------------------
    # IMPORTANT:
    # Start a completely new cache session.
    #
    # This is the regression scenario that previously failed.
    # ---------------------------------------------------------
    cache.begin_cache_session()

    try:

        reloaded = cache.get_observation(
            DOMAIN,
            "network",
        )

        assert reloaded is not None

        # -----------------------------------------------------
        # get_observation() must return:
        #
        # {
        #     "features": {...},
        #     "metadata": {...}
        # }
        #
        # NOT:
        #
        # {
        #     "version": ...,
        #     "cached_at": ...,
        #     "data": {...}
        # }
        # -----------------------------------------------------

        assert "features" in reloaded
        assert "metadata" in reloaded

        assert reloaded["features"] == TEST_OBSERVATION["features"]
        assert reloaded["metadata"] == TEST_OBSERVATION["metadata"]

        # Explicitly ensure that the persistence wrapper
        # is not leaked to the caller.
        assert "version" not in reloaded
        assert "cached_at" not in reloaded
        assert "data" not in reloaded

    finally:

        cache.end_cache_session()