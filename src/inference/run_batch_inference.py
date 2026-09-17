"""
run_batch_inference.py
----------------------

Batch inference orchestration.

Responsibilities
----------------
1. Execute batch phishing prediction.
2. Execute campaign detection.
3. Execute campaign risk assessment.
4. Return all results.

This module intentionally does NOT:
- extract features
- perform clustering
- compute prediction scores
- generate reports
- generate visualizations
"""

from __future__ import annotations

from typing import Dict

import pandas as pd

from src.inference.predictor import PhishingPredictor
from src.campaign.campaign_detector import CampaignDetector
from src.campaign.campaign_risk import CampaignRisk
from src.campaign.campaign_report import CampaignReport


def run_batch(
    df: pd.DataFrame,
    url_column: str = "url",
) -> Dict:
    """
    Execute complete batch phishing analysis.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe containing URLs.

    url_column : str
        URL column name.

    Returns
    -------
    Dict
        Complete batch analysis.
    """

    if df is None or df.empty:
        return {}

    if url_column not in df.columns:
        raise ValueError(
            f"Missing URL column '{url_column}'."
        )

    # -------------------------------------------------
    # Remove duplicate URLs
    # -------------------------------------------------

    original_count = len(df)

    df = (
        df
        .drop_duplicates(subset=[url_column], keep="first")
        .reset_index(drop=True)
    )

    duplicates_removed = original_count - len(df)

    print("\n========== BATCH INPUT ==========")
    print(f"Original URLs          : {original_count}")
    print(f"Unique URLs            : {len(df)}")
    print(f"Duplicate URLs removed : {duplicates_removed}")

    if duplicates_removed > 0:
        print(
            "INFO: Duplicate URLs detected in the input "
            "and removed before batch analysis."
        )

    # -------------------------------------------------
    # Batch prediction
    # -------------------------------------------------

    predictor = PhishingPredictor()

    prediction_results = predictor.predict_batch(
        df[[url_column]]
    )

    # -------------------------------------------------
    # Campaign detection
    # -------------------------------------------------

    detector = CampaignDetector()

    campaign_results = detector.detect(
        df=df,
        url_column=url_column,
    )

    # -------------------------------------------------
    # Merge prediction results into campaign dataframe
    # -------------------------------------------------

    campaign_df = campaign_results["campaign_dataframe"]

    prediction_df = pd.DataFrame(prediction_results)[
        [
            "url",
            "label",
            "model_risk",
            "final_risk",
            "risk_tier",
        ]
    ]

    campaign_df = campaign_df.merge(
        prediction_df,
        on="url",
        how="left",
        validate="one_to_one",
    )

    campaign_results["campaign_dataframe"] = campaign_df

    # -------------------------------------------------
    # Campaign risk assessment
    # -------------------------------------------------

    risk_engine = CampaignRisk()

    campaign_risk = risk_engine.assess(
        prediction_results=prediction_results,
        campaign_results=campaign_results,
    )

    # -------------------------------------------------
    # Attach campaign risk summary to detector output
    # -------------------------------------------------

    campaign_results["campaign_summary"] = (
        campaign_risk["campaign_summary"]
    )

    report_generator = CampaignReport()

    campaign_report = report_generator.generate(
        campaign_results
    )

    # -------------------------------------------------
    # Return
    # -------------------------------------------------

    return {

        "prediction_results": prediction_results,

        "campaign_results": campaign_report,

        "campaign_risk": campaign_risk,

    }