"""
divergence.py

Statistical divergence measures used for drift detection.

Implemented Metrics
-------------------
1. Kullback-Leibler (KL) Divergence
2. Jensen-Shannon (JS) Divergence
3. Jensen-Shannon Distance

Author : Vivek Pise
Project: Infrastructure-Aware Drift-Adaptive Multimodal
         Phishing Risk Intelligence Framework
"""

from typing import Dict

import numpy as np

from .statistics import (
    ArrayLike,
    shared_probability_distributions,
    safe_log
)


# ---------------------------------------------------------------------
# Kullback-Leibler Divergence
# ---------------------------------------------------------------------

def calculate_kl_divergence(
    reference: ArrayLike,
    current: ArrayLike,
    bins: int = 10
) -> float:
    """
    Calculate KL Divergence.

    KL(P || Q)

    Measures how much the current distribution differs
    from the reference distribution.

    Returns
    -------
    float
    """

    ref_probs, cur_probs, _ = shared_probability_distributions(
        reference,
        current,
        bins=bins
    )

    kl = np.sum(
        ref_probs *
        safe_log(ref_probs / cur_probs)
    )

    return float(kl)


# ---------------------------------------------------------------------
# Jensen-Shannon Divergence
# ---------------------------------------------------------------------

def calculate_js_divergence(
    reference: ArrayLike,
    current: ArrayLike,
    bins: int = 10
) -> float:
    """
    Calculate Jensen-Shannon Divergence.

    Unlike KL Divergence, JS Divergence is
    symmetric and always finite.

    Returns
    -------
    float
    """

    ref_probs, cur_probs, _ = shared_probability_distributions(
        reference,
        current,
        bins=bins
    )

    midpoint = 0.5 * (ref_probs + cur_probs)

    kl_ref = np.sum(
        ref_probs *
        safe_log(ref_probs / midpoint)
    )

    kl_cur = np.sum(
        cur_probs *
        safe_log(cur_probs / midpoint)
    )

    js = 0.5 * (kl_ref + kl_cur)

    return float(js)


# ---------------------------------------------------------------------
# Jensen-Shannon Distance
# ---------------------------------------------------------------------

def calculate_js_distance(
    reference: ArrayLike,
    current: ArrayLike,
    bins: int = 10
) -> float:
    """
    Jensen-Shannon Distance.

    JS Distance = sqrt(JS Divergence)

    Range
    -----
    0.0 -> identical distributions

    1.0 -> maximally different distributions

    Returns
    -------
    float
    """

    js = calculate_js_divergence(
        reference,
        current,
        bins=bins
    )

    return float(np.sqrt(js))


# ---------------------------------------------------------------------
# Feature-wise KL Divergence
# ---------------------------------------------------------------------

def calculate_feature_kl(
    reference_features,
    current_features,
    bins: int = 10
) -> Dict[str, float]:
    """
    Calculate KL Divergence
    for every feature.

    Returns
    -------
    dict
    """

    if list(reference_features.columns) != list(current_features.columns):
        raise ValueError(
            "Reference and current features "
            "must contain identical columns."
        )

    scores = {}

    for feature in reference_features.columns:

        scores[feature] = calculate_kl_divergence(
            reference_features[feature],
            current_features[feature],
            bins=bins
        )

    return scores


# ---------------------------------------------------------------------
# Feature-wise JS Distance
# ---------------------------------------------------------------------

def calculate_feature_js(
    reference_features,
    current_features,
    bins: int = 10
) -> Dict[str, float]:
    """
    Calculate Jensen-Shannon Distance
    for every feature.

    Returns
    -------
    dict
    """

    if list(reference_features.columns) != list(current_features.columns):
        raise ValueError(
            "Reference and current features "
            "must contain identical columns."
        )

    scores = {}

    for feature in reference_features.columns:

        scores[feature] = calculate_js_distance(
            reference_features[feature],
            current_features[feature],
            bins=bins
        )

    return scores


# ---------------------------------------------------------------------
# Overall KL Divergence
# ---------------------------------------------------------------------

def overall_kl(
    feature_scores: Dict[str, float]
) -> float:
    """
    Aggregate feature-wise KL scores.

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
# Overall JS Distance
# ---------------------------------------------------------------------

def overall_js(
    feature_scores: Dict[str, float]
) -> float:
    """
    Aggregate feature-wise JS Distance.

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
# Top Divergent Features
# ---------------------------------------------------------------------

def top_divergent_features(
    feature_scores: Dict[str, float],
    top_n: int = 10
):
    """
    Return the highest divergent features.

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