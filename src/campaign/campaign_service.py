"""
campaign_service.py
-------------------

Service layer for Campaign Analysis.

This module serves as the public entry point for campaign analysis.
It orchestrates the campaign detection and report generation while
keeping Streamlit pages independent of the implementation details.

Responsibilities
----------------

1. Provide the public API for campaign analysis.
2. Coordinate campaign detection and reporting.
3. Return a standardized campaign analysis result.

This module intentionally contains no feature extraction,
preprocessing, clustering, reporting logic, or visualization.

This module intentionally contains minimal business logic.
"""

from __future__ import annotations

import pandas as pd

from src.campaign.campaign_detector import CampaignDetector
from src.campaign.campaign_report import CampaignReport


class CampaignService:
    """
    Public service layer for campaign analysis.

    Coordinates campaign detection and report generation while
    keeping callers independent of the underlying implementation.

    """

    def __init__(self):

        self.detector = CampaignDetector()
        self.report = CampaignReport()

    def analyze(
        self,
        df: pd.DataFrame,
        url_column: str = "url",
    ) -> dict:
        """
        Execute the complete campaign analysis workflow.

        This method orchestrates campaign detection followed by
        report generation and returns a standardized analysis report.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe containing URLs.

        url_column : str
            Name of URL column.

        Returns
        -------
        dict
            Complete campaign analysis report.
        """

        detection_result = self.detector.detect(
            df=df,
            url_column=url_column,
        )

        report = self.report.generate(
            detection_result
        )

        return report