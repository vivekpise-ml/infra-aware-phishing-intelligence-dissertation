import streamlit as st

st.set_page_config(
    page_title="Model Information",
    layout="wide"
)

st.title("Model Information")

st.markdown(
    """
    This page summarizes the machine learning model used for phishing URL
    detection. It presents the prediction model, feature engineering approach,
    training dataset, performance evaluation, and the supporting intelligence
    modules integrated into the overall phishing risk intelligence framework.
    """
)

st.divider()

# ---------------------------------------------------------
# Prediction Model
# ---------------------------------------------------------

st.subheader("Prediction Model")

st.table({
    "Attribute": [
        "Algorithm",
        "Learning Type",
        "Task",
        "Status"
    ],
    "Value": [
        "XGBoost",
        "Supervised",
        "Binary Classification",
        "Loaded"
    ]
})

st.caption(
    "The prediction engine classifies URLs as Benign or Phishing using an "
    "XGBoost classifier trained on engineered lexical, HTML, and "
    "infrastructure-based features."
)

st.divider()

# ---------------------------------------------------------
# Feature Engineering
# ---------------------------------------------------------

st.subheader("Feature Engineering")

st.table({
    "Feature Category": [
        "URL Lexical Features",
        "HTML Content Features",
        "Infrastructure Features",
        "Total Model Input Features"
    ],
    "Count": [
        60,
        5,
        14,
        79
    ]
})

st.caption(
    "The prediction model is trained using engineered URL lexical, HTML "
    "content, and infrastructure-based features."
)

st.divider()

# ---------------------------------------------------------
# Training Dataset
# ---------------------------------------------------------

st.subheader("Training Dataset")

st.table({
    "Attribute": [
        "Dataset",
        "Training Samples",
        "Train/Test Split",
        "Classes"
    ],
    "Value": [
        "Balanced URLs",
        "1,500",
        "80/20 (Stratified)",
        "2 (Benign, Phishing)"
    ]
})

st.caption(
    "The deployed model was trained using a stratified sample of 1,500 URLs "
    "selected from a balanced dataset containing over 632,000 URLs. "
    "Stratified sampling preserved the class distribution while reducing "
    "the computational cost associated with extracting network-dependent "
    "infrastructure features."
)

st.divider()

# ---------------------------------------------------------
# Model Performance
# ---------------------------------------------------------

st.subheader("Model Performance")

st.table({
    "Metric": [
        "Accuracy",
        "Precision",
        "Recall",
        "F1-Score",
        "ROC-AUC"
    ],
    "Value": [
        "87.33%",
        "89.44%",
        "84.67%",
        "86.99%",
        "94.23%"
    ]
})

st.caption(
    "Performance metrics were obtained using an 80/20 stratified train-test "
    "split on the infrastructure-aware feature set."
)

st.divider()

# ---------------------------------------------------------
# Prediction Pipeline
# ---------------------------------------------------------

st.subheader("Prediction Pipeline")

pipeline = """
+-----------+
| Input URL |
+-----------+
       |
       v
+------------------------+
| Feature Extraction     |
| (79 Features)          |
+------------------------+
       |
       v
+-------------------------+
| Feature Scaling         |
| (StandardScaler)        |
+-------------------------+
       |
       v
+-------------------------+
| XGBoost Classifier      |
+-------------------------+
       |
       v
+-------------------------+
| Risk Assessment         |
+-------------------------+
       |
       v
+-------------------------+
| Prediction              |
| (Benign / Phishing)     |
+-------------------------+
"""

st.code(pipeline, language="text")

st.caption(
    "The prediction pipeline illustrates the end-to-end processing of a URL "
    "within the phishing risk intelligence framework."
)