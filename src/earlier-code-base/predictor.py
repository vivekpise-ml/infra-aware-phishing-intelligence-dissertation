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

        threshold = 0.5  # make configurable later
        label = "malicious" if prob > threshold else "benign"
        
        risk_tier = PhishingPredictor.get_risk_tier(prob)

        # for Debug
        print(f"DEBUG: prob={prob:.4f}, label={label}")

        return {
            "url": url,
            "label": label,
            "risk_score": float(prob),
            "features": raw_features,
            "risk_tier": risk_tier,
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
        
