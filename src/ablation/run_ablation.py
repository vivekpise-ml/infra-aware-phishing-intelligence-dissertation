"""
run_ablation.py

Controlled ablation experiment for the phishing risk intelligence
framework.

Experiment modes
----------------
    full
    lexical
    infra
    lexical_infra

Experimental design
-------------------
1. Load the original dataset.
2. Apply the same trusted-data augmentation used by the PCEMS pipeline.
3. Create ONE common stratified 1500-URL sample.
4. Create ONE common 80/20 train/test split.
5. Extract the COMPLETE feature representation exactly once per URL.
6. Persist that representation to sampled_features.csv.
7. Derive lexical, infra and lexical+infra representations by selecting
   columns from that cached feature dataset.
8. Train one independent XGBoost model for each representation.
9. Save metrics and model artifacts.

Important
---------
Infrastructure extraction is performed only during Phase 1.

The existing infrastructure cache:

    data/cache/infra_cache.json

continues to be used by the underlying infrastructure feature code.

The experiment-level cache:

    results/ablation/feature_cache/sampled_features.csv

prevents repeated feature extraction between ablation modes.

This module does not modify:

    predictor.py
    drift_service.py
    campaign modules
    Streamlit application
    production model files
"""


import hashlib
import json
from datetime import datetime

import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)

from xgboost import XGBClassifier


# ============================================================================
# Project imports
# ============================================================================

from src.ablation.ablation_config import (
    ABLATION_MODES,
    DATA_PATH,
    USE_TRUSTED_DATASET,
    SAMPLE_SIZE,
    SAMPLE_RANDOM_STATE,
    TEST_SIZE,
    SPLIT_RANDOM_STATE,
    URL_COLUMN,
    LABEL_COLUMN,
    BENIGN_LABEL,
    MALICIOUS_LABEL,
    XGB_PARAMS,
    USE_STANDARD_SCALER,
    RESULTS_DIR,
    FIGURES_DIR,
    SPLIT_MANIFEST_PATH,
    ABLATION_RESULTS_PATH,
    get_mode_results_dir,
    get_mode_model_dir,
)

from src.features_with_infra import (
    extract_url_features,
    extract_html_features,
)

from src.infrastructure.infra_features import (
    collect_infrastructure_features,
    FEATURE_SECTION_DATA,
)

import src.infrastructure.infra_cache as infra_cache


from src.trusted_dataset import (
    get_trusted_dataframe,
)


# ============================================================================
# Experiment-level feature cache
# ============================================================================

FEATURE_CACHE_DIR = (
    RESULTS_DIR / "feature_cache"
)

FEATURE_CACHE_PATH = (
    FEATURE_CACHE_DIR / "sampled_features.csv"
)

FEATURE_CACHE_METADATA_PATH = (
    FEATURE_CACHE_DIR / "feature_metadata.json"
)

# ============================================================================
# Authoritative training sample
# ============================================================================

TRAINING_SAMPLE_PATH = (
    RESULTS_DIR / "training_sample_1500.csv"
)

# ============================================================================
# Utility functions
# ============================================================================

def sha256_text(
    value: str,
) -> str:
    """
    Return SHA-256 hash for a string.
    """

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def sha256_url_series(
    series: pd.Series,
) -> str:
    """
    Create an ordered SHA-256 fingerprint of a URL series.
    """

    joined = "\n".join(
        series.astype(str).tolist()
    )

    return sha256_text(
        joined
    )


def ensure_output_directories() -> None:
    """
    Create all required experiment output directories.
    """

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    FIGURES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    FEATURE_CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    for mode in ABLATION_MODES:

        get_mode_results_dir(
            mode
        ).mkdir(
            parents=True,
            exist_ok=True,
        )

        get_mode_model_dir(
            mode
        ).mkdir(
            parents=True,
            exist_ok=True,
        )


# ============================================================================
# Dataset preparation
# ============================================================================

def load_base_dataset() -> pd.DataFrame:
    """
    Load and prepare the same dataset representation used by the
    historical PCEMS training pipeline.
    """

    if not DATA_PATH.exists():

        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    print("=" * 80)
    print("LOADING PCEMS DATASET")
    print("=" * 80)

    df = pd.read_csv(
        DATA_PATH
    )

    print(
        f"Original dataset rows : {len(df)}"
    )

    if URL_COLUMN not in df.columns:

        raise ValueError(
            f"Dataset does not contain '{URL_COLUMN}'."
        )

    if LABEL_COLUMN not in df.columns:

        raise ValueError(
            f"Dataset does not contain '{LABEL_COLUMN}'."
        )

    # ------------------------------------------------------------------------
    # Trusted dataset augmentation
    # ------------------------------------------------------------------------

    if USE_TRUSTED_DATASET:

        trusted_df = (
            get_trusted_dataframe()
        )

        print(
            f"Trusted dataset rows  : "
            f"{len(trusted_df)}"
        )

        df = pd.concat(
            [
                df,
                trusted_df,
            ],
            ignore_index=True,
        )

    # ------------------------------------------------------------------------
    # URL normalization
    # ------------------------------------------------------------------------

    df[URL_COLUMN] = (
        df[URL_COLUMN]
        .astype(str)
        .str.strip()
    )

    # ------------------------------------------------------------------------
    # Label normalization
    # ------------------------------------------------------------------------

    df[LABEL_COLUMN] = (
        df[LABEL_COLUMN]
        .astype(str)
        .str.lower()
        .str.strip()
    )

    df = df[
        df[LABEL_COLUMN].isin(
            [
                BENIGN_LABEL,
                MALICIOUS_LABEL,
            ]
        )
    ].copy()

    # ------------------------------------------------------------------------
    # URL deduplication
    # ------------------------------------------------------------------------

    before_dedup = len(df)

    df = df.drop_duplicates(
        subset=[
            URL_COLUMN
        ],
        keep="first",
    ).reset_index(
        drop=True
    )

    print(
        f"Rows before dedup     : "
        f"{before_dedup}"
    )

    print(
        f"Rows after dedup      : "
        f"{len(df)}"
    )

    print(
        "\nLabel distribution:"
    )

    print(
        df[LABEL_COLUMN].value_counts()
    )

    return df


def prepare_common_sample(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create the single common 1500-URL stratified sample.
    """

    print("\n" + "=" * 80)
    print("CREATING COMMON PCEMS SAMPLE")
    print("=" * 80)

    if len(df) < SAMPLE_SIZE:

        raise ValueError(
            f"Dataset contains only {len(df)} rows, "
            f"but SAMPLE_SIZE={SAMPLE_SIZE}."
        )

    sampled_df, _ = train_test_split(
        df,
        train_size=SAMPLE_SIZE,
        stratify=df[LABEL_COLUMN],
        random_state=SAMPLE_RANDOM_STATE,
    )

    sampled_df = (
        sampled_df
        .reset_index(
            drop=True
        )
    )

    print(
        f"Sample size : {len(sampled_df)}"
    )

    print(
        "\nSample label distribution:"
    )

    print(
        sampled_df[
            LABEL_COLUMN
        ].value_counts()
    )

    return sampled_df


def load_authoritative_training_sample() -> pd.DataFrame:
    """
    Load the exact 1500-row sample used by train_xgboost_infra.py.

    This is intentionally used instead of reconstructing the 1500-row
    sample independently. The training sample is the source of truth
    for the ablation experiment.

    Required columns:
        url
        type
        domain

    The 'domain' column is the exact infrastructure lookup domain used
    by train_xgboost_infra.py.
    """

    print("\n" + "=" * 80)
    print("LOADING AUTHORITATIVE TRAINING SAMPLE")
    print("=" * 80)

    if not TRAINING_SAMPLE_PATH.exists():
        raise FileNotFoundError(
            "Authoritative training sample not found:\n"
            f"{TRAINING_SAMPLE_PATH}"
        )

    sampled_df = pd.read_csv(
        TRAINING_SAMPLE_PATH
    )

    required_columns = {
        URL_COLUMN,
        LABEL_COLUMN,
        "domain",
    }

    missing_columns = (
        required_columns
        - set(sampled_df.columns)
    )

    if missing_columns:
        raise ValueError(
            "Authoritative training sample is missing "
            f"required columns: {sorted(missing_columns)}"
        )

    if len(sampled_df) != SAMPLE_SIZE:
        raise ValueError(
            "Authoritative training sample size mismatch.\n"
            f"Expected : {SAMPLE_SIZE}\n"
            f"Found    : {len(sampled_df)}"
        )

    sampled_df = sampled_df.copy()

    print(
        f"Training sample path : "
        f"{TRAINING_SAMPLE_PATH}"
    )

    print(
        f"Training sample rows : "
        f"{len(sampled_df)}"
    )

    print(
        "\nSample label distribution:"
    )

    print(
        sampled_df[
            LABEL_COLUMN
        ].value_counts()
    )

    return sampled_df


def prepare_common_train_test_split(
    sampled_df: pd.DataFrame,
):
    """
    Create the one authoritative train/test split used by every
    ablation mode.
    """

    train_df, test_df = train_test_split(
        sampled_df,
        test_size=TEST_SIZE,
        random_state=SPLIT_RANDOM_STATE,
        stratify=sampled_df[LABEL_COLUMN],
    )

    train_df = train_df.copy()
    test_df = test_df.copy()

    print("\n" + "=" * 80)
    print("CREATING COMMON TRAIN / TEST SPLIT")
    print("=" * 80)

    print(
        f"Training rows : {len(train_df)}"
    )

    print(
        f"Testing rows  : {len(test_df)}"
    )

    print(
        "\nTraining labels:"
    )

    print(
        train_df[
            LABEL_COLUMN
        ].value_counts()
    )

    print(
        "\nTesting labels:"
    )

    print(
        test_df[
            LABEL_COLUMN
        ].value_counts()
    )

    return (
        train_df,
        test_df,
    )


# ============================================================================
# Split manifest
# ============================================================================

def create_split_manifest(
    sampled_df: pd.DataFrame,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create the authoritative split manifest.
    """

    train_urls = set(
        train_df[
            URL_COLUMN
        ].astype(str)
    )

    test_urls = set(
        test_df[
            URL_COLUMN
        ].astype(str)
    )

    records = []

    for _, row in sampled_df.iterrows():

        url = str(
            row[URL_COLUMN]
        )

        if url in train_urls:

            split = "train"

        elif url in test_urls:

            split = "test"

        else:

            raise RuntimeError(
                f"URL is missing from train/test split: {url}"
            )

        records.append(
            {
                "url": url,
                "url_sha256": sha256_text(
                    url
                ),
                "label": row[
                    LABEL_COLUMN
                ],
                "split": split,
            }
        )

    manifest = pd.DataFrame(
        records
    )

    manifest.to_csv(
        SPLIT_MANIFEST_PATH,
        index=False,
    )

    print(
        f"\nSplit manifest saved:\n"
        f"{SPLIT_MANIFEST_PATH}"
    )

    return manifest


# ============================================================================
# Feature-set discovery
# ============================================================================

def discover_feature_sets(
    feature_df: pd.DataFrame,
):
    """
    Discover the ablation feature groups from the canonical 92-feature
    dataframe without performing any additional feature extraction.

    No infrastructure/cache/network operations occur here.
    """

    print("\n" + "=" * 80)
    print("DISCOVERING FEATURE SETS FROM CANONICAL FEATURE CACHE")
    print("=" * 80)

    metadata_columns = {
        URL_COLUMN,
        LABEL_COLUMN,
        "split",
        "training_domain",
    }

    full_names = [
        column
        for column in feature_df.columns
        if column not in metadata_columns
    ]

    if "domain" not in full_names:
        raise RuntimeError(
            "The numeric lexical 'domain' feature is missing "
            "from the canonical feature cache."
        )

    if "training_domain" in full_names:
        raise RuntimeError(
            "The infrastructure lookup domain 'training_domain' "
            "must not be treated as a model feature."
        )

    if len(full_names) != 92:
        raise RuntimeError(
            "Unexpected canonical feature count.\n"
            f"Expected : 92\n"
            f"Found    : {len(full_names)}"
        )

    # ------------------------------------------------------------------------
    # Current canonical feature ordering:
    #
    #   60 URL lexical
    #    5 HTML
    #   27 infrastructure
    #   ----------------
    #   92 total
    #
    # HTML features are intentionally excluded from the lexical+infra
    # ablation.
    # ------------------------------------------------------------------------

    lexical_names = full_names[:60]

    html_names = full_names[60:65]

    infrastructure_names = full_names[65:]

    if len(lexical_names) != 60:
        raise RuntimeError(
            "Unexpected lexical feature count."
        )

    if len(html_names) != 5:
        raise RuntimeError(
            "Unexpected HTML feature count."
        )

    expected_html_features = {
        "num_forms",
        "num_iframes",
        "num_scripts",
        "num_links",
        "has_event_handlers",
    }

    if set(html_names) != expected_html_features:
        raise RuntimeError(
            "Canonical HTML feature set does not match "
            "the expected five HTML features.\n"
            f"Found: {html_names}"
        )

    if len(infrastructure_names) != 27:
        raise RuntimeError(
            "Unexpected infrastructure feature count."
        )

    expected_infrastructure_features = {
        "domain_age_days",
        "has_domain_age",
        "is_new_domain",
        "domain_age_bucket",
        "has_ip",
        "has_asn",
        "is_foreign_hosting",
        "asn_reputation",
        "infra_stability_score",
        "infra_trust_score",
        "infra_trust_score_scaled",
        "trusted_infra_flag",
        "strong_trusted_infra",
        "strong_trusted_infra_weighted",
        "has_ssl",
        "certificate_age_days",
        "certificate_lifetime_days",
        "certificate_remaining_days",
        "self_signed",
        "wildcard_certificate",
        "san_count",
        "ct_has_history",
        "ct_record_count",
        "registration_lifetime_days",
        "registration_remaining_days",
        "privacy_protected",
        "domain_status_count",
    }

    if set(infrastructure_names) != expected_infrastructure_features:
        raise RuntimeError(
            "Canonical infrastructure feature set does not "
            "match the expected 27 infrastructure features.\n"
            f"Found: {infrastructure_names}"
        )

    lexical_infra_names = (
        lexical_names
        + infrastructure_names
    )

    print(
        f"Full feature count           : "
        f"{len(full_names)}"
    )

    print(
        f"Lexical feature count        : "
        f"{len(lexical_names)}"
    )

    print(
        f"Infrastructure feature count : "
        f"{len(infrastructure_names)}"
    )

    print(
        f"Lexical + infrastructure     : "
        f"{len(lexical_infra_names)}"
    )

    return {
        "full": full_names,
        "lexical": lexical_names,
        "infra": infrastructure_names,
        "lexical_infra": lexical_infra_names,
    }

# ============================================================================
# Canonical feature extraction
# ============================================================================

def build_feature_cache(
    sampled_df: pd.DataFrame,
):
    """
    Extract the complete feature representation exactly once per URL.

    IMPORTANT
    ---------
    This feature-engineering path intentionally mirrors the authoritative
    train_xgboost_infra.py pipeline:

        1. URL lexical features
        2. Zero-valued HTML features
        3. Domain extraction
        4. Infrastructure feature collection
        5. Prediction Feature Cache persistence
        6. Infrastructure cache session finalization

    The resulting 92-feature representation is additionally persisted
    into the experiment-level sampled_features.csv so that all ablation
    modes can use exactly the same feature values.

    No ablation mode performs feature extraction again.
    """

    print("\n" + "=" * 80)
    print("PHASE 1: ONE-TIME FEATURE EXTRACTION")
    print("=" * 80)

    feature_rows = []

    total = len(sampled_df)

    extraction_started = datetime.now()

    # ------------------------------------------------------------------------
    # IMPORTANT:
    # Use the same cache-session ownership as train_xgboost_infra.py.
    #
    # The infrastructure package performs observation reuse/collection.
    # This experiment owns persistence of the Prediction DATA Feature Cache.
    # ------------------------------------------------------------------------

    infra_cache.begin_cache_session()

    try:

        for index, (_, sample_row) in enumerate(
            sampled_df.iterrows(),
            start=1,
        ):

            url = str(
                sample_row[URL_COLUMN]
            )

            training_domain = sample_row["domain"]

            try:

                # ----------------------------------------------------------------
                # 1. URL lexical features
                # ----------------------------------------------------------------

                url_features = extract_url_features(
                    url
                )

                # ----------------------------------------------------------------
                # 2. HTML features
                #
                # train_xgboost_infra.py uses URL-only training data, therefore
                # HTML features are represented as zero-valued features.
                # ----------------------------------------------------------------

                html_features = extract_html_features(
                    None
                )


                # ----------------------------------------------------------------
                # 3. Infrastructure feature collection
                #
                # This is the same API and feature section used by
                # train_xgboost_infra.py.
                # ----------------------------------------------------------------

                infra_result = (
                    collect_infrastructure_features(
                        training_domain,
                        FEATURE_SECTION_DATA,
                    )
                )

                if not isinstance(
                    infra_result,
                    dict,
                ):
                    raise TypeError(
                        "collect_infrastructure_features() "
                        "must return a dictionary."
                    )

                infra_features = (
                    infra_result.get(
                        "features",
                        {},
                    )
                )

                # ----------------------------------------------------------------
                # 4. Persist Prediction DATA Feature Cache
                #
                # This is intentionally the same persistence behavior used by
                # train_xgboost_infra.py.
                #
                # save=False is used because the complete cache session is
                # persisted once at the end.
                # ----------------------------------------------------------------

                if infra_features:

                    infra_cache.update_feature_section(
                        training_domain,
                        FEATURE_SECTION_DATA,
                        infra_features,
                        save=False,
                    )

                # ----------------------------------------------------------------
                # 6. Construct the canonical feature representation
                #
                # Ordering follows the same logical composition as the
                # training pipeline:
                #
                # URL + HTML + Infrastructure
                # ----------------------------------------------------------------

                features = {}

                features.update(
                    url_features
                )

                features.update(
                    html_features
                )

                features.update(
                    infra_features
                )

            except Exception as exc:

                raise RuntimeError(
                    "\nFeature extraction failed.\n"
                    f"URL   : {url}\n"
                    f"Error : {exc}"
                ) from exc

            if not isinstance(
                features,
                dict,
            ):
                raise TypeError(
                    "Combined feature representation "
                    "must be a dictionary."
                )

            row = {
                URL_COLUMN: url,
                "training_domain": training_domain,
            }

            row.update(
                features
            )

            feature_rows.append(
                row
            )

            if (
                index % 100 == 0
                or index == total
            ):

                print(
                    f"  Extracted {index}/{total}"
                )

    finally:

        # --------------------------------------------------------------------
        # Persist both infrastructure cache layers exactly once.
        #
        # This mirrors train_xgboost_infra.py.
        # --------------------------------------------------------------------

        infra_cache.end_cache_session()

    feature_df = pd.DataFrame(
        feature_rows
    )

    # ------------------------------------------------------------------------
    # Attach labels
    # ------------------------------------------------------------------------

    label_df = sampled_df[
        [
            URL_COLUMN,
            LABEL_COLUMN,
        ]
    ].copy()

    feature_df = feature_df.merge(
        label_df,
        on=URL_COLUMN,
        how="left",
        validate="one_to_one",
    )

    # ------------------------------------------------------------------------
    # Attach train/test split
    # ------------------------------------------------------------------------

    split_manifest = pd.read_csv(
        SPLIT_MANIFEST_PATH
    )

    feature_df = feature_df.merge(
        split_manifest[
            [
                URL_COLUMN,
                "split",
            ]
        ],
        on=URL_COLUMN,
        how="left",
        validate="one_to_one",
    )

    # ------------------------------------------------------------------------
    # Metadata columns first
    # ------------------------------------------------------------------------

    metadata_columns = [
        URL_COLUMN,
        LABEL_COLUMN,
        "split",
        "training_domain",
    ]

    feature_columns = [
        column
        for column in feature_df.columns
        if column not in metadata_columns
    ]

    feature_df = feature_df[
        metadata_columns
        + feature_columns
    ]

    # ------------------------------------------------------------------------
    # Numeric conversion
    # ------------------------------------------------------------------------

    feature_df[
        feature_columns
    ] = (
        feature_df[
            feature_columns
        ]
        .apply(
            pd.to_numeric,
            errors="coerce",
        )
        .fillna(0)
    )

    # ------------------------------------------------------------------------
    # Save canonical experiment feature cache
    # ------------------------------------------------------------------------

    FEATURE_CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    feature_df.to_csv(
        FEATURE_CACHE_PATH,
        index=False,
    )

    extraction_finished = datetime.now()

    extraction_seconds = (
        extraction_finished
        - extraction_started
    ).total_seconds()

    metadata = {
        "created_at": extraction_finished.isoformat(),
        "extraction_duration_seconds": (
            extraction_seconds
        ),
        "rows": len(feature_df),
        "feature_count": len(feature_columns),
        "feature_names": feature_columns,
        "url_column": URL_COLUMN,
        "label_column": LABEL_COLUMN,
        "split_column": "split",
        "feature_source": (
            "train_xgboost_infra-compatible "
            "feature extraction path"
        ),
        "infrastructure_cache": (
            "Prediction DATA Feature Cache and "
            "shared Observation Cache were used "
            "through the infrastructure cache session."
        ),
    }

    with open(
        FEATURE_CACHE_METADATA_PATH,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metadata,
            file,
            indent=4,
        )

    print(
        "\nCanonical feature cache saved:"
    )

    print(
        FEATURE_CACHE_PATH
    )

    print(
        "\nFeature metadata saved:"
    )

    print(
        FEATURE_CACHE_METADATA_PATH
    )

    print(
        f"\nExtraction duration : "
        f"{extraction_seconds:.2f} seconds"
    )

    print(
        f"Cached rows         : "
        f"{len(feature_df)}"
    )

    print(
        f"Cached features     : "
        f"{len(feature_columns)}"
    )

    return feature_df

# ============================================================================
# Feature-cache validation
# ============================================================================

def validate_feature_cache(
    feature_df: pd.DataFrame,
    sampled_df: pd.DataFrame,
) -> None:
    """
    Verify that the feature cache corresponds exactly to the common sample.
    """

    sampled_urls = set(
        sampled_df[
            URL_COLUMN
        ]
        .astype(str)
    )

    cached_urls = set(
        feature_df[
            URL_COLUMN
        ]
        .astype(str)
    )

    if sampled_urls != cached_urls:

        missing = sorted(
            sampled_urls
            - cached_urls
        )

        extra = sorted(
            cached_urls
            - sampled_urls
        )

        raise RuntimeError(
            "Feature cache URL mismatch.\n"
            f"Missing URLs: {missing[:10]}\n"
            f"Extra URLs  : {extra[:10]}"
        )

    if len(feature_df) != len(
        sampled_df
    ):

        raise RuntimeError(
            "Feature cache row count does not match "
            "the common sample."
        )

    if feature_df[
        URL_COLUMN
    ].duplicated().any():

        raise RuntimeError(
            "Feature cache contains duplicate URLs."
        )

    if feature_df[
        LABEL_COLUMN
    ].isna().any():

        raise RuntimeError(
            "Feature cache contains missing labels."
        )

    if feature_df[
        "split"
    ].isna().any():

        raise RuntimeError(
            "Feature cache contains missing train/test split values."
        )

    print(
        "\nFeature cache validation passed."
    )


# ============================================================================
# Build matrices directly from cache
# ============================================================================

def build_mode_matrices_from_cache(
    feature_df: pd.DataFrame,
    feature_names: list,
):
    """
    Select one ablation representation from the canonical feature cache.

    No feature extraction occurs here.
    """

    missing = [
        name
        for name in feature_names
        if name not in feature_df.columns
    ]

    if missing:

        raise RuntimeError(
            "Required feature columns are missing from "
            "the canonical feature cache:\n"
            f"{missing}"
        )

    train_df = feature_df[
        feature_df["split"] == "train"
    ].copy()

    test_df = feature_df[
        feature_df["split"] == "test"
    ].copy()

    X_train = train_df[
        feature_names
    ].copy()

    X_test = test_df[
        feature_names
    ].copy()

    y_train = train_df[
        LABEL_COLUMN
    ].copy()

    y_test = test_df[
        LABEL_COLUMN
    ].copy()

    return (
        X_train,
        X_test,
        y_train,
        y_test,
    )


# ============================================================================
# Model training
# ============================================================================

def train_and_evaluate(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    feature_names: list,
    mode: str,
) -> dict:
    """
    Train and evaluate one XGBoost model.
    """

    print("\n" + "=" * 80)
    print(
        f"TRAINING ABLATION MODE: {mode}"
    )
    print("=" * 80)

    # ------------------------------------------------------------------------
    # Scaling
    # ------------------------------------------------------------------------

    scaler = None

    if USE_STANDARD_SCALER:

        scaler = StandardScaler()

        X_train_model = (
            scaler.fit_transform(
                X_train
            )
        )

        X_test_model = (
            scaler.transform(
                X_test
            )
        )

    else:

        X_train_model = (
            X_train.values
        )

        X_test_model = (
            X_test.values
        )

    # ------------------------------------------------------------------------
    # Binary labels
    # ------------------------------------------------------------------------

    y_train_binary = (
        y_train
        == MALICIOUS_LABEL
    ).astype(int)

    y_test_binary = (
        y_test
        == MALICIOUS_LABEL
    ).astype(int)

    # ------------------------------------------------------------------------
    # XGBoost
    # ------------------------------------------------------------------------

    model = XGBClassifier(
        **XGB_PARAMS
    )

    model.fit(
        X_train_model,
        y_train_binary,
    )

    # ------------------------------------------------------------------------
    # Predictions
    # ------------------------------------------------------------------------

    probabilities = (
        model.predict_proba(
            X_test_model
        )[:, 1]
    )

    predictions = (
        probabilities >= 0.5
    ).astype(int)

    # ------------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------------

    accuracy = accuracy_score(
        y_test_binary,
        predictions,
    )

    precision = precision_score(
        y_test_binary,
        predictions,
        zero_division=0,
    )

    recall = recall_score(
        y_test_binary,
        predictions,
        zero_division=0,
    )

    f1 = f1_score(
        y_test_binary,
        predictions,
        zero_division=0,
    )

    roc_auc = roc_auc_score(
        y_test_binary,
        probabilities,
    )

    cm = confusion_matrix(
        y_test_binary,
        predictions,
        labels=[0, 1],
    )

    tn, fp, fn, tp = cm.ravel()

    # ------------------------------------------------------------------------
    # Classification report
    # ------------------------------------------------------------------------

    class_report = classification_report(
        y_test_binary,
        predictions,
        target_names=[
            BENIGN_LABEL,
            MALICIOUS_LABEL,
        ],
        output_dict=True,
        zero_division=0,
    )

    # ------------------------------------------------------------------------
    # Feature importance
    # ------------------------------------------------------------------------

    feature_importance = pd.DataFrame(
        {
            "feature": feature_names,
            "importance": (
                model.feature_importances_
            ),
        }
    ).sort_values(
        "importance",
        ascending=False,
    )

    # ------------------------------------------------------------------------
    # Output paths
    # ------------------------------------------------------------------------

    mode_results_dir = (
        get_mode_results_dir(
            mode
        )
    )

    mode_model_dir = (
        get_mode_model_dir(
            mode
        )
    )

    mode_results_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    mode_model_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ------------------------------------------------------------------------
    # Metrics artifact
    # ------------------------------------------------------------------------

    metrics = {
        "feature_mode": mode,
        "n_features": len(
            feature_names
        ),
        "n_train": len(
            X_train
        ),
        "n_test": len(
            X_test
        ),
        "accuracy": float(
            accuracy
        ),
        "precision": float(
            precision
        ),
        "recall": float(
            recall
        ),
        "f1": float(
            f1
        ),
        "roc_auc": float(
            roc_auc
        ),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
        "feature_names": feature_names,
        "xgb_parameters": XGB_PARAMS,
        "scaler": (
            "StandardScaler"
            if USE_STANDARD_SCALER
            else "None"
        ),
    }

    with open(
        mode_results_dir
        / "metrics.json",
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metrics,
            file,
            indent=4,
        )

    # ------------------------------------------------------------------------
    # Feature names
    # ------------------------------------------------------------------------

    with open(
        mode_results_dir
        / "feature_names.json",
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            feature_names,
            file,
            indent=4,
        )

    # ------------------------------------------------------------------------
    # Feature importance
    # ------------------------------------------------------------------------

    feature_importance.to_csv(
        mode_results_dir
        / "feature_importance.csv",
        index=False,
    )

    # ------------------------------------------------------------------------
    # Confusion matrix
    # ------------------------------------------------------------------------

    confusion_df = pd.DataFrame(
        cm,
        index=[
            "actual_benign",
            "actual_malicious",
        ],
        columns=[
            "predicted_benign",
            "predicted_malicious",
        ],
    )

    confusion_df.to_csv(
        mode_results_dir
        / "confusion_matrix.csv"
    )

    # ------------------------------------------------------------------------
    # Classification report
    # ------------------------------------------------------------------------

    classification_df = pd.DataFrame(
        class_report
    ).transpose()

    classification_df.to_csv(
        mode_results_dir
        / "classification_report.csv"
    )

    # ------------------------------------------------------------------------
    # Save model
    # ------------------------------------------------------------------------

    joblib.dump(
        model,
        mode_model_dir
        / "xgboost_model.pkl",
    )

    if scaler is not None:

        joblib.dump(
            scaler,
            mode_model_dir
            / "scaler.pkl",
        )

    joblib.dump(
        feature_names,
        mode_model_dir
        / "feature_names.pkl",
    )

    # ------------------------------------------------------------------------
    # Console summary
    # ------------------------------------------------------------------------

    print(
        f"Feature count : {len(feature_names)}"
    )

    print(
        f"Accuracy      : {accuracy:.4f}"
    )

    print(
        f"Precision     : {precision:.4f}"
    )

    print(
        f"Recall        : {recall:.4f}"
    )

    print(
        f"F1            : {f1:.4f}"
    )

    print(
        f"ROC-AUC       : {roc_auc:.4f}"
    )

    print(
        "\nConfusion Matrix:"
    )

    print(cm)

    return {
        "feature_mode": mode,
        "n_features": len(
            feature_names
        ),
        "n_train": len(
            X_train
        ),
        "n_test": len(
            X_test
        ),
        "accuracy": float(
            accuracy
        ),
        "precision": float(
            precision
        ),
        "recall": float(
            recall
        ),
        "f1": float(
            f1
        ),
        "roc_auc": float(
            roc_auc
        ),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


# ============================================================================
# Main experiment
# ============================================================================

def run_ablation() -> pd.DataFrame:
    """
    Execute the complete controlled ablation experiment.
    """

    print("\n")
    print("=" * 80)
    print("CONTROLLED PCEMS ABLATION EXPERIMENT")
    print("=" * 80)

    ensure_output_directories()

    # =========================================================================
    # PHASE 1 - DATASET
    # =========================================================================

    # df = load_base_dataset()

    sampled_df = load_authoritative_training_sample()

    train_df, test_df = (
        prepare_common_train_test_split(
            sampled_df
        )
    )

    # =========================================================================
    # COMMON SPLIT MANIFEST
    # =========================================================================

    create_split_manifest(
        sampled_df,
        train_df,
        test_df,
    )

    sampled_fingerprint = (
        sha256_url_series(
            sampled_df[
                URL_COLUMN
            ]
        )
    )

    train_fingerprint = (
        sha256_url_series(
            train_df[
                URL_COLUMN
            ]
        )
    )

    test_fingerprint = (
        sha256_url_series(
            test_df[
                URL_COLUMN
            ]
        )
    )

    print(
        "\nSplit fingerprints:"
    )

    print(
        f"Sample : {sampled_fingerprint}"
    )

    print(
        f"Train  : {train_fingerprint}"
    )

    print(
        f"Test   : {test_fingerprint}"
    )

    # =========================================================================
    # PHASE 1 - ONE-TIME FEATURE EXTRACTION
    # =========================================================================

    feature_df = build_feature_cache(
        sampled_df
    )

    # =========================================================================
    # PHASE 1 - FEATURE SET DISCOVERY
    #
    # Discover the feature subsets after the canonical feature dataset has
    # been created. The actual ablation models never re-extract features.
    # =========================================================================


    mode_feature_names = (
        discover_feature_sets(
            feature_df
        )
    )

    # =========================================================================
    # FEATURE CACHE VALIDATION
    # =========================================================================

    validate_feature_cache(
        feature_df=feature_df,
        sampled_df=sampled_df,
    )

    # =========================================================================
    # VALIDATE COMPLETE FEATURE SET
    # =========================================================================

    cached_feature_names = [
        column
        for column in feature_df.columns
        if column not in [
            URL_COLUMN,
            LABEL_COLUMN,
            "split",
            "training_domain",
        ]
    ]

    full_feature_names = (
        mode_feature_names[
            "full"
        ]
    )

    if set(
        cached_feature_names
    ) != set(
        full_feature_names
    ):

        missing = sorted(
            set(full_feature_names)
            - set(cached_feature_names)
        )

        extra = sorted(
            set(cached_feature_names)
            - set(full_feature_names)
        )

        raise RuntimeError(
            "Canonical feature cache does not match "
            "the discovered full feature representation.\n"
            f"Missing: {missing}\n"
            f"Extra  : {extra}"
        )

    # =========================================================================
    # PHASE 2 - TRAIN ALL ABLATION MODES
    # =========================================================================

    print("\n" + "=" * 80)
    print(
        "PHASE 2: ABLATION MODELS FROM CACHED FEATURES"
    )
    print("=" * 80)

    all_results = []

    for mode in ABLATION_MODES:

        print("\n")
        print("#" * 80)
        print(
            f"ABLATION MODE: {mode}"
        )
        print("#" * 80)

        feature_names = (
            mode_feature_names[
                mode
            ]
        )

        print(
            f"Using cached features: "
            f"{len(feature_names)}"
        )

        (
            X_train,
            X_test,
            y_train,
            y_test,
        ) = build_mode_matrices_from_cache(
            feature_df=feature_df,
            feature_names=feature_names,
        )

        result = train_and_evaluate(
            X_train=X_train,
            X_test=X_test,
            y_train=y_train,
            y_test=y_test,
            feature_names=feature_names,
            mode=mode,
        )

        # ---------------------------------------------------------------------
        # Reproducibility information
        # ---------------------------------------------------------------------

        result[
            "sample_size"
        ] = SAMPLE_SIZE

        result[
            "sample_random_state"
        ] = SAMPLE_RANDOM_STATE

        result[
            "test_size"
        ] = TEST_SIZE

        result[
            "split_random_state"
        ] = SPLIT_RANDOM_STATE

        result[
            "sample_fingerprint"
        ] = sampled_fingerprint

        result[
            "train_fingerprint"
        ] = train_fingerprint

        result[
            "test_fingerprint"
        ] = test_fingerprint

        all_results.append(
            result
        )

    # =========================================================================
    # CONSOLIDATED RESULTS
    # =========================================================================

    results_df = pd.DataFrame(
        all_results
    )

    # =========================================================================
    # PRIMARY DELTAS VS LEXICAL
    # =========================================================================

    if (
        "lexical"
        in results_df[
            "feature_mode"
        ].values
        and
        "lexical_infra"
        in results_df[
            "feature_mode"
        ].values
    ):

        lexical_row = (
            results_df[
                results_df[
                    "feature_mode"
                ]
                == "lexical"
            ]
            .iloc[0]
        )

        results_df[
            "delta_vs_lexical_accuracy"
        ] = (
            results_df[
                "accuracy"
            ]
            - lexical_row[
                "accuracy"
            ]
        )

        results_df[
            "delta_vs_lexical_precision"
        ] = (
            results_df[
                "precision"
            ]
            - lexical_row[
                "precision"
            ]
        )

        results_df[
            "delta_vs_lexical_recall"
        ] = (
            results_df[
                "recall"
            ]
            - lexical_row[
                "recall"
            ]
        )

        results_df[
            "delta_vs_lexical_f1"
        ] = (
            results_df[
                "f1"
            ]
            - lexical_row[
                "f1"
            ]
        )

        results_df[
            "delta_vs_lexical_roc_auc"
        ] = (
            results_df[
                "roc_auc"
            ]
            - lexical_row[
                "roc_auc"
            ]
        )

    # =========================================================================
    # SAVE CONSOLIDATED RESULTS
    # =========================================================================

    ABLATION_RESULTS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    results_df.to_csv(
        ABLATION_RESULTS_PATH,
        index=False,
    )

    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================

    print("\n" + "=" * 80)
    print("ABLATION EXPERIMENT COMPLETED")
    print("=" * 80)

    print(
        "\nCanonical feature cache:"
    )

    print(
        FEATURE_CACHE_PATH
    )

    print(
        "\nConsolidated results:"
    )

    print(
        ABLATION_RESULTS_PATH
    )

    print(
        "\nResults summary:"
    )

    print(
        results_df[
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
        ].to_string(
            index=False
        )
    )

    return results_df


# ============================================================================
# Entry point
# ============================================================================

if __name__ == "__main__":

    try:

        run_ablation()

    except Exception as exc:

        print("\n" + "=" * 80)
        print("ABLATION EXPERIMENT FAILED")
        print("=" * 80)

        print(
            f"\nError: {exc}"
        )

        raise