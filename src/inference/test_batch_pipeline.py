"""
test_batch_pipeline.py
----------------------

End-to-end integration test for the complete phishing
batch analysis pipeline.

Pipeline
--------
CSV
    ↓
run_batch()
    ↓
Batch Prediction
    ↓
Campaign Detection
    ↓
Campaign Risk Assessment
    ↓
Validation
"""

from pathlib import Path

import pandas as pd

from src.inference.run_batch_inference import run_batch


# ---------------------------------------------------------
# Test Dataset
# ---------------------------------------------------------

#TEST_DATA = Path("data/test_batch_urls.csv")

from src.config import TEST_DATA_BATCH

TEST_DATA = Path(TEST_DATA_BATCH) / "test_batch_urls.csv"


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    print("\n" + "=" * 70)
    print("END-TO-END BATCH PIPELINE TEST")
    print("=" * 70)

    # -----------------------------------------------------
    # Load dataset
    # -----------------------------------------------------

    if not TEST_DATA.exists():
        raise FileNotFoundError(
            f"Test dataset not found:\n{TEST_DATA}"
        )

    df = pd.read_csv(TEST_DATA)

    assert not df.empty, "Input dataframe is empty."

    assert "url" in df.columns, (
        "Missing 'url' column."
    )

    # -----------------------------------------------------
    # Run complete pipeline
    # -----------------------------------------------------

    results = run_batch(df)

    # -----------------------------------------------------
    # Validate top-level API
    # -----------------------------------------------------

    assert "prediction_results" in results

    assert "campaign_results" in results

    assert "campaign_risk" in results

    prediction_results = results["prediction_results"]

    campaign_results = results["campaign_results"]

    campaign_risk = results["campaign_risk"]

    # -----------------------------------------------------
    # Campaign detector outputs
    # -----------------------------------------------------

    campaign_df = campaign_results["campaign_dataframe"]

    campaign_count = campaign_results["campaign_count"]

    noise_urls = campaign_results["noise_urls"]

    largest_campaign = campaign_results["largest_campaign_size"]

    # -----------------------------------------------------
    # Campaign risk outputs
    # -----------------------------------------------------

    campaign_summary = campaign_risk["campaign_summary"]

    # -----------------------------------------------------
    # Campaign Risk Summary
    # -----------------------------------------------------

    print()

    print("=" * 70)
    print("CAMPAIGN RISK SUMMARY")
    print("=" * 70)

    print(campaign_summary)

    print()

    if not campaign_summary.empty:

        print("=" * 70)
        print("CAMPAIGN RISK DETAILS")
        print("=" * 70)

        for _, row in campaign_summary.iterrows():

            print()

            print(f"Campaign ID          : {row['campaign_id']}")
            print(f"URLs                 : {row['url_count']}")
            print(f"Average Model Risk   : {row['average_model_risk']:.3f}")
            print(f"Average Final Risk   : {row['average_final_risk']:.3f}")
            print(f"Maximum Final Risk   : {row['max_final_risk']:.3f}")
            print(f"Malicious URLs       : {row['malicious_urls']}")
            print(f"Suspicious URLs      : {row['suspicious_urls']}")

            print("-" * 70)

        print()
        
    # -----------------------------------------------------
    # Prediction validation
    # -----------------------------------------------------

    assert len(prediction_results) == len(df), (
        "Prediction count mismatch."
    )

    required_prediction_keys = {

        "url",

        "label",

        "model_risk",

        "final_risk",

        "risk_tier",

        "features",

        "X",

    }

    for prediction in prediction_results:

        assert required_prediction_keys.issubset(
            prediction.keys()
        )

    # -----------------------------------------------------
    # Campaign dataframe validation
    # -----------------------------------------------------

    assert len(campaign_df) == len(df), (
        "Campaign dataframe row mismatch."
    )

    assert campaign_df["url"].is_unique, (
        "Duplicate URLs found in campaign dataframe."
    )

    required_campaign_columns = {

        "url",

        "campaign_id",

        "model_risk",

        "final_risk",

        "label",

    }

    assert required_campaign_columns.issubset(
        campaign_df.columns
    )

    # -----------------------------------------------------
    # URL mapping validation
    # -----------------------------------------------------

    prediction_urls = {

        item["url"]

        for item in prediction_results

    }

    campaign_urls = set(campaign_df["url"])

    assert prediction_urls == campaign_urls, (
        "Prediction URLs and campaign URLs differ."
    )

    # -----------------------------------------------------
    # Campaign summary validation
    # -----------------------------------------------------

    required_summary_columns = {

        "campaign_id",

        "url_count",

        "average_model_risk",

        "average_final_risk",

        "max_final_risk",

        "malicious_urls",

        "suspicious_urls",

    }

    assert required_summary_columns.issubset(
        campaign_summary.columns
    )

    # -----------------------------------------------------
    # Print summary
    # -----------------------------------------------------

    print()

    print(f"Input URLs               : {len(df)}")
    print(f"Prediction Results       : {len(prediction_results)}")
    print(f"Campaign DataFrame Rows  : {len(campaign_df)}")
    print(f"Campaign Count           : {campaign_count}")
    print(f"Noise URLs               : {noise_urls}")
    print(f"Largest Campaign         : {largest_campaign}")
    print(f"Campaign Summary Rows    : {len(campaign_summary)}")

    print()

    print("Pipeline Validation      : PASSED")

    print("=" * 70)
    print("END-TO-END PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":

    main()