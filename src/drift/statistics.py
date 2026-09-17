"""
statistics.py

Statistical utility functions for the Drift Detection package.

Responsibilities
----------------
- Input validation
- Array conversion
- Histogram computation
- Probability distribution generation
- Shared histogram construction
- Feature statistics
- Numerical stability helpers

This module is intentionally independent of PSI, KL Divergence,
and Jensen-Shannon Distance so that it can be reused by multiple
drift algorithms.

Author : Vivek Pise
Project: Infrastructure-Aware Drift-Adaptive Multimodal
         Phishing Risk Intelligence Framework
"""

from typing import Tuple, Union

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------
# Type Definitions
# ---------------------------------------------------------------------

ArrayLike = Union[np.ndarray, pd.Series, list]

# ---------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------

DEFAULT_EPSILON = 1e-10

# ---------------------------------------------------------------------
# Internal Helper
# ---------------------------------------------------------------------


def _to_numpy(data: ArrayLike) -> np.ndarray:
    """
    Convert supported input types into a flattened NumPy array.

    Supports:
        - NumPy ndarray
        - Pandas Series
        - Python list

    Returns
    -------
    np.ndarray
    """

    return np.asarray(data).ravel()


# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------


def validate_numeric_array(data: ArrayLike) -> np.ndarray:
    """
    Validate that input is a valid numeric array.

    Parameters
    ----------
    data : ArrayLike

    Returns
    -------
    np.ndarray
        Validated NumPy array.

    Raises
    ------
    ValueError
    """

    data = _to_numpy(data)

    if data.size == 0:
        raise ValueError("Input array is empty.")

    if not np.issubdtype(data.dtype, np.number):
        raise ValueError("Input must contain numeric values.")

    if np.isnan(data).any():
        raise ValueError("Input contains NaN values.")

    if np.isinf(data).any():
        raise ValueError("Input contains infinite values.")

    return data


# ---------------------------------------------------------------------
# Histogram Utilities
# ---------------------------------------------------------------------


def compute_histogram(
    data: ArrayLike,
    bins: int = 10,
    strategy: str = "equal_width"
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute histogram.

    Parameters
    ----------
    data : ArrayLike

    bins : int
        Number of bins.

    strategy : str
        Histogram strategy.

        Current supported:
            - equal_width

    Returns
    -------
    histogram_counts
    histogram_edges
    """

    data = validate_numeric_array(data)

    if strategy != "equal_width":
        raise NotImplementedError(
            f"Histogram strategy '{strategy}' is not implemented."
        )

    counts, edges = np.histogram(
        data,
        bins=bins
    )

    return counts.astype(float), edges


# ---------------------------------------------------------------------
# Histogram Using Existing Bin Edges
# ---------------------------------------------------------------------


def histogram_from_edges(
    data: ArrayLike,
    bin_edges: np.ndarray
) -> np.ndarray:
    """
    Compute histogram using precomputed bin edges.

    This ensures identical histogram bins are used
    for reference and current datasets.
    """

    data = validate_numeric_array(data)

    counts, _ = np.histogram(
        data,
        bins=bin_edges
    )

    return counts.astype(float)


# ---------------------------------------------------------------------
# Distribution Normalization
# ---------------------------------------------------------------------


def normalize_distribution(
    counts: np.ndarray,
    epsilon: float = DEFAULT_EPSILON
) -> np.ndarray:
    """
    Convert histogram counts into a probability distribution.

    Parameters
    ----------
    counts : np.ndarray

    epsilon : float

    Returns
    -------
    np.ndarray
    """

    counts = counts.astype(float)

    counts += epsilon

    return counts / counts.sum()


# ---------------------------------------------------------------------
# Probability Distribution
# ---------------------------------------------------------------------


def probability_distribution(
    data: ArrayLike,
    bins: int = 10
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate probability distribution directly from raw values.

    Returns
    -------
    probabilities
    histogram_edges
    """

    counts, edges = compute_histogram(
        data,
        bins=bins
    )

    probs = normalize_distribution(counts)

    return probs, edges


# ---------------------------------------------------------------------
# Shared Probability Distributions
# ---------------------------------------------------------------------


def shared_probability_distributions(
    reference: ArrayLike,
    current: ArrayLike,
    bins: int = 10
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate probability distributions for two datasets
    using identical histogram edges.

    Returns
    -------
    reference_probabilities

    current_probabilities

    histogram_edges
    """

    ref_counts, edges = compute_histogram(
        reference,
        bins=bins
    )

    cur_counts = histogram_from_edges(
        current,
        edges
    )

    ref_probs = normalize_distribution(ref_counts)

    cur_probs = normalize_distribution(cur_counts)

    return ref_probs, cur_probs, edges


# ---------------------------------------------------------------------
# Feature Statistics
# ---------------------------------------------------------------------


def feature_statistics(data: ArrayLike) -> dict:
    """
    Compute descriptive statistics for a feature.

    Returns
    -------
    dict
    """

    data = validate_numeric_array(data)

    return {
        "count": int(data.size),
        "mean": float(np.mean(data)),
        "std": float(np.std(data)),
        "min": float(np.min(data)),
        "max": float(np.max(data)),
        "median": float(np.median(data))
    }


# ---------------------------------------------------------------------
# Safe Logarithm
# ---------------------------------------------------------------------


def safe_log(
    values: np.ndarray,
    epsilon: float = DEFAULT_EPSILON
) -> np.ndarray:
    """
    Numerically stable logarithm.

    Prevents log(0).

    Parameters
    ----------
    values : np.ndarray

    epsilon : float

    Returns
    -------
    np.ndarray
    """

    return np.log(values + epsilon)