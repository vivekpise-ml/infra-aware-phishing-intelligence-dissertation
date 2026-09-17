# Infrastructure-Aware Drift-Adaptive Multimodal Phishing Risk Intelligence Framework

**M.Tech (Applied AI) — Final Year Dissertation**

An infrastructure-aware phishing risk intelligence framework that extends conventional URL-based phishing detection with **multi-source infrastructure intelligence, adaptive risk assessment, campaign-level intelligence, drift monitoring, explainability, and reusable infrastructure caching**.

> **Dissertation repository:**
> `https://github.com/vivekpise-ml/infra-aware-phishing-intelligence-dissertation`

> **Conference baseline:**
> `https://github.com/vivekpise-ml/infra-aware-phishing-intelligence`

---

## Dissertation Phase

This repository is the **active M.Tech dissertation implementation** and evolves from the implementation developed for the **PCEMS 2026 conference submission**.

The original conference workspace has been intentionally preserved as a **frozen baseline**. This repository contains the subsequent engineering enhancements, research experimentation, architectural refinements, and planned dissertation extensions.

The core architecture remains stable while the dissertation work progressively deepens the:

* Prediction Intelligence layer
* Infrastructure Intelligence layer
* Campaign Intelligence layer
* Drift Intelligence layer
* Adaptive Decision Intelligence layer

The dissertation therefore moves beyond a static phishing classifier toward an integrated **phishing risk intelligence system**.

---

# 1. Project Overview

Traditional phishing detection systems commonly operate as binary classifiers that determine whether an individual URL or webpage is benign or malicious.

However, phishing activity can involve much richer contextual information:

* Domain and registration characteristics
* DNS and network infrastructure
* IP and ASN relationships
* Hosting information
* SSL/TLS certificates
* Certificate Transparency observations
* Relationships among multiple URLs
* Campaign-level similarities
* Temporal changes in phishing behaviour

This project approaches phishing detection as a **risk intelligence problem rather than only a URL classification problem**.

The framework combines:

* URL lexical intelligence
* HTML/webpage structural features
* Network and DNS intelligence
* WHOIS/domain intelligence
* SSL/TLS certificate intelligence
* Certificate Transparency (CT) intelligence
* Machine-learning prediction
* Infrastructure trust and stability signals
* Adaptive decision intelligence
* Campaign-level analysis
* Drift monitoring
* Explainability
* Risk-oriented reporting

The intended output is not limited to:

```text
BENIGN / PHISHING
```

Instead, the system produces contextual intelligence including:

```text
Model Risk
Model Confidence
Infrastructure Intelligence
Infrastructure Trust / Stability
Adaptive Final Risk
Risk Tier
Decision
Campaign Evidence
Drift Evidence
Explainable Risk Report
```

---

# 2. Research Direction

The central research direction is the transition:

```text
Static Phishing Classification
            |
            v
Infrastructure-Aware Prediction
            |
            v
Phishing Risk Intelligence
            |
            v
Campaign + Drift Intelligence
            |
            v
Learning-Based Adaptive Risk Decision
```

The dissertation investigates whether phishing risk assessment can be improved by combining multiple independent sources of evidence rather than relying solely on the probability produced by an individual classifier.

The overall framework is organized into four major intelligence layers:

```text
                    ┌──────────────────────────┐
                    │     Prediction           │
                    │     Intelligence          │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   Infrastructure         │
                    │   Intelligence            │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │      Campaign             │
                    │      Intelligence         │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │       Drift               │
                    │       Intelligence        │
                    └────────────┬─────────────┘
                                 │
                                 v
                    Adaptive Decision Intelligence
                                 |
                                 v
                         Final Risk Assessment
```

---

# 3. Evolution of the Project

The dissertation implementation has evolved incrementally.

```text
Semester 3
    |
    | Research proposal
    | Research gap
    | Framework design
    v
PCEMS 2026
    |
    | 79-feature prediction
    | Infrastructure intelligence
    | Campaign analysis
    | Drift monitoring
    v
Post-PCEMS Enhancement
    |
    | SSL + Certificate Transparency
    | 92-feature prediction representation
    | Stronger infrastructure caching
    v
M.Tech Dissertation
    |
    | Learning-based adaptive decision intelligence
    | Campaign Intelligence v2.0
    | Temporal / campaign drift
    | Selective retraining
    v
Integrated Risk Intelligence System
```

The dissertation work is therefore an **augmentation of the conference implementation**, rather than a replacement of the original architecture.

---

# 4. Current Framework Architecture

The current framework accepts information from multiple sources:

```text
URL / Domain
HTML / Web Content
DNS / Network
WHOIS
SSL Certificate
Certificate Transparency
```

These sources feed three major operational components.

## 4.1 Prediction Intelligence

```text
URL
 |
 +--> Lexical Features
 |
 +--> HTML Features
 |
 +--> Infrastructure Features
 |
 v
Unified Feature Vector
 |
 v
XGBoost Classifier
 |
 v
Raw Model Risk + Confidence
 |
 v
Adaptive Decision Intelligence
 |
 v
Final Risk
 |
 v
Risk Intelligence Report
```

---

## 4.2 Campaign Intelligence

Campaign analysis operates independently from URL-level prediction.

```text
Batch URLs
    |
    v
Campaign Metadata
    |
    v
Similarity / Infrastructure Features
    |
    v
DBSCAN
    |
    v
Campaign Clusters
    |
    v
Campaign Risk
    |
    v
Campaign Confidence
    |
    v
Campaign Intelligence Report
```

The dissertation direction extends this toward explicit shared-infrastructure relationships:

```text
URL A ───── Shared IP ───── URL B
  │                           │
  ├──── Shared ASN ───────────┤
  │                           │
  ├──── Shared DNS ───────────┤
  │                           │
  └──── Shared SSL / Cert ────┘
                |
                v
        Campaign Discovery
                |
                v
         Campaign Risk
                |
                v
       Campaign Confidence
```

Campaign Intelligence does **not replace URL-level prediction**.

Instead:

```text
URL Prediction
      +
Campaign Evidence
      +
Infrastructure Evidence
      +
Drift Evidence
      |
      v
Adaptive Decision Intelligence
```

---

## 4.3 Drift Intelligence

The drift framework compares reference and current data distributions.

```text
Reference Data
      |
      +------------------+
      |                  |
      v                  v
Current Data        Distribution Analysis
                           |
                           v
                  PSI / KL / JS
                           |
                           v
                    Overall Drift
                           |
                           v
                       Severity
                           |
                           v
               Retraining Recommendation
```

Current drift metrics include:

* Population Stability Index (PSI)
* KL Divergence
* Jensen-Shannon Distance
* Overall Drift Score
* Drift Severity
* Retraining Recommendation

The dissertation extends this toward:

* Temporal drift
* Campaign / cluster drift
* Drift-aware campaign intelligence
* Selective retraining
* Integration with adaptive risk decisions

---

# 5. Prediction Intelligence

The prediction pipeline is the stable foundation of the dissertation system.

It supports:

* Single URL prediction
* Batch URL prediction
* URL lexical feature extraction
* HTML feature extraction
* Infrastructure enrichment
* XGBoost prediction
* Risk scoring
* Adaptive decision processing
* Explainability
* Risk reporting

The current prediction representation contains **92 features**, compared with the **79-feature PCEMS 2026 baseline**.

The post-PCEMS enhancement includes additional SSL and Certificate Transparency-derived infrastructure information.

---

# 6. Multi-Source Feature Engineering

The framework combines multiple categories of evidence.

## 6.1 URL Features

Examples include:

* URL length
* Host length
* Path length
* Query length
* Dot count
* Special-character counts
* Parameter counts
* Subdomain information
* Entropy
* Keyword-based signals
* URL structural characteristics

---

## 6.2 HTML Features

Where webpage content is available, structural signals include:

* Forms
* Links
* Scripts
* iFrames
* Event handlers
* Other webpage structural characteristics

---

## 6.3 Infrastructure Features

Infrastructure intelligence includes observations and derived attributes from:

### Network / DNS

* IP resolution
* ASN
* Hosting information
* DNS observations
* Network context

### WHOIS

* Domain age
* Registration information
* Registrar
* Domain status
* WHOIS availability

### SSL / TLS

* Certificate presence
* Certificate validity
* Issuer information
* SAN entries
* Certificate attributes

### Certificate Transparency

* Certificate issuance information
* Issuer / SAN patterns
* First-seen / last-seen observations
* CT log information

Infrastructure observations are normalized before being converted into reusable prediction and campaign features.

---

# 7. Infrastructure Intelligence Architecture

The infrastructure package is organized as a reusable subsystem.

```text
Prediction / Campaign Processing
             |
             v
       infra_batch.py
             |
             v
      infra_features.py
             |
      +------+------------------+
      |                         |
      v                         v
 Feature Cache           Observation Cache
      |                         |
      |                 +-------+-------+-------+
      |                 |       |       |       |
      |                 v       v       v       |
      |              Network  WHOIS   SSL/CT   |
      |                                         |
      +-----------------------------------------+
```

The architecture separates:

### Feature Cache

Stores derived infrastructure features used by prediction and campaign processing.

### Observation Cache

Stores normalized observations collected from:

* Network
* WHOIS
* SSL
* Certificate Transparency

If derived features are unavailable or stale, valid underlying observations can be reused before external collectors are invoked.

The design principle is:

```text
Collect once
     ↓
Normalize
     ↓
Cache
     ↓
Reuse
     ↓
Refresh only when required
```

This improves:

* Repeatability
* Execution time
* Resilience
* Scalability

---

# 8. Adaptive Decision Intelligence

A major research direction of the dissertation is the evolution of the decision layer.

The conference/current implementation uses transparent rule-based adaptive calibration after XGBoost inference.

Conceptually:

```text
XGBoost
   |
   +--> Model Risk
   |
   +--> Confidence
   |
   v
Adaptive Decision Layer
   |
   +--> Infrastructure Evidence
   +--> Contextual Evidence
   |
   v
Final Risk
   |
   v
Decision / Risk Tier
```

The dissertation target is a **learning-based adaptive decision layer** rather than simple threshold tuning.

The proposed meta-feature representation includes:

* Model risk
* Model confidence
* Infrastructure trust
* Infrastructure stability
* Campaign score
* Drift score
* Selected contextual features

Conceptual architecture:

```text
                Model Risk
                    |
                Confidence
                    |
        Infrastructure Evidence
                    |
          Campaign Evidence
                    |
             Drift Evidence
                    |
                    v
          Meta-Feature Vector
                    |
                    v
        Second-Stage Learner
                    |
                    v
             Learned Risk
                    |
                    v
          Final Risk Decision
```

The objective is to learn how contextual evidence should influence the final risk assessment.

---

# 9. Campaign Intelligence

Campaign analysis treats phishing as potentially coordinated activity rather than only independent malicious URLs.

The current campaign architecture includes:

* Campaign metadata
* Similarity feature generation
* Infrastructure relationships
* Campaign clustering
* DBSCAN-based campaign discovery
* Campaign characterization
* Campaign risk
* Campaign confidence
* Campaign reporting
* Campaign visualization

The current campaign feature schema contains **51 features**.

The dissertation augmentation moves toward explicit relationships such as:

```text
Shared IP
Shared ASN
Shared DNS
Shared SSL / Certificate
Domain relationships
Infrastructure similarity
Naming / URL similarity
```

The design principle is:

```text
Clustering discovers relationships
              +
URL prediction supplies risk
              +
Infrastructure provides contextual evidence
              |
              v
      Campaign Intelligence
```

Campaign intelligence remains a separate layer so that campaign processing does not unnecessarily alter the stable URL prediction pipeline.

---

# 10. Campaign Analysis Modes

Campaign processing can operate independently of URL prediction.

### A. After Batch Prediction

```text
Batch Prediction
       |
       v
Prediction Complete
       |
       v
Campaign Package
       |
       v
Campaign Analysis
```

Previously collected infrastructure observations can be reused.

### B. Standalone Campaign Analysis

```text
Campaign Analysis
       |
       v
Campaign Package
       |
       v
Campaign Metadata
       |
       v
Observation Cache
       |
       v
Collectors when required
       |
       v
Campaign Analysis
```

This separation supports modular experimentation and avoids coupling campaign analysis unnecessarily to the prediction pipeline.

---

# 11. Drift Monitoring

The drift package provides statistical comparison between reference and current data.

Implemented measures include:

```text
PSI
KL Divergence
Jensen-Shannon Distance
        |
        v
Overall Drift Score
        |
        v
Drift Severity
        |
        v
Retraining Recommendation
```

A stable-scenario experiment from the PCEMS implementation produced:

```text
Overall Drift Score : 0.0402
PSI                  : 0.0463
KL Divergence        : 0.0365
JS Distance          : 0.0324

Severity             : Stable
Retraining           : No
```

The dissertation work extends the framework toward:

* Temporal drift
* Campaign / cluster drift
* Drift-aware campaign intelligence
* Selective retraining
* Integration with adaptive decision learning

---

# 12. Experimental Results

The dissertation prediction pipeline currently contains **92 features**, compared with the **79-feature PCEMS baseline**.

An evaluation using 300 URLs consisted of:

```text
150 benign
150 phishing
```

The reported confusion matrices are:

### PCEMS 2026 — 79 Features

```text
TN = 135
FP = 15
FN = 23
TP = 127
```

### Dissertation — 92 Features

```text
TN = 132
FP = 18
FN = 9
TP = 141
```

The corresponding reported metrics are:

| Metric    | PCEMS 2026 | Dissertation |
| --------- | ---------: | -----------: |
| Accuracy  |     87.33% |       91.00% |
| Precision |     89.44% |       88.68% |
| Recall    |     84.67% |       94.00% |
| F1-score  |     86.99% |       91.26% |
| ROC-AUC   |     94.23% |       96.88% |

The current results indicate that the expanded infrastructure representation is associated with improved recall, F1-score and ROC-AUC in this evaluation.

These results are treated as **current experimental results**, not as a final dissertation conclusion. Further controlled experiments and validation are planned.

---

# 13. Campaign Experimentation

Campaign analysis has also been evaluated using the same 500-URL input across different execution stages.

The campaign feature schema remains at 51 features.

Observed results:

| Metric               | PCEMS Run | PCEMS Rerun | Dissertation Run |
| -------------------- | --------: | ----------: | ---------------: |
| Silhouette           |     0.545 |       0.563 |            0.520 |
| Davies-Bouldin       |     0.642 |       0.601 |            0.713 |
| Calinski-Harabasz    |     106.4 |       114.7 |             99.7 |
| Campaigns / Clusters |        20 |          18 |               21 |
| Clustered URLs       |       103 |          97 |              110 |
| Noise / Unclustered  |       397 |         403 |              390 |
| Largest Campaign     |        16 |          16 |               16 |

The observed differences demonstrate that campaign clustering is sensitive to infrastructure observations and cache/domain handling.

The same 500 URLs and the same campaign feature schema do not necessarily produce identical enriched feature values across executions.

This is therefore being treated as an **observation/data sensitivity issue requiring controlled experimentation**, rather than automatically interpreting the difference as a software regression.

---

# 14. Dataset

## Primary Dataset

The primary prediction dataset is:

```text
balanced_urls.csv
```

Source:

```text
Kaggle
```

Approximate size:

```text
632,000 labelled URLs
```

Distribution:

```text
~50% benign
~50% malicious / phishing
```

The original dataset provides URL labels.

Infrastructure attributes are collected dynamically during feature extraction.

---

## Experimental Sample

Because infrastructure collection involves network-dependent operations, the current feature-engineering/training experiments use:

```text
1,500 stratified URLs
```

The evaluation experiment currently uses:

```text
300 URLs
150 benign
150 phishing
```

Additional experimental data is used for:

* Drift monitoring
* Campaign analysis
* Synthetic campaign validation
* Reference/current distribution comparison

---

# 15. Engineering Constraints

Infrastructure enrichment is considerably more expensive than conventional local URL feature extraction.

The framework may require external observations from:

* DNS
* IP resolution
* ASN services
* WHOIS
* SSL/TLS
* Certificate Transparency

Consequently, large-scale infrastructure enrichment can become network-bound and time-consuming.

The dissertation implementation addresses this through a reusable caching architecture.

### Infrastructure Caching

```text
Valid Feature Cache?
       |
   Yes ───────> Reuse
       |
      No
       |
Valid Observation Cache?
       |
   Yes ───────> Derive Features
       |
      No
       |
Collector
       |
       v
Normalize
       |
       v
Cache
       |
       v
Derive Features
```

This architecture is intended to reduce repeated external collection and improve reproducibility.

---

# 16. Streamlit Application

The project includes a multi-page Streamlit application.

Current application pages include:

```text
1. URL Prediction
2. Batch Analysis
3. Drift Analysis
4. Campaign Analysis
5. Model Information
6. About
```

Launch the application with:

```bash
streamlit run app/streamlit_app.py
```

The application provides an interactive interface for:

* Single URL prediction
* Batch URL analysis
* Infrastructure intelligence
* Risk assessment
* Explainability
* Drift analysis
* Campaign analysis
* Model information

---

# 17. Explainability

The framework includes SHAP-based model explainability.

The objective is to provide insight into the factors contributing to the model's prediction rather than presenting the XGBoost model as a completely opaque classifier.

The explainability component is located in:

```text
src/explainability/shap_explainer.py
```

The resulting information is integrated into the broader risk intelligence reporting workflow.

---

# 18. Project Structure

The dissertation repository is organized into application, data, documentation, prediction, infrastructure, campaign, drift, and testing components.

```text
infra-aware-phishing-intelligence-dissertation/
│
├── app/
│   ├── assets/
│   │   ├── framework_architecture_v1.png
│   │   └── framework_architecture_v2.png
│   │
│   ├── backup-of-sem3-demoed-streamlit_app/
│   │   ├── 2_Batch_Analysis_ver2.py
│   │   ├── streamlit_app.py
│   │   └── streamlit_app_ver2.py
│   │
│   ├── pages/
│   │   ├── 1_URL_Prediction.py
│   │   ├── 2_Batch_Analysis.py
│   │   ├── 3_Drift_Analysis.py
│   │   ├── 4_Campaign_Analysis.py
│   │   ├── 5_Model_Information.py
│   │   └── 6_About.py
│   │
│   └── streamlit_app.py
│
├── data/
│   ├── campaign_reference.csv
│   ├── drift_reference.csv
│   ├── feature_cache/
│   ├── ind_strat_sample_campaign.csv
│   └── test_batch/
│       └── test_batch_urls.csv
│
├── docs/
│   ├── Architecture_Decisions.md
│   └── Dissertation-Roadmap.md
│
├── src/
│   ├── campaign/
│   │   ├── campaign_characterizer.py
│   │   ├── campaign_cluster.py
│   │   ├── campaign_detector.py
│   │   ├── campaign_features.py
│   │   ├── campaign_metadata.py
│   │   ├── campaign_preprocessor.py
│   │   ├── campaign_report.py
│   │   ├── campaign_risk.py
│   │   ├── campaign_service.py
│   │   └── campaign_visualizer.py
│   │
│   ├── drift/
│   │   ├── divergence.py
│   │   ├── drift_detector.py
│   │   ├── drift_service.py
│   │   ├── drift_simulator.py
│   │   ├── psi.py
│   │   ├── statistics.py
│   │   └── thresholds.py
│   │
│   ├── explainability/
│   │   └── shap_explainer.py
│   │
│   ├── inference/
│   │   ├── predictor.py
│   │   ├── report_generator.py
│   │   ├── run_batch_inference.py
│   │   └── run_inference.py
│   │
│   ├── infrastructure/
│   │   ├── cache.py
│   │   ├── enrich_dataset.py
│   │   ├── infra_batch.py
│   │   ├── infra_behavior.py
│   │   ├── infra_cache.py
│   │   ├── infra_ct.py
│   │   ├── infra_features.py
│   │   ├── infra_network.py
│   │   ├── infra_ssl.py
│   │   ├── infra_utils.py
│   │   └── infra_whois.py
│   │
│   ├── features.py
│   ├── features_with_infra.py
│   ├── evaluate.py
│   ├── evaluate_infra_vs_baseline.py
│   ├── tfidf_model.py
│   ├── train_char_cnn.py
│   ├── train_tfidf_classical.py
│   ├── train_xgboost_infra.py
│   └── train_xgboost_only.py
│
├── tests/
│   ├── test_features.py
│   └── test_models.py
│
├── main.py
├── requirements.txt
├── .gitignore
└── README.md
```

The repository also retains selected earlier implementations and debugging/experimental code to preserve research traceability during dissertation development.

---

# 19. Installation

Clone the dissertation repository:

```bash
git clone https://github.com/vivekpise-ml/infra-aware-phishing-intelligence-dissertation.git
```

Move into the project directory:

```bash
cd infra-aware-phishing-intelligence-dissertation
```

Install dependencies:

```bash
pip install -r requirements.txt
```

A dedicated Python/Conda environment is recommended.

---

# 20. Running the Application

Launch the Streamlit application:

```bash
streamlit run app/streamlit_app.py
```

The application opens the available pages for:

```text
URL Prediction
Batch Analysis
Drift Analysis
Campaign Analysis
Model Information
About
```

---

# 21. Training

The infrastructure-aware XGBoost training pipeline is implemented in:

```text
src/train_xgboost_infra.py
```

Run:

```bash
python -m src.train_xgboost_infra
```

The training workflow includes:

```text
Dataset
   |
   v
Feature Extraction
   |
   v
Infrastructure Enrichment
   |
   v
Feature Matrix
   |
   v
XGBoost Training
   |
   v
Evaluation
   |
   v
Model Persistence
```

---

# 22. Drift Analysis

The drift implementation is contained in:

```text
src/drift/
```

Important components include:

```text
drift_detector.py
drift_service.py
drift_simulator.py
psi.py
divergence.py
statistics.py
thresholds.py
```

The framework supports experimentation with:

* PSI
* KL divergence
* Jensen-Shannon distance
* Overall drift scoring
* Severity classification
* Retraining recommendation

Generated drift-simulation datasets are treated as experimental artifacts and are excluded from the repository where appropriate through `.gitignore`.

---

# 23. Campaign Analysis

The campaign implementation is contained in:

```text
src/campaign/
```

Major components include:

```text
campaign_features.py
campaign_metadata.py
campaign_preprocessor.py
campaign_cluster.py
campaign_detector.py
campaign_characterizer.py
campaign_risk.py
campaign_report.py
campaign_visualizer.py
campaign_service.py
```

The current clustering implementation uses:

```text
DBSCAN
```

The dissertation target is to extend campaign intelligence toward explicit shared-infrastructure relationships and campaign-level evidence.

---

# 24. Current Dissertation Status

The current implementation status is:

```text
Prediction Intelligence
        Completed / stabilizing

Infrastructure Intelligence
        Enhanced / operational

Infrastructure Caching
        Enhanced / operational

Adaptive Decision Intelligence
        Working
        Rule-based calibration currently implemented

Campaign Intelligence v1
        Working
        DBSCAN + campaign risk summaries

Campaign Intelligence v2.0
        Next
        Shared infrastructure relationships

Drift Monitoring
        Working
        PSI + KL + JS + severity / recommendation

Learning-Based Adaptive Calibration
        Planned
        Second-stage learner

Selective Retraining / MLOps
        Planned
```

The current focus is therefore on stabilizing the existing layers before integrating the learning-based adaptive architecture.

---

# 25. Dissertation Roadmap

The dissertation implementation follows an incremental development strategy.

## Phase 1 — Prediction Pipeline Stabilization

Complete and stabilize:

* URL-level prediction
* Batch prediction
* Infrastructure integration
* Risk scoring
* Explainability
* Streamlit prediction workflow

## Phase 2 — Campaign Intelligence v2.0

Extend campaign analysis with:

* Shared IP relationships
* Shared ASN relationships
* Shared DNS relationships
* Shared SSL/certificate relationships
* Campaign confidence
* Campaign-level risk evidence

## Phase 3 — Adaptive Decision Learning

Develop a second-stage learning model using:

* Model risk
* Model confidence
* Infrastructure evidence
* Campaign evidence
* Drift evidence
* Selected contextual features

## Phase 4 — Drift-Aware Adaptation

Extend drift intelligence toward:

* Temporal drift
* Campaign / cluster drift
* Selective retraining
* Drift-aware adaptive decisions

## Phase 5 — Integrated Risk Intelligence System

Perform:

* End-to-end integration
* Controlled experiments
* Ablation studies
* Validation
* Dissertation-level evaluation
* Deployment-oriented experimentation

The final dissertation contribution is intended to be the **integration and learning-based adaptation of multiple intelligence layers**, rather than simply adding more individual features.

---

# 26. Research Contributions Under Development

The dissertation is designed around the following contributions:

### 1. Infrastructure-Aware Phishing Risk Prediction

Use multiple independent infrastructure intelligence sources alongside URL and HTML features.

### 2. Reusable Infrastructure Collection and Caching

Separate infrastructure observations from derived features to support repeated inference and campaign processing.

### 3. Campaign-Level Intelligence

Move from URL-level classification toward campaign discovery and explicit shared-infrastructure evidence.

### 4. Learning-Based Adaptive Decision Intelligence

Combine model, infrastructure, campaign, and drift signals through a second-stage learner for final risk assessment.

### 5. Drift-Aware Adaptation

Monitor changes in the data environment and provide a path toward selective model adaptation and retraining.

### 6. Operational Prototype

Provide an interactive Streamlit system rather than an isolated machine-learning experiment.

---

# 27. Important Design Principles

The dissertation implementation follows several architectural principles.

### Prediction and Campaign Analysis Remain Separate

Campaign analysis should not unnecessarily alter the stable URL prediction pipeline.

### Infrastructure Observations Are Reusable

Infrastructure collection should not be repeated when valid observations are already available.

### Caching Is Part of the Architecture

Caching is not merely an optimization; it supports reproducibility, resilience and scalable experimentation.

### Model Probability Is Not the Entire Risk Decision

The final risk assessment is intended to incorporate contextual evidence.

### Drift Does Not Automatically Mean Retraining

Drift monitoring provides evidence and a retraining recommendation. The dissertation investigates how that evidence can subsequently influence adaptive decision-making.

### Research Components Are Added Incrementally

Each layer is stabilized before becoming a dependency of the next layer.

---

# 28. Reproducibility and Data Handling

Infrastructure collection may depend on external services and the availability of DNS, WHOIS, SSL and CT observations.

Consequently, infrastructure observations can change over time.

The repository therefore uses caching and reference datasets to support reproducible experimentation where possible.

Generated or large experimental artifacts are excluded through `.gitignore` where appropriate.

In particular, generated drift simulation CSV files are not intended to be committed as ordinary repository data.

---

# 29. Conference Baseline vs Dissertation Implementation

The conference implementation is preserved separately:

```text
Conference Repository
infra-aware-phishing-intelligence
        |
        | Frozen baseline
        v
PCEMS 2026 implementation
```

The dissertation implementation is:

```text
Dissertation Repository
infra-aware-phishing-intelligence-dissertation
        |
        +--> Conference baseline
        |
        +--> 92-feature prediction
        |
        +--> SSL + CT enhancement
        |
        +--> Infrastructure caching
        |
        +--> Campaign Intelligence v2.0
        |
        +--> Learning-based adaptive decision
        |
        +--> Drift-aware adaptation
```

This separation maintains a clear research lineage and allows the conference implementation to remain reproducible and unchanged.

---

# 30. Related Research

The implementation builds upon research in:

* Gradient-boosted decision trees
* Phishing website detection
* Infrastructure-based cyber threat intelligence
* Density-based clustering
* Concept drift detection
* Explainable machine learning
* Campaign-level phishing analysis

Selected references include:

1. Chen, T., & Guestrin, C. (2016). *XGBoost: A Scalable Tree Boosting System*. KDD.

2. Ester, M., Kriegel, H.-P., Sander, J., & Xu, X. (1996). *A Density-Based Algorithm for Discovering Clusters in Large Spatial Databases with Noise*. KDD-96.

3. Gama, J., Žliobaitė, I., Bifet, A., Pechenizkiy, M., & Bouchachia, A. (2014). *A Survey on Concept Drift Adaptation*. ACM Computing Surveys, 46(4).

4. Lundberg, S. M., & Lee, S.-I. (2017). *A Unified Approach to Interpreting Model Predictions*. NeurIPS.

5. Li, W., et al. (2024). *A State-of-the-Art Review on Phishing Website Detection Techniques*. IEEE Access, 12.

6. Althobaiti, K., et al. (2023). *Using Clustering Algorithms to Automatically Identify Phishing Campaigns*. IEEE Access, 11.

---

# 31. Research Dissemination

The framework has been developed as part of the M.Tech Applied AI research work at:

```text
Visvesvaraya National Institute of Technology, Nagpur
Electronics and Communication Engineering Department
```

The conference research work was submitted to **PCEMS 2026** under the title:

```text
Infrastructure-Aware Drift-Adaptive Phishing Risk Intelligence
Framework with Multi-Source Feature Engineering,
Campaign-Level Analysis, and Drift Monitoring
```

The dissertation repository represents the subsequent research and engineering evolution of this work.

---

# 32. Intellectual Property

A provisional specification relating to the phishing-detection framework has been filed with **IP India**.

Details are maintained separately from the implementation repository where appropriate.

---

# 33. Author

**Vivek Pise**

Executive M.Tech. in Applied AI
Visvesvaraya National Institute of Technology, Nagpur

GitHub:

`https://github.com/vivekpise-ml`

---

# 34. Project Status

```text
========================================================
        INFRASTRUCTURE-AWARE PHISHING
             RISK INTELLIGENCE
========================================================

Conference Baseline             FROZEN

Prediction Intelligence         STABLE / ENHANCED

Infrastructure Intelligence     OPERATIONAL

Infrastructure Caching          OPERATIONAL

Adaptive Decision Layer         WORKING

Campaign Intelligence v1        WORKING

Campaign Intelligence v2        IN DEVELOPMENT

Drift Monitoring                WORKING

Learning-Based Adaptation       PLANNED

Selective Retraining            PLANNED

Integrated Dissertation System  IN DEVELOPMENT
========================================================
```

**Research direction:**

```text
Phishing Classifier
       ↓
Infrastructure-Aware Predictor
       ↓
Phishing Risk Intelligence
       ↓
Campaign + Drift Intelligence
       ↓
Learning-Based Adaptive Risk Intelligence
```
