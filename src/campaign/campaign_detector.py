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

DEBUG = False
DEBUG_CLUSTER_OUTPUT = True

from src.campaign.campaign_cluster import CampaignCluster

from src.campaign.campaign_features import (
    extract_campaign_features_batch,
)

from src.campaign.campaign_preprocessor import (
    CampaignPreprocessor,
)

from src.campaign.campaign_utils import (
    calculate_campaign_sizes,
    calculate_noise_count,
)

from src.campaign.campaign_characterizer import (
    characterize_campaigns,
)

class CampaignDetector:
    """
    Campaign detection engine based on DBSCAN clustering.
    """

    def __init__(self):

        self.preprocessor = CampaignPreprocessor()
        
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

        if DEBUG:
                
            ##
            # TEmporary for debug
            ##
            print("\n" + "=" * 80)
            print("RAW FEATURE DATAFRAME")
            print("=" * 80)

            print("\nColumns:")
            for c in feature_df.columns:
                print(c)

            print("\nData Types:")
            print(feature_df.dtypes)

            print("\nCategorical Columns:")
            print(feature_df.select_dtypes(exclude="number").columns.tolist())

            print("\nNumeric Columns:")
            print(feature_df.select_dtypes(include="number").columns.tolist())

        # -------------------------------------------------
        # Preprocess campaign features
        # -------------------------------------------------

        feature_matrix = self.preprocessor.fit_transform(
            feature_df
        )

        if DEBUG:
            ##
            # Temporary Debug
            ##
            print("\n" + "=" * 80)
            print("PREPROCESSOR OUTPUT")
            print("=" * 80)

            print("Feature Matrix Shape :", feature_matrix.shape)

            print("\nFinal Feature Names:")

            for i, name in enumerate(self.preprocessor.get_feature_names()):
                print(f"{i+1:3d}. {name}")        

            print("\nNumeric Columns :", len(self.preprocessor.numeric_columns))
            print("Categorical Columns :", len(self.preprocessor.categorical_columns))
            print("Final Output Features :", len(self.preprocessor.get_feature_names()))


        # -------------------------------------------------
        # Perform clustering
        # -------------------------------------------------

        labels = self.cluster_engine.fit_predict(
            feature_matrix
        )


        # -------------------------------------------------
        # Build URL-level campaign dataframe
        # -------------------------------------------------

        # Retain all extracted campaign features so that
        # downstream campaign characterization can operate
        # directly on the engineered feature space.

        campaign_df = feature_df.reset_index(drop=True).copy()

        campaign_df[url_column] = df[url_column].values

        campaign_df["campaign_id"] = labels

        campaign_df["is_noise"] = (
            campaign_df["campaign_id"] == -1
        )

        # -------------------------------------------------
        # Campaign characterization
        # -------------------------------------------------

        campaign_characterization = characterize_campaigns(
            campaign_df
        )

        # -------------------------------------------------
        # Campaign statistics
        # -------------------------------------------------

        '''
        valid_campaigns = campaign_df[
            campaign_df["campaign_id"] != -1
        ]

        
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

        cluster_statistics = (
            self.cluster_engine.get_statistics()
        )

        if DEBUG_CLUSTER_OUTPUT:

            print("\n" + "=" * 70)
            print("CLUSTER STATISTICS")
            print("=" * 70)

            stats = cluster_statistics

            print()
            print(f"Total Samples     : {stats.total_samples}")
            print(f"Noise Samples     : {stats.n_noise}")
            print(f"Clusters Found    : {stats.n_clusters}")

            print()
            print("Cluster Sizes")
            print("-" * 40)

            for cluster_id, size in sorted(stats.cluster_sizes.items()):
                print(f"Cluster {cluster_id:2d} : {size} URLs")

            print()

            print(f"Largest Cluster   : {largest_campaign_size}")

            print()

            if stats.silhouette_score is not None:
                print(f"Silhouette Score  : {stats.silhouette_score:.4f}")
            else:
                print("Silhouette Score  : N/A")

            print()

        if DEBUG_CLUSTER_OUTPUT:

            print("=" * 70)
            print("CLUSTER MEMBERS")
            print("=" * 70)

            if campaign_count == 0:

                print("\nNo campaign clusters discovered.\n")

            else:

                for campaign_id in sorted(campaign_sizes):

                    print()
                    print("-" * 70)
                    print(f"Cluster {campaign_id}")
                    print("-" * 70)

                    members = campaign_df.loc[
                        campaign_df["campaign_id"] == campaign_id,
                        url_column,
                    ]

                    for url in members:
                        print(url)

                print()

        if DEBUG_CLUSTER_OUTPUT:

            print("=" * 70)
            print("UNCLUSTERED URLS")
            print("=" * 70)

            noise_urls = campaign_df.loc[
                campaign_df["campaign_id"] == -1,
                url_column,
            ]

            print()

            if len(noise_urls) == 0:

                print("None")

            else:

                for url in noise_urls:
                    print(url)

            print()

        if DEBUG_CLUSTER_OUTPUT:

            print("=" * 70)
            print("FINAL SUMMARY")
            print("=" * 70)

            print()

            print(f"URLs Analysed      : {len(campaign_df)}")
            print(f"Raw Features       : {feature_df.shape[1]}")
            print(f"Clusters Found     : {campaign_count}")
            print(f"Unclustered URLs   : {noise_count}")

            print()

            print("Campaign detection completed successfully.")

            print()

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

            "cluster_statistics": cluster_statistics,

            "silhouette_score":
                self.cluster_engine.get_silhouette_score(),

            "cluster_summary":
                self.cluster_engine.get_summary(),

            "campaign_characterization":
                campaign_characterization,

        }