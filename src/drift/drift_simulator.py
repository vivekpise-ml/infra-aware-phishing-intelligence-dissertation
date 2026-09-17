"""
drift_simulator.py

Feature-aware Drift Simulator

Generates synthetic drifted datasets by modifying a configurable
percentage of URLs while leaving the remaining URLs unchanged.

The original dataset is NEVER modified.

Author : Vivek Pise
Project: Infrastructure-Aware Drift-Adaptive Multimodal
         Phishing Risk Intelligence Framework
"""

from pathlib import Path
import random

import pandas as pd


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

PHISHING_WORDS = [
    "login",
    "verify",
    "account",
    "update",
    "secure",
    "bank",
    "signin",
    "wallet",
    "payment",
    "confirm"
]

# ------------------------------------------------------------
# Feature Groups
#
# Documentation mapping between simulated drift categories
# and the engineered lexical features expected to be affected.
# ------------------------------------------------------------

FEATURE_GROUPS = {

    "query_length": [
        "query_length",
        "equal_count",
        "question_count"
    ],

    "path_depth": [
        "path_depth",
        "slash_count"
    ],

    "url_length": [
        "url_length",
        "letter_count",
        "digit_count"
    ],

    "keywords": [
        "kw_login",
        "kw_bank",
        "kw_verify",
        "kw_secure"
    ],

    "entropy": [
        "url_entropy",
        "domain_entropy"
    ]
}


# ------------------------------------------------------------
# URL Modification Functions
# ------------------------------------------------------------

def add_query(url):

    connector = "&" if "?" in url else "?"

    return url + connector + "id=123"


def add_path(url):

    return url.rstrip("/") + "/verify/account"


def add_length(url):

    return url.rstrip("/") + "/abcdefghijklmnopqrstuvwxyz"


def add_keywords(url):

    words = "/".join(
        random.sample(PHISHING_WORDS, 3)
    )

    return url.rstrip("/") + "/" + words


def add_entropy(url):

    random_string = "".join(

        random.choices(

            "abcdefghijklmnopqrstuvwxyz0123456789",

            k=25

        )

    )

    return url.rstrip("/") + "/" + random_string


# ------------------------------------------------------------
# Apply Feature Drift
# ------------------------------------------------------------

def modify_url(url, target_features):

    if not isinstance(url, str):
        return url

    modified = url

    if "query_length" in target_features:
        modified = add_query(modified)

    if "path_depth" in target_features:
        modified = add_path(modified)

    if "url_length" in target_features:
        modified = add_length(modified)

    if "keywords" in target_features:
        modified = add_keywords(modified)

    if "entropy" in target_features:
        modified = add_entropy(modified)

    return modified


# ------------------------------------------------------------
# Drift Simulation
# ------------------------------------------------------------

def simulate_drift(
    input_csv,
    output_csv,
    drift_percentage,
    target_features,
    url_column="url",
    random_state=42
):
    """
    Generate a synthetic drifted dataset.

    Parameters
    ----------
    input_csv : str

    output_csv : str

    drift_percentage : int
        Percentage of URLs to modify.

    target_features : list
        High-level feature groups to perturb.
    """

    random.seed(random_state)

    df = pd.read_csv(input_csv)

    drift_df = df.copy()

    total_rows = len(df)

    rows_to_modify = int(
        total_rows * drift_percentage / 100
    )

    selected_rows = random.sample(
        list(df.index),
        rows_to_modify
    )

    print("=" * 65)
    print("FEATURE-AWARE DRIFT SIMULATION")
    print("=" * 65)

    print(f"Dataset Size      : {total_rows}")
    print(f"Rows Modified     : {rows_to_modify}")
    print(f"Drift Percentage  : {drift_percentage}%")

    print("\nTarget Feature Groups")

    for group in target_features:

        print(f"\n{group}")

        for feature in FEATURE_GROUPS.get(group, []):

            print(f"   - {feature}")

    print("\nApplying drift...")

    for idx in selected_rows:

        drift_df.at[idx, url_column] = modify_url(

            drift_df.at[idx, url_column],

            target_features

        )

    Path(output_csv).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    drift_df.to_csv(
        output_csv,
        index=False
    )

    print("\nSaved :", output_csv)

    print("=" * 65)


# ------------------------------------------------------------
# Generate Experimental Drift Datasets
# ------------------------------------------------------------

if __name__ == "__main__":

    # LOW DRIFT
    simulate_drift(

        input_csv="data/kaggle/balanced_urls.csv",

        output_csv="data/drift/current_low_drift.csv",

        drift_percentage=10,

        target_features=[
            "query_length"
        ]
    )

    # MEDIUM DRIFT
    simulate_drift(

        input_csv="data/kaggle/balanced_urls.csv",

        output_csv="data/drift/current_medium_drift.csv",

        drift_percentage=30,

        target_features=[
            "query_length",
            "path_depth",
            "url_length"
        ]
    )

    # HIGH DRIFT
    simulate_drift(

        input_csv="data/kaggle/balanced_urls.csv",

        output_csv="data/drift/current_high_drift.csv",

        drift_percentage=60,

        target_features=[
            "query_length",
            "path_depth",
            "url_length",
            "keywords",
            "entropy"
        ]
    )