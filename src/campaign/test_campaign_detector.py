from __future__ import annotations

import pandas as pd

from src.campaign.campaign_detector import CampaignDetector

TEST_URLS = [

    # --------------------------------------------------
    # Google
    # --------------------------------------------------

    "https://accounts.google.com",
    "https://mail.google.com",
    "https://drive.google.com",
    "https://docs.google.com",
    "https://photos.google.com",

    # --------------------------------------------------
    # Microsoft
    # --------------------------------------------------

    "https://login.microsoftonline.com",
    "https://outlook.live.com",
    "https://office.com",
    "https://azure.microsoft.com",

    # --------------------------------------------------
    # Amazon
    # --------------------------------------------------

    "https://amazon.in",
    "https://amazon.com",
    "https://aws.amazon.com",
    "https://sellercentral.amazon.in",

    # --------------------------------------------------
    # Facebook
    # --------------------------------------------------

    "https://facebook.com",
    "https://m.facebook.com",
    "https://business.facebook.com",

    # --------------------------------------------------
    # GitHub
    # --------------------------------------------------

    "https://github.com",
    "https://gist.github.com",

    # --------------------------------------------------
    # Benign
    # --------------------------------------------------

    "https://python.org",
    "https://wikipedia.org",
    "https://stackoverflow.com",
    "https://openai.com",

    # --------------------------------------------------
    # Phishing-looking URLs
    # --------------------------------------------------

    "http://paypal-login-security.example.com",
    "http://verify-account-example.xyz/login",
    "http://amazon-security-alert.xyz",
    "http://facebook-verification-login.ru",
    "http://secure-google-login-alert.top",
    "http://office365-login-update.xyz",
    "http://netflix-secure-login.info",
    "http://bank-account-update-login.xyz",
]

def main():

    df = pd.DataFrame({
        "url": TEST_URLS
    })

    detector = CampaignDetector()

    result = detector.detect(df)

    print(result)

if __name__ == "__main__":
    main()