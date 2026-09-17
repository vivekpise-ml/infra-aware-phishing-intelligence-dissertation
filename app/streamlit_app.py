import streamlit as st
from PIL import Image

# -----------------------------------------------------
# Page Configuration
# -----------------------------------------------------

st.set_page_config(
    page_title="Phishing Risk Intelligence Framework",
    layout="wide"
)

# -----------------------------------------------------
# Title
# -----------------------------------------------------

st.markdown(
    """
<h1 style="text-align:center;">
Infrastructure-Aware Drift-Adaptive Phishing Risk Intelligence Framework
</h1>
""",
    unsafe_allow_html=True
)

st.divider()

# -----------------------------------------------------
# Framework Overview
# -----------------------------------------------------

st.header("Framework Overview")

st.markdown(
    """
This application presents an end-to-end phishing risk intelligence framework
developed as part of the Executive M.Tech (Applied Artificial Intelligence)
program at Visvesvaraya National Institute of Technology (VNIT), Nagpur.

The framework integrates machine learning, infrastructure-aware
feature engineering, statistical drift detection, explainable AI, and
campaign-level clustering to provide comprehensive phishing URL risk
assessment and adaptive model intelligence.
"""
)

st.divider()

# -----------------------------------------------------
# Framework Architecture
# -----------------------------------------------------

st.header("Framework Architecture")

architecture = Image.open("app/assets/framework_architecture_v2.png")

col1, col2, col3 = st.columns([1, 3, 1])

with col2:
    st.image(
        architecture,
        use_container_width=True,
        caption="Overall Framework Architecture"
    )

st.divider()

# -----------------------------------------------------
# Framework Modules
# -----------------------------------------------------

st.header("Application Modules")

st.table(
    {
        "Module": [
            "URL Prediction",
            "Batch Analysis",
            "Drift Analysis",
            "Campaign Analysis",
            "Model Information",
            "About Project",
        ],
        "Description": [
            "Predict phishing URLs using the trained XGBoost model",
            "Analyze multiple URLs simultaneously",
            "Detect statistical drift using PSI, KL Divergence and JS Distance",
            "Identify phishing campaigns using DBSCAN clustering",
            "View model architecture, dataset and evaluation metrics",
            "Project objectives, implementation details and research scope",
        ],
    }
)

st.divider()

# -----------------------------------------------------
# Technology Stack
# -----------------------------------------------------

st.header("Technology Stack")

st.table(
    {
        "Component": [
            "Programming Language",
            "Machine Learning",
            "Clustering",
            "Explainability",
            "Web Framework",
            "Infrastructure Intelligence",
            "Drift Detection",
        ],
        "Technology": [
            "Python",
            "XGBoost",
            "DBSCAN",
            "SHAP",
            "Streamlit",
            "DNS, WHOIS, SSL, IP, ASN",
            "PSI, KL Divergence, Jensen-Shannon Distance",
        ],
    }
)

st.divider()

# -----------------------------------------------------
# Footer
# -----------------------------------------------------

st.info(
    """
**Executive M.Tech (Applied Artificial Intelligence)**

Department of Computer Science & Engineering

Visvesvaraya National Institute of Technology (VNIT), Nagpur
"""
)