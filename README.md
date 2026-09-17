## Dissertation Phase

This repository extends the frozen conference-phase implementation
with additional research components developed during the M.Tech
dissertation phase.

### Baseline
- URL-based phishing detection
- Infrastructure-aware features
- XGBoost-based prediction
- Campaign-level analysis
- Drift monitoring

# infra-aware-phishing-intelligence
Infrastructure-Aware Drift-Adaptive Multimodal Phishing Risk  Intelligence Framework with Campaign-Level Analysis


# Infrastructure-Aware Drift-Adaptive Phishing Risk Intelligence Framework

An infrastructure-aware phishing risk intelligence framework that combines URL-based machine learning, infrastructure intelligence, adaptive risk calibration, and explainable reporting to move beyond binary phishing classification.

This project was developed as part of an M.Tech research effort focused on improving phishing detection through contextual infrastructure signals and intelligence-driven risk assessment.

Repository:  
https://github.com/vivekpise-ml/infra-aware-phishing-intelligence

---

## Project Overview

Traditional phishing detection systems often operate as binary classifiers and make decisions solely based on URL structure or webpage features. While effective in many cases, such systems may generate high-confidence false positives for trusted domains because structural similarities between phishing URLs and legitimate domains can exist.

This project approaches phishing detection as a **risk intelligence problem** rather than a simple classification task.

The framework integrates:

- URL lexical analysis
- Infrastructure intelligence
- Adaptive risk calibration
- Drift-aware design
- Explainable intelligence reporting
- Campaign-level analysis (work in progress)

Instead of producing only:

```text
benign / malicious
```

the system generates:

- Model risk score
- Calibrated final risk
- Infrastructure trust assessment
- Explainable reasoning
- Risk tiering
- Intelligence report

---

## System Workflow

```text
URL Input
    ↓
Feature Extraction
    ↓
Infrastructure Intelligence
    ↓
ML Risk Prediction
    ↓
Adaptive Decision Layer
    ↓
Risk Intelligence Report
```

The framework combines model confidence with contextual infrastructure signals to reduce false positives and improve interpretability.

---

## Key Features

### 1. Classical URL Feature Extraction

The framework extracts multiple phishing-related URL signals.

#### Lexical Features

Examples include:

- Query length
- Path length
- Dot count
- Equal count
- Special character usage
- Entropy
- Subdomain count
- Parameter count

#### Keyword-Based Signals

Detection of phishing-associated keywords such as:

```text
login
verify
secure
billing
account
update
paypal
amazon
```

#### HTML Structural Features

Where applicable, webpage structural signals are extracted:

- Number of forms
- Number of links
- Scripts
- iFrames
- Event handlers

---

### 2. Infrastructure Intelligence Layer

A dedicated infrastructure intelligence module enriches URLs with operational trust signals.

Implemented in:

```text
src/infrastructure/infra_features.py
```

Current infrastructure features include:

#### Domain Intelligence

- Domain age
- Domain age bucket
- New domain detection
- WHOIS availability

#### Network Intelligence

- ASN availability
- IP resolution
- Hosting country
- Foreign hosting detection

#### Stability Signals

Infrastructure stability is derived using:

```text
Domain age
+ IP availability
+ ASN availability
```

#### Infrastructure Trust Score

A trust score is calculated using:

- ASN reputation
- Mature domain age
- Infrastructure completeness

Range:

```text
0 → Low trust
3 → High trust
```

---

## Major Engineering Challenge

During experimentation, trusted domains such as:

```text
google.com
amazon.com
netflix.com
```

were predicted as:

```text
MALICIOUS
```

with extremely high confidence despite infrastructure enrichment.

Example:

```text
Model Risk: 0.99
Prediction: MALICIOUS
```

### Debugging Performed

The following possibilities were investigated:

- Feature mismatch
- Feature ordering errors
- Training bugs
- Pipeline inconsistencies
- Infrastructure feature variance issues

Feature alignment was verified successfully.

The issue was eventually traced to **XGBoost's greedy tree behavior**.

Although infrastructure trust was informative, the model statistically learned that:

```text
trusted infrastructure ≠ guaranteed benign
```

because portions of phishing samples still used relatively trusted infrastructure.

This was not a bug but a statistical learning behavior.

---

## Adaptive Decision Layer

To mitigate high-confidence false positives, an adaptive risk calibration layer was introduced.

Architecture changed from:

```text
Model Probability
        ↓
Final Prediction
```

to:

```text
Model Risk
+ Infrastructure Confidence
        ↓
Final Risk
        ↓
Final Decision
```

Implemented in:

```text
src/inference/predictor.py
```

### Risk Calibration Logic

Raw model probability:

```python
prob = model.predict_proba(X)[0][1]
```

Infrastructure confidence:

```python
infra_conf = infra_trust_score / 3
```

Calibrated risk:

```python
final_risk = prob * (1 - 0.6 * infra_conf)
```

Additional infrastructure stability adjustment:

```python
if infra_stability_score == 1:
    final_risk *= 0.8
```

### Final Risk Thresholds

| Risk Score | Decision |
|------------|----------|
| < 0.40 | Benign |
| 0.40 – 0.75 | Suspicious |
| > 0.75 | Malicious |

Example:

```text
google.com

Model Risk : 0.99
Final Risk : 0.32
Decision   : BENIGN
```

This reflects an important design transition:

**Classifier → Risk Intelligence Framework**

---

## Risk Intelligence Reporting

The framework includes a structured phishing intelligence report generator.

Implemented in:

```text
src/inference/report_generator.py
```

The report includes:

1. Domain Summary  
2. Risk Intelligence Analysis  
3. Infrastructure Intelligence  
4. Drift Analysis (placeholder)  
5. Campaign Analysis (placeholder)  
6. Model Explanation

The objective is to provide explainable phishing reasoning instead of a black-box prediction.

---

## Streamlit GUI

A Streamlit-based interface has been added for interactive phishing risk analysis.

Run the application:

```bash
streamlit run app/streamlit_app.py
```

The GUI displays:

- URL prediction
- Model risk score
- Final calibrated risk
- Risk tier
- Infrastructure assessment
- Explainable reasoning
- Intelligence report

---

## Dataset

Primary Dataset:

**Kaggle Phishing URL Dataset**

Approximate size:

```text
~632K URLs
```

Distribution:

```text
Benign     : ~316K
Malicious  : ~316K
```

### Practical Constraint

Infrastructure feature extraction requires:

- WHOIS lookup
- ASN resolution
- IP resolution
- Country lookup

These operations are network-bound and expensive.

For the complete dataset:

```text
Training time → multiple days
```

To maintain experimentation speed, the current implementation uses:

```text
1500 stratified samples
```

Advantages:

- Balanced sampling preserved
- Reproducibility using `random_state=42`
- Training runtime reduced to ~1–1.5 hours

---

## Project Structure

```text
infra-aware-phishing-intelligence/
│
├── app/
│   └── streamlit_app.py
│
├── data/
│   ├── cache/
│   ├── external/
│   ├── kaggle/
│   ├── processed/
│   └── raw/
│
├── models/
│
├── src/
│   ├── campaign/
│   │   └── campaign_detector.py
│   │
│   ├── drift/
│   │   └── drift_detector.py
│   │
│   ├── explainability/
│   │
│   ├── inference/
│   │   ├── predictor.py
│   │   ├── report_generator.py
│   │   └── run_inference.py
│   │
│   ├── infrastructure/
│   │   ├── enrich_dataset.py
│   │   ├── infra_features.py
│   │   ├── infra_utils.py
│   │   ├── cache.py
│   │   └── infra_dummy.py
│   │
│   ├── features.py
│   ├── features_with_infra.py
│   ├── train_xgboost_infra.py
│   └── evaluate.py
│
├── tests/
├── requirements.txt
├── main.py
└── README.md
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/vivekpise-ml/infra-aware-phishing-intelligence.git
```

Move into the project directory:

```bash
cd infra-aware-phishing-intelligence
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Requirements

Main dependencies:

```text
pandas
numpy
scikit-learn
xgboost
tensorflow
streamlit
beautifulsoup4
tldextract
torch
matplotlib
seaborn
shap
requests
python-whois
```

---

## Training

To train the infrastructure-aware XGBoost model:

```bash
python -m src.train_xgboost_infra.py
```

Expected behavior:

- Feature extraction
- Infrastructure enrichment
- Model training
- Evaluation
- Model persistence

---

## Running the GUI

Launch Streamlit:

```bash
streamlit run app/streamlit_app.py
```

Open the browser URL shown in terminal.

---

## Current Limitations

### 1. Limited Training Scale

Current experiments use:

```text
1500 samples
```

because infrastructure extraction is time intensive.

Future improvement areas:

- Async infrastructure lookups
- Parallel enrichment
- Smarter caching
- Batch WHOIS resolution

### 2. Drift Module

Currently placeholder implementation.

Future work:

- PSI
- KL divergence
- Jensen-Shannon divergence
- Feature distribution monitoring

### 3. Campaign-Level Analysis

Currently under development.

Planned signals:

- Shared ASN
- Shared IP subnet
- URL similarity
- Keyword similarity
- Hosting overlap
- Infrastructure correlation

### 4. Intelligence Narrative

Current reports are rule-based.

Future direction:

SOC-style intelligence reasoning with richer contextual narratives.

---

## Future Roadmap

Planned development areas:

- Real drift detection
- Campaign clustering
- Infrastructure intelligence expansion
- SSL certificate intelligence
- Infrastructure graph modeling
- Enhanced explainability
- Larger-scale training
- Multimodal phishing intelligence

---

## Current Project Status

Current state of the framework:

```text
Core ML stable
Infrastructure intelligence operational
False positives mitigated
Adaptive decision layer implemented
Explainability improved
Streamlit GUI operational
```

Current transition:

```text
Phishing Classifier
        →
Phishing Risk Intelligence Framework
```

---

## Author

**Vivek Pise**  
M.Tech (Applied AI)

GitHub:  
https://github.com/vivekpise-ml