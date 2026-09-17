import sys
import os
import traceback

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


# ------------------------------------------------
# Page
# ------------------------------------------------

st.set_page_config(
    page_title="URL Prediction",
    layout="centered"
)

st.title("🔍 URL Prediction")

st.caption(
    "Analyze a single URL using the "
    "Infrastructure-Aware Phishing Risk Intelligence Framework"
)

st.markdown("---")

# ======================================================
# SINGLE URL ANALYSIS
# ======================================================

url_input = st.text_input(
    "Enter a URL",
    placeholder="e.g. https://secure-paypal-login.com/update"
)

if st.button("Analyze URL"):

    if not url_input.strip():

        st.warning("Please enter a valid URL.")

    else:

        try:

            with st.spinner("Analyzing URL..."):

                result = run(url_input)

            st.success("Analysis Complete")

            # -------------------------------------------------
            # REPORT
            # -------------------------------------------------

            st.subheader("📄 Risk Intelligence Report")

            st.code(
                result["report"],
                language="text"
            )

            # -------------------------------------------------
            # SUMMARY
            # -------------------------------------------------

            st.subheader("📊 Risk Intelligence Summary")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Model Risk",
                f"{result['model_risk']:.2f}"
            )

            col2.metric(
                "Final Risk",
                f"{result['final_risk']:.2f}"
            )

            col3.metric(
                "Decision",
                result["label"].upper()
            )

            col4.metric(
                "Risk Tier",
                result["risk_tier"]
            )

            # -------------------------------------------------
            # INTERPRETATION
            # -------------------------------------------------

            st.subheader("Risk Interpretation")

            st.write(f"""
- 🔍 Model Risk : **{result['model_risk']:.2f}**

- 🏗️ Infrastructure Adjusted Risk : **{result['final_risk']:.2f}**

- ⚖️ Final decision is based on lexical + infrastructure intelligence.
""")

            # -------------------------------------------------
            # ALERT
            # -------------------------------------------------

            if result["label"].lower() == "benign":

                st.success("✅ Low-Risk Benign Domain")

            elif result["label"].lower() == "malicious":

                st.error("🚨 High-Risk Malicious Domain")

            else:

                st.warning("⚠️ Suspicious Domain")


        except Exception as e:

            st.exception(e)

            traceback.print_exc()