"""
campaign_features.py
--------------------

Feature extraction module for Campaign Analysis.

This module prepares the feature matrix used by the Campaign Analysis
pipeline. It reuses the existing feature engineering implementation
(features_with_infra.py) to avoid code duplication and selects only the
features relevant for campaign clustering.

Responsibilities
----------------
1. Extract combined lexical + infrastructure features.
2. Select campaign-relevant features.
3. Produce a DataFrame ready for clustering.

This module intentionally does NOT perform clustering, reporting,
or visualization.
"""

from __future__ import annotations

from typing import Dict, List

import pandas as pd

from src.features_with_infra import extract_all_features


# ---------------------------------------------------------------------
# Campaign Feature Set
# ---------------------------------------------------------------------

CAMPAIGN_FEATURES: List[str] = [

    # -------------------------------------------------
    # Lexical Features
    # -------------------------------------------------

    "url_length",
    "domain_length",
    "path_length",
    "query_length",

    "url_entropy",
    "domain_entropy",

    "subdomain_count",

    # -------------------------------------------------
    # Infrastructure Features
    # -------------------------------------------------

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


# ---------------------------------------------------------------------
# Internal Helper
# ---------------------------------------------------------------------

def _select_campaign_features(
    feature_dict: Dict
) -> Dict:
    """
    Select campaign-relevant features from the complete
    extracted feature dictionary.

    Missing features are replaced with zero to ensure
    a consistent feature vector.
    """

    return {
        feature: feature_dict.get(feature, 0)
        for feature in CAMPAIGN_FEATURES
    }


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------

def extract_campaign_features(url: str) -> Dict:
    """
    Extract campaign features for a single URL.

    Parameters
    ----------
    url : str

    Returns
    -------
    Dict
        Campaign feature vector.
    """

    all_features = extract_all_features(url)

    return _select_campaign_features(all_features)


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
        URL column name.

    Returns
    -------
    pd.DataFrame
        Campaign feature matrix.
    """

    if url_column not in df.columns:
        raise ValueError(
            f"Column '{url_column}' not found in dataframe."
        )

    feature_rows = [
        extract_campaign_features(url)
        for url in df[url_column]
    ]

    return pd.DataFrame(feature_rows)


def get_campaign_feature_names() -> List[str]:
    """
    Return campaign feature names.

    Returns
    -------
    List[str]
        Ordered campaign feature list.
    """

    return CAMPAIGN_FEATURES.copy()