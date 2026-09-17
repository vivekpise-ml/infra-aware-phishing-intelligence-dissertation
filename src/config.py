#DATA_PATH = "data/kaggle/Phishing_Legitimate_full.csv"
#DATA_PATH = "data/kaggle/malicious_phish.csv"
DATA_PATH = "data/kaggle/balanced_urls.csv"
MODEL_DIR = "models"
MAXLEN = 100 # for RNN
USE_REAL_INFRA = True   # 🔴 For demo (fast & safe)

CAMPAIGN_MODEL_DIR = "models/campaign"

TEST_DATA_BATCH = "data/test_batch"

# =============================================================================
# Campaign Clustering Configuration
# =============================================================================

CAMPAIGN_CLUSTERING_CONFIG = {

    # -------------------------------------------------------------
    # DBSCAN Parameters
    # -------------------------------------------------------------
    "eps": 2.0,
    "min_samples": 3,

    # -------------------------------------------------------------
    # Top-N category retention for categorical features
    # Remaining categories will be grouped into "Other"
    # -------------------------------------------------------------
    "top_n": {
        "organization": 20,
        "hosting_provider": 15,
        "ssl_issuer": 15,
        "country": 10,
        "registrar": 10,
        "as":20,
    },

    # -------------------------------------------------------------
    # Missing categorical values
    # -------------------------------------------------------------
    "fill_value": "Unknown",

    # -------------------------------------------------------------
    # Saved preprocessing pipeline
    # -------------------------------------------------------------
    "preprocessor_filename": f"{CAMPAIGN_MODEL_DIR}/campaign_preprocessor.joblib",

    # -------------------------------------------------------------
    # Saved DBSCAN clustering model
    # -------------------------------------------------------------
    "cluster_model_filename":
        f"{CAMPAIGN_MODEL_DIR}/campaign_cluster.joblib",

    # -------------------------------------------------------------
    # OneHotEncoder configuration
    # -------------------------------------------------------------
    "handle_unknown": "ignore",
    "sparse_output": False,
    "group_other_label": "Other",
}
