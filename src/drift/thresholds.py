"""
thresholds.py

Central configuration and decision logic for drift detection.

Responsibilities
----------------
- Drift severity thresholds
- Drift metric weights
- Retraining recommendation
- Human-readable recommendations

Author : Vivek Pise
Project: Infrastructure-Aware Drift-Adaptive Multimodal
         Phishing Risk Intelligence Framework
"""

from typing import Dict


# ---------------------------------------------------------------------
# Drift Severity Thresholds
# ---------------------------------------------------------------------

# Industry-standard PSI thresholds
PSI_LOW_THRESHOLD = 0.10
PSI_MEDIUM_THRESHOLD = 0.25

# Jensen-Shannon Distance thresholds
JS_LOW_THRESHOLD = 0.10
JS_MEDIUM_THRESHOLD = 0.20

# KL Divergence thresholds
KL_LOW_THRESHOLD = 0.10
KL_MEDIUM_THRESHOLD = 0.20


# ---------------------------------------------------------------------
# Overall Drift Score Thresholds
# ---------------------------------------------------------------------

OVERALL_STABLE_THRESHOLD = 0.10
OVERALL_LOW_THRESHOLD = 0.20
OVERALL_MEDIUM_THRESHOLD = 0.35

# ---------------------------------------------------------------------
# Metric Weights
# ---------------------------------------------------------------------

# These weights are used when computing the overall drift score.
# They should always sum to 1.0.

PSI_WEIGHT = 0.50
JS_WEIGHT = 0.30
KL_WEIGHT = 0.20


# ---------------------------------------------------------------------
# Overall Drift Score
# ---------------------------------------------------------------------

def calculate_overall_score(
    psi_score: float,
    js_score: float,
    kl_score: float
) -> float:
    """
    Calculate weighted overall drift score.

    Parameters
    ----------
    psi_score : float

    js_score : float

    kl_score : float

    Returns
    -------
    float
    """

    return (
        PSI_WEIGHT * psi_score +
        JS_WEIGHT * js_score +
        KL_WEIGHT * kl_score
    )


# ---------------------------------------------------------------------
# Drift Severity Classification
# ---------------------------------------------------------------------

def classify_drift(overall_score: float) -> str:
    """
    Classify the overall drift severity.

    Categories
    ----------
    STABLE :  overall_score < 0.10
    LOW     : 0.10 <= overall_score < 0.20
    MEDIUM  : 0.20 <= overall_score < 0.35
    HIGH    : overall_score >= 0.35

    Parameters
    ----------
    overall_score : float

    Returns
    -------
    str
        One of:
        - STABLE
        - LOW
        - MEDIUM
        - HIGH
    """

    if overall_score < OVERALL_STABLE_THRESHOLD:
        return "STABLE"

    elif overall_score < OVERALL_LOW_THRESHOLD:
        return "LOW"

    elif overall_score < OVERALL_MEDIUM_THRESHOLD:
        return "MEDIUM"

    else:
        return "HIGH"

# ---------------------------------------------------------------------
# Retraining Recommendation
# ---------------------------------------------------------------------

def requires_retraining(
    overall_score: float
) -> bool:
    """
    Determine whether retraining is recommended.

    Returns
    -------
    bool
    """

    return overall_score >= OVERALL_MEDIUM_THRESHOLD


# ---------------------------------------------------------------------
# Human-readable Recommendation
# ---------------------------------------------------------------------

def recommendation(overall_score: float) -> str:
    """
    Generate analyst recommendation based on drift severity.
    """

    severity = classify_drift(overall_score)

    recommendations = {
        "STABLE": (
            "No significant drift detected. "
            "Continue routine monitoring."
        ),

        "LOW": (
            "Low drift detected. "
            "Increase monitoring frequency."
        ),

        "MEDIUM": (
            "Moderate drift detected. "
            "Validate model performance and prepare for retraining if drift persists."
        ),

        "HIGH": (
            "High drift detected. "
            "Immediate model retraining is recommended."
        )
    }

    return recommendations[severity]

# ---------------------------------------------------------------------
# Decision Summary
# ---------------------------------------------------------------------

def build_decision(
    psi_score: float,
    js_score: float,
    kl_score: float
) -> Dict:
    """
    Build a complete drift decision.

    Returns
    -------
    dict
    """

    overall = calculate_overall_score(
        psi_score,
        js_score,
        kl_score
    )

    return {

        "overall_score": overall,

        "severity": classify_drift(overall),

        "requires_retraining":
            requires_retraining(overall),

        "recommendation":
            recommendation(overall)

    }