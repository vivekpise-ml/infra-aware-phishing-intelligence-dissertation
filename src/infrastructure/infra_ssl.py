"""
Infrastructure SSL Intelligence

Collects SSL / TLS certificate intelligence.

Public API
----------
collect_ssl(domain)

Returns
-------
{
    "features": {...},
    "metadata": {...}
}
"""

import socket
import ssl
import time

from datetime import datetime, timezone

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import NameOID


###########################################################################
# CONFIGURATION
###########################################################################

SSL_PORT = 443

SOCKET_TIMEOUT = 5


###########################################################################
# PRIVATE HELPERS
###########################################################################

def _normalize_domain(domain):
    """
    Normalize domain name.
    """

    return (
        domain.lower()
              .replace("www.", "")
              .strip()
    )


def _create_ssl_context():
    """
    Create a non-validating SSL context.

    Certificate validation is intentionally disabled.

    See ADR-005.
    """

    context = ssl.SSLContext(
        ssl.PROTOCOL_TLS_CLIENT
    )

    context.check_hostname = False

    context.verify_mode = ssl.CERT_NONE

    return context


###########################################################################
# CERTIFICATE COLLECTION
###########################################################################

def _load_certificate(domain):
    """
    Retrieve X509 certificate from remote server.

    Returns
    -------
    dict

    {
        success: bool,
        certificate: x509 | None,
        error: str | None
    }
    """

    context = _create_ssl_context()

    try:

        start = time.time()

        with socket.create_connection(

            (domain, SSL_PORT),

            timeout=SOCKET_TIMEOUT

        ) as sock:

            with context.wrap_socket(

                sock,

                server_hostname=domain

            ) as tls_socket:

                der = tls_socket.getpeercert(
                    binary_form=True
                )

        certificate = x509.load_der_x509_certificate(

            der,

            default_backend()

        )

        print(

            f"SSL {domain} took "

            f"{time.time()-start:.2f}s"

        )

        return {

            "success": True,

            "certificate": certificate,

            "error": None

        }

    except Exception as e:

        return {

            "success": False,

            "certificate": None,

            "error": str(e)

        }


###########################################################################
# COMMON HELPERS
###########################################################################

def _certificate_exists(result):

    return int(result["success"])


def _certificate(result):

    if not result["success"]:

        return None

    return result["certificate"]


def _safe_name_attribute(name, oid):
    """
    Extract first attribute from X509 Name.
    """

    try:

        values = name.get_attributes_for_oid(oid)

        if values:

            return values[0].value

    except Exception:

        pass

    return None


def _utc_now():
    """
    UTC timestamp helper.
    """

    return datetime.now(timezone.utc)

###########################################################################
# PREDICTION FEATURE EXTRACTION
###########################################################################

def _certificate_age_days(certificate):
    """
    Age of certificate in days.
    """

    if certificate is None:
        return None

    try:

        return (

            _utc_now()

            - certificate.not_valid_before_utc

        ).days

    except Exception:

        return None


def _certificate_lifetime_days(certificate):
    """
    Total validity period of certificate.
    """

    if certificate is None:
        return None

    try:

        return (

            certificate.not_valid_after_utc

            - certificate.not_valid_before_utc

        ).days

    except Exception:

        return None


def _certificate_remaining_days(certificate):
    """
    Remaining certificate validity.
    """

    if certificate is None:
        return None

    try:

        return (

            certificate.not_valid_after_utc

            - _utc_now()

        ).days

    except Exception:

        return None


def _is_self_signed(certificate):
    """
    Determine whether certificate is self-signed.
    """

    if certificate is None:
        return 0

    try:

        return int(

            certificate.subject

            ==

            certificate.issuer

        )

    except Exception:

        return 0


def _is_wildcard(certificate):
    """
    Check whether certificate contains wildcard SAN.
    """

    if certificate is None:

        return 0

    try:

        extension = certificate.extensions.get_extension_for_class(

            x509.SubjectAlternativeName

        )

        san = extension.value.get_values_for_type(

            x509.DNSName

        )

        return int(

            any(

                name.startswith("*.")

                for name in san

            )

        )

    except Exception:

        return 0


def _san_count(certificate):
    """
    Number of Subject Alternative Names.
    """

    if certificate is None:

        return 0

    try:

        extension = certificate.extensions.get_extension_for_class(

            x509.SubjectAlternativeName

        )

        san = extension.value.get_values_for_type(

            x509.DNSName

        )

        return len(san)

    except Exception:

        return 0


###########################################################################
# PREDICTION FEATURES
###########################################################################

def _prediction_features(result):
    """
    Extract SSL prediction features.
    """

    certificate = _certificate(result)

    age = _certificate_age_days(certificate)

    lifetime = _certificate_lifetime_days(certificate)

    remaining = _certificate_remaining_days(certificate)

    return {

        # ---------------------------------------------------------
        # Availability
        # ---------------------------------------------------------

        "has_ssl":

            _certificate_exists(result),

        # ---------------------------------------------------------
        # Raw
        # ---------------------------------------------------------

        "certificate_age_days":

            age if age is not None else 0,

        "certificate_lifetime_days":

            lifetime if lifetime is not None else 0,

        "certificate_remaining_days":

            remaining if remaining is not None else 0,

        # ---------------------------------------------------------
        # Behaviour
        # ---------------------------------------------------------

        "self_signed":

            _is_self_signed(certificate),

        "wildcard_certificate":

            _is_wildcard(certificate),

        "san_count":

            _san_count(certificate)

    }

###########################################################################
# CAMPAIGN METADATA EXTRACTION
###########################################################################

def _campaign_metadata(result):
    """
    Extract SSL identity metadata for Campaign Analysis.

    Returns
    -------
    dict
    """

    certificate = _certificate(result)

    metadata = {}

    # ---------------------------------------------------------
    # SSL Availability
    # ---------------------------------------------------------

    metadata["ssl_supported"] = result["success"]

    metadata["ssl_error"] = result["error"]

    metadata["ssl_issuer"] = (
        ", ".join(
            attribute.value
            for rdn in certificate.issuer.rdns
            for attribute in rdn
        )
        if certificate is not None
        else ""
    )

    # ---------------------------------------------------------
    # Certificate Validity
    # ---------------------------------------------------------

    metadata["ssl_valid_from"] = (
        certificate.not_valid_before_utc.isoformat()
        if certificate is not None
        else None
    )

    metadata["ssl_valid_to"] = (
        certificate.not_valid_after_utc.isoformat()
        if certificate is not None
        else None
    )

    remaining = _certificate_remaining_days(
        certificate
    )

    metadata["ssl_days_remaining"] = (
        remaining
        if remaining is not None
        else 0
    )

    if remaining is None:

        metadata["ssl_validity_bucket"] = 0

    elif remaining < 30:

        metadata["ssl_validity_bucket"] = 1

    elif remaining < 90:

        metadata["ssl_validity_bucket"] = 2

    elif remaining < 180:

        metadata["ssl_validity_bucket"] = 3

    else:

        metadata["ssl_validity_bucket"] = 4

    if certificate is None:

        metadata.update({

            "subject_common_name": None,

            "issuer_common_name": None,

            "serial_number": None,

            "signature_algorithm": None,

            "subject_alternative_names": [],

            "san_count": 0,

            "wildcard_certificate": 0

        })

        return metadata

    # ---------------------------------------------------------
    # Subject Common Name
    # ---------------------------------------------------------

    metadata["subject_common_name"] = _safe_name_attribute(

        certificate.subject,

        NameOID.COMMON_NAME

    )

    # ---------------------------------------------------------
    # Issuer Common Name
    # ---------------------------------------------------------

    metadata["issuer_common_name"] = _safe_name_attribute(

        certificate.issuer,

        NameOID.COMMON_NAME

    )

    # ---------------------------------------------------------
    # Signature Algorithm
    # ---------------------------------------------------------

    try:

        metadata["signature_algorithm"] = (

            certificate.signature_hash_algorithm.name

        )

    except Exception:

        metadata["signature_algorithm"] = None

    # ---------------------------------------------------------
    # Subject Alternative Names
    # ---------------------------------------------------------

    san_list = []

    try:

        extension = certificate.extensions.get_extension_for_class(

            x509.SubjectAlternativeName

        )

        san_list = sorted(

            extension.value.get_values_for_type(

                x509.DNSName

            )

        )

    except Exception:

        san_list = []

    metadata["subject_alternative_names"] = san_list

    metadata["san_count"] = len(san_list)

    metadata["wildcard_certificate"] = int(

        any(

            entry.startswith("*.")

            for entry in san_list

        )

    )

    return metadata

###########################################################################
# PUBLIC API
###########################################################################

def collect_ssl(domain):
    """
    Collect SSL / TLS infrastructure intelligence.

    Returns
    -------
    dict

    {
        "features": {...},
        "metadata": {...}
    }

    Notes
    -----
    - "features" are consumed by the Prediction pipeline.
    - "metadata" are consumed by the Campaign pipeline.
    - This collector performs no caching.
    - Cache ownership belongs to the caller.
    """

    domain = _normalize_domain(domain)

    result = _load_certificate(domain)

    return {

        "features": _prediction_features(result),

        "metadata": _campaign_metadata(result)

    }


###########################################################################
# DEBUG
###########################################################################

if __name__ == "__main__":

    domains = [

        "google.com",

        "amazon.com",

        "github.com",

        "expired.badssl.com",

        "self-signed.badssl.com",

        "wrong.host.badssl.com",

        "http.badssl.com"

    ]

    for domain in domains:

        print("\n")

        print("=" * 80)

        print(domain)

        print("=" * 80)

        ssl_data = collect_ssl(domain)

        print("\nPrediction Features\n")

        for key, value in sorted(

            ssl_data["features"].items()

        ):

            print(f"{key:35s}: {value}")

        print("\nCampaign Metadata\n")

        for key, value in sorted(

            ssl_data["metadata"].items()

        ):

            print(f"{key:35s}: {value}")

