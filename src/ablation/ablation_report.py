"""
ablation_report.py

Reporting and visualization for the controlled ablation experiment.

Ablation modes
--------------
    full
    lexical
    infra
    lexical_infra

Interpretation
--------------
full:
    Complete feature representation. Reference/reproduction mode.

lexical:
    Lexical URL features only. Baseline.

infra:
    Infrastructure features only. Secondary diagnostic experiment.

lexical_infra:
    Lexical + infrastructure features. Primary infrastructure-aware
    comparison.

This module is reporting-only.

It does NOT:
    - extract features
    - call infrastructure APIs
    - access infra_cache.json
    - train models
    - modify production models
    - modify predictor.py
    - modify drift_service.py
    - modify campaign modules
    - modify Streamlit
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# ============================================================================
# Project configuration
# ============================================================================

from src.ablation.ablation_config import (
    RESULTS_DIR,
    FIGURES_DIR,
    ABLATION_RESULTS_PATH,
    ABLATION_REPORT_PATH,
    SAMPLE_SIZE,
    SAMPLE_RANDOM_STATE,
    TEST_SIZE,
    SPLIT_RANDOM_STATE,
    USE_TRUSTED_DATASET,
    USE_STANDARD_SCALER,
    XGB_PARAMS,
)

from src.ablation.ablation_features import (
    FEATURE_MODE_FULL,
    FEATURE_MODE_LEXICAL,
    FEATURE_MODE_INFRA,
    FEATURE_MODE_LEXICAL_INFRA,
)


# ============================================================================
# Feature-cache paths
# ============================================================================

FEATURE_CACHE_DIR = RESULTS_DIR / "feature_cache"

FEATURE_CACHE_PATH = (
    FEATURE_CACHE_DIR / "sampled_features.csv"
)

FEATURE_CACHE_METADATA_PATH = (
    FEATURE_CACHE_DIR / "feature_metadata.json"
)


# ============================================================================
# Utilities
# ============================================================================

def ensure_figures_directory() -> None:
    """Ensure the figure output directory exists."""

    FIGURES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def load_results() -> pd.DataFrame:
    """Load consolidated ablation results."""

    if not ABLATION_RESULTS_PATH.exists():
        raise FileNotFoundError(
            "Ablation results were not found:\n"
            f"{ABLATION_RESULTS_PATH}\n\n"
            "Run run_ablation.py first."
        )

    results = pd.read_csv(
        ABLATION_RESULTS_PATH
    )

    required_columns = [
        "feature_mode",
        "n_features",
        "accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
        "tn",
        "fp",
        "fn",
        "tp",
    ]

    missing = [
        column
        for column in required_columns
        if column not in results.columns
    ]

    if missing:
        raise ValueError(
            "Ablation results are missing required columns:\n"
            f"{missing}"
        )

    return results


def load_feature_cache_metadata() -> dict:
    """Load metadata for the canonical feature cache."""

    if not FEATURE_CACHE_METADATA_PATH.exists():
        return {}

    with open(
        FEATURE_CACHE_METADATA_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def pct(value: float) -> str:
    """Format a metric as a percentage."""

    return f"{value * 100:.2f}%"


def pp(value: float) -> str:
    """Format a metric difference as percentage points."""

    sign = "+" if value > 0 else ""

    return (
        f"{sign}{value * 100:.2f} pp"
    )


def mode_display_name(
    mode: str,
) -> str:
    """Convert internal mode names to presentation names."""

    names = {
        FEATURE_MODE_FULL: "Full",
        FEATURE_MODE_LEXICAL: "Lexical",
        FEATURE_MODE_INFRA: "Infrastructure",
        FEATURE_MODE_LEXICAL_INFRA:
            "Lexical + Infrastructure",
    }

    return names.get(
        mode,
        mode,
    )


# ============================================================================
# Result validation
# ============================================================================

def validate_required_modes(
    results: pd.DataFrame,
) -> None:
    """Verify that all four expected modes are available."""

    available_modes = set(
        results[
            "feature_mode"
        ].astype(str)
    )

    required_modes = {
        FEATURE_MODE_FULL,
        FEATURE_MODE_LEXICAL,
        FEATURE_MODE_INFRA,
        FEATURE_MODE_LEXICAL_INFRA,
    }

    missing = (
        required_modes
        - available_modes
    )

    if missing:
        raise ValueError(
            "The following required ablation modes are missing:\n"
            f"{sorted(missing)}"
        )


def get_mode_row(
    results: pd.DataFrame,
    mode: str,
) -> pd.Series:
    """Return the unique result row for a mode."""

    rows = results[
        results[
            "feature_mode"
        ] == mode
    ]

    if rows.empty:
        raise ValueError(
            f"No result found for mode: {mode}"
        )

    if len(rows) > 1:
        raise ValueError(
            f"Multiple results found for mode: {mode}"
        )

    return rows.iloc[0]


# ============================================================================
# Primary comparison
# ============================================================================

def calculate_primary_delta(
    lexical: pd.Series,
    lexical_infra: pd.Series,
) -> dict:
    """
    Calculate the observed change from lexical to
    lexical + infrastructure.
    """

    metrics = [
        "accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
    ]

    delta = {}

    for metric in metrics:
        delta[metric] = (
            float(
                lexical_infra[metric]
            )
            -
            float(
                lexical[metric]
            )
        )

    delta["false_negatives"] = (
        int(
            lexical_infra["fn"]
        )
        -
        int(
            lexical["fn"]
        )
    )

    delta["false_positives"] = (
        int(
            lexical_infra["fp"]
        )
        -
        int(
            lexical["fp"]
        )
    )

    return delta


# ============================================================================
# Metric table
# ============================================================================

def build_metric_table(
    results: pd.DataFrame,
) -> pd.DataFrame:
    """Build the main comparison table."""

    table = results[
        [
            "feature_mode",
            "n_features",
            "accuracy",
            "precision",
            "recall",
            "f1",
            "roc_auc",
            "fn",
            "fp",
        ]
    ].copy()

    table["feature_mode"] = (
        table["feature_mode"].map(
            mode_display_name
        )
    )

    table = table.rename(
        columns={
            "feature_mode": "Feature Set",
            "n_features": "Features",
            "accuracy": "Accuracy",
            "precision": "Precision",
            "recall": "Recall",
            "f1": "F1",
            "roc_auc": "ROC-AUC",
            "fn": "False Negatives",
            "fp": "False Positives",
        }
    )

    return table


def markdown_metric_table(
    table: pd.DataFrame,
) -> str:
    """Convert a dataframe into a Markdown table."""

    headers = list(
        table.columns
    )

    lines = []

    lines.append(
        "| "
        + " | ".join(headers)
        + " |"
    )

    lines.append(
        "| "
        + " | ".join(
            ["---"] * len(headers)
        )
        + " |"
    )

    for _, row in table.iterrows():

        values = []

        for column in headers:

            value = row[column]

            if column in [
                "Accuracy",
                "Precision",
                "Recall",
                "F1",
                "ROC-AUC",
            ]:
                values.append(
                    f"{float(value) * 100:.2f}%"
                )
            else:
                values.append(
                    str(value)
                )

        lines.append(
            "| "
            + " | ".join(values)
            + " |"
        )

    return "\n".join(lines)


# ============================================================================
# Figure 1 - all four modes
# ============================================================================

def create_metrics_figure(
    results: pd.DataFrame,
) -> Path:
    """Create overall metric comparison for all four modes."""

    ensure_figures_directory()

    metrics = [
        "accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
    ]

    metric_labels = [
        "Accuracy",
        "Precision",
        "Recall",
        "F1",
        "ROC-AUC",
    ]

    modes = results[
        "feature_mode"
    ].tolist()

    x = list(
        range(len(metrics))
    )

    width = (
        0.8
        / max(
            len(modes),
            1,
        )
    )

    plt.figure(
        figsize=(11, 6)
    )

    for index, mode in enumerate(
        modes
    ):

        row = get_mode_row(
            results,
            mode,
        )

        values = [
            float(
                row[metric]
            )
            for metric in metrics
        ]

        positions = [
            value
            + (
                index
                - (
                    len(modes) - 1
                ) / 2
            )
            * width
            for value in x
        ]

        plt.bar(
            positions,
            values,
            width=width,
            label=mode_display_name(
                mode
            ),
        )

    plt.xticks(
        x,
        metric_labels,
    )

    plt.ylim(
        0,
        1.05,
    )

    plt.ylabel(
        "Score"
    )

    plt.title(
        "Ablation Study: Feature Representation Comparison"
    )

    plt.legend()

    plt.tight_layout()

    output_path = (
        FIGURES_DIR
        / "ablation_metrics.png"
    )

    plt.savefig(
        output_path,
        dpi=200,
        bbox_inches="tight",
    )

    plt.close()

    return output_path


# ============================================================================
# Figure 2 - primary delta
# ============================================================================

def create_primary_delta_figure(
    lexical: pd.Series,
    lexical_infra: pd.Series,
) -> Path:
    """Create primary lexical vs lexical+infra delta figure."""

    ensure_figures_directory()

    metrics = [
        "accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
    ]

    labels = [
        "Accuracy",
        "Precision",
        "Recall",
        "F1",
        "ROC-AUC",
    ]

    deltas = [
        float(
            lexical_infra[metric]
        )
        -
        float(
            lexical[metric]
        )
        for metric in metrics
    ]

    positions = list(
        range(len(labels))
    )

    plt.figure(
        figsize=(9, 5)
    )

    plt.bar(
        positions,
        deltas,
    )

    plt.axhline(
        0,
        linewidth=1,
    )

    plt.xticks(
        positions,
        labels,
    )

    plt.ylabel(
        "Change in score"
    )

    plt.title(
        "Primary Ablation: Lexical + Infrastructure vs Lexical"
    )

    plt.tight_layout()

    output_path = (
        FIGURES_DIR
        / "ablation_delta_vs_lexical.png"
    )

    plt.savefig(
        output_path,
        dpi=200,
        bbox_inches="tight",
    )

    plt.close()

    return output_path


# ============================================================================
# Figure 3 - infrastructure diagnostic
# ============================================================================

def create_infra_diagnostic_figure(
    results: pd.DataFrame,
) -> Path:
    """
    Compare:

        lexical
        infrastructure
        lexical + infrastructure

    This is a secondary diagnostic figure.
    """

    ensure_figures_directory()

    modes = [
        FEATURE_MODE_LEXICAL,
        FEATURE_MODE_INFRA,
        FEATURE_MODE_LEXICAL_INFRA,
    ]

    labels = [
        "Lexical",
        "Infrastructure",
        "Lexical + Infrastructure",
    ]

    metrics = [
        "accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
    ]

    metric_labels = [
        "Accuracy",
        "Precision",
        "Recall",
        "F1",
        "ROC-AUC",
    ]

    x = list(
        range(len(metrics))
    )

    width = (
        0.8
        / len(modes)
    )

    plt.figure(
        figsize=(11, 6)
    )

    for index, mode in enumerate(
        modes
    ):

        row = get_mode_row(
            results,
            mode,
        )

        values = [
            float(
                row[metric]
            )
            for metric in metrics
        ]

        positions = [
            value
            + (
                index
                - (
                    len(modes) - 1
                ) / 2
            )
            * width
            for value in x
        ]

        plt.bar(
            positions,
            values,
            width=width,
            label=labels[index],
        )

    plt.xticks(
        x,
        metric_labels,
    )

    plt.ylim(
        0,
        1.05,
    )

    plt.ylabel(
        "Score"
    )

    plt.title(
        "Standalone and Combined Infrastructure Evaluation"
    )

    plt.legend()

    plt.tight_layout()

    output_path = (
        FIGURES_DIR
        / "infra_diagnostic.png"
    )

    plt.savefig(
        output_path,
        dpi=200,
        bbox_inches="tight",
    )

    plt.close()

    return output_path


# ============================================================================
# Figure 4 - feature importance
# ============================================================================

def create_feature_importance_figure(
    top_n: int = 15,
) -> Path:
    """
    Create feature-importance figure for lexical + infrastructure.
    """

    ensure_figures_directory()

    path = (
        RESULTS_DIR
        / FEATURE_MODE_LEXICAL_INFRA
        / "feature_importance.csv"
    )

    if not path.exists():
        raise FileNotFoundError(
            "Feature importance file not found:\n"
            f"{path}"
        )

    importance = pd.read_csv(
        path
    )

    required_columns = [
        "feature",
        "importance",
    ]

    missing = [
        column
        for column in required_columns
        if column not in importance.columns
    ]

    if missing:
        raise ValueError(
            "Feature importance file is missing:\n"
            f"{missing}"
        )

    importance = (
        importance
        .sort_values(
            "importance",
            ascending=False,
        )
        .head(top_n)
        .sort_values(
            "importance",
            ascending=True,
        )
    )

    plt.figure(
        figsize=(10, 7)
    )

    plt.barh(
        importance["feature"],
        importance["importance"],
    )

    plt.xlabel(
        "XGBoost feature importance"
    )

    plt.ylabel(
        "Feature"
    )

    plt.title(
        "Top Features: Lexical + Infrastructure Model"
    )

    plt.tight_layout()

    output_path = (
        FIGURES_DIR
        / "feature_importance_lexical_infra.png"
    )

    plt.savefig(
        output_path,
        dpi=200,
        bbox_inches="tight",
    )

    plt.close()

    return output_path


# ============================================================================
# Markdown report generation
# ============================================================================

def generate_report(
    results: pd.DataFrame,
    cache_metadata: dict,
    metrics_figure: Path,
    delta_figure: Path,
    infra_figure: Path,
    importance_figure: Path,
) -> str:
    """
    Generate the Markdown report.

    The report is deliberately constructed as a list of lines rather
    than one large triple-quoted f-string. This avoids accidental
    unterminated-string errors caused by Markdown/code content.
    """

    validate_required_modes(
        results
    )

    full = get_mode_row(
        results,
        FEATURE_MODE_FULL,
    )

    lexical = get_mode_row(
        results,
        FEATURE_MODE_LEXICAL,
    )

    infra = get_mode_row(
        results,
        FEATURE_MODE_INFRA,
    )

    lexical_infra = get_mode_row(
        results,
        FEATURE_MODE_LEXICAL_INFRA,
    )

    delta = calculate_primary_delta(
        lexical,
        lexical_infra,
    )

    metric_table = build_metric_table(
        results
    )

    # ------------------------------------------------------------------------
    # Feature counts
    # ------------------------------------------------------------------------

    full_features = int(
        full["n_features"]
    )

    lexical_features = int(
        lexical["n_features"]
    )

    infra_features = int(
        infra["n_features"]
    )

    lexical_infra_features = int(
        lexical_infra[
            "n_features"
        ]
    )

    # ------------------------------------------------------------------------
    # Cache metadata
    # ------------------------------------------------------------------------

    cache_rows = cache_metadata.get(
        "rows",
        SAMPLE_SIZE,
    )

    cache_feature_count = (
        cache_metadata.get(
            "feature_count",
            "N/A",
        )
    )

    extraction_time = (
        cache_metadata.get(
            "extraction_duration_seconds",
            None,
        )
    )

    if extraction_time is not None:
        extraction_time_text = (
            f"{float(extraction_time):.2f} seconds"
        )
    else:
        extraction_time_text = (
            "Not recorded"
        )

    # ------------------------------------------------------------------------
    # Primary deltas
    # ------------------------------------------------------------------------

    accuracy_change = pp(
        delta["accuracy"]
    )

    precision_change = pp(
        delta["precision"]
    )

    recall_change = pp(
        delta["recall"]
    )

    f1_change = pp(
        delta["f1"]
    )

    auc_change = pp(
        delta["roc_auc"]
    )

    fn_change = delta[
        "false_negatives"
    ]

    fp_change = delta[
        "false_positives"
    ]

    # ------------------------------------------------------------------------
    # Infrastructure-only metrics
    # ------------------------------------------------------------------------

    infra_accuracy = pct(
        float(
            infra["accuracy"]
        )
    )

    infra_precision = pct(
        float(
            infra["precision"]
        )
    )

    infra_recall = pct(
        float(
            infra["recall"]
        )
    )

    infra_f1 = pct(
        float(
            infra["f1"]
        )
    )

    infra_auc = pct(
        float(
            infra["roc_auc"]
        )
    )

    # ------------------------------------------------------------------------
    # Build Markdown line-by-line
    # ------------------------------------------------------------------------

    lines = []

    lines.append("# Controlled Ablation Study")
    lines.append("")

    lines.append("## 1. Purpose")
    lines.append("")

    lines.append(
        "This experiment evaluates the contribution of the "
        "infrastructure-aware feature representation within the "
        "phishing risk intelligence framework."
    )
    lines.append("")

    lines.append(
        "Four feature representations are evaluated:"
    )
    lines.append("")

    lines.append(
        "1. **Full** — complete feature representation used by the pipeline."
    )
    lines.append(
        "2. **Lexical** — URL lexical features only. Baseline."
    )
    lines.append(
        "3. **Infrastructure** — infrastructure features only. "
        "Secondary diagnostic experiment."
    )
    lines.append(
        "4. **Lexical + Infrastructure** — combined representation."
    )
    lines.append("")

    lines.append(
        "The **primary ablation comparison** is:"
    )
    lines.append("")
    lines.append(
        "**Lexical vs Lexical + Infrastructure**"
    )
    lines.append("")

    lines.append(
        "The **Infrastructure-only** experiment is treated as a "
        "secondary diagnostic to measure the standalone predictive "
        "signal contained in the infrastructure feature group."
    )
    lines.append("")

    # ------------------------------------------------------------------------
    # Protocol
    # ------------------------------------------------------------------------

    lines.append("---")
    lines.append("")
    lines.append("## 2. Experimental Protocol")
    lines.append("")

    lines.append("| Parameter | Value |")
    lines.append("|---|---|")
    lines.append(
        f"| Dataset | `balanced_urls.csv` |"
    )
    lines.append(
        f"| Sample size | {SAMPLE_SIZE} |"
    )
    lines.append(
        f"| Sample random state | {SAMPLE_RANDOM_STATE} |"
    )
    lines.append(
        f"| Test size | {TEST_SIZE:.0%} |"
    )
    lines.append(
        f"| Split random state | {SPLIT_RANDOM_STATE} |"
    )
    lines.append(
        f"| Trusted dataset augmentation | "
        f"{USE_TRUSTED_DATASET} |"
    )
    lines.append(
        f"| StandardScaler | {USE_STANDARD_SCALER} |"
    )
    lines.append(
        f"| XGBoost estimators | "
        f"{XGB_PARAMS.get('n_estimators')} |"
    )
    lines.append(
        f"| XGBoost max depth | "
        f"{XGB_PARAMS.get('max_depth')} |"
    )
    lines.append(
        f"| XGBoost learning rate | "
        f"{XGB_PARAMS.get('learning_rate')} |"
    )
    lines.append(
        f"| XGBoost random state | "
        f"{XGB_PARAMS.get('random_state')} |"
    )
    lines.append("")

    lines.append(
        "The same sampled URLs and the same train/test split are used "
        "for all four feature representations."
    )
    lines.append("")

    lines.append(
        "This controls the dataset and partition variables while "
        "changing only the feature representation supplied to the "
        "classifier."
    )
    lines.append("")

    # ------------------------------------------------------------------------
    # Feature cache
    # ------------------------------------------------------------------------

    lines.append("---")
    lines.append("")
    lines.append("## 3. Feature Extraction and Caching")
    lines.append("")

    lines.append(
        "The complete feature representation was extracted once for "
        "the common experimental sample."
    )
    lines.append("")

    lines.append(
        "The resulting feature matrix was persisted as:"
    )
    lines.append("")
    lines.append(
        "`results/ablation/feature_cache/sampled_features.csv`"
    )
    lines.append("")

    lines.append(
        "The existing infrastructure cache remains part of the "
        "underlying infrastructure feature collection process."
    )
    lines.append("")

    lines.append(
        "The experiment-level CSV cache allows all four model "
        "experiments to reuse the same extracted feature values "
        "without repeating infrastructure collection."
    )
    lines.append("")

    lines.append("| Property | Value |")
    lines.append("|---|---|")
    lines.append(
        f"| Cached rows | {cache_rows} |"
    )
    lines.append(
        f"| Cached feature columns | {cache_feature_count} |"
    )
    lines.append(
        f"| One-time feature extraction | "
        f"{extraction_time_text} |"
    )
    lines.append("")

    lines.append(
        "Thus, adding the Infrastructure-only experiment does not "
        "require a second infrastructure extraction pass."
    )
    lines.append("")

    # ------------------------------------------------------------------------
    # Feature representations
    # ------------------------------------------------------------------------

    lines.append("---")
    lines.append("")
    lines.append("## 4. Feature Representations")
    lines.append("")

    lines.append(
        "| Representation | Features | Role |"
    )
    lines.append("|---|---:|---|")
    lines.append(
        f"| Full | {full_features} | "
        f"Reference / reproduction |"
    )
    lines.append(
        f"| Lexical | {lexical_features} | "
        f"Baseline |"
    )
    lines.append(
        f"| Infrastructure | {infra_features} | "
        f"Secondary diagnostic |"
    )
    lines.append(
        f"| Lexical + Infrastructure | "
        f"{lexical_infra_features} | "
        f"Primary infrastructure-aware comparison |"
    )
    lines.append("")

    lines.append(
        "The feature representations are constructed by selecting "
        "columns from the same canonical feature cache."
    )
    lines.append("")

    lines.append(
        "No new feature-engineering formulas are introduced by the "
        "ablation experiment."
    )
    lines.append("")

    # ------------------------------------------------------------------------
    # Overall results
    # ------------------------------------------------------------------------

    lines.append("---")
    lines.append("")
    lines.append("## 5. Overall Results")
    lines.append("")

    lines.append(
        markdown_metric_table(
            metric_table
        )
    )
    lines.append("")

    # ------------------------------------------------------------------------
    # Primary ablation
    # ------------------------------------------------------------------------

    lines.append("---")
    lines.append("")
    lines.append(
        "## 6. Primary Ablation: Lexical vs Lexical + Infrastructure"
    )
    lines.append("")

    lines.append(
        "The primary experiment evaluates whether the infrastructure-"
        "aware representation changes predictive performance when "
        "added to the lexical representation."
    )
    lines.append("")

    lines.append("### Observed results")
    lines.append("")

    lines.append(
        "| Metric | Lexical | Lexical + Infrastructure | Change |"
    )
    lines.append(
        "|---|---:|---:|---:|"
    )

    lines.append(
        f"| Accuracy | "
        f"{pct(float(lexical['accuracy']))} | "
        f"{pct(float(lexical_infra['accuracy']))} | "
        f"{accuracy_change} |"
    )

    lines.append(
        f"| Precision | "
        f"{pct(float(lexical['precision']))} | "
        f"{pct(float(lexical_infra['precision']))} | "
        f"{precision_change} |"
    )

    lines.append(
        f"| Recall | "
        f"{pct(float(lexical['recall']))} | "
        f"{pct(float(lexical_infra['recall']))} | "
        f"{recall_change} |"
    )

    lines.append(
        f"| F1 | "
        f"{pct(float(lexical['f1']))} | "
        f"{pct(float(lexical_infra['f1']))} | "
        f"{f1_change} |"
    )

    lines.append(
        f"| ROC-AUC | "
        f"{pct(float(lexical['roc_auc']))} | "
        f"{pct(float(lexical_infra['roc_auc']))} | "
        f"{auc_change} |"
    )

    lines.append(
        f"| False negatives | "
        f"{int(lexical['fn'])} | "
        f"{int(lexical_infra['fn'])} | "
        f"{fn_change:+d} |"
    )

    lines.append(
        f"| False positives | "
        f"{int(lexical['fp'])} | "
        f"{int(lexical_infra['fp'])} | "
        f"{fp_change:+d} |"
    )

    lines.append("")

    lines.append(
        "The lexical + infrastructure representation therefore shows "
        f"an observed accuracy change of **{accuracy_change}**, "
        f"recall change of **{recall_change}**, "
        f"F1 change of **{f1_change}**, and "
        f"ROC-AUC change of **{auc_change}** relative to the "
        "lexical-only representation."
    )
    lines.append("")

    lines.append(
        f"False negatives changed from **{int(lexical['fn'])}** "
        f"to **{int(lexical_infra['fn'])}** in this experiment."
    )
    lines.append("")

    lines.append(
        "These values describe the observed result on the fixed "
        "evaluation sample. They do not by themselves establish "
        "causal attribution to individual infrastructure features."
    )
    lines.append("")

    # ------------------------------------------------------------------------
    # Infra-only diagnostic
    # ------------------------------------------------------------------------

    lines.append("---")
    lines.append("")
    lines.append(
        "## 7. Infrastructure-Only Diagnostic"
    )
    lines.append("")

    lines.append(
        f"The Infrastructure-only representation contains "
        f"**{infra_features} features**."
    )
    lines.append("")

    lines.append(
        "Its observed performance is:"
    )
    lines.append("")

    lines.append(
        "| Metric | Infrastructure Only |"
    )
    lines.append(
        "|---|---:|"
    )

    lines.append(
        f"| Accuracy | {infra_accuracy} |"
    )
    lines.append(
        f"| Precision | {infra_precision} |"
    )
    lines.append(
        f"| Recall | {infra_recall} |"
    )
    lines.append(
        f"| F1 | {infra_f1} |"
    )
    lines.append(
        f"| ROC-AUC | {infra_auc} |"
    )
    lines.append(
        f"| False negatives | {int(infra['fn'])} |"
    )
    lines.append(
        f"| False positives | {int(infra['fp'])} |"
    )
    lines.append("")

    lines.append(
        "This experiment answers a different question from the "
        "primary ablation:"
    )
    lines.append("")

    lines.append(
        "> How much standalone predictive signal is available from "
        "the infrastructure representation without URL lexical "
        "features?"
    )
    lines.append("")

    lines.append(
        "The Infrastructure-only result should therefore be "
        "interpreted as a diagnostic measure of standalone "
        "infrastructure signal, rather than as the expected "
        "production prediction configuration."
    )
    lines.append("")

    lines.append(
        "A relatively weak infrastructure-only result would not "
        "invalidate the infrastructure-aware approach. Infrastructure "
        "information may provide complementary contextual information "
        "when combined with lexical characteristics."
    )
    lines.append("")

    lines.append(
        "Conversely, a strong infrastructure-only result would "
        "indicate that the infrastructure representation contains "
        "substantial standalone predictive signal."
    )
    lines.append("")

    lines.append(
        "The actual interpretation should follow the measured result "
        "rather than being assumed in advance."
    )
    lines.append("")

    # ------------------------------------------------------------------------
    # Why primary comparison
    # ------------------------------------------------------------------------

    lines.append("---")
    lines.append("")
    lines.append(
        "## 8. Why the Primary Comparison Remains Lexical + Infrastructure"
    )
    lines.append("")

    lines.append(
        "The principal contribution being evaluated is the addition "
        "of infrastructure intelligence to URL-based phishing analysis."
    )
    lines.append("")

    lines.append(
        "Therefore the primary comparison is:"
    )
    lines.append("")
    lines.append(
        "**Lexical → Lexical + Infrastructure**"
    )
    lines.append("")

    lines.append(
        "The Infrastructure-only experiment is included to "
        "characterize the standalone information content of the "
        "infrastructure feature group."
    )
    lines.append("")

    lines.append(
        "This produces a more complete experimental decomposition:"
    )
    lines.append("")

    lines.append(
        "```text"
    )
    lines.append(
        "Lexical"
    )
    lines.append(
        "   |"
    )
    lines.append(
        "   +-------------------+"
    )
    lines.append(
        "   |                   |"
    )
    lines.append(
        "   v                   v"
    )
    lines.append(
        "Baseline          Infrastructure"
    )
    lines.append(
        "                       |"
    )
    lines.append(
        "                       v"
    )
    lines.append(
        "             Lexical + Infrastructure"
    )
    lines.append(
        "```"
    )
    lines.append("")

    # ------------------------------------------------------------------------
    # Interpretation
    # ------------------------------------------------------------------------

    lines.append("---")
    lines.append("")
    lines.append(
        "## 9. Interpretation and Causal Attribution"
    )
    lines.append("")

    lines.append(
        "The ablation controls:"
    )
    lines.append("")

    lines.append(
        "- sampled URLs;"
    )
    lines.append(
        "- class distribution;"
    )
    lines.append(
        "- train/test partition;"
    )
    lines.append(
        "- XGBoost configuration;"
    )
    lines.append(
        "- preprocessing;"
    )
    lines.append(
        "- feature extraction source."
    )
    lines.append("")

    lines.append(
        "Therefore observed differences between the representations "
        "are empirical differences under a common experimental protocol."
    )
    lines.append("")

    lines.append(
        "However, the experiment does not establish that any "
        "individual infrastructure feature caused a particular "
        "performance change."
    )
    lines.append("")

    lines.append(
        "In particular, the results should not be interpreted as "
        "proof that:"
    )
    lines.append("")

    lines.append(
        "- a particular infrastructure feature is causally responsible;"
    )
    lines.append(
        "- every infrastructure feature contributes positively;"
    )
    lines.append(
        "- infrastructure information always improves phishing detection;"
    )
    lines.append(
        "- the observed result generalizes to every phishing dataset;"
    )
    lines.append(
        "- the result is statistically significant without repeated "
        "trials or appropriate statistical testing."
    )
    lines.append("")

    lines.append(
        "The Infrastructure-only mode is especially useful for "
        "separating standalone infrastructure signal from the "
        "combined infrastructure-aware representation."
    )
    lines.append("")

    # ------------------------------------------------------------------------
    # Full representation
    # ------------------------------------------------------------------------

    lines.append("---")
    lines.append("")
    lines.append(
        "## 10. Full Representation"
    )
    lines.append("")

    lines.append(
        f"The Full mode contains **{full_features} features**."
    )
    lines.append("")

    lines.append(
        "It serves primarily as a reference/reproduction mode for "
        "the complete feature representation."
    )
    lines.append("")

    lines.append(
        "It is not treated as a separate contribution in the "
        "interpretation."
    )
    lines.append("")

    lines.append(
        "The main scientific comparison remains:"
    )
    lines.append("")
    lines.append(
        "**Lexical vs Lexical + Infrastructure**"
    )
    lines.append("")

    # ------------------------------------------------------------------------
    # Feature importance
    # ------------------------------------------------------------------------

    lines.append("---")
    lines.append("")
    lines.append(
        "## 11. Feature Importance"
    )
    lines.append("")

    lines.append(
        "The feature-importance artifact for the lexical + "
        "infrastructure model is generated from the trained "
        "XGBoost model."
    )
    lines.append("")

    lines.append(
        "Feature importance is descriptive model information. "
        "It should not be interpreted as causal evidence that a "
        "feature independently improves phishing detection."
    )
    lines.append("")

    lines.append(
        f"![Top feature importance](figures/{importance_figure.name})"
    )
    lines.append("")

    # ------------------------------------------------------------------------
    # Figures
    # ------------------------------------------------------------------------

    lines.append("---")
    lines.append("")
    lines.append(
        "## 12. Figures"
    )
    lines.append("")

    lines.append(
        "### Overall feature-representation comparison"
    )
    lines.append("")

    lines.append(
        f"![Ablation metrics](figures/{metrics_figure.name})"
    )
    lines.append("")

    lines.append(
        "### Primary infrastructure-aware ablation"
    )
    lines.append("")

    lines.append(
        f"![Primary ablation delta](figures/{delta_figure.name})"
    )
    lines.append("")

    lines.append(
        "### Standalone infrastructure diagnostic"
    )
    lines.append("")

    lines.append(
        f"![Infrastructure diagnostic](figures/{infra_figure.name})"
    )
    lines.append("")

    lines.append(
        "### Lexical + infrastructure feature importance"
    )
    lines.append("")

    lines.append(
        f"![Feature importance](figures/{importance_figure.name})"
    )
    lines.append("")

    # ------------------------------------------------------------------------
    # Reproducibility
    # ------------------------------------------------------------------------

    lines.append("---")
    lines.append("")
    lines.append(
        "## 13. Reproducibility"
    )
    lines.append("")

    lines.append(
        "The experiment stores:"
    )
    lines.append("")

    lines.append(
        "- common sample split manifest;"
    )
    lines.append(
        "- URL SHA-256 fingerprints;"
    )
    lines.append(
        "- canonical feature cache;"
    )
    lines.append(
        "- feature-cache metadata;"
    )
    lines.append(
        "- feature names for every representation;"
    )
    lines.append(
        "- XGBoost parameters;"
    )
    lines.append(
        "- trained models;"
    )
    lines.append(
        "- scalers;"
    )
    lines.append(
        "- confusion matrices;"
    )
    lines.append(
        "- classification reports;"
    )
    lines.append(
        "- feature importance;"
    )
    lines.append(
        "- consolidated ablation results."
    )
    lines.append("")

    lines.append(
        "The canonical feature cache is particularly important "
        "because infrastructure feature collection can involve "
        "cached or externally collected infrastructure observations."
    )
    lines.append("")

    lines.append(
        "Persisting the extracted feature matrix makes the model "
        "comparisons repeatable without recollecting infrastructure "
        "information."
    )
    lines.append("")

    # ------------------------------------------------------------------------
    # HTML limitation
    # ------------------------------------------------------------------------

    lines.append("---")
    lines.append("")
    lines.append(
        "## 14. HTML Feature Limitation"
    )
    lines.append("")

    lines.append(
        "The current controlled ablation does not claim an "
        "independent HTML-content contribution."
    )
    lines.append("")

    lines.append(
        "The historical PCEMS prediction extraction includes HTML "
        "feature dimensions, but the training protocol does not "
        "provide a separate consistent HTML-content dataset for "
        "this ablation."
    )
    lines.append("")

    lines.append(
        "Therefore this experiment does not manufacture an HTML-only "
        "result."
    )
    lines.append("")

    lines.append(
        "The controlled feature-group comparison reported here is:"
    )
    lines.append("")

    lines.append(
        "**Lexical vs Infrastructure vs Lexical + Infrastructure**"
    )
    lines.append("")

    lines.append(
        "The Full representation is retained as a reference/"
        "reproduction mode."
    )
    lines.append("")

    lines.append(
        "A genuine HTML contribution study would require a "
        "consistent URL/HTML dataset and a predefined collection "
        "and evaluation protocol."
    )
    lines.append("")

    # ------------------------------------------------------------------------
    # Dissertation relation
    # ------------------------------------------------------------------------

    lines.append("---")
    lines.append("")
    lines.append(
        "## 15. Relation to the Dissertation"
    )
    lines.append("")

    lines.append(
        "This ablation provides quantitative evidence for the "
        "infrastructure-aware component of the dissertation framework."
    )
    lines.append("")

    lines.append(
        "It evaluates:"
    )
    lines.append("")

    lines.append(
        "1. the lexical baseline;"
    )
    lines.append(
        "2. standalone infrastructure signal;"
    )
    lines.append(
        "3. the combined lexical + infrastructure representation;"
    )
    lines.append(
        "4. the complete feature representation as a reference."
    )
    lines.append("")

    lines.append(
        "The primary result should therefore be presented as a "
        "controlled feature-group ablation rather than as a claim "
        "that infrastructure features universally improve phishing "
        "detection."
    )
    lines.append("")

    # ------------------------------------------------------------------------
    # Conclusion
    # ------------------------------------------------------------------------

    lines.append("---")
    lines.append("")
    lines.append(
        "## 16. Conclusion"
    )
    lines.append("")

    lines.append(
        "The controlled experiment evaluates the infrastructure-aware "
        "feature representation under an identical dataset, sampling, "
        "train/test split, preprocessing and XGBoost configuration."
    )
    lines.append("")

    lines.append(
        "The primary evidence comes from the comparison between the "
        "lexical-only and lexical + infrastructure representations."
    )
    lines.append("")

    lines.append(
        "The Infrastructure-only experiment provides an additional "
        "diagnostic view of the standalone predictive signal contained "
        "in the infrastructure feature group."
    )
    lines.append("")

    lines.append(
        "Together, these experiments provide a more complete empirical "
        "characterization of the infrastructure-aware prediction "
        "component."
    )
    lines.append("")

    return "\n".join(
        lines
    )


# ============================================================================
# Save report
# ============================================================================

def save_report(
    report: str,
) -> None:
    """Save the generated Markdown report."""

    ABLATION_REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        ABLATION_REPORT_PATH,
        "w",
        encoding="utf-8",
    ) as file:

        file.write(
            report
        )

    print(
        "\nReport saved:"
    )

    print(
        ABLATION_REPORT_PATH
    )


# ============================================================================
# Main reporting pipeline
# ============================================================================

def run_report() -> None:
    """Generate all figures and the Markdown report."""

    print("\n" + "=" * 80)
    print("GENERATING ABLATION REPORT")
    print("=" * 80)

    ensure_figures_directory()

    # ------------------------------------------------------------------------
    # Load results
    # ------------------------------------------------------------------------

    results = load_results()

    validate_required_modes(
        results
    )

    print(
        "\nLoaded ablation results:"
    )

    print(
        results[
            [
                "feature_mode",
                "n_features",
                "accuracy",
                "precision",
                "recall",
                "f1",
                "roc_auc",
            ]
        ].to_string(
            index=False
        )
    )

    # ------------------------------------------------------------------------
    # Load cache metadata
    # ------------------------------------------------------------------------

    cache_metadata = (
        load_feature_cache_metadata()
    )

    # ------------------------------------------------------------------------
    # Primary comparison
    # ------------------------------------------------------------------------

    lexical = get_mode_row(
        results,
        FEATURE_MODE_LEXICAL,
    )

    lexical_infra = get_mode_row(
        results,
        FEATURE_MODE_LEXICAL_INFRA,
    )

    # ------------------------------------------------------------------------
    # Generate figures
    # ------------------------------------------------------------------------

    print(
        "\nGenerating overall metrics figure..."
    )

    metrics_figure = (
        create_metrics_figure(
            results
        )
    )

    print(
        "Generating primary ablation figure..."
    )

    delta_figure = (
        create_primary_delta_figure(
            lexical,
            lexical_infra,
        )
    )

    print(
        "Generating infrastructure diagnostic figure..."
    )

    infra_figure = (
        create_infra_diagnostic_figure(
            results
        )
    )

    print(
        "Generating feature-importance figure..."
    )

    importance_figure = (
        create_feature_importance_figure()
    )

    # ------------------------------------------------------------------------
    # Generate report
    # ------------------------------------------------------------------------

    report = generate_report(
        results=results,
        cache_metadata=cache_metadata,
        metrics_figure=metrics_figure,
        delta_figure=delta_figure,
        infra_figure=infra_figure,
        importance_figure=importance_figure,
    )

    save_report(
        report
    )

    # ------------------------------------------------------------------------
    # Final summary
    # ------------------------------------------------------------------------

    print("\n" + "=" * 80)
    print("ABLATION REPORT COMPLETED")
    print("=" * 80)

    print(
        f"\nReport:\n"
        f"{ABLATION_REPORT_PATH}"
    )

    print(
        f"\nFigures:\n"
        f"{FIGURES_DIR}"
    )


# ============================================================================
# Entry point
# ============================================================================

if __name__ == "__main__":

    run_report()