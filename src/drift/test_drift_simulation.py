"""
test_drift_simulation.py

Validate drift detection using a synthetically drifted dataset.

Workflow
--------
Reference Dataset (Original)
        │
Stratified Sampling
        │
Current Dataset (Drifted)
        │
Stratified Sampling
        │
Feature Extraction
        │
Statistical Drift Analysis
        │
Console Summary
        │
JSON Report

Author : Vivek Pise
Project: Infrastructure-Aware Drift-Adaptive Multimodal
         Phishing Risk Intelligence Framework
"""

import pandas as pd
from sklearn.model_selection import train_test_split

from src.config import DATA_PATH
from src.drift.drift_service import DriftService
from src.drift.drift_detector import print_drift_summary


# ----------------------------------------------------------
# Configuration
# ----------------------------------------------------------

SAMPLE_SIZE = 1500

RANDOM_STATE = 42

LABEL_COLUMN = "type"

# ----------------------------------------------------------
# Drift Dataset
# Change only this line for LOW / MEDIUM / HIGH experiments
# ----------------------------------------------------------

CURRENT_DATASET = "data/drift/current_low_drift.csv"

# Examples:
#
# CURRENT_DATASET = "data/drift/current_low_drift.csv"
#
# CURRENT_DATASET = "data/drift/current_medium_drift.csv"
#
# CURRENT_DATASET = "data/drift/current_high_drift.csv"


# ----------------------------------------------------------
# Main
# ----------------------------------------------------------

def main():

    print("=" * 70)
    print("      DRIFT SIMULATION VALIDATION")
    print("=" * 70)

    # ------------------------------------------------------
    # Load datasets
    # ------------------------------------------------------

    print("\nLoading reference dataset...")

    reference_df = pd.read_csv(DATA_PATH)

    print(f"Reference Dataset Size : {len(reference_df)}")

    print("\nLoading drifted dataset...")

    current_df = pd.read_csv(CURRENT_DATASET)

    print(f"Current Dataset Size : {len(current_df)}")

    # ------------------------------------------------------
    # Stratified sampling
    # ------------------------------------------------------

    reference_dataset, _ = train_test_split(

        reference_df,

        train_size=SAMPLE_SIZE,

        random_state=RANDOM_STATE,

        stratify=reference_df[LABEL_COLUMN]

    )

    current_dataset, _ = train_test_split(

        current_df,

        train_size=SAMPLE_SIZE,

        random_state=RANDOM_STATE,

        stratify=current_df[LABEL_COLUMN]

    )

    print("\nReference Sample Size :", len(reference_dataset))

    print("Current Sample Size   :", len(current_dataset))

    print("\nReference Class Distribution")

    print(reference_dataset[LABEL_COLUMN].value_counts())

    print("\nCurrent Class Distribution")

    print(current_dataset[LABEL_COLUMN].value_counts())

    # ------------------------------------------------------
    # Drift Analysis
    # ------------------------------------------------------

    print("\n" + "=" * 70)
    print("Running Drift Analysis...")
    print("=" * 70)

    service = DriftService()

    drift_result = service.analyze(

        reference_dataset=reference_dataset,

        current_dataset=current_dataset,

        reference_name="Balanced URLs (Reference)",

        current_name=CURRENT_DATASET,

        save_json=True,

        report_path="reports/drift_simulation_report.json"

    )

    # ------------------------------------------------------
    # Console Summary
    # ------------------------------------------------------

    print()

    print_drift_summary(drift_result)

    print("\nJSON Report Saved Successfully")

    print("reports/drift_simulation_report.json")

    print("\nDrift Simulation Validation Completed Successfully.")

    print("=" * 70)


# ----------------------------------------------------------
# Entry Point
# ----------------------------------------------------------

if __name__ == "__main__":

    main()