"""
Infrastructure Cache Persistence Integration Test

Validates the REAL two-cache architecture:

    infra_observation_cache.json
            +
    infra_cache.json

External collectors are mocked so that no real network
traffic is generated.

The REAL infra_cache.py and infra_features.py are exercised.
"""

import json


DOMAIN = "example.com"


def _read_json(path):

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_real_two_cache_persistence(tmp_path, monkeypatch):

    # -------------------------------------------------------------
    # Import REAL implementations
    # -------------------------------------------------------------

    import src.infrastructure.infra_cache as cache
    import src.infrastructure.infra_features as infra

    # -------------------------------------------------------------
    # Redirect the two REAL cache files to temporary files.
    #
    # We must NOT modify the project's actual cache files.
    # -------------------------------------------------------------

    feature_cache_path = (
        tmp_path / "infra_cache.json"
    )

    observation_cache_path = (
        tmp_path / "infra_observation_cache.json"
    )

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

    # -------------------------------------------------------------
    # IMPORTANT:
    #
    # infra_cache.py has already loaded its globals when imported.
    # Therefore initialise the globals from our temporary files.
    # -------------------------------------------------------------

    cache.FEATURE_CACHE = (
        cache.load_feature_cache()
    )

    cache.OBSERVATION_CACHE = (
        cache.load_observation_cache()
    )

    cache.CACHE_SESSION_ACTIVE = False

    # -------------------------------------------------------------
    # Deterministic collector doubles.
    #
    # Only the external collectors are replaced.
    # The REAL cache implementation remains active.
    # -------------------------------------------------------------

    def fake_network(domain):

        return {

            "features": {

                "has_ip": 1,

                "has_asn": 1,

                "asn_reputation": 1,

                "is_foreign_hosting": 0

            },

            "metadata": {

                "ip_address":
                    "192.0.2.10",

                "asn":
                    "AS15169 Google LLC",

                "hosting_country":
                    "US"

            }

        }

    def fake_whois(domain):

        return {

            "features": {

                "domain_age_days":
                    3650,

                "has_domain_age":
                    1,

                "is_new_domain":
                    0,

                "domain_age_bucket":
                    4

            },

            "metadata": {

                "registrar":
                    "Test Registrar"

            }

        }

    def fake_ssl(domain):

        return {

            "features": {

                "ssl_present":
                    1,

                "ssl_valid":
                    1

            },

            "metadata": {

                "issuer":
                    "Let's Encrypt",

                "subject":
                    "example.com"

            }

        }

    def fake_ct(domain):

        return {

            "features": {

                "ct_has_history":
                    1,

                "ct_record_count":
                    3

            },

            "metadata": {

                "issuer_frequency": {

                    "Let's Encrypt": 2,

                    "Google Trust": 1

                },

                "san_frequency": {

                    "example.com": 3,

                    "www.example.com": 2

                },

                "first_seen":
                    "2024-01-01T00:00:00+00:00",

                "last_seen":
                    "2026-01-01T00:00:00+00:00"

            }

        }

    # -------------------------------------------------------------
    # Replace only collector calls in infra_features.py.
    # -------------------------------------------------------------

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

    # -------------------------------------------------------------
    # FIRST EXECUTION
    #
    # No cache entries exist.
    #
    # infra_features.py should:
    #
    #   collectors
    #       ↓
    #   Observation Cache
    #       ↓
    #   derive features
    #       ↓
    #   Feature Cache
    #
    # -------------------------------------------------------------

    result = infra.collect_infrastructure_features(
        DOMAIN,
        infra.FEATURE_SECTION_DATA
    )

    assert result["features"]

    cache.update_feature_section(
        DOMAIN,
        infra.FEATURE_SECTION_DATA,
        result["features"]
    )

    print(
        "\nDEBUG FEATURE_CACHE AFTER UPDATE:"
    )

    print(
        json.dumps(
            cache.FEATURE_CACHE,
            indent=2
        )
    )

    assert DOMAIN in cache.FEATURE_CACHE

    # -------------------------------------------------------------
    # Explicitly verify REAL Observation Cache.
    # -------------------------------------------------------------

    for collector in (
        "network",
        "whois",
        "ssl",
        "ct"
    ):

        observation = cache.get_observation(
            DOMAIN,
            collector
        )

        assert observation is not None

        # get_observation() returns the normalized
        # collector observation payload.
        assert "features" in observation
        assert "metadata" in observation

    # -------------------------------------------------------------
    # Persist the REAL caches.
    #
    # These are the actual frozen APIs.
    # -------------------------------------------------------------

    cache.save_observation_cache(
        cache.OBSERVATION_CACHE
    )

    cache.save_feature_cache(
        cache.FEATURE_CACHE
    )

    # -------------------------------------------------------------
    # BOTH physical files must now exist.
    # -------------------------------------------------------------

    assert observation_cache_path.exists()

    assert feature_cache_path.exists()

    # -------------------------------------------------------------
    # Read physical Observation Cache.
    # -------------------------------------------------------------

    observation_disk = _read_json(
        observation_cache_path
    )

    assert DOMAIN in observation_disk

    domain_observations = (
        observation_disk[DOMAIN]
    )

    # -------------------------------------------------------------
    # All four observations must be persisted.
    # -------------------------------------------------------------

    assert "network" in domain_observations

    assert "whois" in domain_observations

    assert "ssl" in domain_observations

    assert "ct" in domain_observations

    # -------------------------------------------------------------
    # Verify Observation Cache structure.
    # -------------------------------------------------------------

    ct_observation = (
        domain_observations["ct"]
    )

    assert "version" in ct_observation

    assert "cached_at" in ct_observation

    assert "data" in ct_observation

    # -------------------------------------------------------------
    # CT must remain normalized.
    #
    # Raw crt.sh records must NOT be persisted.
    # -------------------------------------------------------------

    serialized_observation = json.dumps(
        observation_disk
    )

    assert "issuer_frequency" in (
        serialized_observation
    )

    assert "san_frequency" in (
        serialized_observation
    )

    assert "Let's Encrypt" in (
        serialized_observation
    )

    assert "Google Trust" in (
        serialized_observation
    )

    assert '"records"' not in (
        serialized_observation
    )

    # -------------------------------------------------------------
    # Read physical Feature Cache.
    # -------------------------------------------------------------

    feature_disk = _read_json(
        feature_cache_path
    )

    assert DOMAIN in feature_disk

    feature_entry = (
        feature_disk[DOMAIN]
    )

    assert feature_entry["version"] == (
        cache.FEATURE_CACHE_VERSION
    )

    assert "data" in feature_entry

    assert "campaign_metadata" in feature_entry

    # -------------------------------------------------------------
    # Prediction Feature Cache must contain data.
    # -------------------------------------------------------------

    assert feature_entry["data"]

    # -------------------------------------------------------------
    # Campaign Metadata section must still exist.
    #
    # It must not have been destroyed by writing "data".
    # -------------------------------------------------------------

    assert isinstance(
        feature_entry["campaign_metadata"],
        dict
    )

    # -------------------------------------------------------------
    # Fresh-process simulation.
    #
    # Clear the in-memory caches.
    # -------------------------------------------------------------

    cache.FEATURE_CACHE = {}

    cache.OBSERVATION_CACHE = {}

    # -------------------------------------------------------------
    # Reload BOTH physical JSON files.
    # -------------------------------------------------------------

    reloaded_feature_cache = (
        cache.load_feature_cache()
    )

    reloaded_observation_cache = (
        cache.load_observation_cache()
    )

    # -------------------------------------------------------------
    # Verify Feature Cache survives reload.
    # -------------------------------------------------------------

    assert DOMAIN in (
        reloaded_feature_cache
    )

    reloaded_feature_entry = (
        reloaded_feature_cache[DOMAIN]
    )

    assert "data" in (
        reloaded_feature_entry
    )

    assert "campaign_metadata" in (
        reloaded_feature_entry
    )

    # -------------------------------------------------------------
    # Verify Observation Cache survives reload.
    # -------------------------------------------------------------

    assert DOMAIN in (
        reloaded_observation_cache
    )

    reloaded_observations = (
        reloaded_observation_cache[DOMAIN]
    )

    assert "network" in reloaded_observations

    assert "whois" in reloaded_observations

    assert "ssl" in reloaded_observations

    assert "ct" in reloaded_observations