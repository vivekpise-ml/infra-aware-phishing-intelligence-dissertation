# src/inference/run_inference.py

from urllib.parse import urlparse

from src.inference.predictor import PhishingPredictor
from src.inference.report_generator import ReportGenerator
from src.infrastructure.infra_features import get_infra_features
from src.drift.drift_detector import compute_drift_score
from src.campaign.campaign_detector import detect_campaign

from src.explainability.shap_explainer import ShapExplainer

from src.drift.drift_service import single_url_drift_status

def extract_domain(url):
    if not url.startswith("http"):
        url = "http://" + url

    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    return domain

def run(url):
    predictor = PhishingPredictor()
    reporter = ReportGenerator()
    explainer = ShapExplainer()

    # Step 1: Prediction
    pred = predictor.predict(url)

    # Step 2: Extract domain properly
    
    domain = extract_domain(url)

    #print("DEBUG DOMAIN:", domain) # debug

    # Step 3: Infra intelligence (uses domain, NOT full URL)
    infra = get_infra_features(domain)

    print("INFRA:", infra)

    # Step 4: Drift
    # This was original Sem3 Demo time function (line # 45) replaced for Sem4 
    # with wrapper function 
    #drift = compute_drift_score(pred["features"], None)

    drift = single_url_drift_status()

    # Step 5: Campaign Analysis (NEW)
    campaign = detect_campaign(
        pred["features"],
        infra
    )

    print("CAMPAIGN:", campaign)
        
    # Step 6: Explanation (placeholder for now)
   
    '''
    explanation_list = explainer.explain(
        pred["X"],
        predictor.feature_names
    )
    '''
    explanation_list = ["SHAP temporarily disabled"]

    explanation = "\n".join(explanation_list)

    # Step 7: Generate report
    pred["campaign"] = campaign

    report = reporter.generate(pred, infra, drift, explanation)

    # return report

    return {
        "report": report,

        # 🔥 NEW (important)
        "model_risk": pred.get("model_risk"),
        "final_risk": pred.get("final_risk"),

        # keep compatibility (optional but useful)
        "risk_score": pred.get("final_risk"),

        "label": pred.get("label"),
        "risk_tier": pred.get("risk_tier"),
        "explanation_list": explanation_list,

        # NEW
        "drift": drift,
        "campaign": campaign
    }


if __name__ == "__main__":
    url = "http://secure-paypal-login.com/update"
    report = run(url)
    print(report)