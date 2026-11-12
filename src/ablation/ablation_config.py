"""
ablation_config.py

Configuration for the controlled ablation experiments.

The ablation study contains four modes:

    full
    lexical
    infra
    lexical_infra

Interpretation
--------------
full:
    Complete feature representation. Used primarily as a
    reproduction/reference mode.

lexical:
    Lexical URL features only. Baseline representation.

infra:
    Infrastructure features only. Secondary diagnostic experiment
    measuring the standalone predictive signal contained in the
    infrastructure representation.

lexical_infra:
    Lexical + infrastructure features. Primary infrastructure-aware
    comparison.

The experiment uses one common sample and one common train/test split
for all modes.
"""

from pathlib import Path


# ============================================================================
# Ablation modes
# ============================================================================

ABLATION_MODES = [
    "full",
    "lexical",
    "infra",
    "lexical_infra",
]


# ============================================================================
# Dataset configuration
# ============================================================================

DATA_PATH = Path(
    "data/kaggle/balanced_urls.csv"
)

USE_TRUSTED_DATASET = True


# ============================================================================
# Sampling protocol
# ============================================================================

SAMPLE_SIZE = 1500

SAMPLE_RANDOM_STATE = 42


# ============================================================================
# Train / test split
# ============================================================================

TEST_SIZE = 0.20

SPLIT_RANDOM_STATE = 42


# ============================================================================
# Dataset columns and labels
# ============================================================================

URL_COLUMN = "url"

LABEL_COLUMN = "type"

BENIGN_LABEL = "benign"

MALICIOUS_LABEL = "malicious"


# ============================================================================
# XGBoost configuration
# ============================================================================

XGB_PARAMS = {
    "n_estimators": 300,
    "max_depth": 4,
    "learning_rate": 0.1,
    "eval_metric": "logloss",
    "random_state": 42,
}


# ============================================================================
# Preprocessing
# ============================================================================

USE_STANDARD_SCALER = True


# ============================================================================
# Output directories
# ============================================================================

RESULTS_DIR = Path(
    "results/ablation"
)

FIGURES_DIR = (
    RESULTS_DIR / "figures"
)

MODELS_DIR = Path(
    "models/ablation"
)


# ============================================================================
# Experiment-level artifacts
# ============================================================================

SPLIT_MANIFEST_PATH = (
    RESULTS_DIR / "split_manifest.csv"
)

ABLATION_RESULTS_PATH = (
    RESULTS_DIR / "ablation_results.csv"
)

ABLATION_REPORT_PATH = (
    RESULTS_DIR / "ablation_report.md"
)


# ============================================================================
# Per-mode output directories
# ============================================================================

def get_mode_results_dir(
    mode: str,
) -> Path:
    """
    Return the result directory for one ablation mode.
    """

    if mode not in ABLATION_MODES:
        raise ValueError(
            f"Unsupported ablation mode: {mode}. "
            f"Supported modes: {ABLATION_MODES}"
        )

    return RESULTS_DIR / mode


def get_mode_model_dir(
    mode: str,
) -> Path:
    """
    Return the model directory for one ablation mode.
    """

    if mode not in ABLATION_MODES:
        raise ValueError(
            f"Unsupported ablation mode: {mode}. "
            f"Supported modes: {ABLATION_MODES}"
        )

    return MODELS_DIR / mode


# ============================================================================
# Frozen experiment protocol
# ============================================================================

EXPERIMENT_PROTOCOL = {
    "sample_size": SAMPLE_SIZE,
    "sample_random_state": SAMPLE_RANDOM_STATE,
    "test_size": TEST_SIZE,
    "split_random_state": SPLIT_RANDOM_STATE,
    "use_trusted_dataset": USE_TRUSTED_DATASET,
    "use_standard_scaler": USE_STANDARD_SCALER,
    "ablation_modes": ABLATION_MODES,
    "xgb_parameters": XGB_PARAMS,
}