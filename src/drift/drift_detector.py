"""
drift_detector.py

Main orchestration module for statistical drift detection.

Responsibilities
----------------
- Feature-wise drift analysis
- Overall drift computation
- Severity classification
- Retraining recommendation
- Analyst-friendly output

Author : Vivek Pise
Project: Infrastructure-Aware Drift-Adaptive Multimodal
         Phishing Risk Intelligence Framework
"""

from typing import Dict

import pandas as pd

import json
from pathlib import Path
from datetime import datetime

from .psi import (
    calculate_feature_psi,
    overall_psi,
    top_drifting_features
)

from .divergence import (
    calculate_feature_kl,
    calculate_feature_js,
    overall_kl,
    overall_js
)

from .thresholds import (
    build_decision
)


# ---------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------

def compute_drift_score(
    reference_features: pd.DataFrame,
    current_features: pd.DataFrame,
    bins: int = 10,
    top_n: int = 10,
    reference_name: str = "Training Dataset",
    current_name: str = "Current Dataset"
) -> Dict:
    """
    Compute complete statistical drift analysis.

    Parameters
    ----------
    reference_features : pandas.DataFrame

    current_features : pandas.DataFrame

    bins : int
        Histogram bins.

    top_n : int
        Number of top drifting features.

    Returns
    -------
    dict

    Example
    -------
    {
        "psi": ...,
        "js_distance": ...,
        "kl_divergence": ...,
        "overall_score": ...,
        "severity": ...,
        "requires_retraining": ...,
        "recommendation": ...,
        "feature_drift": {...},
        "top_drifting_features": [...]
    }
    """

    if list(reference_features.columns) != list(current_features.columns):
        raise ValueError(
            "Reference and current feature sets "
            "must contain identical columns."
        )
    
    # ---------------------------------------------------------
    # Keep only numeric feature columns
    # (Ignore metadata columns such as URL)
    # ---------------------------------------------------------

    reference_features = reference_features.select_dtypes(
        include="number"
    )

    current_features = current_features.select_dtypes(
        include="number"
    )
    
    # -------------------------------------------------------------
    # Feature-wise metrics
    # -------------------------------------------------------------

    psi_scores = calculate_feature_psi(
        reference_features,
        current_features,
        bins=bins
    )

    kl_scores = calculate_feature_kl(
        reference_features,
        current_features,
        bins=bins
    )

    js_scores = calculate_feature_js(
        reference_features,
        current_features,
        bins=bins
    )

    # -------------------------------------------------------------
    # Overall metrics
    # -------------------------------------------------------------

    overall_psi_score = overall_psi(
        psi_scores
    )

    overall_kl_score = overall_kl(
        kl_scores
    )

    overall_js_score = overall_js(
        js_scores
    )

    # -------------------------------------------------------------
    # Decision layer
    # -------------------------------------------------------------

    decision = build_decision(
        overall_psi_score,
        overall_js_score,
        overall_kl_score
    )

    # -------------------------------------------------------------
    # Final result
    # -------------------------------------------------------------

    result = {

        # -------------------------------------------------------------
        # Metadata
        # -------------------------------------------------------------

        "analysis_version": "1.0",

        "analysis_timestamp":
            datetime.now().isoformat(),

        "reference_dataset":
            reference_name,

        "current_dataset":
            current_name,
        
        "reference_samples":
            len(reference_features),

        "current_samples":
            len(current_features),

        "feature_count":
            len(reference_features.columns),

        # Overall metrics
        "psi": overall_psi_score,

        "js_distance": overall_js_score,

        "kl_divergence": overall_kl_score,

        # Decision output
        "overall_score":
            decision["overall_score"],

        "severity":
            decision["severity"],

        "requires_retraining":
            decision["requires_retraining"],

        "recommendation":
            decision["recommendation"],

        # Feature-level analysis
        "feature_drift":
            psi_scores,

        "feature_kl":
            kl_scores,

        "feature_js":
            js_scores,

        "top_drifting_features":
            top_drifting_features(
                psi_scores,
                top_n=top_n
            )

    }

    return result


# ---------------------------------------------------------------------
# Summary Printer (Useful for Testing)
# ---------------------------------------------------------------------

def print_drift_summary(
    drift_result: Dict
):
    """
    Print a concise drift summary.

    Useful during development and debugging.
    """

    print("\n==============================")
    print("DRIFT DETECTION SUMMARY")
    print("==============================")

    print(f"PSI             : {drift_result['psi']:.4f}")
    print(f"JS Distance     : {drift_result['js_distance']:.4f}")
    print(f"KL Divergence   : {drift_result['kl_divergence']:.4f}")

    print("--------------------------------")

    print(f"Overall Score   : {drift_result['overall_score']:.4f}")
    print(f"Severity        : {drift_result['severity']}")
    print(f"Retraining      : {drift_result['requires_retraining']}")

    print("--------------------------------")

    print("Recommendation")

    print(drift_result["recommendation"])

    print("--------------------------------")

    print("Top Drifting Features")

    for feature, score in drift_result["top_drifting_features"]:

        print(f"{feature:30s} {score:.4f}")

    print("==============================")

# ---------------------------------------------------------------------
# Save Drift Report
# ---------------------------------------------------------------------

def save_drift_report(
    drift_result: Dict,
    output_file: str = "drift_report.json"
):
    """
    Save drift analysis results as a JSON report.

    Parameters
    ----------
    drift_result : Dict

    output_file : str

    Returns
    -------
    None
    """

    Path(output_file).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(output_file, "w") as fp:

        json.dump(
            drift_result,
            fp,
            indent=4
        )