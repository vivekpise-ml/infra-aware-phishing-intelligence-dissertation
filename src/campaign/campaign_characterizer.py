"""
campaign_characterizer.py
-------------------------

Campaign characterization module.

This module converts DBSCAN campaign clusters into
structured campaign intelligence.

Phase-1
-------
Structural characterization only.

Risk characterization using the XGBoost prediction
pipeline will be integrated in Phase-2.
"""

from __future__ import annotations

from collections import Counter

import pandas as pd


# ==========================================================
# Column Names
# ==========================================================

COL_URL = "url"

COL_CAMPAIGN_ID = "campaign_id"

COL_ORGANIZATION = "organization"

COL_HOSTING_PROVIDER = "hosting_provider"

COL_ASN = "as"

COL_DOMAIN_AGE = "domain_age_days"

COL_INFRA_TRUST = "infra_trust_score_scaled"

COL_ENTROPY = "url_entropy"

COL_URL_LENGTH = "url_length"

COL_URL_DEPTH = "path_depth"


# ==========================================================
# Utility Functions
# ==========================================================

def _safe_mode(series: pd.Series):
    """
    Return the most frequent non-null value.
    """

    values = series.dropna()

    if values.empty:
        return None

    return values.mode().iloc[0]


def _distribution(series: pd.Series) -> dict:
    """
    Return value frequency distribution.
    """

    values = series.dropna()

    if values.empty:
        return {}

    return dict(Counter(values))


# ==========================================================
# Metadata
# ==========================================================

def _build_metadata(
    campaign_id: int,
    campaign_df: pd.DataFrame,
) -> dict:
    """
    Build campaign metadata.
    """

    return {

        "campaign_id": int(campaign_id),

        "campaign_size": len(campaign_df),

        "noise": campaign_id == -1,

    }


# ==========================================================
# Identity Summary
# ==========================================================

def _build_identity_summary(
    campaign_df: pd.DataFrame,
) -> dict:
    """
    Build organization identity summary.
    """

    organization_distribution = _distribution(
        campaign_df[COL_ORGANIZATION]
    )

    dominant_org = _safe_mode(
        campaign_df[COL_ORGANIZATION]
    )

    if organization_distribution:

        identity_consistency = (
            max(organization_distribution.values())
            / len(campaign_df)
        )

    else:

        identity_consistency = 0.0

    return {

        "dominant_organization":

            dominant_org,

        "organization_distribution":

            organization_distribution,

        "identity_consistency":

            round(identity_consistency, 3),

    }


# ==========================================================
# Infrastructure Summary
# ==========================================================

def _build_infrastructure_summary(
    campaign_df: pd.DataFrame,
) -> dict:
    """
    Build infrastructure statistics.
    """

    dominant_asn = _safe_mode(
        campaign_df[COL_ASN]
    )

    dominant_hosting = _safe_mode(
        campaign_df[COL_HOSTING_PROVIDER]
    )


    average_domain_age = (
        campaign_df[COL_DOMAIN_AGE]
        .fillna(0)
        .mean()
    )

    average_trust_score = (
        campaign_df[COL_INFRA_TRUST]
        .fillna(0)
        .mean()
    )

    if len(campaign_df) == 0:

        infrastructure_reuse = 0.0

    else:

        infrastructure_reuse = (
            campaign_df[COL_HOSTING_PROVIDER]
            .value_counts(normalize=True)
            .max()
        )

    return {

        "dominant_asn":
            dominant_asn,

        "dominant_hosting_provider":
            dominant_hosting,

        "average_domain_age":
            round(average_domain_age, 2),

        "average_trust_score":
            round(average_trust_score, 3),

        "infrastructure_reuse":
            round(infrastructure_reuse, 3),

    }


# ==========================================================
# Lexical Summary
# ==========================================================

def _build_lexical_summary(
    campaign_df: pd.DataFrame,
) -> dict:
    """
    Build lexical statistics.
    """

    return {

        "average_url_length":

            round(
                campaign_df[COL_URL_LENGTH]
                .mean(),
                2,
            ),

        "average_entropy":

            round(
                campaign_df[COL_ENTROPY]
                .mean(),
                3,
            ),

        "average_path_depth":

            round(
                campaign_df[COL_URL_DEPTH]
                .mean(),
                2,
            ),

    }


# ==========================================================
# Structural Confidence
# ==========================================================

def _calculate_structural_confidence(
    identity: dict,
    infrastructure: dict,
) -> dict:
    """
    Compute campaign structural confidence.
    """

    confidence = (

        identity["identity_consistency"]

        +

        infrastructure["infrastructure_reuse"]

    ) / 2.0

    return {

        "structural_confidence":

            round(confidence, 3),

    }


# ==========================================================
# Overall Summary
# ==========================================================

def _build_summary(
    campaigns: list,
) -> dict:
    """
    Build overall campaign summary.
    """

    if not campaigns:

        return {

            "campaign_count": 0,

            "average_campaign_size": 0,

            "average_structural_confidence": 0,

        }

    campaign_sizes = [

        c["metadata"]["campaign_size"]

        for c in campaigns

    ]

    confidence_scores = [

        c["confidence"]["structural_confidence"]

        for c in campaigns

    ]

    return {

        "campaign_count":

            len(campaigns),

        "average_campaign_size":

            round(
                sum(campaign_sizes) / len(campaign_sizes),
                2,
            ),

        "average_structural_confidence":

            round(
                sum(confidence_scores)
                / len(confidence_scores),
                3,
            ),

    }


# ==========================================================
# Public API
# ==========================================================

def characterize_campaigns(
    campaign_df: pd.DataFrame,
) -> dict:
    """
    Characterize discovered campaigns.

    Phase-1 currently implements

    - Metadata
    - Identity Summary
    - Infrastructure Summary
    - Lexical Summary
    - Structural Confidence
    """

    campaigns = []

    grouped = campaign_df.groupby(
        COL_CAMPAIGN_ID
    )

    for campaign_id, group in grouped:

        identity = _build_identity_summary(group)

        infrastructure = _build_infrastructure_summary(group)

        lexical = _build_lexical_summary(group)

        confidence = _calculate_structural_confidence(

            identity,

            infrastructure,

        )

        campaign = {

            "metadata":

                _build_metadata(
                    campaign_id,
                    group,
                ),

            "identity":

                identity,

            "infrastructure":

                infrastructure,

            "lexical":

                lexical,

            "confidence":

                confidence,

            "urls":

                group[COL_URL].tolist(),

        }

        campaigns.append(campaign)

    return {

        "campaigns":

            campaigns,

        "summary":

            _build_summary(campaigns),

        "campaign_sizes":

            {},

        "cluster_statistics":

            {},

    }