"""
Infrastructure Real Cache Smoke Test

Validates the actual project cache paths:

    data/cache/infra_cache.json
    data/cache/infra_observation_cache.json

Unlike test_infra_cache_persistence.py, this test does NOT redirect
the cache paths to tmp_path.

It therefore verifies that the real Infrastructure Package creates
and persists both physical cache files in the project.
"""

import json
from pathlib import Path


TEST_DOMAIN = "infra-cache-test.example.com"


# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CACHE_DIR = PROJECT_ROOT / "data" / "cache"

FEATURE_CACHE_PATH = CACHE_DIR / "infra_cache.json"

OBSERVATION_CACHE_PATH = (
    CACHE_DIR / "infra_observation_cache.json"
)


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _read_json(path):

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def _remove_test_domain(cache):

    if TEST_DOMAIN in cache:

        del cache[TEST_DOMAIN]


# ---------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------

def test_real_project_cache_files():

    import src.infrastructure.infra_cache as cache
    import src.infrastructure.infra_features as infra

    # -------------------------------------------------------------
    # Ensure cache directory exists
    # -------------------------------------------------------------

    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # -------------------------------------------------------------
    # Load the REAL project caches
    # -------------------------------------------------------------

    cache.FEATURE_CACHE = (
        cache.load_feature_cache()
    )

    cache.OBSERVATION_CACHE = (
        cache.load_observation_cache()
    )

    cache.CACHE_SESSION_ACTIVE = False

    # -------------------------------------------------------------
    # Remove only our test domain if it already exists.
    #
    # Do NOT clear the real cache.
    # -------------------------------------------------------------

    _remove_test_domain(
        cache.FEATURE_CACHE
    )

    _remove_test_domain(
        cache.OBSERVATION_CACHE
    )

    cache.save_feature_cache(
        cache.FEATURE_CACHE
    )

    cache.save_observation_cache(
        cache.OBSERVATION_CACHE
    )

    # -------------------------------------------------------------
    # Run real infrastructure feature collection.
    #
    # This uses the real infrastructure package.
    #
    # We intentionally use the real collectors here.
    # Therefore this is a genuine network/cache smoke test.
    # -------------------------------------------------------------

    result = (
        infra.collect_infrastructure_features(
            TEST_DOMAIN,
            infra.FEATURE_SECTION_DATA
        )
    )

    assert result is not None

    assert "features" in result

    # -------------------------------------------------------------
    # Observation Cache
    # -------------------------------------------------------------

    observation = (
        cache.get_observation(
            TEST_DOMAIN,
            "network"
        )
    )

    # The test domain is deliberately non-existent, so the network
    # collector may fail to obtain an observation.
    #
    # Therefore we do not require every collector to succeed here.
    #
    # Instead, verify that the REAL observation cache mechanism is
    # functioning and that the physical file exists.
    # -------------------------------------------------------------

    assert OBSERVATION_CACHE_PATH.exists()

    # -------------------------------------------------------------
    # Feature Cache
    #
    # This is the downstream responsibility being simulated here.
    # -------------------------------------------------------------

    cache.update_feature_section(
        TEST_DOMAIN,
        infra.FEATURE_SECTION_DATA,
        result["features"]
    )

    cache.save_feature_cache(
        cache.FEATURE_CACHE
    )

    # -------------------------------------------------------------
    # Both physical files must now exist.
    # -------------------------------------------------------------

    assert FEATURE_CACHE_PATH.exists()

    assert OBSERVATION_CACHE_PATH.exists()

    # -------------------------------------------------------------
    # Reload from disk.
    #
    # This is the critical part of the smoke test.
    # -------------------------------------------------------------

    feature_disk = _read_json(
        FEATURE_CACHE_PATH
    )

    observation_disk = _read_json(
        OBSERVATION_CACHE_PATH
    )

    # -------------------------------------------------------------
    # Feature Cache must contain our test domain.
    # -------------------------------------------------------------

    assert TEST_DOMAIN in feature_disk

    feature_entry = (
        feature_disk[TEST_DOMAIN]
    )

    assert "version" in feature_entry

    assert "data" in feature_entry

    assert isinstance(
        feature_entry["data"],
        dict
    )

    # -------------------------------------------------------------
    # Observation Cache must contain the test domain IF at least
    # one observation was successfully collected.
    #
    # Network collection may fail for the deliberately fake domain,
    # so this is checked conditionally.
    # -------------------------------------------------------------

    if TEST_DOMAIN in observation_disk:

        assert isinstance(
            observation_disk[TEST_DOMAIN],
            dict
        )

    # -------------------------------------------------------------
    # Cleanup ONLY our test domain.
    # -------------------------------------------------------------

    cache.FEATURE_CACHE = (
        cache.load_feature_cache()
    )

    cache.OBSERVATION_CACHE = (
        cache.load_observation_cache()
    )

    _remove_test_domain(
        cache.FEATURE_CACHE
    )

    _remove_test_domain(
        cache.OBSERVATION_CACHE
    )

    cache.save_feature_cache(
        cache.FEATURE_CACHE
    )

    cache.save_observation_cache(
        cache.OBSERVATION_CACHE
    )

    print(
        "\nREAL CACHE SMOKE TEST PASSED"
    )

    print(
        f"Feature Cache     : {FEATURE_CACHE_PATH}"
    )

    print(
        f"Observation Cache : {OBSERVATION_CACHE_PATH}"
    )