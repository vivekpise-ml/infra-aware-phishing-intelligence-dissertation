"""
Infrastructure Batch Orchestrator

Coordinates infrastructure intelligence collection for a
complete batch of URLs.

The batch is loaded and prepared once, then processed as one
batch execution.

The batch orchestrator delegates:

- Infrastructure intelligence -> infra_features.py
- Behavioral intelligence    -> infra_behavior.py

Cache ownership
---------------
Feature Cache:
    Owned by the calling Prediction or Campaign pipeline.

Observation Cache:
    Accessed and updated through infra_features.py.

This module does not directly implement cache management.

Public API
----------
process_batch(urls, feature_section)

Returns
-------
dict
    Batch-level result containing the results for all URLs
    and batch execution statistics.
"""

###########################################################################
# IMPORTS
###########################################################################

from copy import deepcopy


###########################################################################
# FEATURE CACHE SECTIONS
###########################################################################

FEATURE_SECTION_DATA = "data"

FEATURE_SECTION_CAMPAIGN_METADATA = "campaign_metadata"

VALID_FEATURE_SECTIONS = (

    FEATURE_SECTION_DATA,

    FEATURE_SECTION_CAMPAIGN_METADATA,

)


###########################################################################
# BATCH CONFIGURATION
###########################################################################

BATCH_VERSION = "v1"


###########################################################################
# INPUT NORMALIZATION
###########################################################################

def _normalize_url(url):
    """
    Normalize one URL for batch processing.

    Parameters
    ----------
    url : str

    Returns
    -------
    str
    """

    if url is None:

        return ""

    return str(url).strip()


def _load_batch(urls):
    """
    Load and prepare the complete URL batch.

    The batch is materialized once so that the complete
    collection is available to the batch execution.

    Empty URL values are discarded.

    Original ordering is preserved.

    Parameters
    ----------
    urls : iterable

    Returns
    -------
    list
    """

    if urls is None:

        return []

    batch = []

    for url in urls:

        normalized_url = _normalize_url(url)

        if normalized_url:

            batch.append(normalized_url)

    return batch


###########################################################################
# FEATURE SECTION VALIDATION
###########################################################################

def _validate_feature_section(feature_section):
    """
    Validate the requested Feature Cache section.

    Parameters
    ----------
    feature_section : str

    Raises
    ------
    ValueError
        If the requested section is unsupported.
    """

    if feature_section not in VALID_FEATURE_SECTIONS:

        raise ValueError(

            f"Unsupported batch feature section: "
            f"{feature_section}"

        )


###########################################################################
# BATCH RESULT HELPERS
###########################################################################

def _empty_batch_result():
    """
    Create an empty batch result.

    Returns
    -------
    dict
    """

    return {

        "batch_version": BATCH_VERSION,

        "results": [],

        "summary": {

            "total": 0,

            "successful": 0,

            "failed": 0,

        }

    }


def _build_url_result(
    url,
    infrastructure,
    behavior
):
    """
    Build the result for one URL within the batch.

    Parameters
    ----------
    url : str

    infrastructure : dict

    behavior : dict

    Returns
    -------
    dict
    """

    return {

        "url": url,

        "infrastructure": deepcopy(

            infrastructure

        ),

        "behavior": deepcopy(

            behavior

        ),

    }


###########################################################################
# BATCH SESSION HELPERS
###########################################################################

def _begin_batch():
    """
    Begin one batch execution.

    This function is intentionally lightweight.

    Cache loading and persistence are not performed here because
    cache ownership belongs to infra_features.py and the calling
    pipeline.
    """

    return {

        "batch_version": BATCH_VERSION,

        "processed": 0,

        "successful": 0,

        "failed": 0,

    }


def _end_batch(
    session,
    results
):
    """
    Finalize one batch execution.

    Parameters
    ----------
    session : dict

    results : list

    Returns
    -------
    dict
    """

    return {

        "batch_version": BATCH_VERSION,

        "results": results,

        "summary": {

            "total": session["processed"],

            "successful": session["successful"],

            "failed": session["failed"],

        }

    }

###########################################################################
# BATCH PROCESSING
###########################################################################

def _process_url(
    url,
    feature_section
):
    """
    Process one URL within the current batch execution.

    Infrastructure intelligence is delegated entirely to
    infra_features.py.

    This function does not:
    - access either cache directly
    - invoke behavioral analysis
    - perform campaign analysis
    - update the Feature Cache

    Parameters
    ----------
    url : str

    feature_section : str

    Returns
    -------
    dict
    """

    from .infra_features import (
        collect_infrastructure_features
    )

    infrastructure = collect_infrastructure_features(

        url,

        feature_section

    )

    return {

        "url": url,

        "infrastructure": deepcopy(

            infrastructure

        )

    }


def _process_loaded_batch(
    batch,
    feature_section,
    session
):
    """
    Process the complete loaded batch.

    The batch has already been materialized by _load_batch().

    Each URL is processed as one unit of work inside this
    single batch execution.

    Parameters
    ----------
    batch : list

    feature_section : str

    session : dict

    Returns
    -------
    list
    """

    results = []

    for url in batch:

        session["processed"] += 1

        try:

            result = _process_url(

                url,

                feature_section

            )

            results.append(

                result

            )

            session["successful"] += 1

        except Exception as exc:

            results.append({

                "url": url,

                "infrastructure": {

                    "features": {},

                    "metadata": {},

                },

                "error": str(exc),

            })

            session["failed"] += 1

    return results


###########################################################################
# PUBLIC API
###########################################################################

def process_batch(
    urls,
    feature_section
):
    """
    Process a complete batch of URLs.

    Parameters
    ----------
    urls : iterable

    feature_section : str
        Requested infrastructure output:

        - "data"
        - "campaign_metadata"

    Returns
    -------
    dict
        {
            "batch_version": "...",
            "results": [...],
            "summary": {
                "total": ...,
                "successful": ...,
                "failed": ...
            }
        }
    """

    _validate_feature_section(

        feature_section

    )

    #######################################################################
    # LOAD COMPLETE BATCH
    #######################################################################

    batch = _load_batch(

        urls

    )

    if not batch:

        return _empty_batch_result()

    #######################################################################
    # BEGIN ONE BATCH SESSION
    #######################################################################

    session = _begin_batch()

    #######################################################################
    # PROCESS COMPLETE BATCH
    #######################################################################

    results = _process_loaded_batch(

        batch,

        feature_section,

        session

    )

    #######################################################################
    # FINALIZE BATCH
    #######################################################################

    return _end_batch(

        session,

        results

    )

