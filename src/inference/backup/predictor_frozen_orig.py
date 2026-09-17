# src/inference/predictor.py

import joblib
import pandas as pd
#from src.features import extract_all_features
from src.features_with_infra import extract_all_features
from src.charcnn_predict import predict_single
from src.config import MODEL_DIR

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
        feats = extract_all_features(url, html)

        # 🔍 DEBUG GOOGLE FEATURES
        if "google.com" in url:
            print("\n🔎 FEATURES FOR GOOGLE:")
            for k, v in feats.items():
                if k in ["equal_count", "subdomain_count", "param_count", "query_length"]:
                    print(f"{k}: {v}")

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
        
