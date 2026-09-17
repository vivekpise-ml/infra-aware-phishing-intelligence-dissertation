# src/campaign/campaign_detector.py

def detect_campaign(url_features, infra_features=None):

    infra_features = infra_features or {}

    score = 0
    reasons = []

    # -----------------------------------------
    # URL STRUCTURE SIGNALS
    # -----------------------------------------

    if url_features.get("subdomain_count", 0) >= 2:
        score += 1
        reasons.append("multiple subdomains")

    if url_features.get("query_length", 0) > 40:
        score += 1
        reasons.append("long query structure")

    if url_features.get("param_count", 0) >= 3:
        score += 1
        reasons.append("many URL parameters")

    if url_features.get("path_depth", 0) >= 3:
        score += 1
        reasons.append("deep URL path")

    # -----------------------------------------
    # PHISHING KEYWORDS
    # -----------------------------------------

    phishing_keywords = [
        "kw_login",
        "kw_verify",
        "kw_account",
        "kw_secure",
        "kw_update",
        "kw_billing",
        "kw_password"
    ]

    keyword_hits = sum(
        url_features.get(k, 0)
        for k in phishing_keywords
    )

    if keyword_hits >= 2:
        score += 2
        reasons.append("multiple phishing keywords")

    # -----------------------------------------
    # INFRASTRUCTURE SIGNALS
    # -----------------------------------------

    if infra_features.get("infra_trust_score", 0) == 0:
        score += 2
        reasons.append("low infrastructure trust")

    if infra_features.get("is_foreign_hosting", 0):
        score += 1
        reasons.append("foreign hosting")

    if infra_features.get("infra_stability_score", 0) == 0:
        score += 1
        reasons.append("unstable hosting")

    # -----------------------------------------
    # FINAL CAMPAIGN INFERENCE
    # -----------------------------------------

    if score >= 6:
        campaign_risk = "HIGH"
        confidence = "HIGH"

    elif score >= 3:
        campaign_risk = "POSSIBLE"
        confidence = "MODERATE"

    else:
        campaign_risk = "LOW"
        confidence = "LOW"

    return {
        "campaign_score": score,
        "campaign_risk": campaign_risk,
        "confidence": confidence,
        "signals": reasons
    }