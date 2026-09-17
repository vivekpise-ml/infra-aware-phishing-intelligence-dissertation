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

sys.path.append(ROOT_DIR)

# ------------------------------------------------
# Imports
# ------------------------------------------------

from src.inference.run_inference import run

from src.campaign.campaign_service import CampaignService
from src.campaign.campaign_visualizer import CampaignVisualizer

from src.drift.drift_service import DriftService

from src.config import DATA_PATH

# ------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------

st.set_page_config(
    page_title="Batch Analysis",
    layout="wide"
)

st.title("📄 Batch URL Analysis")

st.caption(
    "Analyze multiple URLs using the Infrastructure-Aware "
    "Phishing Risk Intelligence Framework."
)

st.markdown("---")

st.info(
    "Upload a CSV file containing a column named **url**."
)

uploaded_file = st.file_uploader(
    "Upload CSV",
    type=["csv"]
)

# ------------------------------------------------
# PROCESS CSV
# ------------------------------------------------

if uploaded_file is not None:

    try:

        df = pd.read_csv(uploaded_file)

        # --------------------------------------------
        # Detect URL column
        # --------------------------------------------

        url_column = next(

            (
                col
                for col in df.columns
                if "url" in col.lower()
            ),

            None

        )

        if url_column is None:

            st.error(
                "❌ No column containing 'url' was found."
            )

            st.stop()

        urls = df[url_column].astype(str)

        st.success(f"Loaded {len(urls)} URLs")

        progress = st.progress(0)

        results = []

        # --------------------------------------------
        # Analyze each URL
        # --------------------------------------------

        for index, url in enumerate(urls):

            try:

                result = run(url)

                results.append({

                    "URL": url,

                    "Prediction": result["label"],

                    "Model Risk": round(
                        result["model_risk"], 4
                    ),

                    "Final Risk": round(
                        result["final_risk"], 4
                    ),

                    "Risk Tier": result["risk_tier"]

                })

            except Exception:

                results.append({

                    "URL": url,

                    "Prediction": "ERROR",

                    "Model Risk": None,

                    "Final Risk": None,

                    "Risk Tier": None

                })

            progress.progress(
                (index + 1) / len(urls)
            )

        # --------------------------------------------
        # Results
        # --------------------------------------------

        results_df = pd.DataFrame(results)

        # ------------------------------------------------
        # Campaign Discovery
        # ------------------------------------------------

        campaign_service = CampaignService()

        campaign_report = campaign_service.analyze(

            df.rename(
                columns={
                    url_column: "url"
                }
            )

        )

        campaign_df = campaign_report["campaign_dataframe"]

        campaign_summary = campaign_report["summary"]

        results_df = results_df.merge(

            campaign_df[
                [
                    "url",
                    "campaign_id",
                    "is_noise"
                ]
            ],

            left_on="URL",

            right_on="url",

            how="left"

        )

        results_df.drop(
            columns=["url"],
            inplace=True
        )

        results_df["Campaign"] = results_df["campaign_id"].apply(

            lambda x:
                "Unclustered"
                if x == -1
                else f"Campaign-{x+1}"

        )

        results_df["Status"] = results_df["is_noise"].apply(

            lambda x:
                "Unclustered"
                if x
                else "Clustered"

        )

        results_df.drop(

            columns=[
                "campaign_id",
                "is_noise"
            ],

            inplace=True

        )

        st.markdown("---")

        st.subheader("Analysis Results")

        st.dataframe(

            results_df,

            use_container_width=True

        )

        # --------------------------------------------
        # Summary
        # --------------------------------------------

        st.subheader("Summary")

        st.markdown("### Campaign Summary")

        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(

                "Campaigns",

                campaign_summary["campaign_count"]

            )

        with c2:

            st.metric(

                "Clustered URLs",

                campaign_summary["clustered_urls"]

            )

        with c3:

            st.metric(

                "Unclustered URLs",

                campaign_summary["noise_urls"]

            )

        st.markdown("---")

        col1, col2, col3 = st.columns(3)

        benign = (
            results_df["Prediction"]
            .str.lower()
            .eq("benign")
            .sum()
        )

        suspicious = (
            results_df["Prediction"]
            .str.lower()
            .eq("suspicious")
            .sum()
        )

        malicious = (
            results_df["Prediction"]
            .str.lower()
            .eq("malicious")
            .sum()
        )

        col1.metric(
            "Benign",
            benign
        )

        col2.metric(
            "Suspicious",
            suspicious
        )

        col3.metric(
            "Malicious",
            malicious
        )

        # --------------------------------------------
        # Download
        # --------------------------------------------

        visualizer = CampaignVisualizer()

        st.subheader("Campaign Size Distribution")

        fig = visualizer.plot_campaign_sizes(

            campaign_report

        )

        if fig is not None:

            st.pyplot(fig)

        st.subheader("Clustered vs Unclustered")

        fig = visualizer.plot_noise_distribution(

            campaign_report

        )

        if fig is not None:

            st.pyplot(fig)


        # ------------------------------------------------
        # Drift Analysis
        # ------------------------------------------------

        with st.spinner("Running statistical drift analysis..."):

            reference_df = pd.read_csv(
                "data/drift_reference.csv"
            )

            drift_service = DriftService()

            drift_output = drift_service.analyze(

                reference_dataset=reference_df,

                current_dataset=df.rename(
                    columns={
                        url_column: "url"
                    }
                )

            )

            drift_report = drift_output["drift_result"]

        st.markdown("### Drift Summary")

        d1, d2, d3 = st.columns(3)

        with d1:

            st.metric(

                "Drift Score",

                f"{drift_report['overall_score']:.3f}"

            )

        with d2:

            st.metric(

                "Status",

                drift_report["severity"]

            )

        with d3:

            st.metric(

                "Retraining Recommendation",

                "Review"
                if drift_report["requires_retraining"]
                else "NO"

            )

        st.markdown("---")

        st.subheader("Drift Analysis")

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(

                "PSI",

                f"{drift_report['psi']:.4f}"

            )

        with col2:

            st.metric(

                "JS Distance",

                f"{drift_report['js_distance']:.4f}"

            )

        with col3:

            st.metric(

                "KL Divergence",

                f"{drift_report['kl_divergence']:.4f}"

            )
        
        st.subheader("Top Drifting Features")

        st.dataframe(
            pd.DataFrame(
                drift_report["top_drifting_features"]
            ),
            use_container_width=True,
            height=250
        )

        
        st.download_button(

            label="⬇ Download Results CSV",

            data=results_df.to_csv(
                index=False
            ).encode("utf-8"),

            file_name="batch_analysis_results.csv",

            mime="text/csv"

        )

    except Exception as e:

        st.exception(e)