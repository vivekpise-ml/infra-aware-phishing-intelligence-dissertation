# Controlled Ablation Study

## 1. Purpose

This experiment evaluates the contribution of the infrastructure-aware feature representation within the phishing risk intelligence framework.

Four feature representations are evaluated:

1. **Full** — complete feature representation used by the pipeline.
2. **Lexical** — URL lexical features only. Baseline.
3. **Infrastructure** — infrastructure features only. Secondary diagnostic experiment.
4. **Lexical + Infrastructure** — combined representation.

The **primary ablation comparison** is:

**Lexical vs Lexical + Infrastructure**

The **Infrastructure-only** experiment is treated as a secondary diagnostic to measure the standalone predictive signal contained in the infrastructure feature group.

---

## 2. Experimental Protocol

| Parameter | Value |
|---|---|
| Dataset | `balanced_urls.csv` |
| Sample size | 1500 |
| Sample random state | 42 |
| Test size | 20% |
| Split random state | 42 |
| Trusted dataset augmentation | True |
| StandardScaler | True |
| XGBoost estimators | 300 |
| XGBoost max depth | 4 |
| XGBoost learning rate | 0.1 |
| XGBoost random state | 42 |

The same sampled URLs and the same train/test split are used for all four feature representations.

This controls the dataset and partition variables while changing only the feature representation supplied to the classifier.

---

## 3. Feature Extraction and Caching

The complete feature representation was extracted once for the common experimental sample.

The resulting feature matrix was persisted as:

`results/ablation/feature_cache/sampled_features.csv`

The existing infrastructure cache remains part of the underlying infrastructure feature collection process.

The experiment-level CSV cache allows all four model experiments to reuse the same extracted feature values without repeating infrastructure collection.

| Property | Value |
|---|---|
| Cached rows | 1500 |
| Cached feature columns | 92 |
| One-time feature extraction | 4.53 seconds |

Thus, adding the Infrastructure-only experiment does not require a second infrastructure extraction pass.

---

## 4. Feature Representations

| Representation | Features | Role |
|---|---:|---|
| Full | 92 | Reference / reproduction |
| Lexical | 60 | Baseline |
| Infrastructure | 27 | Secondary diagnostic |
| Lexical + Infrastructure | 87 | Primary infrastructure-aware comparison |

The feature representations are constructed by selecting columns from the same canonical feature cache.

No new feature-engineering formulas are introduced by the ablation experiment.

---

## 5. Overall Results

| Feature Set | Features | Accuracy | Precision | Recall | F1 | ROC-AUC | False Negatives | False Positives |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Full | 92 | 90.33% | 88.05% | 93.33% | 90.61% | 97.00% | 10 | 19 |
| Lexical | 60 | 87.33% | 87.84% | 86.67% | 87.25% | 94.85% | 20 | 18 |
| Infrastructure | 27 | 82.67% | 79.88% | 87.33% | 83.44% | 87.53% | 19 | 33 |
| Lexical + Infrastructure | 87 | 90.33% | 88.05% | 93.33% | 90.61% | 97.00% | 10 | 19 |

---

## 6. Primary Ablation: Lexical vs Lexical + Infrastructure

The primary experiment evaluates whether the infrastructure-aware representation changes predictive performance when added to the lexical representation.

### Observed results

| Metric | Lexical | Lexical + Infrastructure | Change |
|---|---:|---:|---:|
| Accuracy | 87.33% | 90.33% | +3.00 pp |
| Precision | 87.84% | 88.05% | +0.21 pp |
| Recall | 86.67% | 93.33% | +6.67 pp |
| F1 | 87.25% | 90.61% | +3.37 pp |
| ROC-AUC | 94.85% | 97.00% | +2.15 pp |
| False negatives | 20 | 10 | -10 |
| False positives | 18 | 19 | +1 |

The lexical + infrastructure representation therefore shows an observed accuracy change of **+3.00 pp**, recall change of **+6.67 pp**, F1 change of **+3.37 pp**, and ROC-AUC change of **+2.15 pp** relative to the lexical-only representation.

False negatives changed from **20** to **10** in this experiment.

These values describe the observed result on the fixed evaluation sample. They do not by themselves establish causal attribution to individual infrastructure features.

---

## 7. Infrastructure-Only Diagnostic

The Infrastructure-only representation contains **27 features**.

Its observed performance is:

| Metric | Infrastructure Only |
|---|---:|
| Accuracy | 82.67% |
| Precision | 79.88% |
| Recall | 87.33% |
| F1 | 83.44% |
| ROC-AUC | 87.53% |
| False negatives | 19 |
| False positives | 33 |

This experiment answers a different question from the primary ablation:

> How much standalone predictive signal is available from the infrastructure representation without URL lexical features?

The Infrastructure-only result should therefore be interpreted as a diagnostic measure of standalone infrastructure signal, rather than as the expected production prediction configuration.

A relatively weak infrastructure-only result would not invalidate the infrastructure-aware approach. Infrastructure information may provide complementary contextual information when combined with lexical characteristics.

Conversely, a strong infrastructure-only result would indicate that the infrastructure representation contains substantial standalone predictive signal.

The actual interpretation should follow the measured result rather than being assumed in advance.

---

## 8. Why the Primary Comparison Remains Lexical + Infrastructure

The principal contribution being evaluated is the addition of infrastructure intelligence to URL-based phishing analysis.

Therefore the primary comparison is:

**Lexical → Lexical + Infrastructure**

The Infrastructure-only experiment is included to characterize the standalone information content of the infrastructure feature group.

This produces a more complete experimental decomposition:

```text
Lexical
   |
   +-------------------+
   |                   |
   v                   v
Baseline          Infrastructure
                       |
                       v
             Lexical + Infrastructure
```

---

## 9. Interpretation and Causal Attribution

The ablation controls:

- sampled URLs;
- class distribution;
- train/test partition;
- XGBoost configuration;
- preprocessing;
- feature extraction source.

Therefore observed differences between the representations are empirical differences under a common experimental protocol.

However, the experiment does not establish that any individual infrastructure feature caused a particular performance change.

In particular, the results should not be interpreted as proof that:

- a particular infrastructure feature is causally responsible;
- every infrastructure feature contributes positively;
- infrastructure information always improves phishing detection;
- the observed result generalizes to every phishing dataset;
- the result is statistically significant without repeated trials or appropriate statistical testing.

The Infrastructure-only mode is especially useful for separating standalone infrastructure signal from the combined infrastructure-aware representation.

---

## 10. Full Representation

The Full mode contains **92 features**.

It serves primarily as a reference/reproduction mode for the complete feature representation.

It is not treated as a separate contribution in the interpretation.

The main scientific comparison remains:

**Lexical vs Lexical + Infrastructure**

---

## 11. Feature Importance

The feature-importance artifact for the lexical + infrastructure model is generated from the trained XGBoost model.

Feature importance is descriptive model information. It should not be interpreted as causal evidence that a feature independently improves phishing detection.

![Top feature importance](figures/feature_importance_lexical_infra.png)

---

## 12. Figures

### Overall feature-representation comparison

![Ablation metrics](figures/ablation_metrics.png)

### Primary infrastructure-aware ablation

![Primary ablation delta](figures/ablation_delta_vs_lexical.png)

### Standalone infrastructure diagnostic

![Infrastructure diagnostic](figures/infra_diagnostic.png)

### Lexical + infrastructure feature importance

![Feature importance](figures/feature_importance_lexical_infra.png)

---

## 13. Reproducibility

The experiment stores:

- common sample split manifest;
- URL SHA-256 fingerprints;
- canonical feature cache;
- feature-cache metadata;
- feature names for every representation;
- XGBoost parameters;
- trained models;
- scalers;
- confusion matrices;
- classification reports;
- feature importance;
- consolidated ablation results.

The canonical feature cache is particularly important because infrastructure feature collection can involve cached or externally collected infrastructure observations.

Persisting the extracted feature matrix makes the model comparisons repeatable without recollecting infrastructure information.

---

## 14. HTML Feature Limitation

The current controlled ablation does not claim an independent HTML-content contribution.

The historical PCEMS prediction extraction includes HTML feature dimensions, but the training protocol does not provide a separate consistent HTML-content dataset for this ablation.

Therefore this experiment does not manufacture an HTML-only result.

The controlled feature-group comparison reported here is:

**Lexical vs Infrastructure vs Lexical + Infrastructure**

The Full representation is retained as a reference/reproduction mode.

A genuine HTML contribution study would require a consistent URL/HTML dataset and a predefined collection and evaluation protocol.

---

## 15. Relation to the Dissertation

This ablation provides quantitative evidence for the infrastructure-aware component of the dissertation framework.

It evaluates:

1. the lexical baseline;
2. standalone infrastructure signal;
3. the combined lexical + infrastructure representation;
4. the complete feature representation as a reference.

The primary result should therefore be presented as a controlled feature-group ablation rather than as a claim that infrastructure features universally improve phishing detection.

---

## 16. Conclusion

The controlled experiment evaluates the infrastructure-aware feature representation under an identical dataset, sampling, train/test split, preprocessing and XGBoost configuration.

The primary evidence comes from the comparison between the lexical-only and lexical + infrastructure representations.

The Infrastructure-only experiment provides an additional diagnostic view of the standalone predictive signal contained in the infrastructure feature group.

Together, these experiments provide a more complete empirical characterization of the infrastructure-aware prediction component.
