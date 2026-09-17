import streamlit as st

st.set_page_config(
    page_title="Phishing Risk Intelligence Framework",
    layout="wide"
)

st.title("🛡️ Infrastructure-Aware Drift-Adaptive")
st.title("Phishing Risk Intelligence Framework")

st.markdown("---")

st.markdown("""
## Welcome

This application demonstrates an end-to-end phishing detection and
risk intelligence framework developed as part of the M.Tech
Applied Artificial Intelligence project.

### Major Components

- 🔍 URL Prediction
- 📄 Batch Analysis
- 📈 Statistical Drift Detection
- 🌐 Campaign-Level Analysis
- 📊 Model Information
- 📚 About Project

Use the **left navigation panel** to access each module.
""")

st.markdown("---")

st.subheader("Framework Architecture")

st.code("""
                URL
                 │
                 ▼
     Feature Extraction
                 │
                 ▼
     Infrastructure Features
                 │
                 ▼
      XGBoost Prediction
                 │
      ┌──────────┴──────────┐
      │                     │
      ▼                     ▼
 Risk Intelligence     Drift Analysis
      │                     │
      └──────────┬──────────┘
                 ▼
      Campaign Intelligence
""", language="text")

st.info("Semester 4 Integrated Research Prototype")