"""
campaign_preprocessor.py

Preprocessing pipeline for campaign clustering.

This module converts raw campaign feature data into a machine-learning-ready
feature matrix suitable for DBSCAN clustering.

Responsibilities
----------------
1. Detect numeric and categorical columns.
2. Group infrequent categorical values using Top-N encoding.
3. One-Hot Encode categorical features.
4. Impute missing values.
5. Standardize numeric features.
6. Produce the final feature matrix.
7. Save and load the preprocessing pipeline.

Author:
    Vivek Pise

Project:
    Infrastructure-Aware Drift-Adaptive Multimodal Phishing Risk
    Intelligence Framework with Campaign-Level Analysis
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

import joblib
import numpy as np
import pandas as pd

import os

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import StandardScaler

from src.config import CAMPAIGN_CLUSTERING_CONFIG


# =============================================================================
# Logger
# =============================================================================

logger = logging.getLogger(__name__)

# =============================================================================
# Top-N Category Transformer
# =============================================================================

class TopNCategoryTransformer(BaseEstimator, TransformerMixin):
    """
    Groups infrequent categorical values into 'Other'.

    During fitting, the transformer learns the most frequent categories
    for each categorical column.

    During transformation, categories outside the learned Top-N are
    replaced with 'Other'.

    This helps:
        - Reduce one-hot dimensionality
        - Improve clustering stability
        - Reduce noise from rare categories
    """

    def __init__(
        self,
        top_n_config: Optional[Dict[str, int]] = None,
        fill_value: str = "Unknown",
    ):
        self.top_n_config = (
            top_n_config
            if top_n_config is not None
            else CAMPAIGN_CLUSTERING_CONFIG["top_n"]
        )

        self.fill_value = fill_value

        self.group_other_label = CAMPAIGN_CLUSTERING_CONFIG["group_other_label"]

        # learned during fit()
        self.top_categories_: Dict[str, set] = {}

    # -----------------------------------------------------------------

    def fit(self, X, y=None):
        """
        Learn Top-N categories for every categorical column.
        """

        if not isinstance(X, pd.DataFrame):
            raise TypeError(
                "TopNCategoryTransformer expects a pandas DataFrame."
            )

        self.top_categories_.clear()

        for column in X.columns:

            n = self.top_n_config.get(column)

            if n is None:
                # Keep every category
                values = (
                    X[column]
                    .fillna(self.fill_value)
                    .astype(str)
                    .unique()
                )

                self.top_categories_[column] = set(values)
                continue

            top_values = (
                X[column]
                .fillna(self.fill_value)
                .astype(str)
                .value_counts()
                .head(n)
                .index
            )

            self.top_categories_[column] = set(top_values)

            logger.info(
                "%s : retained top %d categories",
                column,
                len(top_values),
            )

        return self

    # -----------------------------------------------------------------

    def transform(self, X):
        """
        Replace infrequent categories with 'Other'.
        """

        if not isinstance(X, pd.DataFrame):
            raise TypeError(
                "TopNCategoryTransformer expects a pandas DataFrame."
            )

        X = X.copy()

        for column in X.columns:

            X[column] = (
                X[column]
                .fillna(self.fill_value)
                .astype(str)
            )

            allowed = self.top_categories_[column]

            X[column] = X[column].where(
                X[column].isin(allowed),
                other=self.group_other_label,
            )

        return X

    # -----------------------------------------------------------------

    def get_feature_names_out(self, input_features=None):
        """
        Returns original feature names.

        Required for sklearn compatibility.
        """

        if input_features is None:
            return np.array(list(self.top_categories_.keys()))

        return np.asarray(input_features)
    

# =============================================================================
# Campaign Preprocessor
# =============================================================================

class CampaignPreprocessor(BaseEstimator):
    """
    End-to-end preprocessing pipeline for campaign clustering.

    Responsibilities
    ----------------
    - Detect numeric and categorical columns
    - Apply Top-N grouping to categorical features
    - One-Hot Encode categorical features
    - Impute missing numeric values
    - Scale numeric features
    - Produce a DBSCAN-ready feature matrix
    """

    def __init__(
        self,
        top_n_config: Optional[Dict[str, int]] = None,
    ):

        self.top_n_config = (
            top_n_config
            if top_n_config is not None
            else CAMPAIGN_CLUSTERING_CONFIG["top_n"]
        )

        self.pipeline: Optional[ColumnTransformer] = None

        self.numeric_columns: List[str] = []

        self.categorical_columns: List[str] = []

        self.feature_names_: List[str] = []

        self.is_fitted = False

    def fit(self, feature_df: pd.DataFrame):
        """
        Fit preprocessing pipeline.
        """

        logger.info("Fitting campaign preprocessing pipeline...")

        if not isinstance(feature_df, pd.DataFrame):
            raise TypeError(
                "CampaignPreprocessor expects a pandas DatatraFrame."
            )

        self.numeric_columns = (
            feature_df
            .select_dtypes(include=np.number)
            .columns
            .tolist()
        )

        self.categorical_columns = (
            feature_df
            .select_dtypes(exclude=np.number)
            .columns
            .tolist()
        )

        logger.info(
            "Detected %d numeric columns.",
            len(self.numeric_columns),
        )

        logger.info(
            "Detected %d categorical columns.",
            len(self.categorical_columns),
        )

        numeric_pipeline = Pipeline(
            steps=[
                (
                    "imputer",
                    SimpleImputer(strategy="median"),
                ),
                (
                    "scaler",
                    StandardScaler(),
                ),
            ]
        )

        categorical_pipeline = Pipeline(
            steps=[
                (
                    "topn",
                    TopNCategoryTransformer(
                        top_n_config=self.top_n_config,
                        fill_value=CAMPAIGN_CLUSTERING_CONFIG["fill_value"],
                    ),
                ),
                (
                    "onehot",
                    OneHotEncoder(
                        handle_unknown=CAMPAIGN_CLUSTERING_CONFIG["handle_unknown"],
                        sparse_output=CAMPAIGN_CLUSTERING_CONFIG["sparse_output"],
                    ),
                ),
            ]
        )

        # Merge two pipelines 
        self.pipeline = ColumnTransformer(
            transformers=[
                (
                    "numeric",
                    numeric_pipeline,
                    self.numeric_columns,
                ),
                (
                    "categorical",
                    categorical_pipeline,
                    self.categorical_columns,
                ),
            ]
        )

        self.pipeline.fit(feature_df)

        self.feature_names_ = (
            self.pipeline.get_feature_names_out().tolist()
        )

        self.is_fitted = True

        logger.info(
            "Campaign preprocessing completed "
            "(numeric=%d, categorical=%d, output=%d).",
            len(self.numeric_columns),
            len(self.categorical_columns),
            len(self.feature_names_),
        )

        logger.info("Campaign preprocessor fitted successfully.")

        return self
    
    def transform(
        self,
        feature_df: pd.DataFrame,
    ) -> np.ndarray:
        """
        Transform raw feature dataframe.
        """

        if not self.is_fitted:
            raise RuntimeError(
                "CampaignPreprocessor has not been fitted."
            )
        
        if not isinstance(feature_df, pd.DataFrame):
            raise TypeError(
                "CampaignPreprocessor expects a pandas DataFrame."
            )

        return self.pipeline.transform(feature_df)
    
    def fit_transform(
        self,
        feature_df: pd.DataFrame,
    ) -> np.ndarray:

        return self.fit(feature_df).transform(feature_df)
    
    def get_feature_names(self) -> List[str]:

        if not self.is_fitted:
            raise RuntimeError(
                "CampaignPreprocessor has not been fitted."
            )

        return self.feature_names_
    
    def save(
        self,
        path: Optional[str] = None,
    ):

        if path is None:
            path = CAMPAIGN_CLUSTERING_CONFIG["preprocessor_filename"]


        os.makedirs(
            os.path.dirname(path),
            exist_ok=True,
        )

        joblib.dump(self, path)

        logger.info(
            "Campaign preprocessor saved to %s",
            path,
        )

    @classmethod
    def load(
        cls,
        path: str,
    ):

        logger.info(
            "Loading campaign preprocessor from %s",
            path,
        )

        return joblib.load(path)