"""
Infrastructure Network Intelligence

Collects:

- IP Address
- ASN
- Hosting Country
- ASN Reputation

Public API
----------
collect_network(domain)

Returns
-------
{
    "features": {...},
    "metadata": {...}
}

"""

import socket
import requests

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

REQUEST_TIMEOUT = 3

TRUSTED_COUNTRIES = [

    "India",

    "US",

    "Singapore",

    "Germany"

]

TRUSTED_ASNS = [

    "Google",

    "Amazon",

    "Microsoft",

    "Cloudflare",

    "Akamai"

]


# ---------------------------------------------------------------------
# Private Helpers
# ---------------------------------------------------------------------

def _get_ip(domain):
    """
    Resolve domain to IP address.
    """

    try:

        return socket.gethostbyname(domain)

    except Exception:

        return None


def _get_ip_information(ip):
    """
    Retrieve ASN, hosting country, organization and ISP.

    Returns
    -------
    tuple
        (asn, country, organization, isp)
    """

    if ip is None:

        return None, None, None, None

    try:

        response = requests.get(

            f"http://ip-api.com/json/{ip}",

            timeout=REQUEST_TIMEOUT

        ).json()

        asn = response.get("as")

        country = response.get("country")

        organization = response.get("org")

        isp = response.get("isp")

        return (
            asn,
            country,
            organization,
            isp
        )

    except Exception:

        return None, None, None, None


def _get_asn_reputation(asn):
    """
    Determine whether ASN belongs to a
    trusted infrastructure provider.
    """

    if asn is None:

        return 0

    asn = str(asn).lower()

    for provider in TRUSTED_ASNS:

        if provider.lower() in asn:

            return 1

    return 0


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------

def collect_network(domain):
    """
    Collect network intelligence.

    Parameters
    ----------
    domain : str

    Returns
    -------
    dict
    """

    domain = domain.lower().replace("www.", "").strip()

    ip = _get_ip(domain)

    asn, country, organization, isp = _get_ip_information(ip)

    return {

        "features": {

            # -------------------------------------------------
            # Availability
            # -------------------------------------------------

            "has_ip":

                int(ip is not None),

            "has_asn":

                int(asn is not None),

            # -------------------------------------------------
            # Behaviour
            # -------------------------------------------------

            "asn_reputation":

                _get_asn_reputation(asn),

            "is_foreign_hosting":

                int(

                    country not in TRUSTED_COUNTRIES

                    if country

                    else 0

                )

        },

        "metadata": {

            # -------------------------------------------------
            # Infrastructure Identity
            # -------------------------------------------------

            "ip_address": ip,

            "asn": asn,

            "hosting_country": country,

            "organization": organization,

            "isp": isp,

            "has_owner_information": int(

                bool(

                    organization

                    or isp

                    or asn

                )

            )

        }
    }


# ---------------------------------------------------------------------
# Debug
# ---------------------------------------------------------------------

if __name__ == "__main__":

    domains = [

        "google.com",

        "amazon.com",

        "paypal.com",

        "github.com"

    ]

    for domain in domains:

        print("\n" + "=" * 70)

        print(domain)

        print("=" * 70)

        network_data = collect_network(domain)

        print("\nPrediction Features\n")

        for key, value in sorted(network_data["features"].items()):

            print(f"{key:25s}: {value}")

        print("\nCampaign Metadata\n")

        for key, value in sorted(network_data["metadata"].items()):

            print(f"{key:25s}: {value}")