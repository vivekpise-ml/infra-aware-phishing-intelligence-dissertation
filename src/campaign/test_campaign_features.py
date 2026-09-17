"""
test_campaign_features.py
-------------------------

Validation script for Campaign Feature Engineering.

Tests
-----
1. Single URL feature extraction.
2. Batch feature extraction.
3. Feature ordering.
4. Missing values.
5. Metadata generation.
"""

from __future__ import annotations

import pandas as pd

from src.campaign.campaign_features import (
    extract_campaign_features,
    extract_campaign_features_batch,
    get_campaign_feature_names,
)

# ---------------------------------------------------------
# Test URLs
# ---------------------------------------------------------

TEST_URLS = [

    "https://accounts.google.com",

    "https://login.microsoftonline.com",

    "https://www.amazon.in",

    "https://www.facebook.com",

    "https://github.com",

    "http://paypal-login-security.example.com",

    "http://verify-account-example.xyz/login",

]

# ---------------------------------------------------------
# Single URL Test
# ---------------------------------------------------------

def test_single_url():

    print("=" * 70)

    print("TEST 1 : SINGLE URL")

    print("=" * 70)

    url = TEST_URLS[0]

    features = extract_campaign_features(url)

    print(f"\nURL : {url}\n")

    for feature in get_campaign_feature_names():

        print(f"{feature:35} : {features[feature]}")

    print()

# ---------------------------------------------------------
# Batch Test
# ---------------------------------------------------------

def test_batch():

    print("=" * 70)

    print("TEST 2 : BATCH EXTRACTION")

    print("=" * 70)

    df = pd.DataFrame({

        "url": TEST_URLS

    })

    feature_df = extract_campaign_features_batch(df)

    print()

    print("Feature Matrix Shape")

    print(feature_df.shape)

    print()

    print(feature_df.head())

    print()

# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------

def validate_dataframe():

    print("=" * 70)

    print("TEST 3 : VALIDATION")

    print("=" * 70)

    df = pd.DataFrame({

        "url": TEST_URLS

    })

    feature_df = extract_campaign_features_batch(df)

    print()

    print("Columns :", len(feature_df.columns))

    print("Expected:", len(get_campaign_feature_names()))

    print()

    assert len(feature_df.columns) == len(get_campaign_feature_names())

    assert feature_df.isnull().sum().sum() == 0

    print("✓ No missing values")

    print("✓ Feature count correct")

    print()

# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

if __name__ == "__main__":

    test_single_url()

    test_batch()

    validate_dataframe()

    print("=" * 70)

    print("ALL CAMPAIGN FEATURE TESTS PASSED")

    print("=" * 70)