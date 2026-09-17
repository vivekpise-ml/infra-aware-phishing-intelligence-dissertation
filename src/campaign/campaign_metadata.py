"""
campaign_metadata.py
--------------------

Campaign-specific infrastructure metadata.

IMPORTANT
---------
This module is COMPLETELY independent from the prediction pipeline.

It MUST NOT modify

    extract_all_features()
    features_with_infra.py
    infra_features.py

It only enriches infra_cache.json by adding

    cache[domain]["campaign_metadata"]

The prediction pipeline continues using

    cache[domain]["data"]

without any modification.

Author:
M.Tech Phishing Risk Intelligence Framework
"""

from __future__ import annotations


import socket
import ssl
import ipaddress


import tldextract

from datetime import datetime, timezone
from typing import Dict

from src.infrastructure.infra_features import (
    collect_infrastructure_features,
    FEATURE_SECTION_CAMPAIGN_METADATA
)

from src.infrastructure.infra_cache import (
    get_feature_entry,
    get_observation_cached_at,
    update_feature_section
)

# ------------------------------------------------------------
# Cache configuration
# ------------------------------------------------------------

CAMPAIGN_METADATA_VERSION = "v1"

CACHE_EXPIRY_DAYS = 30

# ------------------------------------------------------------
# Cache Management
# ------------------------------------------------------------
#
# Cache persistence is owned by infra_cache.py.
#
# Existing Campaign Metadata cache intention is unchanged:
#
#     fresh metadata  -> reuse
#     stale/missing   -> rebuild
#
# Only the underlying cache-management mechanism is centralized.

# ------------------------------------------------------------
# Utility
# ------------------------------------------------------------

def utc_now():

    return datetime.now(timezone.utc)


def cache_is_expired(timestamp: str) -> bool:

    if not timestamp:
        return True

    try:

        old = datetime.fromisoformat(timestamp)

        age = utc_now() - old

        return age.days >= CACHE_EXPIRY_DAYS

    except Exception:

        return True



# ------------------------------------------------------------
# IP -> /24 subnet
# ------------------------------------------------------------

def get_subnet24(ip):

    if ip is None:
        return ""

    try:

        network = ipaddress.ip_network(
            f"{ip}/24",
            strict=False
        )

        return str(network.network_address)

    except Exception:

        return ""


# ------------------------------------------------------------
# Hosting Provider
# ------------------------------------------------------------

def derive_hosting_provider(asn):

    if asn is None:
        return ""

    text = str(asn).lower()

    providers = {

        "amazon": "Amazon",

        "google": "Google",

        "cloudflare": "Cloudflare",

        "akamai": "Akamai",

        "microsoft": "Microsoft",

        "digitalocean": "DigitalOcean",

        "linode": "Linode",

        "ovh": "OVH",

        "hetzner": "Hetzner",

        "oracle": "Oracle",

    }

    for key, value in providers.items():

        if key in text:

            return value

    return "Other"


# ------------------------------------------------------------
# Campaign Metadata
# ------------------------------------------------------------

def build_campaign_metadata(domain: str) -> Dict:
    """
    Build campaign-specific infrastructure metadata.

    This function NEVER modifies the prediction feature dictionary.

    It consumes the Infrastructure Package and converts its
    collector metadata into the legacy flat Campaign Metadata
    schema used by the campaign pipeline.
    """

    #
    # Host domain
    #
    original_domain = domain.replace("www.", "").strip()

    #
    # Root domain (used for campaign/domain-level metadata)
    #
    ext = tldextract.extract(original_domain)

    if ext.suffix:
        root_domain = f"{ext.domain}.{ext.suffix}"
    else:
        root_domain = ext.domain

    # temporary for debugging
    print(f"domain is {domain}")

    '''
    #
    # ---------------------------------------------------------
    # Infrastructure Package
    # ---------------------------------------------------------
    #
    # The Infrastructure Package is now the single collection
    # path for network / WHOIS / SSL / CT observations.
    #
    infra_result = collect_infrastructure_features(
        root_domain,
        FEATURE_SECTION_CAMPAIGN_METADATA
    )

    infra_metadata = infra_result.get(
        "metadata",
        {}
    )
    '''

    #
    # ---------------------------------------------------------
    # Infrastructure Package
    # ---------------------------------------------------------
    #
    # The Infrastructure Package is now the single collection
    # path for network / WHOIS / SSL / CT observations.
    #
    # Preserve the conference-era sourcing semantics:
    #
    #   - Host-specific infrastructure:
    #       original_domain
    #       (IP / ASN / organization / ISP / SSL)
    #
    #   - Domain-level infrastructure:
    #       root_domain
    #       (WHOIS / nameserver information)
    #
    # The prediction pipeline is unaffected.
    #
    host_infra_result = collect_infrastructure_features(
        original_domain,
        FEATURE_SECTION_CAMPAIGN_METADATA
    )

    root_infra_result = collect_infrastructure_features(
        root_domain,
        FEATURE_SECTION_CAMPAIGN_METADATA
    )

    host_infra_metadata = host_infra_result.get(
        "metadata",
        {}
    )

    root_infra_metadata = root_infra_result.get(
        "metadata",
        {}
    )

    infra_metadata = {
        "network": host_infra_metadata.get(
            "network",
            {}
        ),
        "whois": root_infra_metadata.get(
            "whois",
            {}
        ),
        "ssl": host_infra_metadata.get(
            "ssl",
            {}
        ),
        "ct": host_infra_metadata.get(
            "ct",
            {}
        ),
    }

    #
    # Collector-specific metadata
    #
    network_metadata = infra_metadata.get(
        "network",
        {}
    )

    whois_metadata = infra_metadata.get(
        "whois",
        {}
    )

    ssl_metadata = infra_metadata.get(
        "ssl",
        {}
    )

    #
    # ---------------------------------------------------------
    # Network Metadata
    # ---------------------------------------------------------
    #

    ip = network_metadata.get(
        "ip_address"
    )

    asn = network_metadata.get(
        "asn"
    )

    organization = network_metadata.get(
        "organization"
    )

    isp = network_metadata.get(
        "isp"
    )

    country = network_metadata.get(
        "hosting_country"
    )

    has_owner_information = network_metadata.get(
        "has_owner_information",
        int(
            bool(
                organization
                or isp
                or asn
            )
        )
    )

    #
    # ---------------------------------------------------------
    # WHOIS Metadata
    # ---------------------------------------------------------
    #

    nameservers = whois_metadata.get(
        "nameservers",
        []
    )

    if not nameservers:
        nameservers = []

    #
    # ---------------------------------------------------------
    # SSL Metadata
    # ---------------------------------------------------------
    #
    # Preserve the legacy Campaign Metadata field names.
    #
    ssl_available = int(
        bool(
            ssl_metadata.get(
                "ssl_supported",
                False
            )
        )
    )

    ssl_issuer = ssl_metadata.get(
        "ssl_issuer",
        ssl_metadata.get(
            "issuer_common_name",
            ""
        )
    )

    ssl_valid_from = ssl_metadata.get(
        "ssl_valid_from"
    )

    ssl_valid_to = ssl_metadata.get(
        "ssl_valid_to"
    )

    ssl_days_remaining = ssl_metadata.get(
        "ssl_days_remaining",
        0
    )

    ssl_validity_bucket = ssl_metadata.get(
        "ssl_validity_bucket",
        0
    )

    #
    # ---------------------------------------------------------
    # Campaign Metadata
    # ---------------------------------------------------------
    #

    metadata = {

        # -----------------------------
        # Cache Information
        # -----------------------------

        "metadata_version":
            CAMPAIGN_METADATA_VERSION,

        "cached_at":
            utc_now().isoformat(),

        # -----------------------------
        # Network
        # -----------------------------

        "ip":
            ip if ip else "",

        "ip_subnet24":
            get_subnet24(ip),

        # -----------------------------
        # DNS
        # -----------------------------

        "nameservers":
            nameservers,

        "nameserver_count":
            len(nameservers),

        # -----------------------------
        # Hosting
        # -----------------------------

        "hosting_provider":
            derive_hosting_provider(asn),

        # -----------------------------
        # IP Ownership Metadata
        # -----------------------------

        "as":
            asn if asn else "",

        "organization":
            organization if organization else "",

        "isp":
            isp if isp else "",

        "country":
            country if country else "",

        "has_owner_information":
            int(
                has_owner_information
            ),

        # -----------------------------
        # SSL
        # -----------------------------

        "ssl_available":
            ssl_available,

        "ssl_issuer":
            ssl_issuer,

        "ssl_valid_from":
            ssl_valid_from,

        "ssl_valid_to":
            ssl_valid_to,

        "ssl_days_remaining":
            ssl_days_remaining,

        "ssl_validity_bucket":
            ssl_validity_bucket,
    }

    return metadata

# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------

def _campaign_metadata_cache_is_current(
    domain: str,
    campaign: Dict
) -> bool:
    """
    Determine whether cached Campaign Metadata is still current
    relative to the infrastructure observations from which it
    was derived.

    The Campaign Metadata builder uses:
        - host domain for Network / SSL / CT
        - root domain for WHOIS / nameservers

    Therefore the derived Campaign Metadata becomes stale when
    any relevant Observation Cache entry is newer than the
    Campaign Metadata cached_at timestamp.
    """

    if not isinstance(campaign, dict):
        return False

    campaign_cached_at = campaign.get(
        "cached_at"
    )

    if not campaign_cached_at:
        return False

    try:
        campaign_time = datetime.fromisoformat(
            campaign_cached_at
        )

        if campaign_time.tzinfo is None:
            campaign_time = campaign_time.replace(
                tzinfo=timezone.utc
            )

    except Exception:
        return False

    #
    # Preserve the existing conference-era sourcing semantics:
    #
    #   original_domain -> network / SSL / CT
    #   root_domain     -> WHOIS
    #
    original_domain = domain.replace(
        "www.",
        ""
    ).strip()

    ext = tldextract.extract(
        original_domain
    )

    if ext.suffix:
        root_domain = (
            f"{ext.domain}.{ext.suffix}"
        )
    else:
        root_domain = ext.domain

    observation_sources = [
        (
            original_domain,
            "network"
        ),
        (
            original_domain,
            "ssl"
        ),
        (
            original_domain,
            "ct"
        ),
        (
            root_domain,
            "whois"
        ),
    ]

    for observation_domain, collector in observation_sources:

        observation_cached_at = (
            get_observation_cached_at(
                observation_domain,
                collector
            )
        )

        if not observation_cached_at:
            continue

        try:
            observation_time = datetime.fromisoformat(
                observation_cached_at
            )

            if observation_time.tzinfo is None:
                observation_time = observation_time.replace(
                    tzinfo=timezone.utc
                )

        except Exception:
            continue

        #
        # If an underlying observation was refreshed after
        # Campaign Metadata was created, the derived metadata
        # must be rebuilt.
        #
        if observation_time > campaign_time:
            return False

    return True

def get_campaign_metadata(domain: str) -> Dict:
    """
    Return campaign metadata.

    Workflow

    1. Read the campaign_metadata section through the
       centralized Infrastructure Cache Manager
    2. If campaign_metadata exists and is fresh:
           return it
    3. Otherwise
           rebuild metadata
           save
           return
    """

    domain = domain.replace("www.", "").strip()

    #
    # Existing Campaign Metadata cache entry?
    #
    # Cache access is handled by the centralized
    # Infrastructure Cache Manager.
    #

    entry = get_feature_entry(domain)

    campaign = entry.get(
        "campaign_metadata",
        None
    )

    '''
    if campaign is not None:

        timestamp = campaign.get(
            "cached_at",
            None
        )

        if not cache_is_expired(timestamp):

            return campaign
    '''

    if campaign is not None:

        timestamp = campaign.get(
            "cached_at",
            None
        )

        # ----------------------------------------------------
        # Cache validity
        # ----------------------------------------------------
        # A Campaign Metadata entry is reusable only when:
        #
        #   1. the timestamp is fresh, AND
        #   2. the metadata contains meaningful collected data.
        #
        # This prevents a failed/empty collection from being
        # treated as a valid 30-day cache entry.
        # ----------------------------------------------------

        has_meaningful_metadata = any([
            campaign.get("ip"),
            campaign.get("nameservers"),
            campaign.get("as"),
            campaign.get("organization"),
            campaign.get("isp"),
            campaign.get("country"),
            campaign.get("ssl_available", 0),
        ])

        if (
            not cache_is_expired(timestamp)
            and has_meaningful_metadata
            and _campaign_metadata_cache_is_current(
                domain,
                campaign
            )
        ):
            return campaign

    #
    # Build fresh metadata
    #
    campaign = build_campaign_metadata(domain)

    #
    # Campaign owns ONLY this Feature Cache section.
    #
    # update_feature_section() preserves the existing
    # Prediction "data" section.
    #

    update_feature_section(
        domain,
        "campaign_metadata",
        campaign
    )

    return campaign

# ------------------------------------------------------------
# Debug
# ------------------------------------------------------------

if __name__ == "__main__":

    sample = "google.com"

    metadata = get_campaign_metadata(sample)

    from pprint import pprint

    pprint(metadata)