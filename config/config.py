"""Central configuration for the Network Traffic Clustering and Novelty
Detection project (Proposal V2).

This module holds only *paths* and *declared feature-group constants*
derived from the exploratory analysis. It contains no learned state and no
model logic, so it is safe to import from every notebook.
"""

from __future__ import annotations

from pathlib import Path

# --------------------------------------------------------------------------
# Project layout
# --------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw" / "UNSW-NB15"
PROCESSED_DIR = DATA_DIR / "processed"

RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
METRICS_DIR = RESULTS_DIR / "metrics"
REPORTS_DIR = RESULTS_DIR / "reports"

# Processed-data sub-folders (one per project chapter).
CHAPTER_A_DIR = PROCESSED_DIR / "chapter_a"
CHAPTER_B_DIR = PROCESSED_DIR / "chapter_b"

# --------------------------------------------------------------------------
# Raw dataset files (never modified)
# --------------------------------------------------------------------------
TRAIN_FILE = RAW_DIR / "UNSW_NB15_training-set.csv"
TEST_FILE = RAW_DIR / "UNSW_NB15_testing-set.csv"
FEATURE_DICT_FILE = RAW_DIR / "NUSW-NB15_features.csv"

# Expected official dimensions (verified in notebook 01, not assumed).
EXPECTED_TRAIN_SHAPE = (82332, 45)
EXPECTED_TEST_SHAPE = (175341, 45)

# --------------------------------------------------------------------------
# Reproducibility
# --------------------------------------------------------------------------
RANDOM_SEED = 42

# --------------------------------------------------------------------------
# Column roles
# --------------------------------------------------------------------------
# `id` is a row index that is NOT unique across the official train/test
# files (both start at 1) and carries no traffic information -> excluded.
ID_COLUMNS = ["id"]

# Reference labels: kept separate from every feature matrix, never learned on.
LABEL_COLUMN = "label"
ATTACK_CAT_COLUMN = "attack_cat"
LABEL_COLUMNS = [LABEL_COLUMN, ATTACK_CAT_COLUMN]

# The official train/test CSVs contain no srcip/dstip columns (those only
# exist in the raw partitioned files). `dsport`/`sport` are likewise absent.
# Nothing to drop there; documented in notebook 01.

# --------------------------------------------------------------------------
# Declared feature groups (verified against dtypes in notebook 01)
# --------------------------------------------------------------------------
CATEGORICAL_FEATURES = ["proto", "service", "state"]

# All 39 numeric feature columns (45 columns minus id, attack_cat, label,
# and the 3 categorical columns).
NUMERIC_FEATURES = [
    "dur", "spkts", "dpkts", "sbytes", "dbytes", "rate", "sttl", "dttl",
    "sload", "dload", "sloss", "dloss", "sinpkt", "dinpkt", "sjit", "djit",
    "swin", "stcpb", "dtcpb", "dwin", "tcprtt", "synack", "ackdat", "smean",
    "dmean", "trans_depth", "response_body_len", "ct_srv_src", "ct_state_ttl",
    "ct_dst_ltm", "ct_src_dport_ltm", "ct_dst_sport_ltm", "ct_dst_src_ltm",
    "is_ftp_login", "ct_ftp_cmd", "ct_flw_http_mthd", "ct_src_ltm",
    "ct_srv_dst", "is_sm_ips_ports",
]

# Features that receive log1p. Rule (notebook 02): non-negative, strongly
# right-skewed (|skew| > 1), non-binary. Binary indicators and sparse 0/1/2
# flags are excluded because log1p is meaningless on them.
LOG1P_FEATURES = [
    "dur", "spkts", "dpkts", "sbytes", "dbytes", "rate", "sload", "dload",
    "sloss", "dloss", "sinpkt", "dinpkt", "sjit", "djit", "tcprtt", "synack",
    "ackdat", "smean", "dmean", "trans_depth", "response_body_len",
    "ct_srv_src", "ct_state_ttl", "ct_dst_ltm", "ct_src_dport_ltm",
    "ct_dst_sport_ltm", "ct_dst_src_ltm", "ct_flw_http_mthd", "ct_src_ltm",
    "ct_srv_dst",
]

# Binary / sparse discrete flags kept on their original scale.
BINARY_OR_SPARSE_FLAGS = ["is_sm_ips_ports", "is_ftp_login", "ct_ftp_cmd"]

# Top-K vocabulary sizes for the "top-k one-hot with an other bucket"
# strategy. Chosen from the coverage analysis in notebook 02
# (proto top-10 -> 95.1%, service top-6 -> 99.1%, state top-5 -> 100%).
TOP_K = {"proto": 10, "service": 6, "state": 5}
