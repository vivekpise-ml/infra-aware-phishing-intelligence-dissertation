import pandas as pd


def generate_trusted_urls():
    """
    Generate realistic trusted URLs with variations.
    No duplication hacks, only natural patterns.
    """

    base_domains = [
        # Google
        "https://google.com",
        "https://mail.google.com",
        "https://docs.google.com",
        "https://drive.google.com",
        "https://maps.google.com",

        # Amazon
        "https://amazon.com",
        "https://aws.amazon.com",

        # Microsoft
        "https://microsoft.com",
        "https://login.microsoftonline.com",

        # Apple
        "https://apple.com",
        "https://icloud.com",

        # Others
        "https://github.com",
        "https://linkedin.com",
        "https://netflix.com",
        "https://paypal.com",
    ]

    paths = [
        "",
        "/home",
        "/login",
        "/account",
        "/dashboard",
        "/support",
        "/help",
    ]

    queries = [
        "",
        "?ref=home",
        "?lang=en",
        "?utm_source=web",
    ]

    urls = []

    for base in base_domains:
        for path in paths:
            for query in queries:
                urls.append(base + path + query)

    return list(set(urls))  # remove duplicates


def get_trusted_dataframe():
    """
    Return DataFrame with trusted URLs labeled as benign
    """
    urls = generate_trusted_urls()

    df_trusted = pd.DataFrame({
        "url": urls,
        "type": ["benign"] * len(urls)
    })

    print(f"✅ Generated {len(df_trusted)} trusted URLs")

    return df_trusted