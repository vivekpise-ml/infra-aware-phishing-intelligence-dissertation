"""
test_drift.py

Standalone validation script for the Drift Detection module.

Workflow
--------
Load Full Dataset
        │
Create Stratified Sample
        │
Split into Reference & Current
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

TEST_SIZE = 0.30

RANDOM_STATE = 42

LABEL_COLUMN = "type"


# ----------------------------------------------------------
# Main
# ----------------------------------------------------------

def main():

    print("=" * 70)
    print("        DRIFT DETECTION VALIDATION")
    print("=" * 70)

    # ------------------------------------------------------
    # Load Dataset
    # ------------------------------------------------------

    print("\nLoading dataset...")

    df = pd.read_csv(DATA_PATH)

    print(f"Original Dataset Size : {len(df)}")

    print("\nOriginal Class Distribution")

    print(df[LABEL_COLUMN].value_counts())

    # ------------------------------------------------------
    # Create Stratified Sample
    # ------------------------------------------------------

    sample_dataset, _ = train_test_split(

        df,

        train_size=SAMPLE_SIZE,

        random_state=RANDOM_STATE,

        stratify=df[LABEL_COLUMN]

    )

    print(f"\nSampled Dataset Size : {len(sample_dataset)}")

    print("\nSample Class Distribution")

    print(sample_dataset[LABEL_COLUMN].value_counts())

    # ------------------------------------------------------
    # Split into Reference / Current
    # ------------------------------------------------------

    reference_dataset, current_dataset = train_test_split(

        sample_dataset,

        test_size=TEST_SIZE,

        random_state=RANDOM_STATE,

        stratify=sample_dataset[LABEL_COLUMN]

    )

    print("\nReference Samples :", len(reference_dataset))

    print("Current Samples   :", len(current_dataset))

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

        reference_name="Balanced URLs - Reference",

        current_name="Balanced URLs - Current",

        save_json=True,

        report_path="reports/drift_report.json"

    )

    # ------------------------------------------------------
    # Console Summary
    # ------------------------------------------------------

    print()

    print_drift_summary(drift_result)

    print("\nJSON Report Saved Successfully")

    print("reports/drift_report.json")

    print("\nDrift Detection Validation Completed Successfully.")

    print("=" * 70)


# ----------------------------------------------------------
# Entry Point
# ----------------------------------------------------------

if __name__ == "__main__":

    main()