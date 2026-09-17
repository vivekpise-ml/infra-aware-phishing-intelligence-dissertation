"""
drift_service.py

Service layer for statistical drift detection.

Responsibilities
----------------
- Feature extraction from datasets
- Drift analysis orchestration
- Report generation
- JSON report persistence

This module acts as the integration layer between the
feature extraction pipeline and the statistical drift
detector.

Author : Vivek Pise
Project: Infrastructure-Aware Drift-Adaptive Multimodal
         Phishing Risk Intelligence Framework
"""

from pathlib import Path
from typing import Dict, Optional
import time

import joblib

import pandas as pd
from src.config import MODEL_DIR

from src.features_with_infra import (
    extract_url_features,
    extract_html_features,
    extract_domain_in_features_with_infra
)

from src.infrastructure.infra_features import (
    collect_infrastructure_features,
    FEATURE_SECTION_DATA
)

from .drift_detector import (
    compute_drift_score,
    save_drift_report
)


def single_url_drift_status():
    """
    Placeholder used for single URL prediction.

    Real statistical drift requires comparison between
    reference and current datasets and is therefore
    performed only from the Drift Analysis module.
    """

    return {
        "score": 0.05,
        "status": "STABLE",
        "severity": "STABLE",
        "retraining_required": False,
        "recommendation": (
            "Single URL analysis does not perform "
            "statistical drift detection."
        )
    }


class DriftService:
    """
    Service class for dataset drift analysis.
    """

    def __init__(self):
        """
        Initialize Drift Service.

        Loads the feature names used during model training so that
        extracted features are aligned exactly as expected by the
        trained XGBoost model.
        """

        self.feature_names = joblib.load(
            f"{MODEL_DIR}/xgb_infra_feature_names.pkl"
        )
    
    # -------------------------------------------------------------
    # Canonical Feature Sourcing
    # -------------------------------------------------------------
    def extract_canonical_features(
        self,
        url,
        html=None
    ) -> Dict:
        """
        Build the same infrastructure-aware feature representation
        used by the Prediction training/inference pipeline.

        Feature sourcing follows the canonical project architecture:

        URL features
        + HTML features
        + Infrastructure DATA features

        This method replaces the legacy direct call to
        extract_all_features() while preserving the final 92-feature
        schema expected by the trained model.
        """

        # ---------------------------------------------------------
        # URL features
        # ---------------------------------------------------------
        url_features = extract_url_features(url)

        # ---------------------------------------------------------
        # HTML features
        # ---------------------------------------------------------
        html_features = extract_html_features(html)

        # ---------------------------------------------------------
        # Infrastructure features
        # ---------------------------------------------------------
        domain = extract_domain_in_features_with_infra(url)

        infra_result = collect_infrastructure_features(
            domain,
            FEATURE_SECTION_DATA
        )

        infra_features = infra_result.get(
            "features",
            {}
        )

        # ---------------------------------------------------------
        # Merge feature sources
        # ---------------------------------------------------------
        features = {}

        features.update(url_features)
        features.update(html_features)
        features.update(infra_features)

        return features

    # -------------------------------------------------------------
    # Feature Extraction
    # -------------------------------------------------------------

   
    def extract_features(
        self,
        dataframe: pd.DataFrame,
        url_column: str = "url",
        html_column: Optional[str] = None,
        dataset_label: str = "DATASET"
    ) -> pd.DataFrame:
        """
        Extract features from a dataframe of URLs.

        Parameters
        ----------
        dataframe : pd.DataFrame

        url_column : str

        html_column : str or None

        Returns
        -------
        pd.DataFrame
        """

        feature_rows = []

        # -------------------------------------------------------------
        # Progress tracking
        # -------------------------------------------------------------

        total = len(dataframe)
        start_time = time.time()

        print(
            f"[DriftService] Starting feature extraction for "
            f"{dataset_label}: {total} URLs",
            flush=True
        )

        for processed, (_, row) in enumerate(
            dataframe.iterrows(),
            start=1
        ):

            url = row[url_column]

            html = None

            if html_column is not None and html_column in dataframe.columns:
                html = row[html_column]

            # -----------------------------------------------------
            # Canonical infrastructure-aware feature sourcing
            # -----------------------------------------------------
            features = self.extract_canonical_features(
                url,
                html
            )

            feature_rows.append(features)

            # ---------------------------------------------------------
            # Progress / ETA
            # ---------------------------------------------------------

            if processed % 10 == 0 or processed == total:

                elapsed = time.time() - start_time

                rate = (
                    processed / elapsed
                    if elapsed > 0
                    else 0
                )

                remaining = total - processed

                eta_seconds = (
                    remaining / rate
                    if rate > 0
                    else 0
                )

                percentage = (
                    (processed / total) * 100
                    if total > 0
                    else 100
                )

                print(
                    f"[DriftService] {dataset_label}: "
                    f"{processed}/{total} "
                    f"({percentage:.1f}%) | "
                    f"Remaining: {remaining} | "
                    f"Rate: {rate:.3f} URLs/s | "
                    f"ETA: {eta_seconds / 60:.1f} min",
                    flush=True
                )

        #return pd.DataFrame(feature_rows)

        feature_df = pd.DataFrame(feature_rows)

        # -------------------------------------------------------------
        # Align features with training feature set
        # -------------------------------------------------------------

        feature_df = feature_df.reindex(
            columns=self.feature_names,
            fill_value=0
        )

        missing = set(self.feature_names) - set(feature_df.columns)

        extra = set(feature_df.columns) - set(self.feature_names)

        if extra:
            print(f"[DriftService] Warning: Ignoring extra features: {extra}")

        if missing:
            print(f"[DriftService] Warning: Missing features filled with 0: {missing}")

        # Ensure all features are numeric
        feature_df = feature_df.apply(
            pd.to_numeric,
            errors="coerce"
        ).fillna(0)

        return feature_df
    

    # -------------------------------------------------------------
    # Detect Feature Dataset
    # -------------------------------------------------------------
    def is_feature_dataset(self, dataframe: pd.DataFrame) -> bool:
        """
        Returns True if the uploaded dataset already contains
        extracted model features.
        """

        return all(
            feature in dataframe.columns
            for feature in self.feature_names
        )

    # -------------------------------------------------------------
    # Load Persisted Feature Dataset
    # -------------------------------------------------------------
    def load_feature_dataset(
        self,
        dataset_name: str
    ) -> Optional[pd.DataFrame]:
        """
        Load a previously persisted Drift feature dataset.

        The cached dataset is reused only when all trained model
        features are present. Otherwise None is returned and the
        dataset is rebuilt using the canonical feature pipeline.
        """

        cache_dir = Path("data/feature_cache")

        feature_path = cache_dir / f"{dataset_name}_features.csv"

        if not feature_path.exists():
            return None

        try:

            feature_df = pd.read_csv(
                feature_path
            )

            if not self.is_feature_dataset(feature_df):
                print(
                    "[DriftService] Persisted feature dataset "
                    "schema mismatch. Rebuilding."
                )

                return None

            feature_df = feature_df[
                self.feature_names
            ].copy()

            feature_df = feature_df.apply(
                pd.to_numeric,
                errors="coerce"
            ).fillna(0)

            return feature_df

        except Exception as exc:

            print(
                "[DriftService] Unable to load persisted "
                f"feature dataset: {exc}"
            )

            return None

    # -------------------------------------------------------------
    # Build Feature Dataset (if required)
    # -------------------------------------------------------------
    def prepare_feature_dataset(
        self,
        dataframe: pd.DataFrame,
        dataset_name: str = "dataset",
        dataset_label: str = "DATASET"
    ) -> pd.DataFrame:

        if self.is_feature_dataset(dataframe):

            print("Feature dataset detected.")

            feature_df = dataframe[self.feature_names].copy()

        else:

            # -----------------------------------------------------
            # Try persisted Drift feature dataset first
            # -----------------------------------------------------
            cached_feature_df = self.load_feature_dataset(
                dataset_name
            )

            if cached_feature_df is not None:

                print(
                    "Persisted Drift feature dataset detected. "
                    "Reusing cached features."
                )

                feature_df = cached_feature_df

            else:

                print(
                    "Raw dataset detected. Building feature dataset "
                    "(reusing infrastructure cache where available)..."
                )

                feature_df = self.extract_features(
                    dataframe,
                    dataset_label=dataset_label
                )

                # Automatically cache extracted features
                self.save_feature_dataset(
                    feature_df,
                    dataset_name
                )

        if "url" not in feature_df.columns:
            feature_df.insert(
                0,
                "url",
                dataframe["url"].values
            )
        

        return feature_df
    

    # -------------------------------------------------------------
    # Save Feature Dataset
    # -------------------------------------------------------------
    def save_feature_dataset(
        self,
        feature_df: pd.DataFrame,
        dataset_name: str
    ) -> Path:
        """
        Save extracted feature dataset for future reuse.

        Parameters
        ----------
        feature_df : pd.DataFrame
            Extracted feature dataset.

        dataset_name : str
            Original dataset name (without extension).

        Returns
        -------
        Path
            Saved feature dataset path.
        """

        cache_dir = Path("data/feature_cache")
        cache_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        output_path = cache_dir / f"{dataset_name}_features.csv"

        feature_df.to_csv(
            output_path,
            index=False
        )

        return output_path


    # -------------------------------------------------------------
    # Drift Analysis
    # -------------------------------------------------------------

    def analyze(
        self,
        reference_dataset: pd.DataFrame,
        current_dataset: pd.DataFrame,
        bins: int = 10,
        top_n: int = 10,
        reference_name: str = "Training Dataset",
        current_name: str = "Current Dataset",
        save_json: bool = False,
        report_path: str = "reports/drift_report.json"
    ) -> Dict:
        """
        Perform complete drift analysis.
        """

        print("\n========================================")
        print("Starting Drift Analysis")
        print("========================================")

        # ---------------------------------------------------------
        # Prepare feature datasets (extract if required)
        # ---------------------------------------------------------

        print(
            f"[DriftService] Preparing REFERENCE dataset: "
            f"{len(reference_dataset)} URLs",
            flush=True
        )

        reference_features = self.prepare_feature_dataset(
            reference_dataset,
            reference_name.replace(" ", "_").lower(),
            dataset_label="REFERENCE"
        )

        print(
            f"[DriftService] Preparing CURRENT dataset: "
            f"{len(current_dataset)} URLs",
            flush=True
        )

        current_features = self.prepare_feature_dataset(
            current_dataset,
            current_name.replace(" ", "_").lower(),
            dataset_label="CURRENT"
        )

        # ---------------------------------------------------------
        # Compute drift
        # ---------------------------------------------------------

        drift_result = compute_drift_score(

            reference_features=reference_features,

            current_features=current_features,

            bins=bins,

            top_n=top_n,

            reference_name=reference_name,

            current_name=current_name

        )

        # ---------------------------------------------------------
        # Save JSON report
        # ---------------------------------------------------------

        if save_json:

            Path(report_path).parent.mkdir(
                parents=True,
                exist_ok=True
            )

            save_drift_report(
                drift_result,
                report_path
            )

        print("Drift Analysis Completed")

        # ---------------------------------------------------------
        # Return everything needed by Streamlit
        # ---------------------------------------------------------

        return {

            "drift_result": drift_result,

            "reference_features": reference_features,

            "current_features": current_features

        }