"""
campaign_utils.py
-----------------

Utility functions for Campaign Analysis.

This module contains lightweight helper functions shared across
multiple campaign modules.

It intentionally contains no business logic, clustering,
feature extraction, reporting, or visualization.
"""

from __future__ import annotations

from typing import Dict, List

import pandas as pd


NOISE_LABEL = -1


def is_noise_cluster(cluster_id: int) -> bool:
    """
    Check whether a cluster label represents DBSCAN noise.

    Parameters
    ----------
    cluster_id : int

    Returns
    -------
    bool
    """

    return cluster_id == NOISE_LABEL


def get_valid_campaign_ids(labels: List[int]) -> List[int]:
    """
    Return all valid campaign IDs (excluding noise).

    Parameters
    ----------
    labels : List[int]

    Returns
    -------
    List[int]
    """

    return sorted(
        label
        for label in set(labels)
        if label != NOISE_LABEL
    )


def calculate_campaign_sizes(
    campaign_df: pd.DataFrame,
    campaign_column: str = "campaign_id",
) -> Dict[int, int]:
    """
    Calculate campaign sizes.

    Parameters
    ----------
    campaign_df : pd.DataFrame

    campaign_column : str

    Returns
    -------
    Dict[int, int]
    """

    if campaign_column not in campaign_df.columns:
        return {}

    valid_df = campaign_df[
        campaign_df[campaign_column] != NOISE_LABEL
    ]

    return (
        valid_df[campaign_column]
        .value_counts()
        .sort_index()
        .to_dict()
    )


def calculate_noise_count(
    campaign_df: pd.DataFrame,
    campaign_column: str = "campaign_id",
) -> int:
    """
    Count DBSCAN noise URLs.

    Parameters
    ----------
    campaign_df : pd.DataFrame

    campaign_column : str

    Returns
    -------
    int
    """

    if campaign_column not in campaign_df.columns:
        return 0

    return int(
        (campaign_df[campaign_column] == NOISE_LABEL).sum()
    )


def format_campaign_name(cluster_id: int) -> str:
    """
    Format campaign label for display.

    Parameters
    ----------
    cluster_id : int

    Returns
    -------
    str
    """

    if is_noise_cluster(cluster_id):
        return "Unclustered"

    return f"Campaign-{cluster_id + 1}"