# src/inference/predictor.py

import joblib
import pandas as pd
import numpy as np
#from src.features import extract_all_features
# Conference-era URL + HTML feature extraction
from src.features_with_infra import (
    extract_url_features,
    extract_html_features,
)

from src.charcnn_predict import predict_single
from src.config import MODEL_DIR

# New Infrastructure Package
from src.infrastructure.infra_features import (
    collect_infrastructure_features,
    FEATURE_SECTION_DATA,
)

class PhishingPredictor:

    def __init__(self):
        # Load main model (XGBoost)
        '''
        self.model = joblib.load(f"{MODEL_DIR}/xgboost_model.pkl")
        self.scaler = joblib.load(f"{MODEL_DIR}/classical_scaler.pkl")
        self.feature_names = joblib.load(f"{MODEL_DIR}/classical_feature_names.pkl")
        '''

        self.model = joblib.load(f"{MODEL_DIR}/xgboost_infra_model.pkl")
        self.scaler = joblib.load(f"{MODEL_DIR}/xgb_infra_scaler.pkl")
        self.feature_names = joblib.load(f"{MODEL_DIR}/xgb_infra_feature_names.pkl")

        # debug 
        print("MODEL FEATURES:", self.model.n_features_in_)
        print("FEATURE NAMES:", len(self.feature_names))

    def extract_features(self, url, html=None):

        # =========================================================
        # CONFERENCE-ERA FEATURE EXTRACTION
        # =========================================================
        # Preserve the original URL + HTML feature construction.
        # Training uses the same URL features and zero-valued HTML
        # features when HTML is unavailable.
        # =========================================================

        feats = {}

        # ---------------------------------------------------------
        # 1. URL features — conference-era frozen feature set
        # ---------------------------------------------------------

        url_features = extract_url_features(url)

        feats.update(url_features)

        # ---------------------------------------------------------
        # 2. HTML features — preserve conference-era behaviour
        # ---------------------------------------------------------
        #
        # If HTML is supplied, extract the five HTML features.
        #
        # If HTML is not supplied, use the same zero values used
        # by train_xgboost_infra.py.
        # ---------------------------------------------------------

        if html:

            html_features = extract_html_features(html)

            feats.update(html_features)

        else:

            feats.update({
                "num_forms": 0,
                "num_iframes": 0,
                "num_scripts": 0,
                "num_links": 0,
                "has_event_handlers": 0,
            })

        # =========================================================
        # NEW INFRASTRUCTURE PACKAGE
        # =========================================================
        #
        # Infrastructure is no longer obtained through the old
        # features_with_infra.extract_all_features() interface.
        #
        # The Infrastructure Package now owns:
        #
        #   Feature Cache
        #   Observation Cache
        #   Network
        #   WHOIS
        #   SSL
        #   CT
        #
        # collect_infrastructure_features() returns:
        #
        #   {
        #       "features": {...}
        #       ...
        #   }
        #
        # =========================================================

        from urllib.parse import urlparse

        normalized_url = url

        if not normalized_url.startswith(("http://", "https://")):
            normalized_url = "http://" + normalized_url

        parsed = urlparse(normalized_url)

        domain = parsed.netloc.replace("www.", "")

        infra_result = collect_infrastructure_features(
            domain,
            FEATURE_SECTION_DATA
        )

        infra_features = infra_result.get(
            "features",
            {}
        )

        # Add the complete infrastructure feature set.
        feats.update(infra_features)

        # =========================================================
        # DEBUG GOOGLE FEATURES
        # =========================================================

        if "google.com" in url:

            print("\n🔎 FEATURES FOR GOOGLE:")

            for k, v in feats.items():

                if k in [
                    "equal_count",
                    "subdomain_count",
                    "param_count",
                    "query_length",
                ]:

                    print(f"{k}: {v}")

        # =========================================================
        # FEATURE MATRIX
        # =========================================================

        X = pd.DataFrame([feats])
        
        print("RAW FEATURE COUNT:", len(feats))
        print("RAW KEYS:", list(feats.keys()))

        # Align features
        '''
        for col in self.feature_names:
            if col not in X.columns:
                X[col] = 0

        X = X[self.feature_names]
        '''

        # Align features in more cleaner and safer way
        # Handles missing columns, Drops extra columns, Ensures correct order, Cleaner
        X = X.reindex(columns=self.feature_names, fill_value=0)

        print("MISSING FEATURES:", set(self.feature_names) - set(X.columns))

        print("EXTRA FEATURES:",
          set(feats.keys()) - set(self.feature_names))

        # before scaling 
        # Prevents: string contamination, NaN issues, silent bugs
        X = X.apply(pd.to_numeric, errors="coerce").fillna(0)

        X = self.scaler.transform(X)

        return X, feats

    def predict(self, url, html=None):
        X, raw_features = self.extract_features(url, html)

        prob = self.model.predict_proba(X)[0][1]

        # ---------------------------------------------------
        # 🔥 ADAPTIVE DECISION LAYER (NEW)
        # ---------------------------------------------------

        # Infra confidence (0–1)
        infra_score = raw_features.get("infra_trust_score", 0)
        infra_conf = infra_score / 3.0  # normalize

        # Adjust model risk using infra confidence
        final_risk = prob * (1 - 0.6 * infra_conf)

        # Optional: stability boost (makes strong infra more reliable)
        if raw_features.get("infra_stability_score", 0) == 1:
            final_risk *= 0.8

        # ---------------------------------------------------
        # FINAL LABEL DECISION
        # ---------------------------------------------------
        if final_risk < 0.4:
            label = "benign"
            tier = "LOW"
        elif final_risk > 0.75:
            label = "malicious"
            tier = "HIGH"
        else:
            label = "suspicious"
            tier = "MEDIUM"

        risk_tier = PhishingPredictor.get_risk_tier(final_risk)

        # DEBUG (important)
        print(f"DEBUG: model_prob={prob:.4f}, final_risk={final_risk:.4f}, label={label}")

        # for Debug
        print(f"DEBUG: prob={prob:.4f}, label={label}")

        return {
            "url": url,
            "label": label,
            "model_risk": float(prob),
            "final_risk": float(final_risk),
            "features": raw_features,
            "risk_tier": tier,
            "X" : X
        }
    
    @staticmethod
    def get_risk_tier(score):
        if score > 0.8:
            return "HIGH"
        elif score > 0.5:
            return "MEDIUM"
        else:
            return "LOW"


    def predict_batch(self, urls_df):
        """
        Predict phishing risk for a batch of URLs.

        Parameters
        ----------
        urls_df : pandas.DataFrame
            DataFrame containing a 'url' column.

        Returns
        -------
        list
            List of prediction dictionaries.
        """

        if urls_df is None or urls_df.empty:
            return []

        if "url" not in urls_df.columns:
            raise ValueError(
                "Input DataFrame must contain a 'url' column."
            )

        batch_urls = []
        batch_X = []
        batch_raw_features = []

        for _, row in urls_df.iterrows():

            url = str(row["url"]).strip()

            if not url:
                continue

            try:

                X, raw_features = self.extract_features(url)

                batch_urls.append(url)
                batch_X.append(X)
                batch_raw_features.append(raw_features)

            except Exception as e:

                print(f"Skipping {url}: {e}")

        if not batch_X:
            return []


        X_batch = np.vstack(batch_X)

        probabilities = self.model.predict_proba(X_batch)

        results = []

        for i, prob in enumerate(probabilities[:, 1]):

            raw_features = batch_raw_features[i]

            infra_score = raw_features.get("infra_trust_score", 0)
            infra_conf = infra_score / 3.0

            final_risk = prob * (1 - 0.6 * infra_conf)

            if raw_features.get("infra_stability_score", 0) == 1:
                final_risk *= 0.8

            if final_risk < 0.4:
                label = "benign"
                tier = "LOW"

            elif final_risk > 0.75:
                label = "malicious"
                tier = "HIGH"

            else:
                label = "suspicious"
                tier = "MEDIUM"

            print(
                f"DEBUG [{i}] "
                f"model_prob={prob:.4f}, "
                f"final_risk={final_risk:.4f}, "
                f"label={label}"
            )

            results.append({

                "url": batch_urls[i],

                "label": label,

                "model_risk": float(prob),

                "final_risk": float(final_risk),

                "features": raw_features,

                "risk_tier": tier,

                "X": batch_X[i]

            })
        
        return results