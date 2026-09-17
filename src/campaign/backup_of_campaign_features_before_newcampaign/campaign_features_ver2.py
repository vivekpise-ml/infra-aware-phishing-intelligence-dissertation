"""
campaign_features.py
--------------------

Feature Engineering Module for Campaign Analysis

This module prepares the feature vectors used by the
Campaign Clustering pipeline.

Unlike the prediction pipeline, these features are
engineered for similarity rather than classification.

Responsibilities
----------------
1. Extract frozen prediction features.
2. Obtain campaign metadata.
3. Convert campaign metadata into numerical features.
4. Produce a feature vector suitable for DBSCAN.

IMPORTANT
---------
This module MUST NOT modify the prediction feature set
or interfere with the XGBoost pipeline.
"""

from __future__ import annotations

import hashlib

from typing import Dict, List

import pandas as pd

from src.features_with_infra import extract_all_features
from src.features_with_infra import extract_domain_in_features_with_infra

from src.campaign.campaign_metadata import (
    get_campaign_metadata,
)

# ============================================================
# Feature Groups
# ============================================================

#
# ------------------------------------------------------------------
# Group A
# Existing lexical similarity features
# ------------------------------------------------------------------
#

LEXICAL_FEATURES = [

    # URL size
    "url_length",
    "domain_length",
    "path_length",
    "query_length",

    # URL statistics
    "url_entropy",
    "domain_entropy",
    "path_entropy",

    # URL structure
    "subdomain_count",
    "path_depth",

    "param_count",

    "key_value_pairs",

    # Token statistics
    "num_tokens",

    "avg_token_len",

    "max_token_len",

    # Character ratios
    "digit_ratio",

    "letter_ratio",

    "special_ratio",

    "encoded_ratio",

    # Counts
    "dot_count",

    "dash_count",

    "underscore_count",

    "tld_length",

    # Suspicious structures
    "double_slash",

    "dot_in_path",

    "long_subdomain",
]


#
# ------------------------------------------------------------------
# Group B
# Existing infrastructure features
# ------------------------------------------------------------------
#

INFRASTRUCTURE_FEATURES = [

    "domain_age_days",

    "has_domain_age",

    "is_new_domain",

    "has_ip",

    "has_asn",

    "domain_age_bucket",

    "is_foreign_hosting",

    "infra_stability_score",

    "asn_reputation",

    "infra_trust_score_scaled",

    "trusted_infra_flag",

    "strong_trusted_infra",
]


#
# ------------------------------------------------------------------
# Group C
# Campaign metadata
#
# These are produced by campaign_metadata.py
#
# IMPORTANT:
#
# DBSCAN requires NUMERICAL features.
#
# Strings are therefore converted into stable hashes.
# ------------------------------------------------------------------
#

CAMPAIGN_METADATA_FEATURES = [

    "ssl_available",

    "ssl_validity_bucket",

    "ssl_days_remaining",

    "nameserver_count",

    #"ssl_issuer_hash",

    #"hosting_provider_hash",

    #"ip_subnet_hash",
]


#
# Final feature list
#

CAMPAIGN_FEATURES = (

    LEXICAL_FEATURES

    +

    INFRASTRUCTURE_FEATURES

    +

    CAMPAIGN_METADATA_FEATURES

)

# ============================================================
# Helper Functions
# ============================================================

def stable_hash(value: str, modulo: int = 100003) -> int:
    """
    Convert arbitrary text into a stable integer.

    Python's built-in hash() is intentionally randomised
    between interpreter sessions.

    SHA256 provides deterministic values.
    """

    if value is None:
        return 0

    value = str(value).strip()

    if value == "":
        return 0

    digest = hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()

    return int(digest[:12], 16) % modulo


def encode_campaign_metadata(
    metadata: Dict,
) -> Dict:
    """
    Convert campaign metadata into numerical features
    suitable for clustering.
    """

    return {

        "ssl_available":

            metadata.get(
                "ssl_available",
                0,
            ),

        "ssl_validity_bucket":

            metadata.get(
                "ssl_validity_bucket",
                0,
            ),

        "ssl_days_remaining":

            max(
                metadata.get(
                    "ssl_days_remaining",
                    0,
                ),
                0,
            ),

        "nameserver_count":

            metadata.get(
                "nameserver_count",
                0,
            ),

        "ssl_issuer_hash":

            stable_hash(

                metadata.get(
                    "ssl_issuer",
                    "",
                )

            ),

        "hosting_provider_hash":

            stable_hash(

                metadata.get(
                    "hosting_provider",
                    "",
                )

            ),

        "ip_subnet_hash":

            stable_hash(

                metadata.get(
                    "ip_subnet24",
                    "",
                )

            ),
    }


def select_prediction_features(
    feature_dict: Dict,
) -> Dict:
    """
    Select only the prediction features required for
    campaign analysis.

    Missing values are replaced with zero.
    """

    selected = {}

    for feature in (

        LEXICAL_FEATURES

        +

        INFRASTRUCTURE_FEATURES

    ):

        selected[feature] = feature_dict.get(
            feature,
            0,
        )

    return selected

# ============================================================
# Feature Extraction
# ============================================================

def extract_campaign_features(
    url: str,
) -> Dict:
    """
    Extract campaign-oriented features for a single URL.

    Pipeline
    --------
        URL
          │
          ├── Frozen prediction features
          │
          └── Campaign metadata
                     │
                     ▼
              Numeric encoding
                     │
                     ▼
            Campaign feature vector

    Parameters
    ----------
    url : str

    Returns
    -------
    Dict
        Numerical feature vector suitable for DBSCAN.
    """

    #
    # -----------------------------
    # Frozen prediction features
    # -----------------------------
    #
    prediction_features = extract_all_features(url)

    prediction_features = select_prediction_features(
        prediction_features
    )

    #
    # -----------------------------
    # Campaign metadata
    # -----------------------------
    #
    domain = extract_domain_in_features_with_infra(url)

    metadata = get_campaign_metadata(domain)

    metadata_features = encode_campaign_metadata(
        metadata
    )

    #
    # -----------------------------
    # Merge
    # -----------------------------
    #
    feature_vector = {}

    #
    # Prediction-derived features
    #
    feature_vector.update(
        prediction_features
    )

    #
    # Campaign metadata features
    #
    feature_vector.update(
        metadata_features
    )

    #
    # -----------------------------
    # Safety check
    # -----------------------------
    #
    # Ensure every expected feature exists.
    #
    for feature in CAMPAIGN_FEATURES:

        if feature not in feature_vector:

            feature_vector[feature] = 0

    return feature_vector


# ============================================================
# Internal Validation
# ============================================================

def validate_feature_vector(
    feature_vector: Dict,
) -> Dict:
    """
    Validate the campaign feature vector.

    This function ensures:

    1. Every required feature exists.
    2. Missing values become zero.
    3. None values become zero.
    """

    validated = {}

    for feature in CAMPAIGN_FEATURES:

        value = feature_vector.get(
            feature,
            0,
        )

        if value is None:
            value = 0

        validated[feature] = value

    return validated


# ============================================================
# Single URL API
# ============================================================

def get_campaign_feature_vector(
    url: str,
) -> Dict:
    """
    Public helper used by the campaign module.

    This wrapper keeps future preprocessing changes
    isolated from callers.
    """

    feature_vector = extract_campaign_features(
        url
    )

    feature_vector = validate_feature_vector(
        feature_vector
    )

    return feature_vector

# ============================================================
# Batch Feature Extraction
# ============================================================

def extract_campaign_features_batch(
    df: pd.DataFrame,
    url_column: str = "url",
) -> pd.DataFrame:
    """
    Extract campaign features for an entire dataframe.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe containing URLs.

    url_column : str
        Name of URL column.

    Returns
    -------
    pd.DataFrame
        Campaign feature matrix.
    """

    if url_column not in df.columns:
        raise ValueError(
            f"Column '{url_column}' not found in dataframe."
        )

    feature_rows = []

    for url in df[url_column]:

        feature_vector = get_campaign_feature_vector(
            url
        )

        feature_rows.append(
            feature_vector
        )

    feature_df = pd.DataFrame(
        feature_rows
    )

    #
    # --------------------------------------------------------
    # Ensure column ordering remains deterministic.
    #
    # This is important because DBSCAN is trained using the
    # feature order defined by CAMPAIGN_FEATURES.
    # --------------------------------------------------------
    #
    feature_df = feature_df[
        CAMPAIGN_FEATURES
    ]

    return feature_df


# ============================================================
# Feature Names
# ============================================================

def get_campaign_feature_names() -> List[str]:
    """
    Return the ordered campaign feature list.

    Returns
    -------
    List[str]
    """

    return CAMPAIGN_FEATURES.copy()


# ============================================================
# Diagnostics
# ============================================================

def get_campaign_feature_groups() -> Dict[str, List[str]]:
    """
    Return feature groups.

    Useful for:

    - Dissertation
    - Ablation studies
    - Debugging
    - Documentation
    """

    return {

        "lexical": LEXICAL_FEATURES,

        "infrastructure": INFRASTRUCTURE_FEATURES,

        "campaign_metadata":
            CAMPAIGN_METADATA_FEATURES,
    }


# ============================================================
# Debug
# ============================================================

if __name__ == "__main__":

    sample_url = "https://accounts.google.com"

    features = get_campaign_feature_vector(
        sample_url
    )

    print("\nCampaign Feature Vector\n")

    for key in CAMPAIGN_FEATURES:

        print(
            f"{key:30} : {features[key]}"
        )