# Dissertation Implementation Roadmap

## Overall Strategy

The dissertation implementation will be developed incrementally.

The objective is not to implement all proposed research components at
once. Instead, each major component will be completed and stabilized
before the next layer is added.

The implementation order is designed so that:

1. The core Prediction Pipeline becomes stable first.
2. Infrastructure intelligence is integrated into that pipeline.
3. Campaign-level intelligence is then used as an additional source of
   evidence.
4. Adaptive Decision Learning is built on top of the stable prediction,
   infrastructure, campaign and drift signals.
5. Campaign-specific feature engineering is deliberately deferred until
   the preceding architecture is stable.
6. Final evaluation and dissertation-level experiments are performed only
   after the complete architecture is integrated.

---

# Priority 1 — Complete and Stabilize the Prediction Pipeline

The first priority is to establish a stable Prediction Pipeline.

This includes:

- URL-level prediction
- Batch URL prediction
- Existing lexical / classical features
- TF-IDF-based intelligence where applicable
- Model inference
- Risk scoring
- Risk tier / decision generation
- Explainability
- Existing Streamlit prediction workflow

The Prediction Pipeline should become the stable baseline against which
all subsequent enhancements are evaluated.

## Infrastructure Integration

Infrastructure intelligence is integrated into the Prediction Pipeline
before moving to adaptive decision learning.

The Infrastructure Package provides:

- Network intelligence
- WHOIS intelligence
- SSL intelligence
- Certificate Transparency intelligence
- Normalized infrastructure observations
- Infrastructure-derived prediction features
- Infrastructure caching
- Observation reuse across executions

The Infrastructure Package has now been architecturally frozen.

The resulting architecture is:

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

The Prediction Pipeline owns the `data` section of the Feature Cache.

The Observation Cache remains reusable across Prediction and Campaign
processing.

---

# Priority 2 — Campaign Analysis as an Independent Intelligence Layer

Once the Prediction Pipeline and Infrastructure Package are stable,
Campaign Analysis is developed as a separate intelligence layer.

The Campaign Package is responsible for:

- Campaign metadata
- Campaign-level infrastructure relationships
- Campaign clustering
- Campaign detection
- Campaign-level reporting
- Campaign visualization
- Behavioral intelligence where required

The Campaign Package must remain independent from the Prediction
Pipeline.

Campaign Analysis can therefore operate in two ways:

### A. After Batch Prediction

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

The Campaign Package can reuse infrastructure observations already
collected during Prediction.

### B. Standalone Campaign Analysis

    Campaign Analysis Page
            |
            v
      Campaign Package
            |
            v
    Campaign metadata Cache
            |
            v
    Observation Cache
            |
            v
    Collectors when required
            |
            v
    Campaign Analysis

Prediction does not need to execute first.

---

# Priority 3 — Adaptive Decision Learning

After the Prediction and Campaign layers are stable, Adaptive Decision
Learning becomes the next major research component.

The objective is not simply to retrain the classifier.

The objective is to make the final risk decision adaptive to changing
evidence.

Adaptive Decision Learning can use signals from:

- Prediction model output
- Infrastructure intelligence
- Campaign-level intelligence
- Drift detection
- Historical decision behaviour
- Temporal changes in the phishing ecosystem

The conceptual flow becomes:

    URL
      |
      v
    Prediction
      |
      +-------------------+
      |                   |
      v                   v
 Infrastructure       Campaign
 Intelligence         Intelligence
      |                   |
      +---------+---------+
                |
                v
        Drift / Temporal Signals
                |
                v
       Adaptive Decision Layer
                |
                v
        Final Risk Decision

The important architectural decision is that Campaign Analysis does not
replace the Prediction Model.

Instead, campaign-level intelligence becomes an additional source of
evidence that can influence the final adaptive decision.

---

# Priority 4 — Campaign-Specific Feature Engineering

Campaign-specific feature engineering is intentionally deferred until
the Prediction, Infrastructure, Campaign and Adaptive Decision layers
are sufficiently stable.

This prevents premature expansion of the Prediction feature space.

Campaign features should be derived from the already-established
campaign and infrastructure intelligence rather than being introduced
directly into the original Prediction Pipeline.

Potential campaign-level signals include:

- Infrastructure similarity
- ASN similarity
- IP / subnet similarity
- SSL certificate reuse
- Historical certificate relationships
- Nameserver similarity
- Domain registration relationships
- Parameter morphology
- Behavioral similarity
- Campaign cluster membership
- Campaign confidence
- Campaign-level prevalence

These features should initially remain within the Campaign/Adaptive
Decision architecture.

They should only be promoted into the Prediction decision process when
their contribution can be demonstrated experimentally.

---

# Priority 5 — Drift Detection and Adaptive Retraining Integration

The existing drift framework is then integrated into the complete
adaptive architecture.

The drift layer provides:

- PSI
- KL divergence
- Jensen-Shannon divergence
- Drift severity
- Retraining recommendation
- Temporal monitoring

The purpose is to determine when the prediction environment has changed
enough to justify model adaptation.

The resulting architecture becomes:

    Reference Data
          |
          v
    Drift Detection
          |
          v
    Drift Severity
          |
          +-------------------+
          |                   |
        Stable              Drift
          |                   |
          v                   v
     Continue             Adaptive
     operation            response
                              |
                 +------------+------------+
                 |                         |
                 v                         v
          Decision adaptation       Model retraining