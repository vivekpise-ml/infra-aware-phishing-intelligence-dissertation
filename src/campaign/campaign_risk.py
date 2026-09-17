"""
campaign_risk.py
----------------

Campaign-level risk assessment.

This module combines URL-level prediction results with
campaign clustering results to produce campaign-level
risk intelligence.

Responsibilities
----------------
1. Merge prediction and campaign outputs.
2. Compute campaign-level risk metrics.
3. Return structured campaign risk results.

This module intentionally does NOT:
- rerun prediction
- rerun clustering
- generate reports
- generate visualizations
"""

from __future__ import annotations

from typing import Dict

import pandas as pd


class CampaignRisk:
    """
    Campaign-level risk assessment engine.
    """

    def assess(
        self,
        prediction_results: list,
        campaign_results: Dict,
    ) -> Dict:
        """
        Assess campaign-level risk.

        Parameters
        ----------
        prediction_results
            Output from predictor.predict_batch()

        campaign_results
            Output from CampaignDetector.detect()

        Returns
        -------
        Dict
            Campaign risk analysis.
        """

        if not prediction_results:
            return {}

        if not campaign_results:
            return {}

        campaign_df = campaign_results["campaign_dataframe"].copy()

        prediction_lookup = {

            item["url"]: item

            for item in prediction_results

        }

        campaign_df["model_risk"] = campaign_df["url"].map(
            lambda url: prediction_lookup[url]["model_risk"]
        )

        campaign_df["final_risk"] = campaign_df["url"].map(
            lambda url: prediction_lookup[url]["final_risk"]
        )

        campaign_df["label"] = campaign_df["url"].map(
            lambda url: prediction_lookup[url]["label"]
        )

        valid_campaigns = campaign_df[
            campaign_df["campaign_id"] != -1
        ]

        campaign_summary = (
            valid_campaigns
            .groupby("campaign_id")
            .agg(
                url_count=("url", "count"),
                average_model_risk=("model_risk", "mean"),
                average_final_risk=("final_risk", "mean"),
                max_final_risk=("final_risk", "max"),
                malicious_urls=("label",
                                lambda s: (s == "malicious").sum()),
                suspicious_urls=("label",
                                 lambda s: (s == "suspicious").sum()),
            )
            .reset_index()
        )

        # -------------------------------------------------
        # Determine campaign type
        # -------------------------------------------------

        def determine_campaign_type(row):

            benign = (
                row["url_count"]
                - row["malicious_urls"]
                - row["suspicious_urls"]
            )

            malicious = row["malicious_urls"]
            suspicious = row["suspicious_urls"]

            if malicious == row["url_count"]:
                return "Malicious"

            if benign == row["url_count"]:
                return "Benign"

            if suspicious == row["url_count"]:
                return "Suspicious"

            return "Mixed"


        campaign_summary["campaign_type"] = (
            campaign_summary.apply(
                determine_campaign_type,
                axis=1,
            )
        )

        return {

            "campaign_dataframe": campaign_df,

            "campaign_summary": campaign_summary,

        }