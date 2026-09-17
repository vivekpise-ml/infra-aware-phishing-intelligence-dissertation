import sys
import os
import streamlit as st
import joblib
import pandas as pd
import traceback

# Ensure project root is in PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from src.inference.run_inference import run


# ------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------
st.set_page_config(
    page_title="Phishing Risk Intelligence",
    layout="centered"
)

st.title("🛡️ Phishing Risk Intelligence System")
st.caption("Infrastructure-Aware Drift-Adaptive Multimodal Detection")

st.markdown("---")


# ======================================================
# SINGLE URL ANALYSIS
# ======================================================
st.subheader("🔍 Analyze URL")

url_input = st.text_input(
    "Enter a URL",
    placeholder="e.g. http://secure-paypal-login.com/update"
)

if st.button("Analyze URL"):
    if not url_input.strip():
        st.warning("Please enter a valid URL.")
    else:
        try:
            with st.spinner("Analyzing..."):
                result = run(url_input)

            st.success("Analysis Complete ✅")

            # -----------------------------------------
            # DISPLAY REPORT
            # -----------------------------------------
            st.subheader("📄 Risk Intelligence Report")
            st.code(result["report"], language="text")

            # -----------------------------------------
            # SHOW KEY METRICS
            # -----------------------------------------
            st.subheader("📊 Risk Intelligence Summary")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Model Risk", f"{result['model_risk']:.2f}")
            col2.metric("Final Risk", f"{result['final_risk']:.2f}")
            col3.metric("Decision", result["label"].upper())
            col4.metric("Risk Tier", result["risk_tier"])

            # -----------------------------------------
            # RISK INTERPRETATION (NEW)
            # -----------------------------------------
            st.markdown("###  Risk Interpretation")

            st.write(f"""
            - 🔍 Model detected suspicious patterns → **{result['model_risk']:.2f}**
            - 🏗️ Infrastructure trust adjusted the risk → **{result['final_risk']:.2f}**
            - ⚖️ Final decision is based on combined intelligence (not raw model output)
            """)

            # -----------------------------------------
            # FINAL DECISION ALERT
            # -----------------------------------------

            if result["label"].lower() == "benign":
                st.success("✅ Low-Risk Benign Domain")

            elif result["label"].lower() == "malicious":
                st.error("🚨 High-Risk Malicious Domain")

            else:
                st.warning("⚠️ Suspicious Domain")

            # -----------------------------------------
            # SHAP EXPLANATION
            # -----------------------------------------
            st.subheader(" Model Explanation (Top Factors)")
            for factor in result["explanation_list"]:
                st.write(f"• {factor}")

        #except Exception as e:
        #    st.error(f"❌ Analysis failed: {e}")

        except Exception:
            st.exception(traceback.format_exc())


st.markdown("---")


# ======================================================
# BATCH ANALYSIS (CSV)
# ======================================================
st.subheader("📄 Batch Analysis (CSV Upload)")
st.info("Upload a CSV file containing a column named 'url'.")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file is not None:
    import pandas as pd

    try:
        df = pd.read_csv(uploaded_file)

        # Detect URL column
        url_col = next((c for c in df.columns if "url" in c.lower()), None)

        if url_col is None:
            st.error("❌ No 'url' column found in uploaded file.")
            st.stop()

        urls = df[url_col].astype(str)

        st.write(f"Processing {len(urls)} URLs...")

        results = []

        for u in urls:
            try:
                res = run(u)

                results.append({
                    "url": u,
                    "prediction": res["label"],
                    "risk_score": res["risk_score"],
                    "risk_tier": res["risk_tier"]
                })

            except Exception as e:
                results.append({
                    "url": u,
                    "prediction": "error",
                    "risk_score": None,
                    "risk_tier": None
                })

        results_df = pd.DataFrame(results)

        st.success("Batch analysis complete ✅")
        st.dataframe(results_df.head(200), use_container_width=True)

        # Download option
        st.download_button(
            "Download Results CSV",
            results_df.to_csv(index=False).encode("utf-8"),
            file_name="phishing_analysis_results.csv",
            mime="text/csv",
        )

    except Exception as e:
        st.error(f"❌ Failed to process CSV: {e}")


st.markdown("---")


# ======================================================
# SYSTEM INFO
# ======================================================
st.subheader("ℹ️ System Information")

st.write("""
This system performs phishing detection using:

- ✅ XGBoost (primary model)
- ✅ Multimodal feature extraction (URL + HTML)
- ✅ Infrastructure intelligence (ASN, WHOIS) 
- ⚙️ Drift monitoring *(structural implementation)*
- ⚙️ Campaign Analysis *(structural implementation)*         
- ⚙️ SHAP-based explainability *(structural implementation)*

Designed for research and real-world cybersecurity applications.
""")

st.subheader(" Upcoming Enhancements")
st.write(""" 
- 🔧 Drift detection (time-based modeling)  
- 🔧 Campaign-level clustering  
- 🔧 Intelligence-driven reporting 
""")