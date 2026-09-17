"""
campaign_detector.py
--------------------

Campaign detection engine.

This module orchestrates campaign feature extraction and DBSCAN clustering
to identify phishing campaigns.

Responsibilities
----------------
1. Extract campaign features.
2. Cluster URLs using DBSCAN.
3. Assign campaign IDs.
4. Generate campaign statistics.

This module intentionally does NOT generate reports,
visualizations or Streamlit UI.
"""

from __future__ import annotations

from typing import Dict

import pandas as pd

from src.campaign.campaign_cluster import CampaignCluster
from src.campaign.campaign_features import extract_campaign_features_batch

from src.campaign.campaign_utils import (
    calculate_campaign_sizes,
    calculate_noise_count,
)

class CampaignDetector:
    """
    Campaign detection engine based on DBSCAN clustering.
    """

    def __init__(self):

        self.cluster_engine = CampaignCluster()

    def detect(
        self,
        df: pd.DataFrame,
        url_column: str = "url",
    ) -> Dict:
        """
        Detect phishing campaigns.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe containing URLs.

        url_column : str
            URL column name.

        Returns
        -------
        Dict
            Campaign analysis results.
        """

        # -------------------------------------------------
        # Extract campaign features
        # -------------------------------------------------

        feature_df = extract_campaign_features_batch(
            df=df,
            url_column=url_column,
        )

        # -------------------------------------------------
        # Perform clustering
        # -------------------------------------------------

        labels = self.cluster_engine.cluster(feature_df)

        # -------------------------------------------------
        # Build URL-level campaign dataframe
        # -------------------------------------------------

        campaign_df = df.copy().reset_index(drop=True)

        campaign_df["campaign_id"] = labels

        campaign_df["is_noise"] = campaign_df["campaign_id"] == -1

        # -------------------------------------------------
        # Campaign statistics
        # -------------------------------------------------

        valid_campaigns = campaign_df[
            campaign_df["campaign_id"] != -1
        ]

        '''
        campaign_sizes = (
            valid_campaigns["campaign_id"]
            .value_counts()
            .sort_index()
            .to_dict()
        )
        '''

        campaign_sizes = calculate_campaign_sizes(campaign_df)

        campaign_count = len(campaign_sizes)

        largest_campaign_size = (
            max(campaign_sizes.values())
            if campaign_sizes
            else 0
        )

        #noise_count = int(campaign_df["is_noise"].sum())

        noise_count = calculate_noise_count(campaign_df)

        # -------------------------------------------------
        # Return structured result
        # -------------------------------------------------

        return {

            # ---------------------------------------------
            # URL-level output
            # ---------------------------------------------
            "campaign_dataframe": campaign_df,

            # ---------------------------------------------
            # Summary
            # ---------------------------------------------
            "campaign_count": campaign_count,

            "largest_campaign_size": largest_campaign_size,

            "noise_urls": noise_count,

            "campaign_sizes": campaign_sizes,

            "cluster_labels": labels,
        }