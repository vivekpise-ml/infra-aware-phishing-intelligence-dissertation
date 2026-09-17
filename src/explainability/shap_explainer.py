import shap
import joblib
import numpy as np

from src.config import MODEL_DIR


class ShapExplainer:

    def __init__(self):

        # Load FINAL infrastructure-aware XGBoost model
        self.model = joblib.load(
            f"{MODEL_DIR}/xgboost_infra_model.pkl"
        )

        self.explainer = shap.TreeExplainer(self.model)

    def explain(
        self,
        X,
        feature_names,
        top_k=10
    ):

        shap_values = self.explainer.shap_values(X)

        # Robust across SHAP versions
        if isinstance(shap_values, list):
            vals = np.asarray(shap_values[1]).flatten()
        else:
            vals = np.asarray(shap_values).flatten()

        pairs = [
            (name, float(value))
            for name, value in zip(feature_names, vals)
        ]

        pairs.sort(
            key=lambda x: abs(x[1]),
            reverse=True
        )

        explanation = []

        for name, value in pairs[:top_k]:

            direction = "↑" if value > 0 else "↓"

            explanation.append(
                f"{direction} {name} ({value:.3f})"
            )

        return explanation