"""
campaign_visualizer.py
----------------------

Visualization utilities for Campaign Analysis.

Provides publication-quality visualizations for:

1. Campaign Size Distribution
2. Clustered vs Noise Distribution
3. Top Campaigns
"""

from typing import Dict, Optional

from src.campaign.campaign_utils import (
    format_campaign_name,
)

import matplotlib.pyplot as plt


class CampaignVisualizer:
    """
    Generate publication-quality visualizations for campaign analysis.

    This class consumes the standardized report produced by
    CampaignService and does not perform feature extraction,
    preprocessing, clustering, or reporting.

    """

    # ------------------------------------------------------------------
    # Campaign Size Distribution
    # ------------------------------------------------------------------

    def plot_campaign_sizes(self, report: Dict) -> Optional[plt.Figure]:

        if not report:
            return None

        campaign_sizes = report["campaign_sizes"]

        campaign_count = report["summary"]["campaign_count"]

        # ---------------------------------------------------------
        # No campaigns
        # ---------------------------------------------------------

        if campaign_count == 0:

            return None

        # ---------------------------------------------------------
        # Single campaign
        # ---------------------------------------------------------

        if campaign_count == 1:

            return None

        # ---------------------------------------------------------
        # Multiple campaigns
        # ---------------------------------------------------------

        labels = [
            format_campaign_name(cid)
            for cid in campaign_sizes.keys()
        ]

        values = list(campaign_sizes.values())

        fig_height = max(
            2.5,
            min(6.0, campaign_count * 0.6)
        )

        fig, ax = plt.subplots(
            figsize=(8, fig_height)
        )

        bars = ax.barh(
            labels,
            values,
            height=0.35
        )

        # Value labels

        for bar in bars:

            width = bar.get_width()

            ax.text(
                width + 0.3,
                bar.get_y() + bar.get_height()/2,
                f"{int(width)}",
                va="center",
                fontsize=10
            )

        ax.set_xlabel("URLs")

        ax.set_title("Campaign Size Distribution")

        ax.margins(y=0.15)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        fig.tight_layout()

        return fig

    '''    
    # ------------------------------------------------------------------
    # Noise vs Clustered
    # ------------------------------------------------------------------

    def plot_noise_distribution(self, report):

        summary = report["summary"]
        if summary["total_urls"] < 30:

            return None

        clustered = summary["clustered_urls"]
        noise = summary["noise_urls"]

        #fig, ax = plt.subplots(figsize=(3.5, 3.5))

        total_urls = summary["total_urls"]

        if total_urls < 100:
            fig_size = 3.0
        elif total_urls < 500:
            fig_size = 3.5
        else:
            fig_size = 4.2

        fig, ax = plt.subplots(figsize=(fig_size, fig_size))

        ax.pie(
            [clustered, noise],
            labels=[
                f"Clustered ({clustered})",
                f"Unclustered ({noise})"
            ],
            autopct="%1.1f%%",
            startangle=90,
            radius=0.75,
            textprops={"fontsize": 10}
        )

        #ax.set_title("Campaign Clustering Result")

        ax.set_title(
            "Campaign Clustering Result",
            fontsize=12,
            fontweight="normal",
            pad=10
        )

        #fig.tight_layout()

        fig.subplots_adjust(
            left=0.20,
            right=0.80,
            top=0.85,
            bottom=0.10
        )

        return fig
    '''
    # ------------------------------------------------------------------
    # Clustered vs Unclustered
    # ------------------------------------------------------------------

    def plot_noise_distribution(self, report: Dict) -> Optional[plt.Figure]:

        if not report:
            return None

        summary = report["summary"]

        #cluster_statistics = report["cluster_statistics"]

        if summary["total_urls"] < 30:
            return None

        clustered = summary["clustered_urls"]
        unclustered = summary["noise_urls"]

        total = clustered + unclustered

        clustered_pct = clustered / total * 100
        unclustered_pct = unclustered / total * 100

        # --------------------------------------------------------
        # Publication-quality horizontal stacked bar
        # --------------------------------------------------------

        fig, ax = plt.subplots(figsize=(8, 1.5))

        # Clustered section
        ax.barh(
            y=[""],
            width=[clustered],
            height=0.45,
            color="#4C72B0",
            label="Clustered"
        )

        # Unclustered section
        ax.barh(
            y=[""],
            width=[unclustered],
            left=[clustered],
            height=0.45,
            color="#DD8452",
            label="Unclustered"
        )

        # --------------------------------------------------------
        # Labels inside bars
        # --------------------------------------------------------

        ax.text(
            clustered / 2,
            0,
            f"Clustered\n{clustered}\n({clustered_pct:.1f}%)",
            ha="center",
            va="center",
            color="white",
            fontsize=10,
            fontweight="bold"
        )

        ax.text(
            clustered + unclustered / 2,
            0,
            f"Unclustered\n{unclustered}\n({unclustered_pct:.1f}%)",
            ha="center",
            va="center",
            color="white",
            fontsize=10,
            fontweight="bold"
        )

        # --------------------------------------------------------
        # Cosmetics
        # --------------------------------------------------------

        ax.set_xlim(0, total)

        ax.set_yticks([])

        ax.set_xlabel("Number of URLs")

        ax.set_title(
            "Campaign Clustering Result",
            fontsize=13,
            pad=8
        )

        '''
        ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, 1.18),
            ncol=2,
            frameon=False,
            fontsize=10
        )
        '''

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)

        fig.tight_layout()

        return fig

    # ------------------------------------------------------------------
    # Top Campaigns
    # ------------------------------------------------------------------

    def plot_top_campaigns(self, report: Dict) -> Optional[plt.Figure]:

        if not report:
            return None
        
        campaign_sizes = report["campaign_sizes"]

        if len(campaign_sizes) <= 1:
            return None
        
        top = sorted(
            campaign_sizes.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        labels = [
            format_campaign_name(cid)
            for cid, _ in top
        ]

        values = [
            size
            for _, size in top
        ]

        #fig, ax = plt.subplots(figsize=(7, 4))

        num = len(top)

        fig_height = max(
            2.0,
            min(5.0, num * 0.55)
        )

        fig, ax = plt.subplots(
            figsize=(8, fig_height)
        )

        #ax.barh(labels, values)

        bars = ax.barh(
                    labels,
                    values,
                    height=0.35
                )

        # Add value labels
        for i, value in enumerate(values):
            ax.text(
                value + 0.5,
                i,
                str(value),
                va="center",
                fontsize=10
            )

        ax.invert_yaxis()

        ax.set_xlabel("Number of URLs")

        ax.set_title("Top Campaigns")

        ax.margins(y=0.15)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        fig.tight_layout()

        return fig