import joblib
import pandas as pd

from src.config import MODEL_DIR

# Load trained model
model = joblib.load(f"{MODEL_DIR}/xgboost_infra_model.pkl")

# Load feature names
feature_names = joblib.load(f"{MODEL_DIR}/xgb_infra_feature_names.pkl")

# Build importance table
importance = pd.Series(
    model.feature_importances_,
    index=feature_names
).sort_values(ascending=False)

print("\n🔝 Top 20 Features:\n")
print(importance.head(20))

print("\n🔻 Bottom 10 Features:\n")
print(importance.tail(10))