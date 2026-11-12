"""
ablation_features.py

Feature-selection utilities for controlled ablation experiments.

Important:
-----------
This module does NOT define new phishing features.

It reuses the existing dissertation feature-extraction functions and
only determines which already-existing feature groups participate in
each ablation experiment.

Supported modes:

    full
    lexical
    infra
    lexical_infra

The primary scientific comparison is:

    lexical
        vs
    lexical_infra

The infra-only mode is a secondary diagnostic experiment that measures
the standalone predictive signal available from the infrastructure
feature group.

Architecture:
-------------
The infrastructure representation is obtained through the current
Infrastructure Package:

    collect_infrastructure_features()
            |
            +-- Feature Cache
            |
            +-- Observation Cache
            |
            +-- Network / WHOIS / SSL / CT

This module does not access the caches directly.
"""

# ---------------------------------------------------------------------------
# Existing project feature APIs
# ---------------------------------------------------------------------------

from src.features_with_infra import (
    extract_all_features,
    extract_url_features,
    extract_domain_in_features_with_infra,
)

from src.infrastructure.infra_features import (
    collect_infrastructure_features,
    FEATURE_SECTION_DATA,
)


# ---------------------------------------------------------------------------
# Feature-mode constants
# ---------------------------------------------------------------------------

FEATURE_MODE_FULL = "full"

FEATURE_MODE_LEXICAL = "lexical"

FEATURE_MODE_INFRA = "infra"

FEATURE_MODE_LEXICAL_INFRA = "lexical_infra"


SUPPORTED_FEATURE_MODES = {
    FEATURE_MODE_FULL,
    FEATURE_MODE_LEXICAL,
    FEATURE_MODE_INFRA,
    FEATURE_MODE_LEXICAL_INFRA,
}


# ---------------------------------------------------------------------------
# Individual feature-group extraction
# ---------------------------------------------------------------------------

def extract_ablation_full_features(
    url: str,
    html=None,
) -> dict:
    """
    Return the complete feature representation used by the existing
    dissertation feature-extraction pipeline.

    This is a thin wrapper around extract_all_features().

    No feature formulas are duplicated here.

    Current dissertation representation:

        URL features
        + HTML features
        + infrastructure features
    """

    features = extract_all_features(
        url,
        html,
    )

    if not isinstance(features, dict):

        raise TypeError(
            "extract_all_features() must return a dictionary."
        )

    return features


def extract_ablation_lexical_features(
    url: str,
) -> dict:
    """
    Return the existing lexical URL feature representation.

    This is a thin wrapper around extract_url_features().
    """

    features = extract_url_features(
        url
    )

    if not isinstance(features, dict):

        raise TypeError(
            "extract_url_features() must return a dictionary."
        )

    return features


def extract_ablation_infra_features(
    url: str,
) -> dict:
    """
    Return the current dissertation infrastructure feature
    representation.

    Infrastructure extraction is delegated entirely to the current
    Infrastructure Package.

    The Infrastructure Package is responsible for:

        Feature Cache
            |
        Observation Cache
            |
        Network / WHOIS / SSL / CT

    This module does not directly access infra_cache.json or the
    observation cache.
    """

    domain = (
        extract_domain_in_features_with_infra(
            url
        )
    )

    infra_result = collect_infrastructure_features(
        domain,
        FEATURE_SECTION_DATA
    )

    if not isinstance(infra_result, dict):

        raise TypeError(
            "collect_infrastructure_features() must return "
            "a dictionary."
        )

    features = infra_result.get(
        "features",
        {}
    )

    if not isinstance(features, dict):

        raise TypeError(
            "Infrastructure result 'features' must be a dictionary."
        )

    return features


def extract_ablation_lexical_infra_features(
    url: str,
) -> dict:
    """
    Return the combined lexical + infrastructure representation.

    Feature values are obtained from the current dissertation
    feature APIs.
    """

    lexical_features = (
        extract_ablation_lexical_features(
            url
        )
    )

    infrastructure_features = (
        extract_ablation_infra_features(
            url
        )
    )

    combined = {}

    combined.update(
        lexical_features
    )

    combined.update(
        infrastructure_features
    )

    return combined


# ---------------------------------------------------------------------------
# Feature-mode dispatcher
# ---------------------------------------------------------------------------

def extract_features_for_ablation(
    url: str,
    feature_mode: str,
    html=None,
) -> dict:
    """
    Extract features for a requested ablation mode.

    Parameters
    ----------
    url:
        URL to analyse.

    feature_mode:
        One of:

            full
            lexical
            infra
            lexical_infra

    html:
        Optional HTML content. Used only by the full representation.
    """

    if feature_mode not in SUPPORTED_FEATURE_MODES:

        raise ValueError(
            f"Unsupported ablation feature mode: "
            f"{feature_mode!r}. "
            f"Supported modes: "
            f"{sorted(SUPPORTED_FEATURE_MODES)}"
        )

    if feature_mode == FEATURE_MODE_FULL:

        return extract_ablation_full_features(
            url,
            html,
        )

    if feature_mode == FEATURE_MODE_LEXICAL:

        return extract_ablation_lexical_features(
            url
        )

    if feature_mode == FEATURE_MODE_INFRA:

        return extract_ablation_infra_features(
            url
        )

    if feature_mode == FEATURE_MODE_LEXICAL_INFRA:

        return extract_ablation_lexical_infra_features(
            url
        )

    # This should never be reached because of the validation above.
    raise RuntimeError(
        f"Unhandled feature mode: {feature_mode}"
    )


# ---------------------------------------------------------------------------
# Feature-name discovery
# ---------------------------------------------------------------------------

def get_ablation_feature_names(
    url: str,
    feature_mode: str,
) -> list:
    """
    Discover feature names for one ablation mode.

    Feature names are obtained dynamically from the existing dissertation
    feature-extraction APIs.

    They are not hard-coded in this module.
    """

    features = extract_features_for_ablation(
        url=url,
        feature_mode=feature_mode,
    )

    return list(
        features.keys()
    )


def get_ablation_feature_count(
    url: str,
    feature_mode: str,
) -> int:
    """
    Return the number of features for an ablation mode.
    """

    return len(
        get_ablation_feature_names(
            url,
            feature_mode,
        )
    )


# ---------------------------------------------------------------------------
# Feature alignment
# ---------------------------------------------------------------------------

def align_ablation_features(
    features: dict,
    feature_names: list,
) -> dict:
    """
    Align a feature dictionary to a predefined feature-name ordering.

    Missing features are treated as an error rather than silently
    invented or ignored.

    This is important for reproducible ablation experiments.
    """

    missing = [
        name
        for name in feature_names
        if name not in features
    ]

    if missing:

        raise ValueError(
            "Feature extraction result is missing "
            f"{len(missing)} expected features: "
            f"{missing}"
        )

    return {
        name: features[name]
        for name in feature_names
    }


def extract_and_align_ablation_features(
    url: str,
    feature_mode: str,
    feature_names: list,
    html=None,
) -> dict:
    """
    Extract features for an ablation mode and align them to the
    supplied feature-name ordering.

    This helper is retained for compatibility and for possible future
    experimental use.

    The main ablation runner uses the canonical feature CSV cache,
    so it does not repeatedly call this function for every mode.
    """

    features = extract_features_for_ablation(
        url=url,
        feature_mode=feature_mode,
        html=html,
    )

    return align_ablation_features(
        features,
        feature_names,
    )