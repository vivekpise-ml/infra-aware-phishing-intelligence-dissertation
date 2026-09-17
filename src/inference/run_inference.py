# src/inference/run_inference.py

from urllib.parse import urlparse
import pandas as pd

from src.inference.predictor import PhishingPredictor
from src.inference.report_generator import ReportGenerator

from src.infrastructure.infra_features import (
    collect_infrastructure_features,
    FEATURE_SECTION_DATA,
)

from src.drift.drift_service import single_url_drift_status

from src.campaign.campaign_service import CampaignService

from src.explainability.shap_explainer import ShapExplainer


# ---------------------------------------------------------------------
# Service Instances
# ---------------------------------------------------------------------

predictor = PhishingPredictor()

reporter = ReportGenerator()

campaign_service = CampaignService()

explainer = ShapExplainer()


# ---------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------

def extract_domain(url):
    """
    Extract domain from URL.
    """

    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    parsed = urlparse(url)

    return parsed.netloc.replace("www.", "")


# ---------------------------------------------------------------------
# Main Inference Pipeline
# ---------------------------------------------------------------------

def run(url):
    """
    Execute complete phishing intelligence pipeline.

    Pipeline
    --------
    Prediction
        ↓
    Infrastructure Intelligence
        ↓
    Drift Status
        ↓
    Campaign Analysis
        ↓
    Explainability
        ↓
    Intelligence Report
    """

    # ---------------------------------------------------------
    # Step 1 : Prediction
    # ---------------------------------------------------------

    pred = predictor.predict(url)

    # ---------------------------------------------------------
    # Step 2 : Infrastructure Intelligence
    # ---------------------------------------------------------

    domain = extract_domain(url)

    infra_result = collect_infrastructure_features(
        domain,
        FEATURE_SECTION_DATA
    )

    infra = infra_result.get("features", {})

    print("INFRA:", infra)
    
    # ---------------------------------------------------------
    # Step 3 : Drift Status
    # ---------------------------------------------------------

    drift = single_url_drift_status()

    # ---------------------------------------------------------
    # Step 4 : Campaign Analysis
    # ---------------------------------------------------------

    campaign = campaign_service.analyze(
        pd.DataFrame(
            {
                "url": [url]
            }
        )
    )

    print("CAMPAIGN:", campaign)

    # ---------------------------------------------------------
    # Step 5 : Explainability
    # ---------------------------------------------------------

    feature_names = predictor.feature_names

    explanation_list = explainer.explain(
        pred["X"],
        feature_names
    )

    explanation = "\n".join(explanation_list)

    # ---------------------------------------------------------
    # Step 6 : Generate Intelligence Report
    # ---------------------------------------------------------

    pred["campaign"] = campaign

    report = reporter.generate(
        prediction=pred,
        infra=infra,
        drift=drift,
        explanation=explanation
    )

    # ---------------------------------------------------------
    # Return Results
    # ---------------------------------------------------------

    return {

        "report": report,

        # Risk Scores
        "model_risk": pred.get("model_risk"),
        "final_risk": pred.get("final_risk"),
        "risk_score": pred.get("final_risk"),

        # Prediction
        "label": pred.get("label"),
        "risk_tier": pred.get("risk_tier"),

        # Explainability
        "explanation_list": explanation_list,

        # Intelligence Modules
        "infrastructure": infra,
        "drift": drift,
        "campaign": campaign
    }


# ---------------------------------------------------------------------
# Example
# ---------------------------------------------------------------------

if __name__ == "__main__":

    sample_url = "http://secure-paypal-login.com/update"

    result = run(sample_url)

    print(result["report"])