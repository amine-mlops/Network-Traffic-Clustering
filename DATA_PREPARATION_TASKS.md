# Data Exploration & Preprocessing — Task Log

**Project:** Network Traffic Clustering and Novelty Detection
**Dataset:** UNSW-NB15 (official train/test splits)
**Source of truth:** `Network_Traffic_Clustering_Novelty_Detection_Proposal.md` (Proposal V2)
**Scope of this work:** Phases 1–3 only — data loading, EDA, feature representation,
and Chapter A / Chapter B data preparation. **No model was trained** (no K-Means,
CAH, GMM, Logistic Regression, no clustering/novelty/supervised experiments).

---

## 1. Repository audit (before any change)

| Item | Finding |
|---|---|
| `pyproject.toml` | `uv`-managed, Python ≥3.14, deps: pandas, numpy, scikit-learn, scipy, matplotlib, seaborn, notebook, ipykernel |
| Raw dataset | `data/raw/UNSW-NB15/`: 2 official splits + 4 partitioned raw files + feature dictionary + events list |
| Actual dims | training **82,332 × 45**, testing **175,341 × 45** (verified, matches expected) |
| Pre-existing notebooks | `01_data_exploration.ipynb` **empty**, `02_data_preprocessing.ipynb` incomplete (3 cells), `03_feature_visualization.ipynb` **empty** — did not match the required structure |
| Pre-existing processed data | stale flat artifacts from the incomplete earlier attempt |
| Raw file integrity | md5 recorded: train `e0beea40…`, test `e55caaba…` |

Environment verified: joblib 1.6.0, scikit-learn 1.9.1, matplotlib 3.11.2, seaborn 0.13.2,
scipy 1.18.1, jupyter nbconvert 7.17.2, nbformat 5.11.1.

---

## 2. Repository changes made

### 2.1 Added — shared code
- `config/config.py` — paths (`PROJECT_ROOT`, `RAW_DIR`, `PROCESSED_DIR`, `FIGURES_DIR`,
  `METRICS_DIR`, `REPORTS_DIR`, `CHAPTER_A_DIR`, `CHAPTER_B_DIR`), `RANDOM_SEED = 42`,
  column-role constants (`ID_COLUMNS`, `LABEL_COLUMNS`, `CATEGORICAL_FEATURES`),
  declared feature groups (`NUMERIC_FEATURES` 39, `LOG1P_FEATURES` 30,
  `BINARY_OR_SPARSE_FLAGS` 3, `TOP_K`).
- `src/__init__.py`, `src/data/__init__.py`
- `src/data/preprocess.py` — data-only utilities:
  - `load_official_datasets()`, `load_feature_dictionary()` (latin-1 decode), 
    `split_features_labels()`, `identify_feature_types()`, `check_finite()`
  - `FrequencyEncoder`, `TopKOneHotEncoder` (fit/transform, picklable)
  - `FeaturePipeline` — log1p → StandardScaler (numeric) + categorical encoder,
    fitted once on a caller-supplied training frame; `transform()` never re-fits.

### 2.2 Added — notebooks (rebuilt from zero, executed top-to-bottom)
- `notebooks/01_data_exploration.ipynb`
- `notebooks/02_feature_representation.ipynb`
- `notebooks/03_chapter_a_data_preparation.ipynb`
- `notebooks/04_chapter_b_data_preparation.ipynb`

### 2.3 Removed (stale / superseded, untracked or regenerated)
- `notebooks/02_data_preprocessing.ipynb`, `notebooks/03_feature_visualization.ipynb`
- `data/processed/feature_names.csv`, `preprocessor.joblib`, `X_train_processed.npz`,
  `X_test_processed.npz`, `y_train.csv`, `y_test.csv`
- `results/figures/categorical_cardinality.png`

### 2.4 Restored (were tracked in git; left untouched)
- `results/figures/log1p_distributions.png`, `results/figures/numerical_distributions.png`
  — superseded by the `01_*` / `02_*` figures; safe to delete if unwanted.

### 2.5 Not modified
- `data/raw/UNSW-NB15/**` (read-only; md5 re-checked at the end — unchanged)

---

## 3. Notebook 01 — Data exploration

**Tasks performed**
1. Dataset inventory + loading; verified both splits against documented dimensions.
2. Structure/schema: 45 columns, dtype families (30 int64, 11 float64, 4 str),
   train/test dtype match.
3. Feature-dictionary inspection (49-column *raw* schema vs 45-column CSV schema).
4. Column-role separation: identifier `id`; reference labels `label`, `attack_cat`;
   42 feature columns.
5. Numerical (39) vs categorical (3) identification — cross-checked against `config`.
6. Data-quality checks: missing, duplicates, infinities, negatives, constants.
7. Numerical descriptive statistics (percentiles, skewness, zero fraction, cardinality).
8. Categorical frequency tables + coverage + unseen-category detection.
9. Label / `attack_cat` distributions (descriptive only, never used as input).
10. Visualisations: numerical distributions, categorical distributions, label balance,
    correlation heat-map.
11. Correlation / redundancy analysis (|r| > 0.9 pairs).

**Key findings**

| Check | Train | Test |
|---|---|---|
| Missing values | 0 | 0 |
| Duplicate rows | 0 | 0 |
| Infinite values | 0 | 0 |
| Negative numeric values | 0 | 0 |
| Constant columns | 0 | 0 |

- IP addresses / ports are **absent** from the official splits (they exist only in the
  raw partitioned files) → the "exclude IPs" rule is satisfied by construction; only
  `id` needed dropping.
- Skewness: ~30 non-negative features with |skew| > 1 (up to `trans_depth` ≈ 171).
- Cardinality: `proto` **131** (train) / 133 (test), top-10 covers 95.1%, 121 categories
  below 1%; `service` 13; `state` 7 (train) / 9 (test).
- Unseen test categories: `proto` 2 (`icmp`, `rtp`), `state` 4 (`ECO`, `PAR`, `URN`, `no`).
- Labels: attack rate **0.5506** train, **0.6806** test; `attack_cat` strongly imbalanced
  (Generic 18,871 … Worms 44); normal training pool = **37,000**.
- Strongest correlations (no exact duplicates): `dbytes↔dloss` 0.997, `sbytes↔sloss` 0.995,
  `is_ftp_login↔ct_ftp_cmd` 0.994; a cluster of `ct_*` features 0.91–0.98.

---

## 4. Notebook 02 — Feature representation

**Tasks performed**
- Part A — numerical: mechanical transform rule (non-negative ∧ |skew| > 1 ∧ not a flag),
  taxonomy of features, log1p before/after skewness for all candidates + figures.
- Part B — categorical: cardinality & coverage curves, head-to-head comparison of three
  representations (dimension, sparsity, **effect on Euclidean distance** via a
  numeric-vs-categorical squared-distance decomposition on a seeded 3,000-flow sample),
  and the unseen-category behaviour of full one-hot.
- Part C — decisions, retained strategies, trade-offs, limitations.

**Categorical encoding comparison**

| Strategy | cat dim | total dim (Ch. A) | cat block zero-frac | share of squared distance | unseen-safe |
|---|---|---|---|---|---|
| `ohe_full` (baseline) | 151 | 190 | 0.980 | 0.043 | no (all-zero rows) |
| `ohe_topk` (primary) | 24 | 63 | 0.875 | 0.043 | yes ("other") |
| `freq` (alternative) | 3 | 42 | 0.000 | 0.073 | yes (→ 0) |

Chosen `TOP_K = {proto: 10, service: 6, state: 5}` — smallest K reaching ≥ 95% coverage each.

**Numerical decisions**
- `log1p` on **30** features (all reduced |skew|; 16 remain skewed due to zero-inflation = sparsity).
- No transform on 3 flags (`is_sm_ips_ports`, `is_ftp_login`, `ct_ftp_cmd`) and
  6 bounded/pseudo-identifier columns (`sttl`, `dttl`, `swin`, `dwin`, `stcpb`, `dtcpb`).
- `StandardScaler` on all numerics, fitted on training data only.

---

## 5. Notebook 03 — Chapter A data preparation (Descriptive Clustering)

**Procedure**
1. Load official train/test; split features vs labels; drop `id`.
2. Fit three `FeaturePipeline`s on the **training split only**.
3. Transform train and test with the already-fitted pipelines.
4. Leakage/integrity audit: alignment, finiteness, no label/identifier names, sparsity.
5. Save matrices, labels, fitted pipelines.
6. Reload-and-verify round trip.

**Results**

| representation | n_features | train | test | zero-frac (test) |
|---|---|---|---|---|
| `ohe_full` | 190 | 82,332 | 175,341 | 0.7789 |
| `ohe_topk` | 63 | 82,332 | 175,341 | 0.3333 |
| `freq` | 42 | 82,332 | 175,341 | 0.0000 |

---

## 6. Notebook 04 — Chapter B data preparation (One-Class Novelty Detection)

**Procedure**
1. Normal traffic = `label == 0` → 37,000 flows.
2. Split into `normal_train` (80% → 29,600) / `normal_val` (20% → 7,400),
   seeded (42), **stratified by `service`** (chosen over `proto`: meaningful, all
   categories ≥ 2 members). Max service-share gap between splits = 0.0001.
3. Held-out test = the official split (mixture: 56,000 normal / 119,341 attack).
4. Fit preprocessing **exclusively on `normal_train`**; transform `normal_val` and test.
5. Leakage checks (normal-only validation, disjoint ids, scaler centred on `normal_train`).
6. Save; reload-and-verify round trip.

**Results**

| representation | n_features | normal_train | normal_val | test |
|---|---|---|---|---|
| `ohe_full` | 58 | 29,600 | 7,400 | 175,341 |
| `ohe_topk` | 58 | 29,600 | 7,400 | 175,341 |
| `freq` | 42 | 29,600 | 7,400 | 175,341 |

> Chapter B is narrower than Chapter A **by design**: the normal model only knows the
> handful of `proto`/`service`/`state` values present in normal traffic. Attack-only
> categories are handled at transform time (`"other"` for top-K, all-zero for full one-hot).

---

## 7. Generated artifacts

### `data/processed/chapter_a/` (14 files)
`X_train_{ohe_full,ohe_topk,freq}.npz`, `X_test_{ohe_full,ohe_topk,freq}.npz`,
`feature_names_{ohe_full,ohe_topk,freq}.csv`, `pipeline_{ohe_full,ohe_topk,freq}.joblib`,
`y_train.csv`, `y_test.csv`

### `data/processed/chapter_b/` (19 files)
`X_normal_train_*.npz`, `X_normal_val_*.npz`, `X_test_*.npz`,
`feature_names_*.csv`, `pipeline_*.joblib` (×3 reps),
`y_normal_train.csv`, `y_normal_val.csv`, `y_test.csv`, `normal_split.csv`

### `results/figures/` (8 files)
`01_numerical_distributions.png`, `01_categorical_distributions.png`,
`01_label_distribution.png`, `01_correlation_heatmap.png`,
`02_log1p_before_after.png`, `02_skewness_before_after.png`,
`02_categorical_cardinality.png`, `02_encoding_distance_comparison.png`

### `results/metrics/` (9 files)
`01_numerical_summary.csv`, `01_categorical_summary.csv`, `01_label_summary.csv`,
`01_attack_cat_summary.csv`, `01_correlation_pairs.csv`,
`02_log1p_skewness.csv`, `02_encoding_comparison.csv`,
`03_chapter_a_audit.csv`, `04_chapter_b_audit.csv`

### `results/reports/` (4 files)
`01_eda_key_facts.md`, `02_feature_representation_decisions.md`,
`03_chapter_a_summary.md`, `04_chapter_b_summary.md`

---

## 8. Verification performed

- **Notebook execution:** all four notebooks re-executed top-to-bottom from fresh
  kernels with `nbconvert --execute`; **0 error outputs** in every notebook.
- **Ad-hoc verification script** (15 checks, exit 0): group parity with `config`, the
  mechanical log1p rule reproducing `config.LOG1P_FEATURES`, encoder widths/finiteness,
  no-refit proof (numeric block zero-mean on fit data, not on unseen test),
  artifact reload/alignment/finiteness/no-label-name for all 6 matrices, and
  Chapter A/B pipeline independence.
- **Shapes:** Ch. A 190/63/42; Ch. B 58/58/42 — columns aligned within each chapter.
- **Finiteness:** all processed matrices finite (NaN/inf count = 0).
- **Leakage:** `normal_train` and `normal_val` are normal-only; test untouched during
  fitting; no `id` / `label` / `attack_cat` name in any feature matrix.
- **Raw data:** md5 of both official splits unchanged.

---

## 9. Deviations, decisions and limitations

- The proposal names `src/data/load_data.py` + `load_data`/`preprocess` split; loading
  and preprocessing are consolidated in `src/data/preprocess.py` (fewer moving parts,
  same responsibilities).
- No feature was dropped: the EDA found **no exact duplicates**, so dropping columns by a
  subjective correlation threshold would be unmotivated. Strong correlations are
  documented instead.
- The proposal's "compare encodings on a validation metric" is met with
  representation-level metrics (dimension, sparsity, distance decomposition) because
  training models is out of scope for this phase; model-based validation belongs to
  Phase 4+.
- `stcpb`/`dtcpb` (TCP base sequence numbers) are kept but flagged as pseudo-identifiers.
- 16 log1p features remain zero-inflated after transformation — documented, not hidden.

## 10. Not done (intentionally out of scope)

K-Means / CAH / GMM fitting, cluster evaluation, novelty scoring, threshold selection,
supervised ceiling, dashboard, and the final detection system. These belong to Phases 4–12.
