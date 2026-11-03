# 03 - Chapter A data preparation summary

Fitted on the official training split only; test transformed with the same pipelines.

| representation | n_features | train | test | zero_frac(test) |
|---|---|---|---|---|
| ohe_full | 190 | 82332 | 175341 | 0.7789 |
| ohe_topk | 63 | 82332 | 175341 | 0.3333 |
| freq | 42 | 82332 | 175341 | 0.0000 |

- Features exclude id / label / attack_cat.
- labels saved to y_train.csv / y_test.csv (separate from matrices).
- fitted pipelines saved as pipeline_<rep>.joblib.
- all matrices finite and column-aligned; round-trip verified.