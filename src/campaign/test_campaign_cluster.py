"""
test_campaign_cluster.py
------------------------

End-to-end validation of the Campaign Clustering module.

Pipeline Tested
---------------

URLs
    │
    ▼
Campaign Feature Extraction
    │
    ▼
Feature Matrix
    │
    ▼
CampaignPreprocessor
    │
    ▼
Preprocessed Feature Matrix
    │
    ▼
DBSCAN    
    │
    ▼
Cluster Statistics

This test is intended for:

- Conference Evaluation
- Dissertation Evaluation
- DBSCAN Parameter Tuning
- Future HDBSCAN Comparison
"""

from __future__ import annotations

from collections import Counter

import pandas as pd


from src.campaign.campaign_features import (
    extract_campaign_features_batch,
    get_campaign_feature_names,
)

from src.campaign.campaign_preprocessor import (
    CampaignPreprocessor,
)

from src.campaign.campaign_cluster import (
    CampaignCluster,
)

# ==========================================================
# Test Dataset
# ==========================================================

TEST_URLS = [

    # --------------------------------------------------
    # Google
    # --------------------------------------------------

    "https://accounts.google.com",
    "https://mail.google.com",
    "https://drive.google.com",
    "https://docs.google.com",
    "https://photos.google.com",

    # --------------------------------------------------
    # Microsoft
    # --------------------------------------------------

    "https://login.microsoftonline.com",
    "https://outlook.live.com",
    "https://office.com",
    "https://azure.microsoft.com",

    # --------------------------------------------------
    # Amazon
    # --------------------------------------------------

    "https://amazon.in",
    "https://amazon.com",
    "https://aws.amazon.com",
    "https://sellercentral.amazon.in",

    # --------------------------------------------------
    # Facebook
    # --------------------------------------------------

    "https://facebook.com",
    "https://m.facebook.com",
    "https://business.facebook.com",

    # --------------------------------------------------
    # GitHub
    # --------------------------------------------------

    "https://github.com",
    "https://gist.github.com",

    # --------------------------------------------------
    # Benign
    # --------------------------------------------------

    "https://python.org",
    "https://wikipedia.org",
    "https://stackoverflow.com",
    "https://openai.com",

    # --------------------------------------------------
    # Phishing-looking URLs
    # --------------------------------------------------

    "http://paypal-login-security.example.com",
    "http://verify-account-example.xyz/login",
    "http://amazon-security-alert.xyz",
    "http://facebook-verification-login.ru",
    "http://secure-google-login-alert.top",
    "http://office365-login-update.xyz",
    "http://netflix-secure-login.info",
    "http://bank-account-update-login.xyz",
]

# ==========================================================
# Dataset
# ==========================================================

def create_test_dataframe() -> pd.DataFrame:
    """
    Build the input dataframe.
    """

    return pd.DataFrame({

        "url": TEST_URLS

    })


# ==========================================================
# Feature Extraction
# ==========================================================

def build_feature_matrix():

    print("=" * 70)
    print("FEATURE EXTRACTION")
    print("=" * 70)

    df = create_test_dataframe()

    feature_df = extract_campaign_features_batch(
        df
    )

    print()


    #distance_matrix = euclidean_distances(feature_df)

    print("URLs               :", len(df))

    print("Feature Count      :", len(feature_df.columns))

    print("Feature Matrix     :", feature_df.shape)

    print()

    return df, feature_df


# ==========================================================
# Feature Validation
# ==========================================================

def validate_feature_matrix(
    feature_df: pd.DataFrame,
):

    print("=" * 70)
    print("FEATURE VALIDATION")
    print("=" * 70)

    expected = len(
        get_campaign_feature_names()
    )

    actual = len(
        feature_df.columns
    )

    print()

    print("Expected Features :", expected)

    print("Actual Features   :", actual)

    print()

    assert expected == actual

    assert feature_df.isnull().sum().sum() == 0

    print("✓ Feature count OK")

    print("✓ No missing values")

    print()

    # ==========================================================
    # DBSCAN Training
    # ==========================================================

def train_campaign_clusters(
    feature_df: pd.DataFrame,
    eps: float,
    min_samples: int,
):
    """
    Train DBSCAN and obtain cluster labels.
    """

    print("=" * 70)
    print("DBSCAN TRAINING")
    print("=" * 70)

    print(f"eps         : {eps}")
    print(f"min_samples : {min_samples}")
    print()

    # ----------------------------------------------------------
    # Feature preprocessing
    # ----------------------------------------------------------

    preprocessor = CampaignPreprocessor()

    feature_matrix = preprocessor.fit_transform(
        feature_df
    )

    cluster = CampaignCluster(eps=eps, min_samples=min_samples,)

    labels = cluster.fit_predict(
        feature_matrix
    )

    #
    # Save the validated clustering configuration
    #
    
    cluster.save()

    preprocessor.save()

    print()

    print("Model trained successfully.")

    #print("Artifacts saved.")

    print()

    return cluster, labels

# ==========================================================
# DBSCAN Parameter Sweep
# ==========================================================

def sweep_dbscan_parameters(
    feature_df: pd.DataFrame,
    min_samples: int = 3,
):
    """
    Evaluate multiple eps values and identify
    the best DBSCAN configuration.
    """

    import pandas as pd

    eps_values = [
        1.2,
        1.4,
        1.6,
        1.8,
        2.0,
        2.2,
        2.4,
        2.6,
        2.8,
        3.0,
    ]

    results = []

    print("=" * 70)
    print("DBSCAN PARAMETER SWEEP")
    print("=" * 70)
    print()

    for min_samples in [2, 3, 4, 5]:

        print()
        print("=" * 70)
        print(f"min_samples = {min_samples}")
        print("=" * 70)

        for eps in eps_values:

            cluster, labels = train_campaign_clusters(
                feature_df,
                eps=eps,
                min_samples=min_samples,
            )

            stats = cluster.get_statistics()

            largest = (
                max(stats.cluster_sizes.values())
                if stats.cluster_sizes
                else 0
            )

            results.append({

                "min_samples": min_samples,

                "eps": eps,

                "clusters": stats.n_clusters,

                "noise": stats.n_noise,

                "noise_ratio": stats.noise_ratio,

                "largest_cluster": largest,

                "silhouette": stats.silhouette_score,

                "davies_bouldin":
                    getattr(
                        stats,
                        "davies_bouldin_score",
                        None,
                    ),

                "calinski_harabasz":
                    getattr(
                        stats,
                        "calinski_harabasz_score",
                        None,
                    ),
            })

    result_df = pd.DataFrame(results)

    print(
        result_df[
            [
                "min_samples",
                "eps",
                "clusters",
                "noise",
                "noise_ratio",
                "largest_cluster",
                "silhouette",
                "davies_bouldin",
                "calinski_harabasz",
            ]
        ].to_string(
            index=False,
            float_format=lambda x: f"{x:.4f}",
        )
    )

    result_df.to_csv(
        "reports/dbscan_parameter_sweep.csv",
        index=False,
    )

    print()
    print(
        "Results saved to "
        "reports/dbscan_parameter_sweep.csv"
    )
    print()

    return result_df

# ==========================================================
# Cluster Statistics
# ==========================================================

def print_cluster_statistics(
    cluster: CampaignCluster,
):
    """
    Print cluster statistics.
    """

    print("=" * 70)
    print("CLUSTER STATISTICS")
    print("=" * 70)

    stats = cluster.get_statistics()

    print()

    print("Total Samples     :", stats.total_samples)

    print("Noise Samples     :", stats.n_noise)

    print(    f"Noise Ratio       : "    f"{stats.noise_ratio:.2%}")

    print("Clusters Found    :", stats.n_clusters)

    print()

    print("Cluster Sizes")

    print("-" * 40)

    for cluster_id, size in stats.cluster_sizes.items():

        print(f"Cluster {cluster_id:2d} : {size} URLs")

    print()

    largest = (
        max(stats.cluster_sizes.values())
        if stats.cluster_sizes
        else 0
    )

    print("Largest Cluster   :", largest)

    print()

    if stats.silhouette_score is not None:

        print(
            f"Silhouette Score : "
            f"{stats.silhouette_score:.4f}"
        )

    else:

        print("Silhouette Score : Not Applicable")

    print()

    # ==========================================================
    # Cluster Explorer
    # ==========================================================

def print_cluster_members(
    df: pd.DataFrame,
    labels,
):
    """
    Display URLs belonging to each cluster.
    """

    print("=" * 70)
    print("CLUSTER MEMBERS")
    print("=" * 70)

    cluster_ids = sorted(

        set(labels) - {-1}

    )

    if not cluster_ids:

        print("\nNo clusters were discovered.\n")

        return

    for cluster_id in cluster_ids:

        print()

        print("-" * 70)

        print(f"Cluster {cluster_id}")

        print("-" * 70)

        members = df.loc[
            [l == cluster_id for l in labels],
            "url"
        ]

        for url in members:

            print(url)

    print()


# ==========================================================
# Unclustered URLs
# ==========================================================

def print_unclustered_urls(
    df: pd.DataFrame,
    labels,
):
    """
    Display URLs that DBSCAN could not assign
    to any campaign cluster.
    """

    print("=" * 70)
    print("UNCLUSTERED URLS")
    print("=" * 70)

    urls = df.loc[
        [l == -1 for l in labels],
        "url"
    ]

    if len(urls) == 0:

        print()

        print("None")

        print()

        return

    print()

    for url in urls:

        print(url)

    print()


# ==========================================================
# Final Summary
# ==========================================================

def print_summary(
    feature_df,
    cluster: CampaignCluster,
):
    stats = cluster.get_statistics()

    print("=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)

    print()

    print(
        f"URLs Analysed        : "
        f"{stats.total_samples}"
    )

    print(
        f"Features             : "
        f"{feature_df.shape[1]}"
    )

    print(
        f"Clusters Found       : "
        f"{stats.n_clusters}"
    )

    print(
        f"Unclustered URLs     : "
        f"{stats.n_noise}"
    )

    print()

    print("Campaign clustering test completed successfully.")

    print()


# ==========================================================
# Main
# ==========================================================

def main():

    print()

    print("=" * 70)
    print("CAMPAIGN CLUSTER EVALUATION")
    print("=" * 70)

    #
    # Feature Engineering
    #
    df, feature_df = build_feature_matrix()

    validate_feature_matrix(
        feature_df
    )

    #
    # DBSCAN
    #

    #
    # Parameter Sweep
    #

    results = sweep_dbscan_parameters(
        feature_df,
        min_samples=3,
    )

    print()
    print("=" * 70)
    print("BEST CONFIGURATION")
    print("=" * 70)

    valid_results = results[
        results["clusters"] >= 2
    ]

    best_row = valid_results.loc[
        valid_results["silhouette"].idxmax()
    ]

    best_eps = float(best_row["eps"])
    best_min_samples = int(best_row["min_samples"])

    print(f"Best eps         : {best_eps}")
    print(f"Best min_samples : {best_min_samples}")

    print()

    cluster_engine, labels = train_campaign_clusters(
        feature_df,
        eps=best_eps,
        min_samples=best_min_samples,
    )
    #
    # Statistics
    #

    print_cluster_statistics(

        cluster_engine,

    )

    #
    # Cluster Explorer
    #

    print_cluster_members(

        df,

        labels,

    )

    #
    # Unclustered URLs
    #

    print_unclustered_urls(

        df,

        labels,

    )

    #
    # Final Summary
    #
    
    print_summary(

        feature_df,

        cluster_engine,

    )


# ==========================================================
# Entry Point
# ==========================================================

if __name__ == "__main__":

    main()