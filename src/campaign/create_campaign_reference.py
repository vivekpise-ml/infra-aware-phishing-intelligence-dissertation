"""
create_campaign_reference.py
----------------------------

Creates a permanent stratified reference dataset for
Campaign Intelligence evaluation.

This script is executed only once.

Author : Vivek Pise
"""

from pathlib import Path

import pandas as pd

from src.config import DATA_PATH


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

OUTPUT_PATH = "data/campaign_reference.csv"

TOTAL_SAMPLES = 500

# Different from drift_reference.py
RANDOM_STATE = 123


# ---------------------------------------------------------
# Validate Configuration
# ---------------------------------------------------------

if TOTAL_SAMPLES % 2 != 0:
    raise ValueError(
        "TOTAL_SAMPLES must be an even number."
    )


# ---------------------------------------------------------
# Load Dataset
# ---------------------------------------------------------

print("Loading dataset...")

df = pd.read_csv(DATA_PATH)

print(f"Original Dataset : {len(df):,} URLs")


# ---------------------------------------------------------
# Validate Label Column
# ---------------------------------------------------------

if "type" not in df.columns:
    raise ValueError("Column 'type' not found.")


# ---------------------------------------------------------
# Normalize Labels
# ---------------------------------------------------------

df["type"] = (
    df["type"]
    .astype(str)
    .str.lower()
    .str.strip()
)


# ---------------------------------------------------------
# Stratified Sampling
# ---------------------------------------------------------

samples_per_class = TOTAL_SAMPLES // 2

print()
print("Creating stratified campaign evaluation dataset...")

benign_df = (
    df[df["type"] == "benign"]
    .sample(
        n=samples_per_class,
        random_state=RANDOM_STATE,
    )
)

malicious_df = (
    df[df["type"] == "malicious"]
    .sample(
        n=samples_per_class,
        random_state=RANDOM_STATE,
    )
)

campaign_df = pd.concat(
    [benign_df, malicious_df],
    ignore_index=True,
)

# Shuffle the combined dataset
campaign_df = (
    campaign_df
    .sample(
        frac=1,
        random_state=RANDOM_STATE,
    )
    .reset_index(drop=True)
)


# ---------------------------------------------------------
# Save Dataset
# ---------------------------------------------------------

Path("data/kaggle").mkdir(
    parents=True,
    exist_ok=True,
)

campaign_df.to_csv(
    OUTPUT_PATH,
    index=False,
)


# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------

print()
print("=" * 60)
print("Campaign Reference Dataset Created")
print("=" * 60)
print(f"Output File : {OUTPUT_PATH}")
print(f"Total URLs  : {len(campaign_df)}")
print()

print("Class Distribution")
print("------------------")
print(campaign_df["type"].value_counts())

print()
print("Columns")
print("-------")
print(campaign_df.columns.tolist())

print("=" * 60)