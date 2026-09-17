"""
psi.py

Population Stability Index (PSI) implementation.

PSI measures the change in feature distributions between
a reference dataset and a current dataset.

Interpretation
--------------
PSI < 0.10
    No significant drift

0.10 <= PSI < 0.25
    Moderate drift

PSI >= 0.25
    Significant drift

Author : Vivek Pise
Project: Infrastructure-Aware Drift-Adaptive Multimodal
         Phishing Risk Intelligence Framework
"""

from typing import Dict, List, Tuple

import numpy as np

from .statistics import (
    ArrayLike,
    shared_probability_distributions,
    safe_log
)


# ---------------------------------------------------------------------
# PSI for a Single Feature
# ---------------------------------------------------------------------

def calculate_psi(
    reference: ArrayLike,
    current: ArrayLike,
    bins: int = 10
) -> float:
    """
    Calculate Population Stability Index (PSI)
    between two feature distributions.

    Parameters
    ----------
    reference : ArrayLike
        Reference feature values.

    current : ArrayLike
        Current feature values.

    bins : int
        Number of histogram bins.

    Returns
    -------
    float
        PSI score.
    """

    ref_probs, cur_probs, _ = shared_probability_distributions(
        reference,
        current,
        bins=bins
    )

    psi = np.sum(
        (cur_probs - ref_probs) *
        safe_log(cur_probs / ref_probs)
    )

    return float(psi)


# ---------------------------------------------------------------------
# Feature-wise PSI
# ---------------------------------------------------------------------

def calculate_feature_psi(
    reference_features,
    current_features,
    bins: int = 10
) -> Dict[str, float]:
    """
    Compute PSI for every feature.

    Parameters
    ----------
    reference_features : pandas.DataFrame

    current_features : pandas.DataFrame

    bins : int

    Returns
    -------
    dict

    Example
    -------
    {
        "url_length":0.04,
        "domain_age_days":0.31,
        "num_digits":0.08
    }
    """

    if list(reference_features.columns) != list(current_features.columns):
        raise ValueError(
            "Reference and current feature sets "
            "must contain identical columns."
        )

    psi_scores = {}

    for column in reference_features.columns:

        psi_scores[column] = calculate_psi(
            reference_features[column],
            current_features[column],
            bins=bins
        )

    return psi_scores


# ---------------------------------------------------------------------
# Overall PSI
# ---------------------------------------------------------------------

def overall_psi(
    feature_scores: Dict[str, float]
) -> float:
    """
    Aggregate feature-wise PSI into a single score.

    Currently uses arithmetic mean.

    Future versions may use weighted aggregation.

    Parameters
    ----------
    feature_scores : dict

    Returns
    -------
    float
    """

    if len(feature_scores) == 0:
        return 0.0

    return float(
        np.mean(
            list(feature_scores.values())
        )
    )


# ---------------------------------------------------------------------
# Top Drifting Features
# ---------------------------------------------------------------------

def top_drifting_features(
    feature_scores: Dict[str, float],
    top_n: int = 10
) -> List[Tuple[str, float]]:
    """
    Return the highest drifting features.

    Parameters
    ----------
    feature_scores : dict

    top_n : int

    Returns
    -------
    List[Tuple]
    """

    return sorted(
        feature_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_n]