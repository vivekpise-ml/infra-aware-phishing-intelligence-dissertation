"""
campaign_cluster.py
-------------------

DBSCAN clustering engine for Campaign Analysis.

Responsibilities
----------------
1. Scale campaign feature vectors.
2. Train DBSCAN clustering model.
3. Save clustering artifacts.
4. Load clustering artifacts.
5. Assign cluster labels.

This module intentionally does NOT perform feature extraction,
report generation or visualization.
"""

from __future__ import annotations

from typing import Tuple

import joblib
import pandas as pd

from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

from src.config import MODEL_DIR
from src.campaign.campaign_features import get_campaign_feature_names


DBSCAN_MODEL_FILE = f"{MODEL_DIR}/campaign_dbscan.pkl"
SCALER_FILE = f"{MODEL_DIR}/campaign_scaler.pkl"
FEATURE_FILE = f"{MODEL_DIR}/campaign_feature_names.pkl"


class CampaignCluster:
    """
    DBSCAN clustering engine.
    """

    def __init__(
        self,
        eps: float = 2.0,
        min_samples: int = 3,
    ):

        self.eps = eps
        self.min_samples = min_samples

        self.scaler = StandardScaler()

        self.model = DBSCAN(
            eps=self.eps,
            min_samples=self.min_samples,
            metric="euclidean",
        )

    # ---------------------------------------------------------
    # Training
    # ---------------------------------------------------------

    def fit(
        self,
        feature_df: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, list]:
        """
        Fit DBSCAN model.

        Parameters
        ----------
        feature_df : pd.DataFrame

        Returns
        -------
        scaled_features, cluster_labels
        """

        scaled = self.scaler.fit_transform(feature_df)

        labels = self.model.fit_predict(scaled)

        return scaled, labels.tolist()

    # ---------------------------------------------------------
    # Persistence
    # ---------------------------------------------------------

    def save(self):
        """
        Save clustering artifacts.
        """

        joblib.dump(
            self.model,
            DBSCAN_MODEL_FILE,
        )

        joblib.dump(
            self.scaler,
            SCALER_FILE,
        )

        joblib.dump(
            get_campaign_feature_names(),
            FEATURE_FILE,
        )

    def load(self):
        """
        Load clustering artifacts.
        """

        self.model = joblib.load(
            DBSCAN_MODEL_FILE
        )

        self.scaler = joblib.load(
            SCALER_FILE
        )

    # ---------------------------------------------------------
    # Clustering
    # ---------------------------------------------------------

    def cluster(
        self,
        feature_df: pd.DataFrame,
    ) -> list:
        """
        Cluster campaign feature matrix.

        If model is not already trained,
        train it first.

        Parameters
        ----------
        feature_df : pd.DataFrame

        Returns
        -------
        List[int]
            Campaign labels.
        """

        if not hasattr(self.scaler, "mean_"):

            _, labels = self.fit(feature_df)

            return labels

        scaled = self.scaler.transform(feature_df)

        labels = self.model.fit_predict(scaled)

        return labels.tolist()