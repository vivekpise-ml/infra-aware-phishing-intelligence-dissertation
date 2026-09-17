"""
test_campaign.py
----------------

Standalone test script for the Campaign Analysis module.

This script validates the complete campaign pipeline:

    CSV Dataset
        ↓
CampaignService
        ↓
CampaignDetector
        ↓
CampaignCluster
        ↓
CampaignReport

Run:

    python -m src.campaign.test_campaign
"""

from __future__ import annotations

import pandas as pd

from src.config import DATA_PATH
from src.campaign.campaign_service import CampaignService


def main():
    """
    Execute Campaign Analysis test.
    """

    print("=" * 70)
    print("Campaign Analysis Test")
    print("=" * 70)

    # ---------------------------------------------------------
    # Load Dataset
    # ---------------------------------------------------------

    df = pd.read_csv(DATA_PATH)

    print(f"\nDataset loaded : {len(df)} URLs")

    if "url" not in df.columns:
        raise ValueError("Dataset must contain a 'url' column.")

    # ---------------------------------------------------------
    # Sample Dataset
    # ---------------------------------------------------------

    sample_size = min(500, len(df))

    df = df.sample(
        n=sample_size,
        random_state=42
    ).reset_index(drop=True)

    print(f"Using sample   : {sample_size} URLs")

    # ---------------------------------------------------------
    # Campaign Analysis
    # ---------------------------------------------------------

    service = CampaignService()

    report = service.analyze(
        df=df,
        url_column="url"
    )

    summary = report["summary"]

    print("\n")
    print("=" * 70)
    print("Campaign Summary")
    print("=" * 70)

    print(f"Total URLs             : {summary['total_urls']}")
    print(f"Campaigns Detected     : {summary['campaign_count']}")
    print(f"Clustered URLs         : {summary['clustered_urls']}")
    print(f"Noise URLs             : {summary['noise_urls']}")
    print(f"Noise Percentage       : {summary['noise_percentage']:.2f}%")
    print(f"Largest Campaign       : {summary['largest_campaign_size']}")
    print(f"Average Campaign Size  : {summary['average_campaign_size']:.2f}")

    print("\n")
    print("=" * 70)
    print("Campaign Sizes")
    print("=" * 70)

    campaign_sizes = report["campaign_sizes"]

    if campaign_sizes:

        for campaign_id, size in campaign_sizes.items():
            print(f"Campaign {campaign_id:>3} : {size} URLs")

    else:

        print("No campaigns detected.")

    print("\n")
    print("=" * 70)
    print("Sample Campaign Assignments")
    print("=" * 70)

    campaign_df = report["campaign_dataframe"]

    print(
        campaign_df[
            [
                "url",
                "campaign_id",
                "is_noise"
            ]
        ].head(15)
    )

    print("\n")
    print("=" * 70)
    print("Campaign Analysis Completed Successfully")
    print("=" * 70)


if __name__ == "__main__":
    main()