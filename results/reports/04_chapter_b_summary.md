# 04 - Chapter B data preparation summary

Normal definition: label == 0. Preprocessing fitted on normal_train ONLY.

- normal_train: 29600 flows (80%, stratified by service)
- normal_val:   7400 flows (20%, normal only)
- held-out test: 175341 flows (mixture, 56000 normal / 119341 attack)

| representation | n_features | normal_train | normal_val | test |
|---|---|---|---|---|
| ohe_full | 58 | 29600 | 7400 | 175341 |
| ohe_topk | 58 | 29600 | 7400 | 175341 |
| freq | 42 | 29600 | 7400 | 175341 |

- normal_val is normal-only; test untouched during fitting.
- labels saved separately (y_normal_train / y_normal_val / y_test).
- split record: normal_split.csv; fitted pipelines: pipeline_<rep>.joblib.
- all matrices finite and column-aligned; round-trip verified.