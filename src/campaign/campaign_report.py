"""
campaign_report.py
------------------

Campaign report generator.

This module converts the raw output from CampaignDetector into a
standardized report dictionary for use by Streamlit, JSON export,
and future reporting components.

Responsibilities
----------------
1. Format campaign detection results.
2. Compute high-level summary statistics.
3. Return a consistent report structure.

This module intentionally does NOT perform feature extraction,
clustering or visualization.
"""

from __future__ import annotations

from typing import Dict


class CampaignReport:
    """
    Generate a standardized campaign analysis report.
    """

    def generate(
        self,
        detection_result: Dict,
    ) -> Dict:
        """
        Generate campaign report.

        Parameters
        ----------
        detection_result : dict
            Output produced by CampaignDetector.

        Returns
        -------
        dict
            Standardized campaign report.
        """

        campaign_df = detection_result["campaign_dataframe"]

        campaign_count = detection_result["campaign_count"]
        largest_campaign = detection_result["largest_campaign_size"]
        noise_urls = detection_result["noise_urls"]
        campaign_sizes = detection_result["campaign_sizes"]
        cluster_labels = detection_result["cluster_labels"]

        cluster_statistics = detection_result["cluster_statistics"]

        silhouette_score = detection_result["silhouette_score"]

        cluster_summary = detection_result["cluster_summary"]

        # -------------------------------------------------
        # Campaign Risk Summary (optional)
        # -------------------------------------------------

        campaign_summary = detection_result.get(
            "campaign_summary",
            None,
        )

        total_urls = len(campaign_df)

        clustered_urls = total_urls - noise_urls

        noise_percentage = (
            (noise_urls / total_urls) * 100
            if total_urls > 0
            else 0.0
        )

        average_campaign_size = (
            clustered_urls / campaign_count
            if campaign_count > 0
            else 0.0
        )

        return {

            # -------------------------------------------------
            # URL-Level Results
            # -------------------------------------------------
            "campaign_dataframe": campaign_df,

            # -------------------------------------------------
            # Summary Statistics
            # -------------------------------------------------
            "summary": {

                "total_urls": total_urls,

                "campaign_count": campaign_count,

                "clustered_urls": clustered_urls,

                "noise_urls": noise_urls,

                "noise_percentage": round(
                    noise_percentage,
                    2
                ),

                "largest_campaign_size": largest_campaign,

                "average_campaign_size": round(
                    average_campaign_size,
                    2
                ),

                "silhouette_score": silhouette_score,
            },

            # -------------------------------------------------
            # Campaign Details
            # -------------------------------------------------
            "campaign_sizes": campaign_sizes,

            "cluster_labels": cluster_labels,

            "cluster_statistics": cluster_statistics,

            "cluster_summary": cluster_summary,

            # -------------------------------------------------
            # Campaign Risk
            # -------------------------------------------------
            "campaign_summary": campaign_summary,
        }