from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import numpy as np
import pandas as pd
import joblib
import os
import json
from functools import lru_cache

from ..utils.database import engine
from ..config.features_config import FEATURES_CONFIG, DB_COLUMN_NAMES
from ..models.qol_score import QoLScore
from ..models.qol_weights_request import QoLWeightRequest


# Load preprocessed Scaler
SCALER_PATH = os.path.join(os.path.dirname(__file__), "..", "ml_models", "scaler.gz")
try:
    SCALER = joblib.load(SCALER_PATH)
except FileNotFoundError:
    raise RuntimeError(f"Scaler not found. Run 'scripts/preprocess_and_save_scaler.py' first.")



router = APIRouter(prefix="/api/dynamicQol", tags=["dynamicQol"])


# Get default weights
DEFAULT_WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "default_weights.json")

@lru_cache()
def get_default_weights_from_file() -> Dict[str, float]:
    try:
        with open(DEFAULT_WEIGHTS_PATH, "r") as f: return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Default weights file is missing.")


# Default weights router
@router.get("/defaultWeights", response_model=Dict[str, float])
def get_default_weights(weights: Dict = Depends(get_default_weights_from_file)):
    return weights



# Get features dataframe
@lru_cache()
def get_features_dataframe() -> pd.DataFrame:
    from ml_scripts.preprocess_and_save_scaler import merge_dataframes
    return merge_dataframes()

# QoL Score Calculation
@router.post("", response_model=List[QoLScore])
def compute_dynamic_qol(weights: QoLWeightRequest):
    try:
        norm_weights = weights.normalize()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    df = get_features_dataframe().copy()
    if df.empty: return []

    listing_ids = df["listing_db_id"].tolist()

    for feature in FEATURES_CONFIG:
        if feature.apply_log:
            df[feature.db_col] = np.log1p(df[feature.db_col])

    X_scaled = SCALER.transform(df[DB_COLUMN_NAMES])
    df_scaled = pd.DataFrame(X_scaled, columns=DB_COLUMN_NAMES)

    final_feature_matrix, weight_vector = [], []
    for feature in FEATURES_CONFIG:
        if feature.api_name in norm_weights:
            scaled_col = df_scaled[feature.db_col].copy()
            if feature.invert_score:
                scaled_col *= -1
            final_feature_matrix.append(scaled_col)
            weight_vector.append(norm_weights[feature.api_name])

    final_feature_matrix = np.array(final_feature_matrix).T
    weight_vector = np.array(weight_vector)
    raw_scores = final_feature_matrix.dot(weight_vector)

    mn, mx = raw_scores.min(), raw_scores.max()
    norm_scores = np.full_like(raw_scores, 50) if mx == mn else (raw_scores - mn) / (mx - mn) * 100

    return [QoLScore(id=int(i), qolScore=round(s, 2)) for i, s in zip(listing_ids, norm_scores)]


