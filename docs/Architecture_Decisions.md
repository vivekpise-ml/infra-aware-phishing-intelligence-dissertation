# Architecture Decision Record (ADR)

This document records important architectural decisions taken during the
development of the Infrastructure-Aware Drift-Adaptive Multimodal
Phishing Risk Intelligence Framework.

------------------------------------------------------------------------

ADR-001
--------

Title
-----
WHOIS Collector returns Features and Metadata separately.

Decision
--------
The WHOIS collector exposes the following interface:

collect_whois(domain)

↓

{
    "features": {...},
    "metadata": {...}
}

Reason
------
Prediction and Campaign Analysis consume different information.

Prediction requires numerical features suitable for machine learning.

Campaign Analysis requires rich identity metadata for similarity analysis.

Returning a structured dictionary avoids tuple ordering dependency,
reduces cascading changes to callers, and preserves ownership separation.

Alternatives Considered
-----------------------
1. Returning a tuple
2. Two independent functions
3. Separate collectors

Decision Outcome
----------------
Single lookup.
Single parser.
Two outputs.
Ownership preserved.

------------------------------------------------------------------------

ADR-002
--------

Title
-----
Infrastructure Collectors do not own cache.

Decision
--------
Infrastructure collectors only perform information collection.

Cache ownership belongs to the caller.

Prediction Pipeline stores prediction features.

Campaign Pipeline stores campaign metadata.

Reason
------
Maintains clear ownership boundaries.

Allows Prediction and Campaign to evolve independently.

Avoids infrastructure modules becoming tightly coupled to cache
implementations.

Alternatives Considered
-----------------------
Collectors writing directly into cache.

Decision Outcome
----------------
Collectors remain reusable services.


------------------------------------------------------------------------

ADR-003
--------

Title
-----
Non-validating SSL Context for Certificate Collection.

Decision
--------
SSL certificates are collected using a non-validating SSL context.

Hostname verification and certificate trust validation are disabled
during collection.

Reason
------
The objective is infrastructure intelligence collection rather than
browser-grade certificate validation.

Phishing infrastructure frequently uses:

- expired certificates
- self-signed certificates
- hostname mismatch
- incomplete certificate chains

Strict certificate verification would prevent retrieval of valuable
certificate intelligence.

Trust evaluation is therefore separated from certificate collection.

Alternatives Considered
-----------------------
Using ssl.create_default_context() with full certificate verification.

Decision Outcome
----------------
Certificate collection succeeds for a wider range of infrastructure,
including malicious domains.

------------------------------------------------------------------------

ADR-004
--------

Title
-----
SSL Collection Independent of URL Scheme.

Decision
--------
SSL collection always attempts TLS communication on TCP port 443
regardless of whether the original URL begins with HTTP or HTTPS.

Reason
------
Infrastructure intelligence is associated with the domain rather than
the URL scheme.

Many domains accepting HTTP requests also support HTTPS through
automatic redirection.

The existence of TLS support is itself a useful infrastructure signal.

Alternatives Considered
-----------------------
Collect SSL information only when URLs explicitly use HTTPS.

Decision Outcome
----------------
The framework measures SSL support of infrastructure instead of merely
observing URL syntax.

------------------------------------------------------------------------

ADR-005
--------

Title
-----
SSL Collection Returns Structured Status.

Decision
--------
Certificate retrieval returns structured results indicating both success
and failure.

Example

{
    "success": True,
    "certificate": ...
}

or

{
    "success": False,
    "error": ...
}

Reason
------
Absence of SSL or certificate retrieval failures are useful intelligence
signals.

Infrastructure collection should distinguish between:

- no HTTPS support
- timeout
- handshake failure
- expired certificate
- self-signed certificate
- hostname mismatch

rather than silently returning None.

Decision Outcome
----------------
Infrastructure intelligence preserves failure semantics for later
feature engineering and campaign analysis.

------------------------------------------------------------------------

ADR-005
--------

Title
-----
Structured SSL Certificate Collection with Failure Intelligence

Decision
--------
The SSL collector returns structured certificate retrieval status rather
than silently returning None on failure.

Certificate collection returns either:

{
    "success": True,
    "certificate": <x509 certificate>,
    "error": None
}

or

{
    "success": False,
    "certificate": None,
    "error": "<failure reason>"
}

Additionally, SSL collection always attempts a TLS connection on
TCP port 443 irrespective of whether the original URL specifies
HTTP or HTTPS.

A non-validating SSL context is used for certificate collection.

Reason
------
The objective of SSL collection is infrastructure intelligence
rather than browser-grade trust validation.

Many phishing infrastructures intentionally use:

- expired certificates
- self-signed certificates
- hostname mismatch
- incomplete certificate chains

Strict certificate validation would prevent certificate retrieval,
causing loss of valuable intelligence.

The absence of SSL support or certificate retrieval failures
constitute useful security signals and should therefore be preserved
rather than discarded.

Cache ownership remains outside the SSL collector.
Prediction and Campaign pipelines independently decide whether
and how collected SSL information is cached.

Alternatives Considered
-----------------------
1. ssl.create_default_context()

2. Returning None on failure

3. Collect SSL only for HTTPS URLs

Decision Outcome
----------------
The framework separates certificate collection from certificate trust.

SSL support is evaluated at the infrastructure level rather than
at the URL syntax level.

Certificate retrieval failures remain available for future feature
engineering, campaign intelligence and adaptive risk calibration.

------------------------------------------------------------------------

------------------------------------------------------------------------

ADR-006
--------

Title
-----
Certificate Transparency (CT) Intelligence Collection

Decision
--------
Certificate Transparency (CT) is implemented as an independent
infrastructure intelligence collector.

The framework queries Certificate Transparency history using the
JSON interface provided by crt.sh.

Example

https://crt.sh/?q=%25.example.com&output=json

The collector does not persist raw Certificate Transparency records.

Instead, it extracts only the information required by the Prediction
and Campaign pipelines.

Prediction receives compact numerical features.

Campaign receives normalized historical identity metadata.

Reason
------
Certificate Transparency records may contain a large historical record
for a domain.

Persisting complete CT records would unnecessarily increase cache size
while providing little additional value to downstream components.

The framework therefore stores only normalized infrastructure
observations required for downstream processing, such as historical
issuers, historical Subject Alternative Names (SANs), certificate
history count and temporal information.

These normalized observations are persisted in the Infrastructure
Observation Cache and are reused across multiple executions of both
Prediction and Campaign pipelines.

This approach preserves cache efficiency while avoiding repeated
network requests to Certificate Transparency services.

Raw CT records are discarded immediately after normalization.

Cache Architecture
------------------

The framework maintains two physical cache repositories.

1. Infrastructure Observation Cache

   Stores normalized reusable infrastructure observations collected
   from external services such as WHOIS, SSL, Certificate Transparency
   and other infrastructure intelligence providers.

   The Observation Cache is owned by the Infrastructure layer.

2. Infrastructure Feature Cache (infra_cache.json)

   Stores derived outputs consumed by downstream pipelines.

   - The Prediction pipeline owns the "data" section.
   - The Campaign pipeline owns the "campaign_metadata" section.

Infrastructure collectors never write directly to either cache.

Cache persistence is handled exclusively by the Cache Manager.

Alternatives Considered
-----------------------

1. Storing complete CT history

2. Separate CT-specific cache

3. Google CT API

4. Censys API

Decision Outcome
----------------

CT augments SSL intelligence rather than replacing it.

SSL represents the currently deployed certificate.

CT represents historical certificate intelligence.

The collector exposes the common infrastructure interface

collect_ct(domain)

↓

{

    "features": {...},

    "metadata": {...}

}

Raw CT records are discarded after normalization into reusable
infrastructure observations.

------------------------------------------------------------------------

ADR-007
--------

Title
-----
Normalized Infrastructure Intelligence Storage

Decision
--------
Infrastructure collectors never persist raw responses obtained from
external services.

Instead, collector outputs are normalized into compact reusable
infrastructure intelligence before being written to the
Infrastructure Intelligence Cache.

Repeated entities such as

- Certificate Issuers
- Subject Alternative Names (SANs)
- Common Names

are aggregated into frequency maps.

Example

Instead of

Let's Encrypt
Let's Encrypt
Let's Encrypt
Google Trust

the cache stores

{
    "Let's Encrypt": 3,
    "Google Trust": 1
}

Reason
------
Raw external responses are often significantly larger than the
information required by downstream components.

Frequency aggregation preserves:

- presence
- prevalence
- reuse patterns

while substantially reducing cache size.

The chronological ordering of repeated entities is intentionally not
preserved because the framework performs infrastructure intelligence,
campaign analysis and phishing prediction rather than certificate
lifecycle reconstruction.

Alternatives Considered
-----------------------
1. Persist raw collector responses

2. Persist ordered historical records

3. Persist unique values only

Decision Outcome
----------------
The Infrastructure Intelligence Cache stores compact normalized
observations that are reusable across Prediction and Campaign
pipelines while remaining storage efficient.

Ordering information that does not contribute to downstream analytics
is intentionally discarded.

------------------------------------------------------------------------

# ADR-008
-------- 

## Title
-----

Infrastructure Observation Cache

Decision
--------

The framework introduces a dedicated Infrastructure Observation Cache.

The Observation Cache stores normalized infrastructure observations
retrieved from external services.

Examples include

    WHOIS

    SSL

    Certificate Transparency

    Network Intelligence

The Observation Cache is physically separate from the Feature Cache.

The Observation Cache is stored in

    infra_observation_cache.json

The Feature Cache remains

    infra_cache.json

The Infrastructure Cache Manager owns both caches.

Collectors never access caches directly.

Instead, collectors remain stateless and simply return normalized
observations.

The Infrastructure Orchestrator decides

    • whether cached observations may be reused

    • when observations should be refreshed

    • when caches should be updated

Cache Validity
--------------

An Observation Cache entry is considered reusable only when the
observation is both temporally valid and semantically usable.

Cache validity therefore requires

    • a valid cache entry

    • a matching observation cache version

    • a valid cached_at timestamp

    • the observation to be within its collector-specific TTL

    • a populated observation payload

A cache entry must not be considered valid merely because its version
and TTL are valid.

For example, the following is not considered a reusable observation

    {
        "features": {},
        "metadata": {}
    }

Such an entry indicates that the collector did not provide usable
infrastructure information.

Therefore, a fresh but empty observation is treated as an unusable
cache entry and the corresponding collector is allowed to execute
again.

This distinction is important because freshness alone does not
guarantee semantic validity.

An observation may contain individual fields with null or empty values
without becoming invalid.

For example

    "registrant_name": null

or

    "ssl_error": null

may be valid because the observation itself contains other usable
information.

The validity decision therefore applies to the observation payload as
a whole rather than requiring every individual field to be populated.

Observation Retrieval
---------------------

The Observation Cache stores a persistence envelope containing

    • version

    • cached_at

    • data

The data portion contains the normalized observation

    • features

    • metadata

The get_observation() interface returns only the normalized data
portion.

Therefore callers receive

    {
        "features": {...},
        "metadata": {...}
    }

rather than the persistence envelope.

Cache validity is evaluated separately because TTL validation requires
access to persistence information such as cached_at.

The cache validity check therefore does not use the normalized
get_observation() result to perform TTL validation.

Reason
------

External infrastructure lookups are significantly more expensive than
local cache access.

Many workflows repeatedly analyse the same domains.

Examples include

    Batch Prediction

    Campaign Analysis

    Historical Campaign Analysis

    Repeated Streamlit executions

Caching normalized observations eliminates repeated network latency
without coupling collectors to cache management.

Raw third-party responses are not stored.

Instead, only normalized observations required by downstream
components are persisted.

This keeps the cache compact while remaining reusable.

The distinction between cache freshness and cache usability is also
required to prevent an empty observation from suppressing a necessary
collector execution.

Without this distinction, the framework could incorrectly report a
cache hit while returning empty infrastructure features.

This could result in infrastructure features disappearing from the
prediction feature matrix even though the underlying collectors are
capable of producing valid observations.

Alternatives Considered
-----------------------

1. Cache management inside collectors.

   Rejected because collectors should remain stateless.

2. Cache only derived prediction features.

   Rejected because Campaign Analysis also requires reusable
   infrastructure observations.

3. Cache raw external responses.

   Rejected because cache size grows unnecessarily and introduces
   external schema dependency.

4. Treat every version-valid and TTL-valid observation as reusable.

   Rejected because a fresh observation may still contain an empty
   feature and metadata payload.

   Cache freshness alone is therefore insufficient to establish
   semantic validity.

Decision Outcome
----------------

Infrastructure collection follows the sequence

Infrastructure Orchestrator

↓

Observation Cache

↓

Validate version, TTL and payload

↓

Collector (if required)

↓

Observation Cache Update

↓

Derived Prediction Features

↓

Derived Campaign Metadata

The resulting cache semantics are

    No cache entry
        → Cache Miss

    Invalid cache version
        → Stale Observation

    Invalid or missing timestamp
        → Stale Observation

    TTL expired
        → Stale Observation

    Valid version and TTL but empty payload
        → Unusable Observation / Cache Miss

    Valid version, TTL and populated payload
        → Cache Hit

This preserves ownership boundaries while minimizing repeated
network requests.

It also ensures that infrastructure features are derived only from
usable observations and prevents empty cached observations from
silently suppressing infrastructure collection.

-----------------------------------------------------------------

# ADR-009

## Title

Batch Infrastructure Orchestration and Pipeline Ownership

---

## Status

Accepted

---

## Context

Infrastructure intelligence may be required for a batch of URLs during
Batch Prediction.

The framework also supports a separate Campaign Analysis pipeline.

Campaign Analysis may execute:

1. After Batch Prediction for the same batch, or
2. Independently through the standalone Campaign Analysis page.

The infrastructure package therefore requires a clear separation between:

- Batch infrastructure orchestration
- Prediction processing
- Campaign processing
- Infrastructure observation caching
- Feature Cache ownership
- Campaign analysis

The batch infrastructure layer must not become responsible for Campaign
Analysis itself.

---

## Decision

`infra_batch.py` is implemented as the batch orchestration layer of the
Infrastructure Package.

It receives a complete batch of URLs, loads/materializes the batch once,
and processes it as a single batch execution.

The public interface is:

    process_batch(urls, feature_section)

The batch orchestrator delegates infrastructure intelligence to:

    infra_features.py

The batch orchestrator does not directly access or manage either cache.

---

## Batch Processing Model

The complete batch is loaded first:

    Batch of URLs
          |
          v
    Load / materialize batch
          |
          v
    Single batch execution
          |
          v
    Process URLs within the batch
          |
          v
    Batch result

Processing individual URLs internally does not constitute separate
pipeline executions.

The batch remains one logical execution unit.

---

## Infrastructure Processing

For each URL, `infra_batch.py` delegates infrastructure intelligence to:

    collect_infrastructure_features(
        url,
        feature_section
    )

The infrastructure orchestration then follows the established cache
hierarchy:

    Feature Cache
          |
       valid?
       /    \
     YES     NO
      |       |
      v       v
     use   Observation Cache
                 |
          valid observation?
             /        \
           YES         NO
            |           |
            v           v
          reuse      collector
                         |
                         v
                  Observation Cache
                         |
                         v
                   derive result

`infra_batch.py` does not duplicate this cache logic.

---

## Feature Cache Ownership

Feature Cache ownership remains with the pipeline that owns the resulting
derived intelligence.

### Prediction

The Prediction Pipeline owns:

    infra_cache.json
    └── data

The Infrastructure Package returns the infrastructure-derived prediction
features.

The Prediction Pipeline is responsible for persisting them in the
`data` section.

### Campaign

The Campaign Package owns:

    infra_cache.json
    └── metadata

The Campaign Package is responsible for validating, deriving, and
persisting campaign metadata.

`infra_batch.py` does not update either Feature Cache section.

---

## Observation Cache

The Observation Cache is the shared reusable infrastructure-observation
layer.

`infra_features.py` manages access to the Observation Cache through
`infra_cache.py`.

The Observation Cache contains normalized reusable observations obtained
from infrastructure collectors.

It does not contain:

- raw external responses;
- Prediction-owned Feature Cache data;
- Campaign-owned Feature Cache metadata.

Infrastructure observations collected during one pipeline execution can
therefore be reused by another pipeline.

---

## Batch Prediction

The primary Infrastructure Package batch use case is Batch Prediction.

The execution is:

    Batch Prediction Pipeline
              |
              v
        infra_batch.py
              |
              v
        infra_features.py
              |
              +---- Feature Cache
              |
              +---- Observation Cache
              |
              +---- Network / WHOIS / SSL / CT
                    collectors when required
              |
              v
        Infrastructure prediction features
              |
              v
        Prediction Pipeline

The Prediction Pipeline subsequently owns the update of:

    infra_cache.json
    └── data

---

## Campaign Analysis After Batch Prediction

Campaign Analysis is a separate pipeline/package.

When Campaign Analysis follows Batch Prediction:

    Batch Prediction
          |
          v
    Prediction completes
          |
          v
    Campaign Package
          |
          v
    Campaign Analysis

The Campaign Package may reuse infrastructure observations already
populated during Batch Prediction.

The Campaign Package independently manages its Campaign metadata
Feature Cache flow.

Campaign Analysis is therefore not automatically executed by
`infra_batch.py`.

---

## Standalone Campaign Analysis

When only the Campaign Analysis page is executed:

    Campaign Analysis Page
            |
            v
      Campaign Package
            |
            v
    Feature Cache["metadata"]
            |
            v
    Validate against Observation Cache
            |
       +----+----+
       |         |
     Valid     Invalid
       |         |
       v         v
      Use    Observation Cache
                 |
            +----+----+
            |         |
          Valid     Missing/Stale
            |         |
            v         v
         Derive    Infrastructure
         metadata  collectors
                      |
                      v
              Observation Cache
                      |
                      v
               Derive campaign
                  metadata
                      |
                      v
              Feature Cache["metadata"]

The Campaign Package does not require Batch Prediction to have run first.

Existing valid observations are reused.

Missing or stale observations may require infrastructure collection,
after which the Observation Cache is updated and campaign metadata is
derived.

---

## Behavioral Intelligence

`infra_behavior.py` is not automatically invoked by `infra_batch.py`.

Behavioral intelligence belongs to Campaign-side processing.

Therefore:

    infra_batch.py
        |
        └── Infrastructure batch orchestration

while:

    Campaign Package
        |
        +── Campaign metadata
        +── Behavioral intelligence
        +── Campaign features
        +── Campaign clustering
        └── Campaign detection

remain separate responsibilities.

---

## Error Handling

A failure while processing one URL must not terminate the complete batch.

The batch result records:

- total
- successful
- failed

An individual URL failure is retained with its associated error
information.

This allows a large batch to continue processing even when individual
URLs cannot be processed successfully.

---

## Alternatives Considered

### 1. Process every URL as an independent pipeline execution

Rejected.

This would introduce unnecessary repeated initialization and weaken
batch-level orchestration.

---

### 2. Let `infra_batch.py` manage the caches

Rejected.

Cache ownership would become ambiguous and duplicate the cache logic
already implemented in `infra_features.py` and `infra_cache.py`.

---

### 3. Make `infra_batch.py` responsible for Campaign Analysis

Rejected.

Campaign Analysis is owned by the Campaign Package.

The Infrastructure Package supplies infrastructure intelligence; it does
not own campaign detection or clustering.

---

### 4. Automatically invoke behavioral analysis for every batch

Rejected.

Behavioral intelligence is required by Campaign Analysis, not by the
Infrastructure Package's Batch Prediction orchestration.

---

## Decision Outcome

The infrastructure architecture is:

    Batch Prediction
            |
            v
      infra_batch.py
            |
            v
     infra_features.py
            |
       +----+----------------+
       |                     |
       v                     v
 Feature Cache        Observation Cache
    "data"                  |
       |              Network / WHOIS /
       v              SSL / CT collectors
  Prediction                 |
                             v
                    Normalized observations

After Prediction:

    Prediction
        |
        v
    Campaign Package
        |
        v
    Campaign Analysis

For standalone Campaign Analysis:

    Campaign Package
        |
        v
    Campaign Feature Cache
        |
        v
    Observation Cache
        |
        v
    Collectors when required
        |
        v
    Campaign metadata
        |
        v
    Campaign Analysis

---

## Final Architectural Principle

`infra_batch.py` orchestrates infrastructure intelligence for a complete
batch.

It does not own:

- Prediction
- Campaign Analysis
- Behavioral analysis
- Campaign clustering
- Campaign detection
- Feature Cache persistence

The Prediction Pipeline owns the `data` Feature Cache section.

The Campaign Package owns the `metadata` Feature Cache section.

The Observation Cache provides shared normalized infrastructure
observations that can be reused across both pipelines.

----------------------------------------------------------------

# ADR-010

## Title

Infrastructure Package Architecture and Pipeline Integration

---

## Status

Accepted

---

## Context

The Infrastructure Package provides reusable infrastructure intelligence
to the Prediction Pipeline and subsequently to Campaign Analysis.

The package must maintain clear separation between:

- Batch infrastructure orchestration
- Infrastructure feature orchestration
- Feature Cache
- Observation Cache
- Infrastructure collectors

The Prediction Pipeline is the primary entry point for batch infrastructure
processing.

Infrastructure intelligence must be reusable across subsequent processing,
including Campaign Analysis, without unnecessary repeated network collection.

---

## Decision

The Infrastructure Package follows the following architecture:

    Prediction Pipeline
            |
            v
      infra_batch.py
            |
            v
     infra_features.py
            |
       +----+--------------------+
       |                         |
       v                         v
    Feature Cache          Observation Cache
       "data"                      |
                                   |
                   +---------------+---------------+
                   |               |               |
                   v               v               v
                Network          WHOIS           SSL / CT

---

## Component Responsibilities

### Prediction Pipeline

The Prediction Pipeline initiates batch infrastructure processing.

It invokes:

    infra_batch.py

The Prediction Pipeline owns the Prediction Feature Cache section:

    infra_cache.json
    └── data

The Prediction Pipeline is responsible for persisting the derived
prediction infrastructure features into this section.

---

### infra_batch.py

`infra_batch.py` is the batch orchestration layer of the Infrastructure
Package.

Its responsibilities are:

- receive a complete batch of URLs;
- materialize the batch once;
- execute the batch as one logical processing unit;
- delegate infrastructure intelligence to `infra_features.py`;
- maintain batch-level success and failure information;
- return the infrastructure results for the batch.

`infra_batch.py` does not:

- implement infrastructure collectors;
- directly access the caches;
- perform Prediction;
- perform Campaign Analysis;
- perform Campaign clustering or detection;
- manage Feature Cache persistence.

---

### infra_features.py

`infra_features.py` is the infrastructure intelligence orchestrator.

Its responsibilities are:

- check the appropriate Feature Cache result;
- validate the underlying Observation Cache entries;
- reuse valid Feature Cache results;
- reuse valid normalized observations;
- invoke collectors only when required;
- update the Observation Cache through `infra_cache.py`;
- derive infrastructure features and metadata from normalized
  observations.

`infra_features.py` does not own the final Feature Cache section.

---

## Feature Cache

The Feature Cache contains derived pipeline-specific intelligence.

Its ownership is divided by downstream responsibility.

### Prediction

The Prediction Pipeline owns:

    infra_cache.json
    └── data

### Campaign

The Campaign Package owns:

    infra_cache.json
    └── metadata

The two sections must be updated independently.

Updating one section must not overwrite or clear the other section.

---

## Observation Cache

The Observation Cache is the shared reusable infrastructure intelligence
layer.

It stores normalized observations obtained from infrastructure collectors.

It does not store:

- raw external service responses;
- Prediction-specific Feature Cache data;
- Campaign-specific Feature Cache data.

The Observation Cache allows infrastructure intelligence collected during
one execution to be reused by another execution.

For example:

    Prediction
        |
        v
    Network observation
        |
        v
    Observation Cache
        |
        v
    Campaign Analysis
        |
        v
    reuse Network observation

---

## Infrastructure Collectors

The Infrastructure Package contains independent collectors for:

- Network
- WHOIS
- SSL
- Certificate Transparency

The collectors are responsible only for collecting and normalizing their
respective infrastructure intelligence.

They do not own persistent cache management.

The normalized observations are made available to `infra_features.py`,
which manages their reuse through the Observation Cache.

---

## Cache Resolution Hierarchy

Infrastructure processing follows the following hierarchy:

    Feature Cache
          |
          v
    Is derived result valid?
          |
       +--+--+
       |     |
      YES    NO
       |     |
       v     v
      Use   Observation Cache
                 |
                 v
        Is observation valid?
             |
          +--+--+
          |     |
         YES    NO
          |     |
          v     v
        Reuse  Collector
                 |
                 v
        Observation Cache
                 |
                 v
             Derive
                 |
                 v
          Feature Cache

Only the missing or stale observation is collected from the external
service.

A valid observation is never unnecessarily recollected merely because
another observation is stale.

---

## Batch Prediction Flow

The complete Batch Prediction infrastructure flow is:

    Prediction Pipeline
            |
            v
      infra_batch.py
            |
            v
     infra_features.py
            |
            +------------------------+
            |                        |
            v                        v
      Feature Cache          Observation Cache
          "data"                      |
            |                         |
            |             +-----------+-----------+
            |             |           |           |
            |             v           v           v
            |          Network      WHOIS       SSL / CT
            |                         |
            +------------+------------+
                         |
                         v
               Prediction Infrastructure
                    Feature Result
                         |
                         v
                    Prediction

---

## Reuse Across Pipelines

The Observation Cache is intentionally shared.

Therefore, infrastructure information collected during Batch Prediction
can subsequently be reused by Campaign Analysis.

The Campaign Package independently determines whether its campaign
metadata Feature Cache is valid.

If the Campaign Feature Cache is invalid:

    Campaign Package
          |
          v
    Observation Cache
          |
     +----+----+
     |         |
   valid     missing/stale
     |         |
     v         v
   derive    collector
     |         |
     |         v
     |   Observation Cache
     |         |
     +----+----+
          |
          v
    Campaign metadata
          |
          v
    Feature Cache["metadata"]

---

## Standalone Campaign Analysis

Campaign Analysis can also execute independently without Batch Prediction.

In this case, the Campaign Package is responsible for its own
campaign-metadata cache resolution.

The absence of a previous Prediction execution does not prevent Campaign
Analysis from obtaining infrastructure intelligence.

Existing valid Observation Cache entries are reused.

Missing or stale observations trigger the appropriate infrastructure
collector.

---

## Design Principles

The Infrastructure Package follows these principles:

1. Collectors remain independent and stateless.
2. Raw external responses are not persisted.
3. Normalized observations are reusable across pipelines.
4. Feature Cache ownership remains with the consuming pipeline.
5. Observation Cache is shared infrastructure state.
6. `infra_features.py` owns infrastructure cache orchestration.
7. `infra_batch.py` owns batch orchestration only.
8. Campaign Analysis remains owned by the Campaign Package.
9. A stale observation does not invalidate unrelated valid observations.
10. External network collection occurs only when required.

---

## Decision Outcome

The Infrastructure Package is structured as:

    Prediction Pipeline
            |
            v
      infra_batch.py
            |
            v
     infra_features.py
            |
       +----+--------------------+
       |                         |
       v                         v
    Feature Cache          Observation Cache
       "data"                      |
                                   |
                   +---------------+---------------+
                   |               |               |
                   v               v               v
                Network          WHOIS           SSL / CT

The Infrastructure Package therefore provides a reusable infrastructure
intelligence layer without taking ownership of Prediction or Campaign
Analysis.

The Prediction Pipeline owns the prediction Feature Cache section.

The Campaign Package owns the campaign metadata Feature Cache section.

The Observation Cache provides the shared normalized infrastructure
observations required by both pipelines.

---------------------------------------------------------------
# ADR-011
=======

## Title
-------

Restoration and Integration of the Complete Infrastructure Feature Set


Decision
--------

The Infrastructure Feature Pipeline retains and integrates the complete
infrastructure feature set established during the earlier experimental
phase of the project.

The infrastructure feature set is not limited to basic availability
signals such as

    has_ip

    has_asn

    has_domain_age

Instead, the derived infrastructure feature layer preserves the richer
feature set required by the predictive pipeline and subsequent adaptive
decision logic.

The infrastructure feature set includes signals derived from

    Network Intelligence

    WHOIS

    SSL / TLS

    Certificate Transparency

The resulting infrastructure feature set includes, among others,

    domain_age_days

    has_domain_age

    is_new_domain

    domain_age_bucket

    has_ip

    has_asn

    is_foreign_hosting

    asn_reputation

    infra_stability_score

    infra_trust_score

    infra_trust_score_scaled

    trusted_infra_flag

    strong_trusted_infra

    strong_trusted_infra_weighted

    has_ssl

    certificate_age_days

    certificate_lifetime_days

    certificate_remaining_days

    self_signed

    wildcard_certificate

    san_count

    ct_has_history

    ct_record_count

    registration_lifetime_days

    registration_remaining_days

    privacy_protected

    domain_status_count

These features are derived from normalized infrastructure observations
rather than directly from raw third-party responses.

The complete feature set is then combined with the existing predictive
features.

The predictive feature construction therefore follows the structure

    URL Features

    +

    HTML Features

    +

    Infrastructure Features

    ↓

    Complete Predictive Feature Vector

The infrastructure trust-related features are explicitly retained:

    infra_trust_score

    infra_trust_score_scaled

    trusted_infra_flag

    strong_trusted_infra

    strong_trusted_infra_weighted

    infra_stability_score

These features are required not only for model training but also for
the adaptive decision logic applied after model prediction.


Reason
------

The earlier conference-era implementation demonstrated that
infrastructure intelligence was intended to provide more than simple
network availability information.

During the subsequent infrastructure-cache refactoring, the
infrastructure collection mechanism was redesigned around normalized
observations and derived features.

During this refactoring, some of the previously established derived
infrastructure features were temporarily lost from the prediction
feature vector.

This caused the infrastructure training pipeline to produce a dataset
containing only the non-infrastructure features.

As a consequence,

    infrastructure columns were absent

    infra_trust_score was unavailable

    adaptive infrastructure signals could not participate in training

    downstream adaptive decision logic would lose the information on
    which it depends

The issue was therefore not a problem with XGBoost itself.

The problem was that the infrastructure-derived feature layer had not
fully preserved the previously established feature contract.

The feature set established during the earlier experimental phase is
therefore treated as part of the intended predictive architecture and
must not be silently removed during infrastructure-cache refactoring.


Feature Count
-------------

The infrastructure feature set is combined with the existing URL and
HTML features.

The resulting current feature vector contains

    60 URL features

    5 HTML features

    27 Infrastructure features

    -------------------------

    92 total features

The exact number of infrastructure features may evolve if the
infrastructure observation model is extended, but existing features
must not be removed without an explicit architectural decision.


Alternatives Considered
-----------------------

1. Retain only basic infrastructure availability features.

   Rejected because this would discard previously established trust,
   stability, SSL, WHOIS and CT intelligence.

2. Reconstruct infrastructure features only during inference.

   Rejected because training and inference would no longer use the same
   feature contract.

3. Remove the trust-related features because XGBoost can learn from
   lower-level features.

   Rejected because these features are also consumed by the adaptive
   decision layer and therefore have architectural value beyond model
   training.

4. Replace the complete feature set with a smaller newly designed set.

   Rejected because this would invalidate comparability with the earlier
   experimental results without a deliberate ablation or architectural
   decision.


Decision Outcome
----------------

The Infrastructure Feature Pipeline preserves the complete established
infrastructure feature set.

Infrastructure cache refactoring may change how observations are
obtained and persisted, but it must not silently change the downstream
feature contract.

The following principle is therefore established:

    Cache architecture may evolve independently from the predictive
    feature contract.

The final predictive pipeline uses the complete combined feature vector
and retains the infrastructure trust and stability signals required by
the adaptive decision layer.

-------------------------------------------------------------

# ADR-012
=======

## Title
--------

Infrastructure Feature Ablation and Contribution Analysis


Decision
--------

The infrastructure feature set will be evaluated using ablation and
feature-contribution analysis rather than assuming that every
infrastructure feature contributes equally to predictive performance.

The purpose of the analysis is to determine

    which infrastructure signals contribute to prediction

    which signals provide complementary information

    which signals are redundant

    which signals provide value primarily to adaptive decision logic

    whether infrastructure intelligence improves the predictive model
    beyond URL and HTML features alone


Experimental Baseline
----------------------

The predictive pipeline uses the same balanced_urls.csv dataset and
the same deterministic sampling and train-test split used in the
earlier experimental evaluation.

The XGBoost model configuration and train-test methodology are retained.

The infrastructure feature integration is therefore evaluated without
changing the underlying dataset split or model configuration.

This allows the effect of infrastructure information to be studied
without simultaneously changing the principal experimental conditions.


Feature Contribution
--------------------

The integrated infrastructure model demonstrates that infrastructure
features participate in the predictive model.

In the observed training run, the feature importance ranking included

    has_asn

    registration_lifetime_days

    domain_age_days

    asn_reputation

    infra_trust_score

    certificate_lifetime_days

    san_count

among the higher-contributing features.

In particular, has_asn was also present in the earlier feature set but
its relative contribution increased after the richer infrastructure
features were restored.

This indicates that the value of infrastructure intelligence is not
necessarily attributable to one newly introduced feature.

Instead, several infrastructure signals provide complementary
information about the domain and its hosting environment.


Infrastructure Trust Features
-----------------------------

The following features are retained as explicit adaptive signals:

    infra_trust_score

    infra_trust_score_scaled

    trusted_infra_flag

    strong_trusted_infra

    strong_trusted_infra_weighted

    infra_stability_score

The observed training data showed meaningful variance in these
features.

For example, the observed variance included non-zero values for

    infra_stability_score

    infra_trust_score

    infra_trust_score_scaled

    trusted_infra_flag

    strong_trusted_infra

    strong_trusted_infra_weighted

Therefore these features are not constant columns and are capable of
contributing information to the predictive model.


Observed Infrastructure Relationship
--------------------------------------

The observed cross-tabulation between infrastructure trust score and
the target demonstrated that trust score distributions differ between
the two classes.

Observed example:

    infra_trust_score    class 0    class 1

    0                       52        293
    1                       58        218
    2                      310        172
    3                      330         67

This indicates that infrastructure trust contains class-discriminative
information.

In particular, higher infrastructure trust scores were substantially
more prevalent in the benign class than in the malicious class.

This provides empirical justification for retaining infrastructure
trust as a meaningful signal rather than treating it merely as
decorative metadata.


Why the Additional Features Can Improve Recall
-----------------------------------------------

The additional infrastructure features provide information that cannot
always be inferred reliably from URL lexical structure alone.

URL lexical features primarily describe

    characters

    tokens

    lengths

    delimiters

    paths

    parameters

    subdomains

HTML features describe aspects of the retrieved page.

Infrastructure features provide a different view of the same domain,
including

    domain age

    hosting identity

    ASN information

    hosting geography

    certificate characteristics

    certificate history

    registration characteristics

    infrastructure stability

These signals can therefore help the classifier distinguish URLs whose
lexical appearance is similar but whose underlying infrastructure is
different.

This complementary information can improve classification of difficult
samples.

In particular, infrastructure features may help recover malicious
samples that are not strongly suspicious from lexical or HTML
characteristics alone.

This provides a plausible mechanism for an increase in recall.

The improvement should nevertheless be attributed to the experimental
results rather than assumed solely from feature semantics.


Interpretation of the Richer Feature Set
----------------------------------------

The richer infrastructure representation is therefore interpreted as
an additional information channel rather than simply an increase in
feature count.

The important distinction is

    More Features

    versus

    More Independent Information

The infrastructure feature set is valuable when it introduces
information that is complementary to lexical and HTML signals.

Features such as

    domain age

    ASN reputation

    registration lifetime

    certificate lifetime

    infrastructure stability

can describe properties of the domain ecosystem that are not directly
encoded in the URL string.


Ablation Principle
------------------

The following conceptual ablation hierarchy is adopted:

    URL only

    ↓

    URL + HTML

    ↓

    URL + HTML + Infrastructure

The comparison should use identical

    dataset

    sampling

    train-test split

    model configuration

    evaluation metrics

where possible.

The primary evaluation metrics are

    Accuracy

    Precision

    Recall

    F1-Score

    ROC-AUC


Decision Outcome
----------------

Infrastructure intelligence is retained as a first-class predictive
feature group.

The contribution of individual infrastructure features is not assumed
from feature count alone.

Feature importance, variance and ablation results are used together to
interpret the role of infrastructure intelligence.

Features that have low predictive importance may still be retained when
they are required by the adaptive decision layer or campaign analysis.

Therefore

    Model Importance

and

    Architectural Importance

are treated as distinct concepts.

--------------------------------------------------------------------

# ADR-013
=======

## Title
---------

Infrastructure Cache Validity, Derived Feature Integrity and
Predictive Feature Contract


Decision
--------

The Infrastructure Cache architecture distinguishes between

    cached observations

    derived infrastructure features

    adaptive decision signals

A cached observation is considered reusable only when the observation
is actually populated and satisfies the cache validity requirements.

The existence of a cache entry alone does not imply that a valid
observation exists.

A cache entry containing an empty or unpopulated observation must not be
treated as a valid cache hit.


Cache Validity
--------------

The Observation Cache stores normalized observations using an envelope
containing information such as

    version

    cached_at

    data

The validity of an observation is determined using the persisted
observation information.

The following conditions are required for a reusable observation:

    the observation exists

    the cache version is compatible

    cached_at is valid

    the observation has not exceeded its collector-specific TTL

A populated observation therefore represents a valid reusable result.

An empty observation does not represent successful infrastructure
collection and must not silently satisfy the cache-validity check.


Reason for the Change
---------------------

During infrastructure-cache refactoring, an important failure mode was
identified.

The cache could contain an entry whose structure existed but whose
actual observation data was empty.

If the presence of such an entry were interpreted as a valid cache hit,
the Infrastructure Orchestrator could skip the collector.

The resulting derived feature set would then contain empty or missing
infrastructure information.

This produced the following failure pattern:

    Cache Entry Exists

    ↓

    Entry Incorrectly Considered Valid

    ↓

    Collector Not Executed

    ↓

    Empty Observation Returned

    ↓

    Empty Derived Infrastructure Features

    ↓

    Infrastructure Columns Missing From Training Dataset


This behaviour was particularly problematic because the pipeline could
appear to execute successfully while silently removing infrastructure
information from the model input.


Separation of Responsibilities
------------------------------

The Feature Cache remains responsible for persisted derived feature
sections.

The Observation Cache remains responsible for reusable normalized
collector observations.

The Infrastructure Orchestrator is responsible for deciding whether

    a feature cache result can be reused

    an observation can be reused

    a collector must be executed

    observations must be persisted

    derived features must be constructed


Collectors remain responsible only for collecting and normalizing
external infrastructure information.

Collectors do not own cache policy.


Feature Cache and Observation Cache
-----------------------------------

The two caches serve different purposes.

Feature Cache

    infra_cache.json

stores derived infrastructure feature sections.

Observation Cache

    infra_observation_cache.json

stores normalized observations.

The Feature Cache may therefore be reused without invoking the
collectors when the complete derived feature section is valid.

If the Feature Cache cannot be reused, the Observation Cache is
consulted.

If an observation is missing or stale, only the corresponding collector
needs to be executed.


Preservation of Derived Features
--------------------------------

The cache refactoring must not alter the downstream infrastructure
feature contract.

The derived infrastructure feature layer must continue to provide the
established trust and stability signals:

    infra_trust_score

    infra_trust_score_scaled

    trusted_infra_flag

    strong_trusted_infra

    strong_trusted_infra_weighted

    infra_stability_score

It must also preserve the other infrastructure intelligence derived
from

    Network

    WHOIS

    SSL

    Certificate Transparency


Regression Validation
---------------------

Regression tests are used to validate cache behaviour.

The cache test suite verifies scenarios including

    cold-start statistics

    feature-cache reuse

    stale observation handling

    selective observation reuse

    statistics reset

The expected behaviour for a partially stale domain is:

    valid observations are reused

    stale observations are recollected

    the feature cache is considered invalid when required

    only the necessary collectors are invoked

This avoids unnecessary external requests while preventing empty
observations from being treated as valid data.


Observed Validation
-------------------

The corrected implementation was validated using direct infrastructure
collection tests.

For a populated domain, the resulting infrastructure feature set
contains the expected trust signals.

Example values observed for example.com include

    infra_trust_score = 3

    infra_trust_score_scaled = 60

    trusted_infra_flag = 1

    strong_trusted_infra = 1

    strong_trusted_infra_weighted = 50

    infra_stability_score = 1

The integrated predictive feature construction was also validated to
contain

    60 URL features

    5 HTML features

    27 infrastructure features

    92 total features

The six required adaptive infrastructure signals were confirmed to be
present in the resulting feature vector.


Predictive Pipeline Integrity
-----------------------------

The infrastructure cache is an implementation mechanism and must not
change the predictive feature contract.

The following invariant is established:

    A valid infrastructure collection must produce the same logical
    derived feature set regardless of whether the information came
    from a valid cache or from a fresh collector execution.

Therefore

    Fresh Collection

and

    Valid Cache Reuse

must be functionally equivalent from the perspective of the predictive
pipeline.


Adaptive Decision Logic
-----------------------

The infrastructure trust and stability features are retained because
their role extends beyond XGBoost training.

The downstream inference architecture uses infrastructure intelligence
as part of adaptive decision logic.

Consequently, removing a feature solely because its XGBoost feature
importance is low may still break the intended inference architecture.

For example,

    strong_trusted_infra_weighted

may have low model feature importance while still being intentionally
used as an explicit adaptive signal.

Therefore predictive feature importance must not be used as the sole
criterion for removing infrastructure features.


Decision Outcome
----------------

The Infrastructure Cache architecture is considered correct only when

    valid populated observations are reusable

    stale observations are refreshed

    empty observations are not treated as valid

    derived infrastructure features are reconstructed correctly

    the complete infrastructure feature contract is preserved

    adaptive decision signals remain available

    cached and freshly collected results are functionally equivalent

This establishes cache correctness and feature integrity as separate
but connected architectural requirements.

The final architecture therefore follows:

    Feature Cache

        ↓

    if reusable
        ↓
    Derived Infrastructure Features

    otherwise

    Observation Cache

        ↓

    if observation valid
        ↓
    Reuse Observation

    otherwise

    Collector

        ↓

    Normalized Observation

        ↓

    Observation Cache

        ↓

    Derived Infrastructure Features

        ↓

    Predictive Model

        ↓

    Adaptive Decision Logic

--------------------------------------------------------------

## ADR-014 — Campaign Clustering Under Incomplete Infrastructure Observability

**Status:** Accepted  
**Date:** 2026-09-07  
**Decision Type:** Architecture / Limitation / Campaign Analysis  
**Related Components:** Network Infrastructure Collector, Observation Cache, Campaign Feature Extraction, Campaign Detector, DBSCAN, Batch Analysis  
**Related ADRs:** ADR-008 (Infrastructure Observation / Feature Cache Architecture)

---

### Context

The campaign-analysis subsystem combines URL-level prediction with a separate campaign-level representation.

The campaign-level feature space contains 51 features comprising:

- 25 lexical features
- 12 infrastructure features
- 8 campaign metadata features
- 3 batch-context reuse features
- 3 infrastructure identity features

Infrastructure information is collected independently from URL lexical characteristics and is reused through the Infrastructure Observation Cache.

The intended domain-sourcing architecture is:

- **Original/host domain** is used for host-level Network, SSL and CT observations.
- **Root domain** is used for WHOIS-derived information.

The Infrastructure Observation Cache validates observation freshness before reuse. If an observation is unavailable, expired, or cannot be obtained during collection, the corresponding infrastructure collector may return unavailable values. These values are currently represented in the feature space using zero-valued availability/behaviour features and `UNKNOWN`/null identity metadata.

This behaviour is intentional from a pipeline-continuity perspective: infrastructure collection failure or unavailability must not prevent URL-level prediction or campaign-level processing.

However, it introduces an important limitation:

> The current campaign feature representation does not distinguish between genuine absence of infrastructure information and failure to observe that infrastructure information at collection time.

---

### Decision

The system will **retain the current fail-soft infrastructure collection behaviour**.

If a Network infrastructure lookup fails, the collector returns the defined zero/unavailable representation rather than terminating the prediction or campaign-analysis pipeline.

For example, the current Network collector performs:

```text
Original / host domain
        │
        ▼
DNS / IP resolution
        │
        ├── Success
        │      │
        │      ▼
        │   IP information lookup
        │      │
        │      ▼
        │   ASN / country /
        │   organization / ISP
        │
        └── Failure
               │
               ▼
        IP = unavailable
               │
               ▼
        Network feature values
        become zero/unavailable

The resulting representation is then passed to the campaign feature construction pipeline.

This decision preserves:

Pipeline robustness — a failed infrastructure lookup does not terminate batch analysis.
Feature-space consistency — every URL still produces the expected 51 campaign features.
Separation of concerns — infrastructure collection remains independent from campaign clustering.
Cache correctness — a collector result is cached as an observation and can subsequently be validated using the normal Observation Cache mechanisms.
URL-level independence — campaign clustering does not replace or override the individual URL-level prediction.

Architectural Flow

The complete campaign-analysis flow under this design is:

                         500 URL Batch
                              │
                              ▼
                    ┌────────────────────┐
                    │ URL-Level Feature  │
                    │ Extraction         │
                    │ + Infrastructure   │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │ XGBoost Prediction │
                    │ 92-feature space   │
                    └─────────┬──────────┘
                              │
                              ▼
                    URL-level risk result
                    (model risk / final risk /
                     label / tier)
                              │
                              │
                              ▼
             ┌─────────────────────────────────┐
             │ Campaign Feature Construction   │
             │                                 │
             │ 25 Lexical                      │
             │ + 12 Infrastructure             │
             │ + 8 Campaign Metadata           │
             │ + 3 Batch Context               │
             │ + 3 Identity                    │
             │                                 │
             │ = 51 Campaign Features          │
             └────────────────┬────────────────┘
                              │
                              ▼
                       DBSCAN Clustering
                              │
                              ▼
                    Campaign Membership
                              │
                              ▼
                 ┌──────────────────────────┐
                 │ Campaign Risk Assessment │
                 │                          │
                 │ URL-level predictions    │
                 │ + campaign membership    │
                 └────────────┬─────────────┘
                              │
                              ▼
                       Campaign Report

The important architectural property is that URL-level prediction and campaign-level clustering are separate analytical layers.

Therefore, campaign membership is not required to have the same risk label as every URL inside the campaign.

Observed Limitation

When infrastructure observability is incomplete, the 12 infrastructure features and associated campaign metadata may contain predominantly zero/unavailable values.

For example, during a validated Batch Analysis run, the Network collector was tested for URLs belonging to Campaign-6.

For the affected domains:

Network Observation
        │
        ▼
DNS resolution
        │
        ▼
Failure
        │
        ▼
socket.gethostbyname()
returned:
[Errno 11001] getaddrinfo failed
        │
        ▼
IP unavailable
        │
        ▼
Network collector returned:
has_ip              = 0
has_asn             = 0
asn_reputation      = 0
is_foreign_hosting  = 0

The corresponding Observation Cache entries were nevertheless valid and current.

Therefore, the zeros in this case were not caused by stale-cache handling or incorrect cache reuse. They reflected the result of the actual infrastructure observation at collection time.

The resulting campaign representation can therefore contain many URLs with similar unavailable/unknown infrastructure states.

Campaign-6 Illustration

Campaign-6 contained:

Total URLs:       16
Malicious:        12
Benign:            4

The individual URL-level predictions were therefore mixed.

However, the campaign-level representation grouped the URLs using the 51-feature campaign space rather than their prediction labels.

For the affected URLs, Network observations produced unavailable infrastructure information, resulting in features such as:

has_ip                  = 0
has_asn                 = 0
asn_reputation          = 0
is_foreign_hosting      = 0

organization            = UNKNOWN
hosting_provider        = UNKNOWN
ASN                     = UNKNOWN

Consequently, when infrastructure evidence is unavailable, the campaign clustering representation relies relatively more heavily on the remaining observable dimensions, particularly the lexical component and any available campaign metadata/context.

Conceptually:

             Campaign-6 URLs
                    │
          ┌─────────┴─────────┐
          │                   │
          ▼                   ▼
   URL-level prediction   Campaign features
          │                   │
          │             ┌─────┴─────┐
          │             │           │
          │         Infrastructure  Lexical /
          │         unavailable     metadata
          │             │           │
          │             └─────┬─────┘
          │                   │
          │                   ▼
          │             51-D feature
          │             representation
          │                   │
          │                   ▼
          │                 DBSCAN
          │                   │
          └─────────────┐     │
                        ▼     ▼
                  Individual  Campaign
                     risk     membership
                        │     │
                        └──┬──┘
                           ▼
                     Mixed Campaign

Thus, Campaign-6 demonstrates that:

A campaign can contain URLs with different URL-level risk classifications when campaign-level similarity exists in the available feature representation.

At the same time, because infrastructure observability was incomplete, Campaign-6 cannot by itself be treated as proof of a single real-world phishing campaign.

Interpretation

Campaign-6 illustrates a distinction between two concepts:

URL-level question:
"Is this individual URL malicious?"

Campaign-level question:
"Do these URLs exhibit sufficiently similar
campaign-level characteristics?"

These questions are intentionally not identical.

A DBSCAN cluster can therefore legitimately contain:

Malicious + Benign
Malicious + Suspicious
Benign + Suspicious

URLs.

This is particularly important when infrastructure evidence is incomplete.

The campaign detector is not instructed to force campaign membership according to the XGBoost prediction label.

Cache and Failure Semantics

The Observation Cache does not create the missing infrastructure values.

The validated flow is:

Infrastructure Collector
        │
        ▼
Observation result
        │
        ├── Valid infrastructure data
        │       ↓
        │   Cache observation
        │
        └── No usable observation
                ↓
            Cache the
            collector result
                │
                ▼
        Campaign feature extraction

Therefore:

Stale cache
    ≠
Infrastructure unavailable

and

Cache miss
    ≠
Infrastructure unavailable

In the Campaign-6 investigation, all four Observation Cache categories tested for the affected URLs were present and valid:
Network   → valid
WHOIS     → valid
SSL       → valid
CT        → valid

The Network observation itself contained zero/unavailable values because DNS resolution failed during collection.

This confirms that the observed Campaign-6 representation was not caused by the previously identified stale-derived-cache issue.

Consequence for Campaign Clustering

The current architecture therefore has the following limitation:

Infrastructure collection failures or unavailable observations can reduce the discriminative power of infrastructure-aware campaign clustering and may cause greater reliance on lexical and other available campaign features.

This can potentially result in:

mixed-risk campaigns,
broader or less semantically pure clusters,
increased dependence on lexical similarity,
reduced confidence in campaign interpretation when infrastructure evidence is sparse.

The behaviour does not invalidate the clustering algorithm itself.

Instead, it identifies an observability limitation of the available campaign representation.

Why the Limitation Is Accepted

The limitation is accepted because forcing failed infrastructure observations to terminate processing would be more damaging to the overall framework.

The current design prioritizes:

graceful degradation,
fixed feature dimensionality,
continuous batch processing,
separation between URL-level and campaign-level intelligence,
explicit infrastructure caching,
and future extensibility.

The limitation is therefore documented rather than hidden.

Future Improvement

A future version may explicitly distinguish:

Infrastructure unavailable
        vs.
Infrastructure collection failed
        vs.
Infrastructure successfully observed

For example, a future observability/status layer could record:

observation_status:
    SUCCESS
    UNAVAILABLE
    DNS_FAILURE
    TIMEOUT
    API_FAILURE

without necessarily adding these status indicators directly to the existing 51-feature campaign representation.

Such an enhancement would allow future experiments to determine whether clustering behaviour is caused by:

genuine infrastructure similarity,
missing infrastructure information,
collection failures,
or lexical/campaign-level similarity.

This is intentionally left as a future enhancement and does not alter the current 51-feature campaign schema.

Validation Evidence

The Campaign-6 case was validated through three independent checks:

Observation Cache validation

All four observation categories for the 16 Campaign-6 domains were present and considered valid.

Direct Network collector execution

Example:

collect_network('rkriss.com')

returned:

{
    'features': {
        'has_ip': 0,
        'has_asn': 0,
        'asn_reputation': 0,
        'is_foreign_hosting': 0
    },
    'metadata': {
        'ip_address': None,
        'asn': None,
        'hosting_country': None,
        'organization': None,
        'isp': None,
        'has_owner_information': 0
    }
}

Independent DNS verification

Direct resolution produced:

socket.gaierror: [Errno 11001] getaddrinfo failed

confirming that the zero-valued Network observation was consistent with DNS resolution failure at the time of observation.

Final Decision

Accepted.

The framework will retain fail-soft infrastructure collection and fixed 51-dimensional campaign feature construction.

Mixed-risk campaign clusters are considered a valid possible output of the architecture and must not automatically be interpreted as clustering errors.

When infrastructure observability is incomplete, campaign-level interpretation must acknowledge that the clustering representation may rely more heavily on lexical and other available features.

Campaign-6 is retained as a representative validation/limitation example demonstrating:

Campaign-level similarity and URL-level risk are complementary rather than identical concepts, and incomplete infrastructure observability can influence campaign composition.

