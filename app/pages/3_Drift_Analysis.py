import sys
import os

import streamlit as st
import pandas as pd

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

from src.drift.drift_service import DriftService


# ------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------

st.set_page_config(
    page_title="Drift Analysis",
    layout="wide"
)

st.title("📈 Statistical Drift Analysis")

st.caption(
    "Compare a reference dataset with a current dataset "
    "to detect feature distribution drift."
)

st.markdown("---")

# ------------------------------------------------
# Upload datasets
# ------------------------------------------------

col1, col2 = st.columns(2)

with col1:

    st.subheader("Reference Dataset")

    reference_file = st.file_uploader(

        "Upload Reference CSV",

        type=["csv"],

        key="reference"

    )

with col2:

    st.subheader("Current Dataset")

    current_file = st.file_uploader(

        "Upload Current CSV",

        type=["csv"],

        key="current"

    )

st.markdown("---")

# ------------------------------------------------
# Run Drift Analysis
# ------------------------------------------------

if st.button("Run Drift Analysis"):

    if reference_file is None:

        st.warning("Please upload the Reference Dataset.")

        st.stop()

    if current_file is None:

        st.warning("Please upload the Current Dataset.")

        st.stop()

    try:

        reference_df = pd.read_csv(reference_file)

        current_df = pd.read_csv(current_file)


        reference_download_name = (
            os.path.splitext(reference_file.name)[0]
            + "_features.csv"
        )

        current_download_name = (
            os.path.splitext(current_file.name)[0]
            + "_features.csv"
        )

        # -----------------------------------------
        # Validate URL column
        # -----------------------------------------
        '''
        if "url" not in reference_df.columns:

            st.error(
                "Reference dataset must contain a 'url' column."
            )

            st.stop()

        if "url" not in current_df.columns:

            st.error(
                "Current dataset must contain a 'url' column."
            )

            st.stop()
        '''

        service = DriftService()

        reference_is_feature = service.is_feature_dataset(reference_df)

        current_is_feature = service.is_feature_dataset(current_df)

        if not reference_is_feature and "url" not in reference_df.columns:

            st.error(
                "Reference dataset must contain either a 'url' column or precomputed features."
            )

            st.stop()

        if not current_is_feature and "url" not in current_df.columns:

            st.error(
                "Current dataset must contain either a 'url' column or precomputed features."
            )

            st.stop()

        if reference_is_feature:

            st.success("✅ Reference Feature Dataset detected.")

        else:

            st.info("ℹ Extracting features from Reference Dataset...")

        if current_is_feature:

            st.success("✅ Current Feature Dataset detected.")

        else:

            st.info("ℹ Extracting features from Current Dataset...")

        # -----------------------------------------
        # Run Drift Analysis
        # -----------------------------------------

        with st.spinner("Running Drift Analysis..."):


            analysis = service.analyze(

                reference_dataset=reference_df,

                current_dataset=current_df,

                reference_name="Reference Dataset",

                current_name="Current Dataset",

                save_json=True,

                report_path="reports/drift_report.json"

            )

            result = analysis["drift_result"]

            reference_features = analysis["reference_features"]

            current_features = analysis["current_features"]

            st.info(
                    f"""
                Generated Feature Datasets

                • Reference : {reference_download_name}

                • Current : {current_download_name}

                These files can be reused directly in future drift analyses
                without repeating feature extraction.
                """
                )
            
            st.download_button(

                "⬇ Download Reference Feature Dataset",

                reference_features.to_csv(index=False).encode("utf-8"),

                file_name=reference_download_name,

                mime="text/csv"

            )

            st.download_button(

                "⬇ Download Current Feature Dataset",

                current_features.to_csv(index=False).encode("utf-8"),

                file_name=current_download_name,

                mime="text/csv"

            )

        st.success("Drift Analysis Completed Successfully.")

        st.markdown("---")

        # ----------------------------------------------------
        # Summary
        # ----------------------------------------------------

        st.subheader("Overall Drift Summary")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Overall Score",
            f"{result['overall_score']:.4f}"
        )

        c2.metric(
            "Severity",
            result["severity"]
        )

        c3.metric(
            "Retraining",
            "YES" if result["requires_retraining"] else "NO"
        )

        c4.metric(
            "Top Features",
            len(result["top_drifting_features"])
        )

        st.info(result["recommendation"])

        st.markdown("---")

        # ----------------------------------------------------
        # Individual Metrics
        # ----------------------------------------------------

        st.subheader("Statistical Metrics")

        m1, m2, m3 = st.columns(3)

        m1.metric(

            "PSI",

            f"{result['psi']:.4f}"

        )

        m2.metric(

            "KL Divergence",

            f"{result['kl_divergence']:.4f}"

        )

        m3.metric(

            "JS Distance",

            f"{result['js_distance']:.4f}"

        )

        st.markdown("---")

        # ----------------------------------------------------
        # Top Features
        # ----------------------------------------------------

        st.subheader("Top Drifting Features")

        feature_df = pd.DataFrame(

            result["top_drifting_features"],

            columns=[

                "Feature",

                "Drift Score"

            ]

        )

        st.dataframe(

            feature_df,

            use_container_width=True

        )

        st.markdown("---")

        # ----------------------------------------------------
        # Download JSON
        # ----------------------------------------------------

        with open(

            "reports/drift_report.json",

            "rb"

        ) as f:

            st.download_button(

                label="⬇ Download Drift Report (JSON)",

                data=f,

                file_name="drift_report.json",

                mime="application/json"

            )

    except Exception as e:

        st.exception(e)