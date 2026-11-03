# 02 - Feature representation decisions

## Numerical
- log1p applied to 30 features: ['dur', 'spkts', 'dpkts', 'sbytes', 'dbytes', 'rate', 'sload', 'dload', 'sloss', 'dloss', 'sinpkt', 'dinpkt', 'sjit', 'djit', 'tcprtt', 'synack', 'ackdat', 'smean', 'dmean', 'trans_depth', 'response_body_len', 'ct_srv_src', 'ct_state_ttl', 'ct_dst_ltm', 'ct_src_dport_ltm', 'ct_dst_sport_ltm', 'ct_dst_src_ltm', 'ct_flw_http_mthd', 'ct_src_ltm', 'ct_srv_dst']
- left untransformed (flags): ['is_sm_ips_ports', 'is_ftp_login', 'ct_ftp_cmd']
- left untransformed (bounded/pseudo-id): ['sttl', 'dttl', 'swin', 'stcpb', 'dtcpb', 'dwin']
- StandardScaler fitted on training data only, applied to all numerics.

## Categorical
| strategy | cat_dim | total_dim | cat_distance_share | unseen-safe |
|---|---|---|---|---|
| ohe_full | 151 | 190 | 0.043 | no |
| ohe_topk | 24 | 63 | 0.043 | yes |
| freq | 3 | 42 | 0.073 | yes |

- Chosen top-K: {'proto': 10, 'service': 6, 'state': 5} (>=95% coverage each).
- Primary representation: ohe_topk. Secondary: ohe_full. Alternative: freq.
- No features dropped (no exact duplicates); roles excluded: id, label, attack_cat.

See results/metrics/02_*.csv and results/figures/02_*.png.