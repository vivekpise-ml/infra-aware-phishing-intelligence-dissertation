"""
create_drift_reference.py
-------------------------

Utility to create a permanent stratified reference dataset
for statistical drift analysis.

This is executed only once.

Author : Vivek Pise
"""

from pathlib import Path

import pandas as pd

from src.config import DATA_PATH


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

OUTPUT_PATH = "data/kaggle/drift_reference.csv"

TOTAL_SAMPLES = 500

RANDOM_STATE = 42


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

benign_df = df[
    df["type"].str.lower() == "benign"
].sample(
    n=samples_per_class,
    random_state=RANDOM_STATE
)

malicious_df = df[
    df["type"].str.lower() == "malicious"
].sample(
    n=samples_per_class,
    random_state=RANDOM_STATE
)

reference_df = pd.concat(
    [benign_df, malicious_df],
    ignore_index=True
)

reference_df = reference_df.sample(
    frac=1,
    random_state=RANDOM_STATE
).reset_index(drop=True)

# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

Path("data").mkdir(
    parents=True,
    exist_ok=True
)

reference_df.to_csv(
    OUTPUT_PATH,
    index=False
)


# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------

print()

print("=" * 60)

print("Drift Reference Dataset Created")

print("=" * 60)

print(f"Output File : {OUTPUT_PATH}")

print(f"Total URLs  : {len(reference_df)}")

print()

print(reference_df["type"].value_counts())

print("=" * 60)

print(reference_df.columns.tolist())
print(reference_df["type"].value_counts())