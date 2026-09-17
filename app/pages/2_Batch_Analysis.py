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

from src.inference.run_batch_inference import run_batch

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

        # --------------------------------------------
        # Batch Inference
        # --------------------------------------------

        with st.spinner("Running batch analysis..."):

            batch_result = run_batch(

                df.rename(
                    columns={
                        url_column: "url"
                    }
                ),

                url_column="url",
            )

        prediction_results = batch_result[
            "prediction_results"
        ]

        campaign_results = batch_result[
            "campaign_results"
        ]

        campaign_risk = batch_result[
            "campaign_risk"
        ]

        results_df = pd.DataFrame(prediction_results)[
            [
                "url",
                "label",
                "model_risk",
                "final_risk",
                "risk_tier",
            ]
        ]

        results_df.rename(

            columns={

                "url": "URL",

                "label": "Prediction",

                "model_risk": "Model Risk",

                "final_risk": "Final Risk",

                "risk_tier": "Risk Tier",

            },

            inplace=True,

        )
        
        results_df.rename(

            columns={

                "url": "URL",

                "label": "Prediction",

                "model_risk": "Model Risk",

                "final_risk": "Final Risk",

                "risk_tier": "Risk Tier",

            },

            inplace=True,

        )

        # ------------------------------------------------
        # Campaign Discovery
        # ------------------------------------------------

        campaign_df = campaign_results[
            "campaign_dataframe"
        ]

        campaign_summary = campaign_results[
            "summary"
        ]

        campaign_report = campaign_results
        
        results_df = results_df.merge(

            campaign_df[
                [
                    "url",
                    "campaign_id",
                    "is_noise",
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

        # ------------------------------------------------
        # Campaign Risk Summary
        # ------------------------------------------------

        campaign_risk_summary = campaign_report.get(
            "campaign_summary"
        )

        if campaign_risk_summary is not None:

            st.markdown("### Campaign Risk Summary")

            display_df = campaign_risk_summary.copy()

            display_df["Campaign"] = display_df[
                "campaign_id"
            ].apply(
                lambda x: f"Campaign-{int(x)+1}"
            )

            display_df = display_df[
                [
                    "Campaign",
                    "campaign_type",
                    "url_count",
                    "average_model_risk",
                    "average_final_risk",
                    "max_final_risk",
                    "malicious_urls",
                    "suspicious_urls",
                ]
            ]

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
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

        # -------------------------------------------------------------
        # Reuse canonical 92-feature vectors already generated by
        # Batch Prediction.
        #
        # This prevents Drift from extracting the same current URLs
        # a second time.
        # -------------------------------------------------------------
        prediction_results = batch_result.get(
            "prediction_results",
            []
        )

        current_feature_df = None

        if prediction_results:

            current_feature_rows = []

            for result in prediction_results:

                features = result.get(
                    "features"
                )

                if features is not None:
                    current_feature_rows.append(
                        features
                    )

            if len(current_feature_rows) == len(df):

                current_feature_df = pd.DataFrame(
                    current_feature_rows
                )

                # -----------------------------------------------------
                # Align exactly with the trained 92-feature schema.
                # -----------------------------------------------------
                current_feature_df = current_feature_df.reindex(
                    columns=drift_service.feature_names,
                    fill_value=0
                )

                # -----------------------------------------------------
                # Preserve existing Drift numeric handling.
                # -----------------------------------------------------
                current_feature_df = current_feature_df.apply(
                    pd.to_numeric,
                    errors="coerce"
                ).fillna(0)

                current_feature_df.insert(
                    0,
                    "url",
                    df[url_column].values
                )

            if current_feature_df is not None:

                print(
                    "[Batch Analysis] Reusing 92-feature prediction "
                    "vectors for Drift Analysis."
                    "Current dataset infrastructure extraction will be skipped.",
                    flush=True
                )

                drift_output = drift_service.analyze(
                    reference_dataset=reference_df,
                    current_dataset=current_feature_df
                )

            else:

                print(
                    "[Batch Analysis] Prediction feature vectors "
                    "unavailable. DriftService will build the current "
                    "feature dataset using the canonical pipeline."
                )

                drift_output = drift_service.analyze(
                    reference_dataset=reference_df,
                    current_dataset=df.rename(
                        columns={url_column: "url"}
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