import pandas as pd
import joblib
import os
import time

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
    roc_auc_score
)
from xgboost import XGBClassifier

# for adding trusted infra url dataset in original dataset
from src.trusted_dataset import get_trusted_dataframe

from src.features_with_infra import (
    extract_url_features,
    extract_html_features
)

from src.infrastructure.infra_features import (
    collect_infrastructure_features,
    FEATURE_SECTION_DATA
)

from src.infrastructure import infra_cache

from src.config import DATA_PATH, MODEL_DIR

def train_xgboost_infra():

    df = pd.read_csv(DATA_PATH)

    
    # ---------------------------------------------------
    # For adding Trusted Infra URLs in original dataset
    # ---------------------------------------------------
    # ✅ Add trusted dataset
    df_trusted = get_trusted_dataframe()

    df = pd.concat([df, df_trusted], ignore_index=True)

    # Remove duplicates (important)
    df = df.drop_duplicates(subset=["url"], keep="first")

    print(f"Dataset size after adding trusted: {len(df)}")

    # detect label column
    
    label_col = "type"

    # normalize string labels
    df[label_col] = df[label_col].astype(str).str.lower()

    # keep only valid rows
    df = df[df[label_col].isin(["benign", "malicious"])]


    # for infra feature
    # 🔥 ADD THIS RIGHT AFTER LOADING
    #df = df.sample(500, random_state=42)

    # this is for getting correct ratio of original dataset of benign/malicious in the 
    # 1500 samples or any number of samples from the original dataset
    
    print("\nLABEL DISTRIBUTION BEFORE SAMPLING:")
    print(df[label_col].value_counts())

    df, _ = train_test_split(
        df,
        train_size=1500,
        stratify=df[label_col],
        random_state=42
    )

    print("\nLABEL DISTRIBUTION AFTER SAMPLING:")
    print(df[label_col].value_counts())

    print("Sampled dataset size:", len(df))
    # printing trusted UELs in sample
    print("Trusted URLs in sample:",
        df["url"].str.contains("google|amazon|microsoft|github|paypal", case=False, na=False).sum())

    # -----------------------------------------
    # DOMAIN DEDUP SANITY CHECK
    # -----------------------------------------
    df["domain"] = (
        df["url"]
        .str.extract(r"https?://([^/]+)", expand=False)
        .fillna(df["url"])
    )

    print("Unique domains:", df["domain"].nunique())
    print("Total URLs:", len(df))

    # detect label
   
    '''
    df[label_col] = df[label_col].astype(str).str.lower()
    df = df[df[label_col].isin(["benign", "malicious"])]

    y = df[label_col].map({"benign": 0, "malicious": 1})
    '''

    
    # map to numeric
    y = df[label_col].map({"benign": 0, "malicious": 1})

    print("\nUNIQUE LABELS:", y.unique())
    print("LABEL COUNTS:\n", y.value_counts())

    # align dataframe
    df = df.loc[y.index]

    print("After label cleaning:", len(df))

    # extract features
    '''
    features = []
    for url in df["url"]:
        features.append(extract_all_features(url))
    '''

    features = []
    valid_indices = []

    start_time = time.time()

    total = len(df)

    trusted_running = 0
    strong_trusted_running = 0

    # -------------------------------------------------
    # Infrastructure Cache Session
    # -------------------------------------------------
    #
    # Load Feature Cache and Observation Cache once
    # before processing the training batch.
    #
    # All URL-level cache operations during training
    # will then use the in-memory caches.
    # -------------------------------------------------

    infra_cache.begin_cache_session()

    for i, url in enumerate(df["url"]):
            
        if i % 50 == 0 and i > 0:

            elapsed = time.time() - start_time

            processed = i + 1
            remaining = total - processed

            avg_time = (
                elapsed / processed
                if processed > 0
                else 0
            )

            est_remaining = remaining * avg_time

            print(
                f"Processed {i} URLs | "
                f"Time elapsed: {elapsed:.2f} sec"
            )

            print(f"\n🔄 Progress: {processed}/{total}")
            print(f"⏱️ Elapsed: {elapsed:.2f} sec")
            print(f"📊 Avg per sample: {avg_time:.2f} sec")
            print(f"⏳ Remaining samples: {remaining}")
            print(
                f"⏳ Estimated remaining time: "
                f"{est_remaining / 60:.2f} min"
            )

        try:

            # -------------------------------------------------
            # 1. Existing frozen URL features
            # -------------------------------------------------

            url_features = extract_url_features(url)

            # -------------------------------------------------
            # 2. Existing frozen HTML feature behaviour
            #
            # The training dataset does not provide HTML.
            # Therefore preserve the exact zero-filled
            # behaviour of the old extract_all_features().
            # -------------------------------------------------

            html_features = {
                "num_forms": 0,
                "num_iframes": 0,
                "num_scripts": 0,
                "num_links": 0,
                "has_event_handlers": 0
            }

            # -------------------------------------------------
            # 3. Infrastructure Package
            #
            # The Infrastructure Package is responsible for
            # the cache hierarchy:
            #
            # Feature Cache
            #       ↓
            # Observation Cache
            #       ↓
            # Network / WHOIS / SSL / CT
            #
            # Training does not directly access collectors.
            # -------------------------------------------------

            domain = df.iloc[i]["domain"]

            infra_result = collect_infrastructure_features(
                domain,
                FEATURE_SECTION_DATA
            )

            infra_features = infra_result["features"]

            # -------------------------------------------------
            # Persist Prediction DATA Feature Cache
            # -------------------------------------------------
            #
            # Training follows the same Infrastructure Cache
            # ownership contract as Prediction:
            #
            #   Feature Cache
            #        ↓
            #   Observation Cache
            #        ↓
            #   Collectors when required
            #
            # collect_infrastructure_features() deliberately
            # does not persist the Feature Cache.
            # The DATA section is owned by this training
            # pipeline and therefore persisted here.
            # -------------------------------------------------

            if infra_features:
                infra_cache.update_feature_section(
                    domain,
                    FEATURE_SECTION_DATA,
                    infra_features,
                    save=False
                )

            # -------------------------------------------------
            # 4. Combine URL + HTML + infrastructure features
            # -------------------------------------------------

            feat = {}

            feat.update(url_features)
            feat.update(html_features)
            feat.update(infra_features)

            if feat:

                features.append(feat)
                valid_indices.append(i)

                # ---------------------------------------------
                # LIVE TRUST COUNTING
                # ---------------------------------------------

                if feat.get(
                    "infra_trust_score",
                    0
                ) >= 3:

                    trusted_running += 1

                if feat.get(
                    "strong_trusted_infra",
                    0
                ) == 1:

                    strong_trusted_running += 1

        except Exception as e:

            print(
                "ERROR:",
                url,
                e
            )

        # -----------------------------------------------------
        # Trusted statistics
        # -----------------------------------------------------

        if i % 50 == 0 and i > 0:

            print(
                f"🔥 Trusted so far: "
                f"{trusted_running}"
            )

            print(
                f"💪 Strong trusted so far: "
                f"{strong_trusted_running}"
            )

            print(
                f"📊 Trusted ratio: "
                f"{trusted_running / (i + 1):.3f}"
            )

    # -------------------------------------------------
    # End Infrastructure Cache Session
    # -------------------------------------------------
    #
    # Persist both caches once after the complete
    # training feature-extraction batch.
    # -------------------------------------------------

    infra_cache.end_cache_session()

    print(
        "\nInfrastructure cache session completed."
    )

    print(
        "Feature Cache and Observation Cache "
        "persisted."
    )

    print(f"Total feature extraction time: {time.time() - start_time:.2f} sec")

    # -----------------------------------------
    # INFRASTRUCTURE CACHE STATS
    # -----------------------------------------
    #
    # Statistics are maintained by the
    # Infrastructure Cache implementation.

    #
    # Cache statistics are provided by the
    # Infrastructure Package.
    #
    # The cache hierarchy is:
    #
    # Feature Cache
    #       ↓
    # Observation Cache
    #       ↓
    # Network / WHOIS / SSL / CT
    #
    # train_xgboost_infra.py only reads the
    # statistics. It does not calculate or
    # modify cache statistics.

    # -----------------------------------------

    cache_stats = infra_cache.cache_statistics()

    print("\n=== INFRASTRUCTURE CACHE STATISTICS ===")

    feature_stats = cache_stats["feature_cache"]

    print(
        "Feature Cache Hits      :",
        feature_stats["hits"]
    )

    print(
        "Feature Cache Misses    :",
        feature_stats["misses"]
    )

    print(
        "Feature Cache Hit Rate  :",
        f"{feature_stats['hit_rate']:.2%}"
    )

    print("\nObservation Cache:")

    for collector, stats in (
        cache_stats["observation_cache"].items()
    ):
        print(
            f"  {collector.upper():8s} "
            f"Hits={stats['hits']} "
            f"Misses={stats['misses']} "
            f"Stale={stats['stale']} "
            f"Hit Rate={stats['effective_hit_rate']:.2%}"
        )

    print("\n=== INFRASTRUCTURE FEATURE EXTRACTION COMPLETE ===")

    # 🔍 DEBUG: count strong trusted infra samples
    trusted_count = sum(
        1 for f in features if f.get("infra_trust_score", 0) >= 3
    )

    strong_trusted_count = sum(
        1 for f in features if f.get("strong_trusted_infra", 0) == 1
    )

    print("Trusted infra count (score>=3):", trusted_count)
    print("Strong trusted infra count:", strong_trusted_count)

    # Align labels
    df = df.iloc[valid_indices].reset_index(drop=True)
    y = y.iloc[valid_indices].reset_index(drop=True)

    X = pd.DataFrame(features).fillna(0)
    X = X.reset_index(drop=True)

    print("Final dataset size:", len(X))

    #X = pd.DataFrame(features).fillna(0)

    # Debug for seeing the features and infra features
    print("\n=== SANITY: columns with 'infra' ===")
    infra_cols = [c for c in X.columns if "infra" in c]
    print(infra_cols)

    print("\nVARIANCE:")
    print(X[infra_cols].var())

    print("\n=== SANITY: variance of infra cols ===")
    print(X[infra_cols].var().sort_values())

    print("\n=== SANITY: sample rows (infra only) ===")
    print(X[infra_cols].head(10))

    print("\n=== INFRA vs LABEL ===")
    print(pd.crosstab(X["infra_trust_score"], y))

    # save feature names
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(list(X.columns), f"{MODEL_DIR}/xgb_infra_feature_names.pkl")

    # split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("\n=== TRAIN / TEST LABEL DISTRIBUTION ===")
    print("Train:\n", y_train.value_counts())
    print("Test:\n", y_test.value_counts())

    # scale
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    joblib.dump(scaler, f"{MODEL_DIR}/xgb_infra_scaler.pkl")

    # model
    model = XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.1,
        eval_metric="logloss",
        random_state=42
    )

    model.fit(X_train_scaled, y_train)

    importance = pd.Series(
        model.feature_importances_,
        index=X.columns
    ).sort_values(ascending=False)

    print("\n🔝 Top 15 Features:")
    print(importance.head(15))

    print("\n🔻 Bottom 10 Features:")
    print(importance.tail(10))

    # ---------------------------------------------------
    # 🔍 GOOGLE-LIKE SAMPLE CHECK (CRITICAL)
    # ---------------------------------------------------
    print("\n=== GOOGLE-LIKE SAMPLE CHECK ===")

    # Take a real sample and override key features
    sample = X.iloc[0].copy()

    # Simulate google.com characteristics
    sample["query_length"] = 0
    sample["equal_count"] = 0
    sample["subdomain_count"] = 0
    sample["param_count"] = 0

    sample["infra_trust_score"] = 3
    sample["infra_stability_score"] = 1
    sample["strong_trusted_infra"] = 1

    # if exists (safe check)
    if "strong_trusted_infra_weighted" in sample:
        sample["strong_trusted_infra_weighted"] = 50

    sample_df = pd.DataFrame([sample])
    sample_scaled = scaler.transform(sample_df)

    prob = model.predict_proba(sample_scaled)[0][1]

    print(f"Google-like malicious probability: {prob:.4f}")

    preds = model.predict(X_test_scaled)
    probs = model.predict_proba(X_test_scaled)[:, 1]

    accuracy = accuracy_score(y_test, preds)
    precision = precision_score(y_test, preds)
    recall = recall_score(y_test, preds)
    f1 = f1_score(y_test, preds)
    roc_auc = roc_auc_score(y_test, probs)

    print("\n========== MODEL PERFORMANCE ==========")
    print(f"Accuracy : {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall   : {recall:.4f}")
    print(f"F1-Score : {f1:.4f}")
    print(f"ROC-AUC  : {roc_auc:.4f}")

    print("\nConfusion Matrix")
    print(confusion_matrix(y_test, preds))

    print("\nClassification Report")
    print(classification_report(y_test, preds))
    
    joblib.dump(model, f"{MODEL_DIR}/xgboost_infra_model.pkl")
    print("💾 Saved XGBoost model")


if __name__ == "__main__":
    train_xgboost_infra()