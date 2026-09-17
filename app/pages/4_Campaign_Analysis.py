"""
4_Campaign_Analysis.py
----------------------

Streamlit page for Campaign Analysis.

This page performs infrastructure-aware phishing campaign discovery
using DBSCAN clustering.

Features
--------
1. Upload URL dataset
2. Campaign Summary
3. Campaign Visualizations
4. Campaign Explorer
5. Campaign Assignment Table
6. Download Results
"""

import sys
import os
import pandas as pd
import streamlit as st

# ------------------------------------------------
# Ensure project root is in PYTHONPATH
# ------------------------------------------------

ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)


from src.campaign.campaign_service import CampaignService
from src.campaign.campaign_visualizer import CampaignVisualizer


# ---------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Campaign Analysis",
    page_icon="🕸️",
    layout="wide"
)

st.title("🕸️ Campaign Analysis")

st.markdown(
    """
Discover phishing campaigns using infrastructure-aware
DBSCAN clustering.
"""
)

# ---------------------------------------------------------------------
# Upload Dataset
# ---------------------------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload CSV containing URLs",
    type=["csv"]
)

if uploaded_file is not None:

    df = pd.read_csv(uploaded_file)

    if "url" not in df.columns:
        st.error("CSV must contain a 'url' column.")
        st.stop()

    st.success(f"Loaded {len(df)} URLs.")

    # ---------------------------------------------------------
    # Campaign Analysis
    # ---------------------------------------------------------

    with st.spinner("Running Campaign Analysis..."):

        campaign_service = CampaignService()

        report = campaign_service.analyze(
            df=df,
            url_column="url"
        )

    summary = report["summary"]

    campaign_df = report["campaign_dataframe"]

    visualizer = CampaignVisualizer()

    cluster_statistics = report["cluster_statistics"]

    # ---------------------------------------------------------
    # Campaign Summary
    # ---------------------------------------------------------

    st.divider()

    st.subheader("📊 Campaign Summary")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Campaigns Detected",
            summary["campaign_count"]
        )

        if summary["campaign_count"] > 1:

            st.metric(
                "Largest Campaign",
                summary["largest_campaign_size"]
            )

    with col2:

        st.metric(
            "Clustered URLs",
            summary["clustered_urls"]
        )

        st.metric(
            "Unclustered URLs",
            summary["noise_urls"]
        )

    with col3:

        st.metric(
            "Unclustered %",
            f"{summary['noise_percentage']:.2f}%"
        )

        if summary["campaign_count"] > 1:

            st.metric(
                "Average Campaign Size",
                f"{summary['average_campaign_size']:.2f}"
            )

    # ---------------------------------------------------------
    # Clustering Quality
    # ---------------------------------------------------------

    st.divider()

    st.subheader(" Clustering Quality")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Silhouette Score",
            f"{cluster_statistics.silhouette_score:.3f}"
        )

    with col2:
        st.metric(
            "Davies-Bouldin Index",
            f"{cluster_statistics.davies_bouldin_score:.3f}"
        )

    with col3:
        st.metric(
            "Calinski-Harabasz Index",
            f"{cluster_statistics.calinski_harabasz_score:.1f}"
        )

    st.markdown("""
        **Interpretation**

        - **Silhouette ↑**: Higher is better (ideal ≈ 1)
        - **Davies–Bouldin ↓**: Lower is better (ideal ≈ 0)
        - **Calinski–Harabasz ↑**: Higher indicates better-defined, compact clusters
        """)
    
    # ---------------------------------------------------------
    # Visualizations
    # ---------------------------------------------------------

    st.divider()

    # ---------------------------------------------------------
    # Campaign Size Distribution
    # ---------------------------------------------------------

    st.subheader("📈 Campaign Size Distribution")

    fig = visualizer.plot_campaign_sizes(report)

    if fig is not None:

        st.pyplot(fig)

    else:

        if summary["campaign_count"] == 1:

            campaign_size = next(
                iter(report["campaign_sizes"].values())
            )

            st.table(
                pd.DataFrame({
                    "Campaign": ["Campaign-1"],
                    "URLs": [campaign_size]
                })
            )

        else:

            st.info("No campaigns detected.")

    # ---------------------------------------------------------
    # Clustered vs Unclustered
    # ---------------------------------------------------------

    st.subheader("📉 Clustered vs Unclustered")

    fig = visualizer.plot_noise_distribution(report)

    if fig is not None:

        st.pyplot(fig)

    else:

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "Clustered URLs",
                summary["clustered_urls"]
            )

        with col2:

            st.metric(
                "Unclustered URLs",
                summary["noise_urls"]
            )

    # ---------------------------------------------------------
    # Top Campaigns
    # ---------------------------------------------------------

    # Show only when there are enough campaigns to make the
    # ranking meaningful.

    if summary["campaign_count"] > 5:

        st.subheader("🏆 Top Campaigns")

        fig = visualizer.plot_top_campaigns(report)

        if fig is not None:

            st.pyplot(fig)
            
    st.divider()
    
    # ---------------------------------------------------------
    # Campaign Explorer
    # ---------------------------------------------------------

    st.subheader("🔍 Campaign Explorer")

    valid_campaigns = sorted(
        campaign_df.loc[
            campaign_df["campaign_id"] != -1,
            "campaign_id"
        ].unique()
    )

    if valid_campaigns:

        campaign_display = {
            f"Campaign-{cid + 1}": cid
            for cid in valid_campaigns
        }

        selected_label = st.selectbox(
            "Select Campaign",
            list(campaign_display.keys())
        )

        selected_campaign = campaign_display[selected_label]

        selected_df = campaign_df[
            campaign_df["campaign_id"] == selected_campaign
        ].reset_index(drop=True)

        st.markdown("### Campaign Statistics")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Campaign",
                f"Campaign-{selected_campaign + 1}"
            )

        with col2:
            st.metric(
                "URLs",
                len(selected_df)
            )

        with col3:

            unique_domains = (
                selected_df["url"]
                .astype(str)
                .str.extract(r"https?://([^/]+)", expand=False)
                .fillna(selected_df["url"])
                .nunique()
            )

            st.metric(
                "Unique Domains",
                unique_domains
            )

        st.markdown("### URLs in Selected Campaign")

        display_selected_df = selected_df.copy()

        display_selected_df["Campaign"] = display_selected_df["campaign_id"].apply(
            lambda x: "Unclustered"
            if x == -1
            else f"Campaign-{x + 1}"
        )

        display_selected_df["Status"] = display_selected_df["campaign_id"].apply(
            lambda x: "Unclustered"
            if x == -1
            else "Clustered"
        )

        display_selected_df = display_selected_df.drop(
            columns=["campaign_id", "is_noise"]
        )

        st.dataframe(
            display_selected_df,
            use_container_width=True,
            height=350
        )

    else:

        st.info(
            "No campaigns detected. All URLs were classified as DBSCAN noise."
        )

    # ---------------------------------------------------------
    # Full Campaign Assignment Table
    # ---------------------------------------------------------

    st.divider()

    st.subheader("📋 Complete Campaign Assignment Table")

    display_df = campaign_df.copy()

    display_df["Campaign"] = display_df["campaign_id"].apply(
        lambda x: "Unclustered"
        if x == -1
        else f"Campaign-{x + 1}"
    )

    display_df["Status"] = display_df["campaign_id"].apply(
        lambda x: "Unclustered"
        if x == -1
        else "Clustered"
    )

    # Remove internal DBSCAN columns from UI
    display_df = display_df.drop(
        columns=["campaign_id", "is_noise"]
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        height=450
    )

    # ---------------------------------------------------------
    # Download Results
    # ---------------------------------------------------------

    st.divider()

    csv = campaign_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="⬇ Download Campaign Results",
        data=csv,
        file_name="campaign_results.csv",
        mime="text/csv"
    )