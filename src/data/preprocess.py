"""Data loading, validation and preprocessing utilities.

This module contains *only* data-level logic: loading the official
UNSW-NB15 train/test splits, separating features from reference labels,
and building feature representations (log1p + scaling for numerics,
categorical encoding). It deliberately contains no clustering, novelty or
supervised model code -- those belong to later project phases.

Design rules enforced here (Proposal V2, Sections 6-8):
  * `label`, `attack_cat` and `id` never enter a feature matrix.
  * Every fitted transformer (scaler / encoder) is fit on exactly one
    caller-supplied training frame; `transform` never re-fits.
  * Output matrices are dense float32 (memory-conscious) and are checked
    to contain finite values only.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from config.config import (
    ATTACK_CAT_COLUMN,
    CATEGORICAL_FEATURES,
    FEATURE_DICT_FILE,
    ID_COLUMNS,
    LABEL_COLUMN,
    LOG1P_FEATURES,
    NUMERIC_FEATURES,
    TEST_FILE,
    TOP_K,
    TRAIN_FILE,
)

OTHER_TOKEN = "other"


# --------------------------------------------------------------------------
# Loading and structural validation
# --------------------------------------------------------------------------
def load_official_datasets() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load the official UNSW-NB15 training and testing CSVs.

    Returns
    -------
    (train_df, test_df) : tuple of pandas.DataFrame
        Raw frames, unmodified apart from having been read from disk.
    """
    train_df = pd.read_csv(TRAIN_FILE)
    test_df = pd.read_csv(TEST_FILE)
    return train_df, test_df


def load_feature_dictionary() -> pd.DataFrame:
    """Load the NUSW-NB15 feature-description file.

    Returns a frame with columns ``No.``, ``Name``, ``Type``, ``Description``.
    """
    # The official feature-description file is not UTF-8 (it contains a
    # Windows-1252 curly apostrophe), so decode it as latin-1.
    feat = pd.read_csv(FEATURE_DICT_FILE, encoding="latin-1")
    feat.columns = [c.strip() for c in feat.columns]
    for col in ("Name", "Type", "Description"):
        if col in feat.columns:
            feat[col] = feat[col].astype(str).str.strip()
    return feat


def split_features_labels(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separate a raw frame into (feature frame, reference-label frame).

    The feature frame drops ``id`` (identifier) and both reference labels
    (``label``, ``attack_cat``). The label frame keeps both labels aligned
    by index so they can be joined back for evaluation later.
    """
    drop_cols = [c for c in ID_COLUMNS + [LABEL_COLUMN, ATTACK_CAT_COLUMN] if c in df.columns]
    features = df.drop(columns=drop_cols)
    labels = df[[ATTACK_CAT_COLUMN, LABEL_COLUMN]].copy()
    return features, labels


def identify_feature_types(df: pd.DataFrame) -> tuple[List[str], List[str]]:
    """Return (numeric_columns, categorical_columns) for a feature frame.

    Numeric = integer/float dtypes. Categorical = string/object/boolean
    dtypes. A boolean column is reported as categorical so it is encoded.
    """
    numeric = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical = [c for c in df.columns if c not in numeric]
    return numeric, categorical


def check_finite(matrix: np.ndarray, name: str = "matrix") -> None:
    """Raise ``ValueError`` if ``matrix`` contains NaN or +/-inf."""
    if not np.isfinite(matrix).all():
        bad = int((~np.isfinite(matrix)).sum())
        raise ValueError(f"{name} contains {bad} non-finite values.")


# --------------------------------------------------------------------------
# Categorical encoders (fit / transform, picklable)
# --------------------------------------------------------------------------
class FrequencyEncoder:
    """Replace each category by the frequency observed in the fit data.

    Unseen categories map to 0.0 at transform time. The result is a dense
    float array of shape ``(n_rows, n_categorical_columns)``.
    """

    def __init__(self, columns: Sequence[str]):
        self.columns = list(columns)

    def fit(self, df: pd.DataFrame) -> "FrequencyEncoder":
        self.maps_: Dict[str, pd.Series] = {
            col: df[col].value_counts(normalize=True) for col in self.columns
        }
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        out = np.zeros((len(df), len(self.columns)), dtype=np.float64)
        for j, col in enumerate(self.columns):
            out[:, j] = df[col].map(self.maps_[col]).fillna(0.0).to_numpy()
        return out

    def get_feature_names(self) -> List[str]:
        return [f"{col}_freq" for col in self.columns]


class TopKOneHotEncoder:
    """One-hot encode only the ``k`` most frequent categories per column.

    Every other training category *and* every unseen category is mapped to
    a shared bucket ``"other"``. This keeps a fixed, small output width and
    prevents high-cardinality columns (``proto``) from exploding the
    Euclidean distance.
    """

    def __init__(self, columns: Sequence[str], top_k: Dict[str, int]):
        self.columns = list(columns)
        self.top_k = dict(top_k)

    def fit(self, df: pd.DataFrame) -> "TopKOneHotEncoder":
        self.vocab_: Dict[str, List[str]] = {}
        categories = []
        for col in self.columns:
            k = self.top_k.get(col, 10)
            vocab = df[col].value_counts().head(k).index.astype(str).tolist()
            self.vocab_[col] = vocab
            categories.append(np.array(vocab + [OTHER_TOKEN], dtype=object))
        self.encoder_ = OneHotEncoder(
            categories=categories,
            handle_unknown="ignore",
            sparse_output=False,
            dtype=np.float32,
        )
        self.encoder_.fit(self._reduce(df))
        return self

    def _reduce(self, df: pd.DataFrame) -> pd.DataFrame:
        reduced = {}
        for col in self.columns:
            vocab = set(self.vocab_[col])
            if pd.api.types.is_string_dtype(df[col]) or df[col].dtype == object:
                values = df[col].astype(str)
            else:
                values = df[col].astype(str)
            reduced[col] = values.where(values.isin(vocab), OTHER_TOKEN)
        return pd.DataFrame(reduced, index=df.index)

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        return self.encoder_.transform(self._reduce(df))

    def get_feature_names(self) -> List[str]:
        return list(self.encoder_.get_feature_names_out(self.columns))


# --------------------------------------------------------------------------
# Full representation pipeline
# --------------------------------------------------------------------------
class FeaturePipeline:
    """Build a numeric feature matrix from raw feature columns.

    Parameters
    ----------
    categorical_strategy : {"ohe_full", "ohe_topk", "freq"}
        How categorical columns are encoded.
    numeric_features / categorical_features / log1p_features / top_k :
        Feature groups; default to the project-wide constants.
    scale_numeric : bool
        StandardScale the (log1p-transformed) numeric block.
    scale_frequency : bool
        StandardScale the frequency-encoded block (ignored by the OHE
        strategies, whose binary columns are left on the 0/1 scale).

    The pipeline is fit on exactly one training frame and then applied to
    validation/test frames with ``transform``. Column order is always
    ``[numeric block ..., categorical block ...]`` and is stable across
    train/val/test, guaranteeing feature alignment.
    """

    STRATEGIES = ("ohe_full", "ohe_topk", "freq")

    def __init__(
        self,
        categorical_strategy: str = "ohe_topk",
        numeric_features: Optional[Sequence[str]] = None,
        categorical_features: Optional[Sequence[str]] = None,
        log1p_features: Optional[Sequence[str]] = None,
        top_k: Optional[Dict[str, int]] = None,
        scale_numeric: bool = True,
        scale_frequency: bool = True,
        dtype: type = np.float32,
    ):
        if categorical_strategy not in self.STRATEGIES:
            raise ValueError(
                f"Unknown strategy {categorical_strategy!r}; "
                f"expected one of {self.STRATEGIES}."
            )
        self.categorical_strategy = categorical_strategy
        self.numeric_features = list(numeric_features or NUMERIC_FEATURES)
        self.categorical_features = list(categorical_features or CATEGORICAL_FEATURES)
        self.log1p_features = [f for f in (log1p_features if log1p_features is not None else LOG1P_FEATURES)]
        self.top_k = dict(top_k or TOP_K)
        self.scale_numeric = scale_numeric
        self.scale_frequency = scale_frequency
        self.dtype = dtype
        self.fitted_ = False

    # -- internals ---------------------------------------------------------
    def _select(self, df: pd.DataFrame) -> pd.DataFrame:
        missing = [c for c in self.numeric_features + self.categorical_features if c not in df.columns]
        if missing:
            raise KeyError(f"Input frame is missing required columns: {missing}")
        return df[self.numeric_features + self.categorical_features]

    def _numeric_block(self, df: pd.DataFrame) -> np.ndarray:
        num = df[self.numeric_features].to_numpy(dtype=np.float64, copy=True)
        if self.log1p_idx_:
            num[:, self.log1p_idx_] = np.log1p(num[:, self.log1p_idx_])
        return num

    def _categorical_block(self, df: pd.DataFrame) -> np.ndarray:
        cat = df[self.categorical_features]
        if self.categorical_strategy == "ohe_full":
            return self.encoder_.transform(cat).astype(self.dtype)
        if self.categorical_strategy == "ohe_topk":
            return self.encoder_.transform(cat).astype(self.dtype)
        # frequency encoding
        freq = self.freq_encoder_.transform(cat)
        if self.scale_frequency:
            freq = self.freq_scaler_.transform(freq)
        return freq.astype(self.dtype)

    # -- public API --------------------------------------------------------
    def fit(self, df: pd.DataFrame) -> "FeaturePipeline":
        df = self._select(df)
        self.log1p_idx_ = [i for i, c in enumerate(self.numeric_features) if c in self.log1p_features]

        numeric = self._numeric_block(df)
        self.scaler_ = StandardScaler().fit(numeric) if self.scale_numeric else None

        if self.categorical_strategy == "ohe_full":
            self.encoder_ = OneHotEncoder(
                handle_unknown="ignore", sparse_output=False, dtype=self.dtype
            ).fit(df[self.categorical_features])
        elif self.categorical_strategy == "ohe_topk":
            self.encoder_ = TopKOneHotEncoder(self.categorical_features, self.top_k).fit(
                df
            )
        else:
            self.freq_encoder_ = FrequencyEncoder(self.categorical_features).fit(df)
            freq = self.freq_encoder_.transform(df[self.categorical_features])
            self.freq_scaler_ = StandardScaler().fit(freq) if self.scale_frequency else None

        self.fitted_ = True
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        if not self.fitted_:
            raise RuntimeError("FeaturePipeline must be fitted before transform().")
        df = self._select(df)
        numeric = self._numeric_block(df)
        if self.scaler_ is not None:
            numeric = self.scaler_.transform(numeric)
        categorical = self._categorical_block(df)
        matrix = np.hstack([numeric.astype(self.dtype), categorical])
        return np.ascontiguousarray(matrix, dtype=self.dtype)

    def fit_transform(self, df: pd.DataFrame) -> np.ndarray:
        return self.fit(df).transform(df)

    def get_feature_names(self) -> List[str]:
        if not self.fitted_:
            raise RuntimeError("FeaturePipeline must be fitted before get_feature_names().")
        if self.categorical_strategy == "freq":
            cat_names = self.freq_encoder_.get_feature_names()
        elif self.categorical_strategy == "ohe_topk":
            cat_names = list(self.encoder_.get_feature_names())
        else:  # ohe_full
            cat_names = list(
                self.encoder_.get_feature_names_out(self.categorical_features)
            )
        return list(self.numeric_features) + cat_names

    def describe(self) -> dict:
        return {
            "categorical_strategy": self.categorical_strategy,
            "n_numeric": len(self.numeric_features),
            "n_categorical_columns": len(self.categorical_features),
            "n_features": len(self.get_feature_names()),
            "log1p_features": list(self.log1p_features),
            "scale_numeric": self.scale_numeric,
            "scale_frequency": self.scale_frequency if self.categorical_strategy == "freq" else False,
        }
