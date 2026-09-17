"""
campaign_cluster.py
-------------------

DBSCAN clustering engine for phishing campaign analysis.

Responsibilities
----------------
1. Perform DBSCAN clustering on preprocessed campaign features.
2. Compute campaign cluster statistics.
3. Compute clustering quality metrics.
4. Persist and restore trained clustering models.
5. Provide cluster metadata for reporting.

This module intentionally does NOT perform:

    • Feature extraction
    • Feature preprocessing
    • Campaign reporting
    • Visualization

Those responsibilities belong to their respective modules.
"""

from __future__ import annotations

import logging
import os

from dataclasses import dataclass
from typing import Dict, List, Optional, Union

import joblib
import numpy as np
import pandas as pd

from sklearn.cluster import DBSCAN
from sklearn.metrics import (silhouette_score, davies_bouldin_score, 
                             calinski_harabasz_score,)

from src.config import CAMPAIGN_CLUSTERING_CONFIG


logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Cluster Statistics
# ---------------------------------------------------------------------


@dataclass
class ClusterStatistics:
    """
    Summary statistics of a DBSCAN clustering run.
    """

    total_samples: int

    n_clusters: int

    n_noise: int

    noise_ratio: float

    silhouette_score: Optional[float]

    davies_bouldin_score: Optional[float]
    calinski_harabasz_score: Optional[float]

    cluster_sizes: Dict[int, int]
    largest_cluster_size: int

# ---------------------------------------------------------------------
# Campaign Cluster Engine
# ---------------------------------------------------------------------


class CampaignCluster:
    """
    DBSCAN clustering engine.

    Notes
    -----
    This class assumes the incoming feature matrix has already been
    preprocessed by CampaignPreprocessor.

    Therefore it performs NO:

        • Scaling
        • Encoding
        • Missing value handling

    It only performs clustering.
    """
    def __init__(
        self,
        eps: Optional[float] = None,
        min_samples: Optional[int] = None,
    ) -> None:
        """
        Initialize DBSCAN clustering engine.
        """

        self.silhouette_score = None
        self.davies_bouldin = None
        self.calinski_harabasz = None

        self.eps = (
            eps
            if eps is not None
            else CAMPAIGN_CLUSTERING_CONFIG["eps"]
        )

        self.min_samples = (
            min_samples
            if min_samples is not None
            else CAMPAIGN_CLUSTERING_CONFIG["min_samples"]
        )

        self.model = DBSCAN(
            eps=self.eps,
            min_samples=self.min_samples,
            metric="euclidean",
        )

        # Learned after fitting

        self.labels_: Optional[np.ndarray] = None

        self.statistics_: Optional[ClusterStatistics] = None

        self.is_fitted_: bool = False

        logger.info(
            "CampaignCluster initialized "
            "(eps=%.3f, min_samples=%d)",
            self.eps,
            self.min_samples,
        )

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def fit(
        self,
        feature_matrix: Union[pd.DataFrame, np.ndarray],
    ) -> "CampaignCluster":
        """
        Train DBSCAN clustering model.

        Parameters
        ----------
        feature_matrix : pandas.DataFrame or numpy.ndarray
            Preprocessed campaign feature matrix.

        Returns
        -------
        CampaignCluster
            Fitted clustering object.
        """

        if not isinstance(
            feature_matrix,
            (pd.DataFrame, np.ndarray),
        ):
            raise TypeError(
                "feature_matrix must be a pandas DataFrame or NumPy array"
            )

        logger.info(
            "Training DBSCAN on %d samples with %d features.",
            feature_matrix.shape[0],
            feature_matrix.shape[1],
        )

        self.labels_ = self.model.fit_predict(feature_matrix)

        self.statistics_ = self._compute_statistics(
            feature_matrix,
            self.labels_,
        )

        self.is_fitted_ = True

        logger.info(
            "DBSCAN completed. "
            "Clusters=%d, Noise=%d",
            self.statistics_.n_clusters,
            self.statistics_.n_noise,
        )

        return self
    
    def fit_predict(
        self,
        feature_matrix: Union[pd.DataFrame, np.ndarray]
    ) -> np.ndarray:
        """
        Fit DBSCAN and return cluster labels.

        Parameters
        ----------
        feature_matrix : pandas.DataFrame or numpy.ndarray

        Returns
        -------
        np.ndarray
            Cluster labels.
        """

        self.fit(feature_matrix)

        return self.labels_
    
    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def get_statistics(
        self,
    ) -> ClusterStatistics:
        """
        Return clustering statistics.

        Returns
        -------
        ClusterStatistics
        """

        if not self.is_fitted_:

            raise RuntimeError(
                "CampaignCluster has not been fitted."
            )

        return self.statistics_
    
    def _compute_statistics(
        self,
        feature_matrix: Union[pd.DataFrame, np.ndarray],
        labels: np.ndarray,
    ) -> ClusterStatistics:
        """
        Compute clustering statistics.
        """

        unique_clusters = sorted(
            label
            for label in np.unique(labels)
            if label != -1
        )

        cluster_sizes = {
            cluster_id: int(
                np.sum(labels == cluster_id)
            )
            for cluster_id in unique_clusters
        }

        n_clusters = len(unique_clusters)

        n_noise = int(
            np.sum(labels == -1)
        )

        total_samples = len(labels)

        noise_ratio = (
            n_noise / total_samples
            if total_samples > 0
            else 0.0
        )

        silhouette = None
        davies_bouldin = None
        calinski_harabasz = None

        largest_cluster = (
            max(cluster_sizes.values())
            if cluster_sizes
            else 0
        )

        #
        # Evaluate clustering quality only on
        # clustered samples (ignore DBSCAN noise)
        #

        valid_mask = labels != -1

        if (
            n_clusters >= 2
            and np.sum(valid_mask) >= 2
        ):

            try:

                X = feature_matrix[valid_mask]
                y = labels[valid_mask]

                silhouette = float(
                    silhouette_score(
                        X,
                        y,
                    )
                )

                davies_bouldin = float(
                    davies_bouldin_score(
                        X,
                        y,
                    )
                )

                calinski_harabasz = float(
                    calinski_harabasz_score(
                        X,
                        y,
                    )
                )

            except Exception as ex:

                logger.warning(
                    "Unable to compute clustering metrics: %s",
                    ex,
                )

        return ClusterStatistics(

            total_samples=total_samples,

            n_clusters=n_clusters,

            n_noise=n_noise,

            noise_ratio=noise_ratio,

            silhouette_score=silhouette,

            davies_bouldin_score=davies_bouldin,

            calinski_harabasz_score=calinski_harabasz,

            cluster_sizes=cluster_sizes,

            largest_cluster_size=largest_cluster,
        )
    
    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(
        self,
        path: Optional[str] = None,
    ) -> None:
        """
        save this clustering session/results.

        Parameters
        ----------
        path : Optional[str]
            Destination path.
            If None, configuration value is used.
        """

        if not self.is_fitted_:
            raise RuntimeError(
                "Cannot save an unfitted CampaignCluster."
            )

        if path is None:
            path = CAMPAIGN_CLUSTERING_CONFIG[
                "cluster_model_filename"
            ]

        os.makedirs(
            os.path.dirname(path),
            exist_ok=True,
        )

        joblib.dump(
            self,
            path,
        )

        logger.info(
            "CampaignCluster saved to %s",
            path,
        )

    @classmethod
    def load(
        cls,
        path: Optional[str] = None,
    ) -> "CampaignCluster":
        """
        Load a previously saved clustering model.

        Parameters
        ----------
        path : Optional[str]

        Returns
        -------
        CampaignCluster
        """

        if path is None:
            path = CAMPAIGN_CLUSTERING_CONFIG[
                "model_filename"
            ]

        model = joblib.load(path)

        logger.info(
            "CampaignCluster loaded from %s",
            path,
        )

        return model
    
    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get_cluster_labels(
        self,
    ) -> np.ndarray:
        """
        Return cluster labels.
        """

        if not self.is_fitted_:
            raise RuntimeError(
                "CampaignCluster has not been fitted."
            )

        return self.labels_
    
    def get_cluster_ids(
        self,
    ) -> List[int]:
        """
        Return discovered cluster IDs.

        Noise (-1) is excluded.
        """

        if not self.is_fitted_:
            raise RuntimeError(
                "CampaignCluster has not been fitted."
            )

        return sorted(
            cluster
            for cluster in np.unique(self.labels_)
            if cluster != -1
        )
    
    def get_noise_indices(
        self,
    ) -> List[int]:
        """
        Return indices of unclustered samples.
        """

        if not self.is_fitted_:
            raise RuntimeError(
                "CampaignCluster has not been fitted."
            )

        return np.where(
            self.labels_ == -1
        )[0].tolist()
    
    def get_cluster_members(
        self,
        cluster_id: int,
    ) -> List[int]:
        """
        Return row indices belonging to a cluster.

        Parameters
        ----------
        cluster_id : int

        Returns
        -------
        List[int]
        """

        if not self.is_fitted_:
            raise RuntimeError(
                "CampaignCluster has not been fitted."
            )

        return np.where(
            self.labels_ == cluster_id
        )[0].tolist()
    
    def get_cluster_count(self) -> int:
        """
        Return the number of discovered clusters.

        Noise (-1) is excluded.
        """

        if not self.is_fitted_:
            raise RuntimeError(
                "CampaignCluster has not been fitted."
            )

        return self.statistics_.n_clusters
    
    def get_noise_count(self) -> int:
        """
        Return the number of unclustered samples.
        """

        if not self.is_fitted_:
            raise RuntimeError(
                "CampaignCluster has not been fitted."
            )

        return self.statistics_.n_noise
    
    def get_noise_ratio(self) -> float:
        """
        Return the fraction of samples marked as unclustered.
        """

        if not self.is_fitted_:
            raise RuntimeError(
                "CampaignCluster has not been fitted."
            )

        return self.statistics_.noise_ratio
    
    def get_silhouette_score(
        self,
    ) -> Optional[float]:
        """
        Return clustering silhouette score.

        Returns
        -------
        Optional[float]
        """

        if not self.is_fitted_:
            raise RuntimeError(
                "CampaignCluster has not been fitted."
            )

        return self.statistics_.silhouette_score
    
    def get_davies_bouldin_score(self) -> Optional[float]:

        if not self.is_fitted_:
            raise RuntimeError(
                "CampaignCluster has not been fitted."
            )

        return self.statistics_.davies_bouldin_score


    def get_calinski_harabasz_score(self) -> Optional[float]:

        if not self.is_fitted_:
            raise RuntimeError(
                "CampaignCluster has not been fitted."
            )

        return self.statistics_.calinski_harabasz_score
    
    def get_summary(self) -> Dict:
        """
        Return clustering summary.
        """

        if not self.is_fitted_:
            raise RuntimeError(
                "CampaignCluster has not been fitted."
            )

        return {
            "total_samples":
                self.statistics_.total_samples,

            "clusters":
                self.statistics_.n_clusters,

            "unclustered":
                self.statistics_.n_noise,

            "noise_ratio":
                round(
                    self.statistics_.noise_ratio,
                    4,
                ),

            "cluster_sizes":
                self.statistics_.cluster_sizes,

            "silhouette_score":
                self.statistics_.silhouette_score,

            "davies_bouldin_score":
                self.statistics_.davies_bouldin_score,

            "calinski_harabasz_score":
                self.statistics_.calinski_harabasz_score,

            "largest_cluster":
                self.statistics_.largest_cluster_size,
        }
    
    def __repr__(self) -> str:

        if not self.is_fitted_:

            return (
                f"{self.__class__.__name__}("
                f"eps={self.eps}, "
                f"min_samples={self.min_samples}, "
                "status='Not Fitted')"
            )

        return (
            f"{self.__class__.__name__}("
            f"clusters={self.statistics_.n_clusters}, "
            f"unclustered={self.statistics_.n_noise}, "
            f"silhouette={self.statistics_.silhouette_score})"
        )
    
