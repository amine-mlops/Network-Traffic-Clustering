# Network Traffic Clustering and Novelty Detection

## Project Proposal and Presentation Brief (v2)

**Algorithms:** K-Means, Agglomerative Hierarchical Clustering (CAH), Gaussian Mixture Model; Logistic Regression as a supervised reference ceiling
**Dataset:** UNSW-NB15
**Field:** Unsupervised Machine Learning and Cybersecurity
**Status:** Revision of the original proposal (`Network_Traffic_Clustering_Project_Proposal.md`), motivated by a methodological critique documented in Section 1.

------------------------------------------------------------------------

## 1. Why the Original Approach Was Revised

The original proposal was methodologically careful but contained two
weaknesses that survive any amount of good experimental hygiene. This
revision exists to fix them, not to polish around them.

### 1.1 Clusters do not discover meaning

Unsupervised clustering discovers **geometric structure**, not semantic
meaning. Any statement such as "cluster 3 is scan-like behavior" is
assigned *afterwards*, by profiling the cluster with human knowledge.
The original proposal treated this as a caveat; this revision treats it
as a definition. Clustering in this project is used as automated
exploratory analysis of traffic — a descriptive tool — and no detection
claim is ever attached to it.

### 1.2 The original "anomaly" definition was circular

The original proposal defined anomalies as observations whose distance
to their K-Means centroid exceeds a chosen percentile of the distance
distribution, computed over **mixed normal and attack data**. This
definition is circular:

- "Anomaly" means "the points I decided to flag by choosing a
  threshold."
- There is no criterion *outside the procedure* that can confirm the
  definition is correct.
- The only way to check whether flagged points are actually attacks is
  to compare against `label` — which smuggles supervision back into a
  supposedly unsupervised procedure.

A definition that cannot fail has no informational value. The fix is not
a better threshold; it is a different question.

### 1.3 The supervised objection, and why it is answered rather than avoided

A reasonable jury objection is: *"The dataset has labels. Attack
detection is a classification problem. Why not supervised learning?"*

The objection is **correct**, and this revision does not argue against
it. It incorporates it. A supervised model (logistic regression on the
same features) is run as a **reference ceiling**, and the project's
central measurable question becomes:

> What exactly do we lose by going label-free, and is that loss
> acceptable in the operating regime where labels do not exist?

Nobody serious claims unsupervised methods outperform supervised
classification on a labeled benchmark. The contribution of this project
is to **quantify the gap** on identical features, and to document the
regime — novel, unlabeled, drift-affected traffic — where supervised
models cannot be built in the first place.

------------------------------------------------------------------------

## 2. Reframed Problem Statement

**Central question:**

> Can a model of *normal* network traffic, learned without attack
> supervision, make attack flows measurably separable from normal flows
> — and how much detection capability does the absence of labels cost,
> compared with a supervised ceiling on identical features?

**Methodological question (retained from v1):**

> How do K-Means and CAH compare in terms of cluster quality,
> computational cost, interpretability, and their usefulness for
> describing network traffic?

**Definitions used throughout this document:**

- **Novelty:** an observation that is *out-of-distribution* with respect
  to a model fitted on normal data. A score, not a verdict.
- **Anomaly:** a novelty whose score exceeds a frozen, budget-based
  threshold. An operational construct, chosen before evaluation.
- **Attack:** a reference-label category (`attack_cat`). Used only for
  evaluation and for selecting the normal training sample. Never an
  input.

An anomaly is not an attack. An attack is not necessarily an anomaly.
Both directions of this asymmetry are measured and reported.

------------------------------------------------------------------------

## 3. Terminology: One-Class / Novelty Detection

The approach is **one-class classification / novelty detection**:
learning a representation of a single class (normal traffic) and scoring
new observations against it.

It is *not* "semi-supervised" in the formal sense. Semi-supervised
learning combines a small labeled set with a large unlabeled set and
learns from both. Here, labels are used in exactly two places, and never
as learning inputs:

1. **Data selection:** `label == 0` flows form the normal training set.
2. **Evaluation:** scores are audited against `label` and `attack_cat`
   after thresholds are frozen.

Using the term "semi-supervised" invites the objection that labels were
used for training. They were not. The correct and defensible framing is
one-class.

------------------------------------------------------------------------

## 4. Why This Approach Holds More Meaning and Is More Useful

### 4.1 The anomaly definition becomes non-circular

Under the new design, "anomaly" has a definition that exists *outside*
the flagging procedure: a flow is anomalous if it is far, in the learned
representation, from the manifold of normal behavior. The question "does
this definition correspond to attacks?" is now **falsifiable and has an
empirical answer in either direction** — including "no, and here is
precisely which attack categories escape it." A negative result is a
result.

### 4.2 It mirrors real operational use

In a real SOC, the plausible role of this method is not "classify these
flows" — supervised tools do that where labels exist — but "surface
behavior that is unlike anything known, for a human to inspect." The
design reflects this reality:

- Scores, not verdicts.
- A **flagging budget** (e.g. "alert on the top 2% most abnormal
  flows"), because a detector that flags everything is unusable:
  analysts drown, and precision at a realistic alert volume is the only
  metric that matters operationally.
- Explicit treatment of **concept drift**: the model of normal goes
  stale as legitimate traffic evolves, and retraining is part of the
  lifecycle, not an afterthought.

### 4.3 The supervised ceiling turns the strongest objection into the thesis

Running a logistic regression on identical features does three things:

1. It acknowledges that labels exist and that supervised learning works
   on this dataset.
2. It converts the unsupervised result from an isolated number into a
   **quantified gap** ("novelty detection recovers X% of the supervised
   ceiling's performance").
3. It makes the project's honesty a feature: the expected outcome —
   supervised wins by a wide margin — is stated in advance, measured,
   and then contextualized by the arguments in Section 4.4.

### 4.4 The defense, in one place

Why unsupervised novelty detection still matters when labels exist
*here*:

- **Production flows are unlabeled.** Labels cost analyst hours and
  arrive late; a benchmark's labels are a luxury no deployment has.
- **Benchmark labels are testbed artifacts.** UNSW-NB15 labels come from
  a synthetic testbed: one network, one time period, synthesized attack
  patterns. Supervised models trained on it are known to degrade sharply
  on other networks — they learn the testbed, not attacks.
- **Novel attacks have no labels by definition.** A supervised model
  cannot flag what its classes do not contain. A model of normal
  behavior can.
- **The unsupervised signal is the complement, not the rival.** In
  practice the two operate side by side: supervised for known threats,
  novelty detection for the unknown.

The one claim this project never makes: that unsupervised detection is
*competitive* with supervised classification as an attack classifier. It
will not be. That is measured, not asserted.

### 4.5 Honest limits, stated up front

1. **Mimicry is invisible by construction.** Attacks whose flow
   statistics resemble legitimate traffic (known offenders on UNSW-NB15:
   Exploits, Generic, much of DoS) land inside the normal manifold and
   will not be flagged. The method detects *unusual shapes*, not
   maliciousness. Detection will therefore be asymmetric: strong on
   scans, rare protocols, unusual service behavior; weak-to-nothing on
   mimicry. This asymmetry is a headline result, not a footnote.
2. **A trusted normal sample is an assumption.** Real deployments do
   not receive a clean `label == 0` set. The method works because such a
   sample exists here; that gap between experiment and deployment is
   stated, not hidden.
3. **Everything is representation-relative.** "Differs from normal" is
   defined entirely by the feature encoding and scaling of Phase 3. The
   same caveat as v1, now with higher stakes, because the entire
   detection signal depends on it.
4. **Threshold selection remains a decision** — but now a proper one:
   chosen on a validation split as a budget, frozen, then applied once
   to the test set. Tuning on test labels is leakage and is treated as
   such.

------------------------------------------------------------------------

## 5. Two-Chapter Structure

The project deliberately keeps both the original work and the new
question. This preserves full compliance with the assigned subject
(K-Means and CAH, compared and evaluated) while adding the chapter that
carries the contribution.

### Chapter A — Descriptive Clustering of Network Traffic (subject compliance)

K-Means and CAH applied to traffic features, compared with internal
metrics (Silhouette, Davies-Bouldin, Calinski-Harabasz), profiled, and
related to reference labels as an external audit. No detection claim.
This chapter answers: *what behavioral structure exists in the traffic,
and which algorithm reveals it better?*

### Chapter B — One-Class Novelty Detection (the contribution)

Model of normal traffic fitted on `label == 0` flows only; held-out
flows (normal and attack) scored against it; threshold frozen at a
flagging budget on validation data; evaluated once against `label` and
`attack_cat`, with the supervised ceiling above it. This chapter
answers: *what does going label-free cost, and where does the signal
survive?*

Chapter A also serves Chapter B practically: the cluster structure and
profiling work directly informs the representation and the scoring
design of Chapter B.

------------------------------------------------------------------------

## 6. Dataset and Label-Usage Policy

Dataset, files, and feature dictionary: unchanged from v1 (Section 5 of
the original proposal). The v1 file inventory and feature tables remain
the reference; this document does not repeat them.

**Label-usage policy (strict):**

| Use | `label` / `attack_cat` allowed? |
| --- | --- |
| Clustering input (Chapter A) | No |
| Normal-training-set selection (Chapter B) | `label` only, as a filter |
| Score-threshold selection | No (validation split of normal flows only) |
| External evaluation / audit | Yes, after freezing |
| Supervised ceiling | Yes (that is its role) |

Identifiers and IP addresses are excluded from inputs for the same
reasons as v1: artificial similarity and dataset-specific leakage.

------------------------------------------------------------------------

## 7. Methodology: From Beginning to End

### Phase 1 — Project setup and data organization

**Tasks**

- Confirm the existing project structure, virtual environment, and
  dependencies (`pandas`, `scikit-learn`, `scipy`, `matplotlib`,
  `seaborn`).
- Keep `data/raw/UNSW-NB15/` untouched; processed data in
  `data/processed/`; results in `results/`.
- Record dataset source, versions, and experiment configuration.

**Output:** Reproducible project structure and working environment.

### Phase 2 — Data loading and exploratory data analysis

**Tasks**

- Load training and testing CSVs; verify row/column counts against
  expectations rather than assumptions.
- Inspect missing values, duplicates, invalid values (including
  infinities in timing/rate features).
- Analyze numerical distributions (expect heavy skew in bytes/packets —
  log1p transformation is a candidate) and categorical frequencies
  (`proto`, `service`, `state` — expect large cardinality and skew).
- Examine `label` and `attack_cat` distributions; quantify the attack
  rate and per-category sizes. This determines the evaluation design of
  Chapter B.
- Examine correlations and near-duplicate features.

**Output:** EDA notebook with statistics and initial visualizations.

### Phase 3 — Feature representation (the highest-leverage phase)

The decisions in this phase swing the results more than the choice of
clustering algorithm. They are made explicitly and documented, not
defaulted.

**Tasks**

- Separate labels from inputs per the Section 6 policy.
- Drop identifiers and dataset-specific columns; justify each removal.
- **Categorical encoding — decided, not defaulted.** One-hot encoding
  over ~130 `proto` values distorts Euclidean distance and dilutes
  numerical signal. Candidate strategies to be compared on a validation
  metric: frequency encoding; one-hot restricted to top-k categories
  with an "other" bucket; dropping dominated categories. The chosen
  strategy must be reported with its effect on distances.
- **Numerical preprocessing:** log1p for heavily skewed count/byte
  features; `StandardScaler` fitted on training data only.
- **Feature selection:** justify the retained set against the feature
  dictionary; remove near-duplicates found in Phase 2.
- Fit all fitted transformers on Chapter-A training data and on the
  Chapter-B normal-training split respectively; never on evaluation
  data.
- Verify the final matrices contain only finite values.

**Important:** in Chapter B, "differs from normal" is *defined* by this
phase. Any change here changes the meaning of every downstream score.

**Output:** Documented preprocessing pipelines and finite numerical
matrices for both chapters.

### Phase 4 — Chapter A: K-Means clustering

**Tasks**

- Apply K-Means to the prepared feature matrix (mixed normal and attack
  traffic — Chapter A is descriptive).
- Test a range of `K`; select with the Elbow Method and Silhouette
  Score; fixed random seed; `k-means++` initialization.
- Record assignments, centroids, inertia, and execution time.
- Visualize via PCA projections, noting explicitly that 2D projections
  hide structure.

**Output:** K-Means model, assignments, evaluation results, plots.

### Phase 5 — Chapter A: Agglomerative Hierarchical Clustering (CAH)

**Tasks**

- Apply CAH on a documented, reproducible sample if the full data is too
  large (expected: it is — CAH is O(n²) in memory).
- Test Ward, Complete, and Average linkages; Ward with Euclidean
  distance on scaled numerical features.
- Dendrogram on a manageable sample.
- Compare cluster counts against the K-Means selection.

**Output:** CAH results, dendrogram, assignments, evaluation results.

### Phase 6 — Chapter A: Evaluation, profiling, and honest audit

**Tasks**

- Internal metrics: Silhouette (higher), Davies-Bouldin (lower),
  Calinski-Harabasz (higher) — computed on the same observations for
  both algorithms.
- External audit: ARI against `attack_cat` and against binary `label`,
  reported separately, computed only after clustering. Expected result,
  stated in advance: low agreement. If so, the chapter explains *why*
  from the cluster profiles (protocol/service-driven structure, not
  maliciousness-driven).
- Profile each cluster: size, share of attacks, per-feature statistics,
  dominant protocols/services/states.
- Algorithm comparison table: quality, execution time, memory, cluster
  balance, interpretability. Where CAH used a sample, state it and do
  not present the comparison as perfectly controlled.

**Output:** Comparison table, cluster profiles, reasoned assessment.

### Phase 7 — Chapter B: Building the model of normal traffic

**Tasks**

- Split `label == 0` flows into **normal-train / normal-val** (seeded,
  stratified by `service` or `proto` if useful for stability). The
  **test set** is a held-out mixture of the remaining normal flows and
  attack flows, untouched until Phase 8.
- Fit two models of normal on normal-train:
  - **K-Means** (k selected by Silhouette *within normal data*), scored
    by **cluster-conditional deviation**: each point's distance
    normalized by its own cluster's spread (Mahalanobis distance within
    the cluster, or per-cluster z-score). Raw distance to centroid is
    not used — it is dominated by global scale and by naturally wide
    clusters.
  - **Gaussian Mixture Model**, scored by **negative log-likelihood**
    under the normal model.
- Record model parameters, scores, and fit times.

**Important:** K-Means has no rejection option — every point is assigned
to its nearest centroid. "Does not fit" therefore means "exceeds the
frozen deviation threshold," and the threshold is defined in Phase 8
*before* any test labels are seen.

**Output:** Two fitted normal models with scoring functions.

### Phase 8 — Chapter B: Thresholding and evaluation

**Tasks**

- On **normal-val only**: compute score distributions; choose the
  threshold as an explicit **flagging budget** (e.g. top 1% and top 5%
  as two operating points). Freeze both. No test labels are touched.
- On the **test set** (normal + attacks), score once with the frozen
  thresholds:
  - Precision, recall, F1 at each budget, against binary `label`.
  - Per-category recall against `attack_cat` — this is where the
    mimicry asymmetry (Exploits/Generic/DoS escaping; scans and rare
    shapes caught) is expected to appear and is reported prominently.
  - PR-AUC for the full score distribution (threshold-free view).
- Report false-alarm composition: what *normal* behaviors get flagged,
  and whether they are plausible analyst workload.
- Compare K-Means-deviation scoring vs GMM-likelihood scoring on
  identical splits and budgets.

**Output:** Frozen thresholds, evaluation tables, per-category
breakdown, score-distribution plots.

### Phase 9 — Supervised reference ceiling

**Tasks**

- Train a logistic regression (and optionally a small random forest as
  a sanity check) on `label` using **identical features and identical
  splits** as Chapter B.
- Report its test precision/recall/PR-AUC next to Chapter B's numbers.
- Express the headline result: novelty detection recovers X% of the
  supervised ceiling's performance, overall and per attack category.
- Identify categories where the gap is smallest (rare-shape attacks) and
  largest (mimicry).

**Output:** Ceiling comparison table; the quantified price of having no
labels.

### Phase 10 — Synthesis: comparison and discussion

**Tasks**

- Synthesize across all axes: K-Means vs CAH (Chapter A); deviation
  scoring vs GMM scoring (Chapter B); unsupervised vs supervised ceiling
  (Phase 9).
- Discuss the operating regime argument (Section 4.4) against the
  measured results: where does the label-free signal survive, where does
  it collapse, and is the collapse acceptable given what deployments
  face?
- Document limitations per Section 4.5, adding anything the experiments
  revealed (e.g. drift sensitivity, budget sensitivity, encoding
  sensitivity).

**Output:** Final discussion linking measured numbers to the reframed
problem statement.

### Phase 11 — Visualization and dashboard (optional enhancement)

An interactive Streamlit dashboard can present:

- Dataset overview and feature distributions.
- Chapter A: elbow curve, dendrogram, cluster profiles, metric
  comparison.
- Chapter B: score distributions (normal vs attack), flagging-budget
  operating points, per-category recall heatmap.
- The ceiling comparison as the closing view.

The dashboard is a presentation layer; it does not replace the
experimental analysis.

**Output:** Interactive dashboard or a set of clear, reproducible
figures.

### Phase 12 — Final report and presentation

The final report should:

- Present Chapter A as descriptive structure, Chapter B as the
  falsifiable question, and the ceiling as the measuring stick.
- Report the mimicry asymmetry as a primary finding, not a limitation
  buried in an appendix.
- State the trusted-normal assumption and the deployment gap explicitly.
- Suggest improvements: DBSCAN-based noise labeling, Isolation Forest as
  a scoring baseline, autoencoder reconstruction error, drift-adaptive
  retraining, and semi-supervised pipelines that combine a small labeled
  sample with the unlabeled bulk.

**Output:** Final written report, presentation slides, code, documented
results.

------------------------------------------------------------------------

## 8. Experimental Design Rules

1. **Labels are never clustering or scoring inputs.** Only selection
   (normal filter), evaluation, and the ceiling.
2. **No leakage.** All fitted transformers, k-selection, and thresholds
   are frozen on training/validation data before any test evaluation.
   The threshold is tuned on normal-validation flows only.
3. **One-shot test evaluation.** The test set is scored once per frozen
   configuration. Repeated peeking turns evaluation into tuning.
4. **Comparable conditions.** All methods share the same feature
   representation, splits, seeds, and budgets. Where CAH (or any method)
   must use a subsample, state it and mark the comparison as
   approximate.
5. **Report seeds and parameters.** K-Means initialization and sampling
   affect results.
6. **Internal scores never imply detection.** Only the external audit
   speaks about attacks.
7. **Document every preprocessing decision**, with the rationale and,
   where feasible, the measured effect.

------------------------------------------------------------------------

## 9. Expected Results

Stated in advance, as falsifiable expectations rather than hopes:

- Chapter A: coherent descriptive clusters driven by protocol/service
  and traffic shape; low ARI against labels; K-Means scalable and
  faster; CAH interpretable via the dendrogram but restricted to
  samples.
- Chapter B: strong novelty scores for shape-unusual attacks (scans,
  rare protocols); weak-to-no signal for mimicry attacks (Exploits,
  Generic, much of DoS); a precision/recall trade-off governed by the
  chosen budget; GMM-likelihood and cluster-deviation scoring within the
  same order of magnitude, with possibly different per-category
  strengths.
- Phase 9: the supervised ceiling clearly above both novelty pipelines
  overall — the gap is the paper's quantified thesis, and its per-category
  decomposition is where the nuance lives.

These are expectations to be confirmed or refuted by running the
experiments. A refuted expectation is a reportable finding.

------------------------------------------------------------------------

## 10. Project Structure

``` text
Network-Traffic-Clustering/
│
├── data/
│   ├── raw/UNSW-NB15/
│   └── processed/
│
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_feature_representation.ipynb
│   ├── 03a_kmeans_descriptive.ipynb
│   ├── 03b_cah_descriptive.ipynb
│   ├── 04_novelty_detection.ipynb
│   ├── 05_supervised_ceiling.ipynb
│   └── 06_synthesis_comparison.ipynb
│
├── src/
│   ├── data/
│   │   ├── load_data.py
│   │   └── preprocess.py
│   ├── clustering/
│   │   ├── kmeans.py
│   │   └── hierarchical.py
│   ├── novelty/
│   │   ├── models.py        # normal-model fitting (K-Means, GMM)
│   │   ├── scoring.py       # cluster-deviation and GMM-NLL scores
│   │   └── thresholds.py    # budget-based threshold selection
│   ├── evaluation/
│   │   ├── metrics.py
│   │   └── comparison.py
│   └── visualization/
│       └── plots.py
│
├── dashboard/
│   └── app.py
│
├── results/
│   ├── figures/
│   ├── metrics/
│   └── reports/
│
├── localDocs/               # proposals and documentation
├── config/
│   └── config.py
├── tests/
├── pyproject.toml
├── README.md
└── .gitignore
```

------------------------------------------------------------------------

## 11. Suggested Presentation Structure (12 slides)

| Slide | Content |
| ----- | ------- |
| 1 | Project title and team members |
| 2 | Context: network traffic and cybersecurity |
| 3 | The problem — reframed: what does going label-free cost? |
| 4 | Why not just supervised? (the defense, delivered first) |
| 5 | UNSW-NB15 dataset and feature representation decisions |
| 6 | Chapter A: K-Means and CAH — descriptive results |
| 7 | Chapter A: cluster profiles and the honest label audit |
| 8 | Chapter B: the model of normal and the scoring design |
| 9 | Chapter B: budgets, frozen thresholds, per-category results |
| 10 | The supervised ceiling and the quantified gap |
| 11 | Limits: mimicry, trusted-normal assumption, drift |
| 12 | Conclusion: operating regimes and open questions |

Slide 4 is placed early deliberately: preempting the strongest objection
is stronger than surviving it.

------------------------------------------------------------------------

## 12. Final Problem Statement for the Presentation

**English version**

> Given a labeled benchmark that real deployments do not have, can
> unsupervised one-class models of normal network traffic make attack
> flows measurably separable, and precisely how much detection
> performance is lost — per attack category — compared with a
> supervised ceiling on identical features?

**French version**

> Étant donné un jeu de données étiqueté dont les déploiements réels ne
> disposent pas, les modèles non supervisés à une classe appris sur le
> trafic réseau normal peuvent-ils rendre les flux d'attaque
> mesurablement séparables, et quelle est précisément la perte de
> performance de détection — par catégorie d'attaque — par rapport à un
> plafond supervisé sur des caractéristiques identiques ?

------------------------------------------------------------------------

## 13. Conclusion

The original proposal asked whether clustering could help identify
anomalous traffic — a question whose answer, under its own anomaly
definition, could never be wrong because the definition was circular.
This revision replaces it with a question that can fail:

> Does a label-free model of normal behavior separate attacks from
> normal flows, and what is the exact price of not having labels?

The answer will be "partially, with a large measured gap to supervised
learning, and almost no signal on mimicry-style attacks." If so, the
project's contribution is not a detector that beats the impossible — it
is a rigorous, quantified map of where the label-free signal survives,
delivered with the supervised ceiling that makes the claim falsifiable.
That is a finding a jury can respect, and a result an interviewer will
remember.
