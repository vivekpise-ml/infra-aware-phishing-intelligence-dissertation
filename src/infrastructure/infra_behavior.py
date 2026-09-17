"""
Infrastructure Behavioral Intelligence

Collects behavioral characteristics from a URL for use by
Prediction and Campaign Analysis.

The behavioral collector is stateless and does not access
the Feature Cache or Observation Cache.

Public API
----------
collect_behavior(url)

Returns
-------
{
    "features": {...},
    "metadata": {...}
}
"""

###########################################################################
# IMPORTS
###########################################################################

from urllib.parse import urlparse, parse_qs


###########################################################################
# CONFIGURATION
###########################################################################

BEHAVIOR_VERSION = "v1"


###########################################################################
# URL NORMALIZATION
###########################################################################

def _normalize_url(url):
    """
    Normalize URL for behavioral analysis.

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


###########################################################################
# RESULT HELPERS
###########################################################################

def _empty_result():
    """
    Create an empty behavioral intelligence result.

    Returns
    -------
    dict
    """

    return {

        "features": {},

        "metadata": {},

    }


def _parse_url(url):
    """
    Parse URL into its standard components.

    Parameters
    ----------
    url : str

    Returns
    -------
    ParseResult | None
    """

    if not url:

        return None

    try:

        return urlparse(url)

    except Exception:

        return None

###########################################################################
# PATH BEHAVIOR
###########################################################################

def _path_depth(parsed_url):
    """
    Number of meaningful path components.

    Example
    -------
    /login/update/password

    returns 3.
    """

    if parsed_url is None:

        return 0

    path = parsed_url.path.strip("/")

    if not path:

        return 0

    return len(

        [
            component
            for component in path.split("/")
            if component
        ]

    )


def _path_segment_count(parsed_url):
    """
    Number of path segments.

    Kept separate from path depth so the behavioral
    contract can distinguish structural path information.
    """

    if parsed_url is None:

        return 0

    path = parsed_url.path.strip("/")

    if not path:

        return 0

    return len(path.split("/"))


###########################################################################
# QUERY PARAMETER BEHAVIOR
###########################################################################

def _query_parameters(parsed_url):
    """
    Extract query parameter keys and values.

    Returns
    -------
    tuple
        (keys, values)
    """

    if parsed_url is None:

        return [], []

    query = parsed_url.query

    if not query:

        return [], []

    try:

        parameters = parse_qs(

            query,

            keep_blank_values=True

        )

    except Exception:

        return [], []

    keys = list(parameters.keys())

    values = []

    for parameter_values in parameters.values():

        values.extend(

            parameter_values

        )

    return keys, values


def _query_parameter_count(parsed_url):
    """
    Number of unique query parameter names.
    """

    keys, _ = _query_parameters(

        parsed_url

    )

    return len(keys)


def _query_value_count(parsed_url):
    """
    Total number of query parameter values.
    """

    _, values = _query_parameters(

        parsed_url

    )

    return len(values)


def _has_query_parameters(parsed_url):
    """
    Whether the URL contains query parameters.
    """

    if parsed_url is None:

        return 0

    return int(

        bool(parsed_url.query)

    )


###########################################################################
# PARAMETER MORPHOLOGY
###########################################################################

def _parameter_key_lengths(parsed_url):
    """
    Calculate query parameter key length statistics.

    Returns
    -------
    dict
    """

    keys, _ = _query_parameters(

        parsed_url

    )

    if not keys:

        return {

            "parameter_key_min_length": 0,

            "parameter_key_max_length": 0,

            "parameter_key_avg_length": 0.0,

        }

    lengths = [

        len(key)

        for key in keys

    ]

    return {

        "parameter_key_min_length": min(lengths),

        "parameter_key_max_length": max(lengths),

        "parameter_key_avg_length":

            sum(lengths) / len(lengths),

    }


def _parameter_value_lengths(parsed_url):
    """
    Calculate query parameter value length statistics.

    Returns
    -------
    dict
    """

    _, values = _query_parameters(

        parsed_url

    )

    if not values:

        return {

            "parameter_value_min_length": 0,

            "parameter_value_max_length": 0,

            "parameter_value_avg_length": 0.0,

        }

    lengths = [

        len(value)

        for value in values

    ]

    return {

        "parameter_value_min_length": min(lengths),

        "parameter_value_max_length": max(lengths),

        "parameter_value_avg_length":

            sum(lengths) / len(lengths),

    }


def _has_empty_parameter_value(parsed_url):
    """
    Detect whether any query parameter has an empty value.
    """

    keys, values = _query_parameters(

        parsed_url

    )

    if not keys:

        return 0

    return int(

        any(

            value == ""

            for value in values

        )

    )


###########################################################################
# QUERY STRUCTURE
###########################################################################

def _has_duplicate_parameter_keys(parsed_url):
    """
    Detect repeated query parameter names.

    Example
    -------
    ?id=1&id=2

    returns 1.
    """

    keys, _ = _query_parameters(

        parsed_url

    )

    return int(

        len(keys) != len(set(keys))

    )


def _query_length(parsed_url):
    """
    Length of the raw query component.
    """

    if parsed_url is None:

        return 0

    return len(

        parsed_url.query

    )


def _path_length(parsed_url):
    """
    Length of the URL path component.
    """

    if parsed_url is None:

        return 0

    return len(

        parsed_url.path

    )


###########################################################################
# ENCODING / STRUCTURAL SIGNALS
###########################################################################

def _encoded_character_count(url):
    """
    Count percent-encoded byte sequences.

    Example
    -------
    %20
    %2F
    %3D

    Each sequence contributes one count.
    """

    if not url:

        return 0

    count = 0

    index = 0

    while index < len(url) - 2:

        if (

            url[index] == "%"

            and

            all(

                character in "0123456789abcdefABCDEF"

                for character in url[
                    index + 1:index + 3
                ]

            )

        ):

            count += 1

            index += 3

        else:

            index += 1

    return count


def _has_encoded_characters(url):
    """
    Whether the URL contains percent-encoded characters.
    """

    return int(

        _encoded_character_count(url) > 0

    )

###########################################################################
# BEHAVIOR FEATURE CONSTRUCTION
###########################################################################

def _build_behavior_features(
    url,
    parsed_url
):
    """
    Build normalized behavioral features.

    Parameters
    ----------
    url : str

    parsed_url : ParseResult | None

    Returns
    -------
    dict
    """

    parameter_key_lengths = _parameter_key_lengths(

        parsed_url

    )

    parameter_value_lengths = _parameter_value_lengths(

        parsed_url

    )

    return {

        # ---------------------------------------------------------------
        # Path structure
        # ---------------------------------------------------------------

        "behavior_path_length":

            _path_length(parsed_url),

        "behavior_path_depth":

            _path_depth(parsed_url),

        "behavior_path_segment_count":

            _path_segment_count(parsed_url),

        # ---------------------------------------------------------------
        # Query structure
        # ---------------------------------------------------------------

        "behavior_has_query":

            _has_query_parameters(parsed_url),

        "behavior_query_parameter_count":

            _query_parameter_count(parsed_url),

        "behavior_query_value_count":

            _query_value_count(parsed_url),

        "behavior_query_length":

            _query_length(parsed_url),

        # ---------------------------------------------------------------
        # Parameter morphology
        # ---------------------------------------------------------------

        **parameter_key_lengths,

        **parameter_value_lengths,

        "behavior_has_empty_parameter_value":

            _has_empty_parameter_value(parsed_url),

        "behavior_has_duplicate_parameter_keys":

            _has_duplicate_parameter_keys(parsed_url),

        # ---------------------------------------------------------------
        # Encoding structure
        # ---------------------------------------------------------------

        "behavior_encoded_character_count":

            _encoded_character_count(url),

        "behavior_has_encoded_characters":

            _has_encoded_characters(url),

    }


###########################################################################
# BEHAVIOR METADATA
###########################################################################

def _build_behavior_metadata(parsed_url):
    """
    Build compact behavioral metadata for Campaign Analysis.

    Raw query values are deliberately not persisted.

    Returns
    -------
    dict
    """

    keys, _ = _query_parameters(

        parsed_url

    )

    return {

        "parameter_names": sorted(

            set(keys)

        ),

    }


###########################################################################
# PUBLIC API
###########################################################################

def collect_behavior(url):
    """
    Collect behavioral intelligence from a URL.

    Parameters
    ----------
    url : str

    Returns
    -------
    dict

        {
            "features": {...},
            "metadata": {...}
        }

    Notes
    -----
    This collector is stateless.

    It does not access the Feature Cache or
    Observation Cache.
    """

    url = _normalize_url(

        url

    )

    if not url:

        return _empty_result()

    parsed_url = _parse_url(

        url

    )

    if parsed_url is None:

        return _empty_result()

    features = _build_behavior_features(

        url,

        parsed_url

    )

    metadata = _build_behavior_metadata(

        parsed_url

    )

    return {

        "features": features,

        "metadata": metadata,

    }

