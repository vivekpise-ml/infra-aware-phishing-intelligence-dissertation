from datetime import datetime
from urllib.parse import urlparse

class ReportGenerator:

    def generate(self, prediction, infra=None, drift=None, explanation=None):

        infra = infra or {}
        drift = drift or {}

        #campaign = prediction.get("campaign", {})

        campaign_report = prediction.get("campaign", {})

        campaign_df = campaign_report.get("campaign_dataframe")

        summary = campaign_report.get("summary", {})

        campaign_sizes = campaign_report.get("campaign_sizes", {})

        url = prediction["url"]
        #domain = urlparse(url).netloc
        parsed = urlparse(url)
        domain = parsed.netloc if parsed.netloc else parsed.path

        model_risk = prediction.get("model_risk", prediction.get("risk_score", 0))
        final_risk = prediction.get("final_risk", prediction.get("risk_score", 0))
        label = prediction["label"]
        tier = prediction.get("risk_tier", "UNKNOWN")

        
        # ---------------------------------------------------------
        # Campaign Assessment (Single URL)
        # ---------------------------------------------------------

        campaign_likelihood = "Very Low"

        campaign_assessment = "No campaign indicators detected"

        campaign_indicators = []

        # High malicious confidence
        if final_risk >= 0.75:

            campaign_likelihood = "High"

            campaign_assessment = "Strong campaign indicators"

        # Suspicious
        elif final_risk >= 0.40:

            campaign_likelihood = "Moderate"

            campaign_assessment = "Possible phishing campaign"

        # ---------------------------------------------------------
        # Indicator generation
        # ---------------------------------------------------------

        # Show campaign indicators only when the overall
        # campaign likelihood is Moderate or High.

        if campaign_likelihood != "Very Low":

            if model_risk >= 0.70:

                campaign_indicators.append(
                    "High model suspicion"
                )

            if infra.get("is_new_domain", False):

                campaign_indicators.append(
                    "Recently registered domain"
                )

            if infra.get("is_foreign_hosting", False):

                campaign_indicators.append(
                    "Foreign hosting"
                )

            if infra.get("infra_trust_score", 5) < 2:

                campaign_indicators.append(
                    "Low infrastructure trust"
                )

            if infra.get("asn_reputation", 1) == 0:

                campaign_indicators.append(
                    "Poor ASN reputation"
                )    
        
        # -----------------------------------------
        # INTELLIGENCE ASSESSMENT (NEW)
        # -----------------------------------------
     
        # Case 1:
        # High model suspicion BUT infra reduced risk
        # (google.com type situation)
        if model_risk > 0.7 and final_risk < 0.4:

             assessment = """
            - High model suspicion was observed
            - Infrastructure trust reduced malicious confidence
            - Stable and mature hosting lowered operational risk
            - Overall risk assessed as LOW BENIGN
            """

        # Case 2:
        # Real benign
        elif final_risk < 0.4:

            assessment = """
            - Low phishing likelihood observed
            - Structural and infrastructure indicators appear benign
            - No major operational phishing signals detected
            - Overall risk assessed as LOW BENIGN
            """

        # Case 3:
        # High malicious confidence
        elif final_risk > 0.75:

            assessment = """
            - Multiple phishing indicators observed
            - Suspicious structural and infrastructure signals detected
            - Elevated malicious likelihood retained after calibration
            - Overall risk assessed as HIGH MALICIOUS
            """

        # Case 4:
        # Suspicious / uncertain
        else:

             assessment = """
            - Mixed phishing indicators observed
            - Infrastructure confidence reduced certainty
            - Additional verification recommended
            - Overall risk assessed as MEDIUM SUSPICIOUS
            """

        # -----------------------------------------
        # DYNAMIC EXPLANATION (NEW)
        # -----------------------------------------

        # Google-like case
        if model_risk > 0.7 and final_risk < 0.4:

            explanation_text = """
        - Model detected phishing-like structural patterns
        - Infrastructure trust signals reduced malicious confidence
        - Long-lived and stable hosting lowered operational risk
        - Final decision reflects calibrated intelligence
        """

        # Truly benign
        elif final_risk < 0.4:

            explanation_text = """
        - Low phishing indicators detected
        - URL and infrastructure signals appear benign
        - No significant structural anomalies observed
        - Final decision reflects low operational risk
        """

        # Malicious
        elif final_risk > 0.75:

            explanation_text = """
        - Multiple phishing indicators observed
        - Structural URL characteristics resemble known phishing patterns
        - Infrastructure confidence insufficient to reduce risk
        - Final decision reflects elevated malicious likelihood
        """

        # Suspicious
        else:

            explanation_text = """
        - Mixed phishing indicators observed
        - Some suspicious structural patterns detected
        - Infrastructure signals reduce certainty
        - Additional verification recommended
        """

        # ---------------------------------------------------------
        # Campaign Indicators Text
        # ---------------------------------------------------------

        if len(campaign_indicators) == 0:

            campaign_indicator_text = "- None"

        else:

            campaign_indicator_text = "\n".join(
                f"- {indicator}"
                for indicator in campaign_indicators
            )

        report = f"""
════════════════════════════════════════
Phishing Risk Intelligence Report
════════════════════════════════════════

[1] DOMAIN SUMMARY
────────────────────────────────────────
Domain              : {domain}
Prediction          : {label.upper()}
Model Risk Score    : {model_risk:.2f}
Final Risk Score    : {final_risk:.2f}
Risk Tier           : {tier}

________________________________________

[2] RISK INTELLIGENCE ANALYSIS
────────────────────────────────────────
Model Assessment    : {"Suspicious patterns detected" if model_risk > 0.7 else "Low suspicion from model"}
Infrastructure      : {"High Trust" if infra.get("infra_trust_score", 0) >= 2 else "Low/Unknown Trust"}
Adjustment Applied  : {"Yes" if abs(model_risk - final_risk) > 0.2 else "No"}
Confidence Level   :  {"High" if final_risk < 0.3 or final_risk > 0.7 else "Moderate"}

Explanation         :
{explanation_text}

Final Assessment   :
{assessment}

────────────────────────────────────────
[3] INFRASTRUCTURE INTELLIGENCE
────────────────────────────────────────
Domain Age (days)   : {infra.get('domain_age_days', 'N/A')}
Has Domain Age      : {infra.get('has_domain_age', 'N/A')}
Has ASN             : {infra.get('has_asn', 'N/A')}
Has IP              : {infra.get('has_ip', 'N/A')}
Foreign Hosting     : {infra.get('is_foreign_hosting', 'N/A')}
Stability Score     : {infra.get('infra_stability_score', 'N/A')}

────────────────────────────────────────
[4] DRIFT ANALYSIS
────────────────────────────────────────
Drift Score         : {drift.get('score', 'N/A')}
Drift Status        : {drift.get('status', 'N/A')}

────────────────────────────────────────
[5] CAMPAIGN ASSESSMENT
────────────────────────────────────────
Campaign Likelihood : {campaign_likelihood}

Assessment          : {campaign_assessment}

Observed Campaign Indicators:

{campaign_indicator_text}

────────────────────────────────────────
[6] MODEL EXPLANATION
────────────────────────────────────────
Top Factors:
{explanation}

────────────────────────────────────────
Model Version       : v1.0
Generated At        : {datetime.now()}
════════════════════════════════════════
"""
        return report