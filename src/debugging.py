import joblib

cols = joblib.load("models/xgb_infra_feature_names.pkl")

print("TOTAL TRAIN FEATURES:", len(cols))
print(cols)


model = joblib.load("models/xgboost_infra_model.pkl")
print(model.n_features_in_)

import whois
print(dir(whois))