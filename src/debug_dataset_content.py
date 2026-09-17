import pandas as pd
from src.config import DATA_PATH

df = pd.read_csv(DATA_PATH)

label_col = "label" if "label" in df.columns else "type"

df[label_col] = df[label_col].astype(str).str.lower()

print(df[label_col].value_counts())
print("\nRatio:")
print(df[label_col].value_counts(normalize=True))