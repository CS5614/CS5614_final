from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from fastapi_cache.decorator import cache
from pydantic import BaseModel, Field, validator
from sklearn.preprocessing import StandardScaler
import numpy as np
from ..utils.db_engine import DBEngine
import pandas as pd
import math


class QoLWeightRequest(BaseModel):
    # All weights optional; will be normalized. Provide at least one.
    price: Optional[float] = Field(None, ge=0)
    airQualityScore: Optional[float] = Field(None, ge=0)
    walkScore: Optional[float] = Field(None, ge=0)
    busStopsNumber: Optional[float] = Field(None, ge=0)
    openStreetNumber: Optional[float] = Field(None, ge=0)
    nearestBusStopDistance: Optional[float] = Field(None, ge=0)
    nearestParkDistance: Optional[float] = Field(None, ge=0)

    @validator("nearestBusStopDistance", "nearestParkDistance", pre=True)
    def allow_zero(cls, v):  # type: ignore[override]
        return v

    def normalized(self) -> Dict[str, float]:
        """Validate that the sum of weights is exactly 1 or 100.

        If sum == 100 (within tolerance) we scale to 1. If sum == 1 already we keep as-is.
        Any other total raises 400 to caller.
        """
        items = {k: v for k, v in self.dict().items() if v is not None and v >= 0}
        if not items:
            raise ValueError("At least one weight must be provided")
        total = sum(items.values())
        if math.isclose(total, 1.0, rel_tol=1e-9, abs_tol=1e-6):
            return items  # already sums to 1
        if math.isclose(total, 100.0, rel_tol=1e-9, abs_tol=1e-6):
            return {
                k: v / 100.0 for k, v in items.items()
            }  # convert percent to fraction
        # Not acceptable
        raise ValueError(
            f"Sum of weights must be 1 or 100. Received total={total:.6f}. Provided keys: {list(items.keys())}"
        )


class QoLScore(BaseModel):
    id: int
    qolScore: float


router = APIRouter(prefix="/api/dynamicQol", tags=["dynamicQol"])


class QoLDefaultWeights(BaseModel):
    price: float = 0.0120
    airQualityScore: float = 0.0525  # aqi
    walkScore: float = 0.1425  # nwi_score
    nearestBusStopDistance: float = 0.2114  # nearest_bus_stop_miles
    busStopsNumber: float = 0.2123  # nearby_bus_stops
    openStreetNumber: float = 0.1565  # nearby_parks (count)
    nearestParkDistance: float = 0.2129  # nearest_park_miles


@cache()
@router.get("/defaultWeights", response_model=QoLDefaultWeights)
def get_default_qol_weights():
    """
    Return the default normalized weights (sum ≈ 1.0) for dynamic QoL scoring.
    """
    return QoLDefaultWeights()


@router.post("", response_model=List[QoLScore])
def compute_dynamic_qol(weights: QoLWeightRequest):
    """Recalculate QoL scores with custom feature weights sent by frontend."""
    try:
        norm_weights = weights.normalized()
        print("Normalized weights:", norm_weights)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Mapping: request field -> SQL column alias used in query
    feature_columns = {
        "price": "price",
        "airQualityScore": "airQualityScore",
        "walkScore": "walkScore",
        "busStopsNumber": "busStopsNumber",
        "openStreetNumber": "openStreetNumber",
        "nearestBusStopDistance": "nearestBusStopDistance",
        "nearestParkDistance": "nearestParkDistance",
    }

    active_features = [f for f in feature_columns.keys() if f in norm_weights]

    if not active_features:
        raise HTTPException(status_code=400, detail="No valid feature weights provided")

    # Build SQL selecting only needed columns plus id
    select_cols = ["rb.listing_db_id AS id"]
    # (joins placeholder removed)

    # Always need RentalBase
    base_cte = """
    WITH RentalBase AS (
      SELECT
        rl.listing_db_id,
        COALESCE(rl.price,0) AS price,
        COALESCE(aq.aqi,0)   AS "airQualityScore",
        COALESCE(gn.nwi_score,0) AS "walkScore"
      FROM rental_listings rl
      LEFT JOIN listing_clusters lc ON rl.listing_db_id = lc.listing_db_id
      LEFT JOIN cluster_air_quality aq ON lc.cluster_id = aq.cluster_id
      LEFT JOIN listings_geo lg ON rl.listing_db_id = lg.listing_db_id
      LEFT JOIN geo_nwi gn ON lg.geo_id = gn.geo_id
      WHERE rl.state IN ('DC','MD','VA')
    ),
    NearestBus AS (
      SELECT rl.listing_db_id, COALESCE(ROUND((ST_Distance(rl.geom::geography, bs.geom::geography)/1609.34)::NUMERIC,2),0) AS "nearestBusStopDistance"
      FROM rental_listings rl
      LEFT JOIN LATERAL (
        SELECT bs.id, bs.geom FROM bus_stops bs ORDER BY rl.geom <-> bs.geom LIMIT 1
      ) bs ON TRUE
      WHERE rl.state IN ('DC','MD','VA')
    ),
    BusStopCount AS (
      SELECT rl.listing_db_id, COUNT(DISTINCT bs.id) AS "busStopsNumber"
      FROM rental_listings rl
      LEFT JOIN bus_stops bs ON ST_DWithin(rl.geom, bs.geom, 0.0145)
      WHERE rl.state IN ('DC','MD','VA')
      GROUP BY rl.listing_db_id
    ),
    ParkCount AS (
      SELECT rl.listing_db_id, COUNT(DISTINCT os.id) AS "openStreetNumber"
      FROM rental_listings rl
      LEFT JOIN open_street os ON ST_DWithin(rl.geom, os.geom, 0.0145) AND os.leisure='park'
      WHERE rl.state IN ('DC','MD','VA')
      GROUP BY rl.listing_db_id
    ),
    NearestPark AS (
      SELECT rl.listing_db_id, COALESCE(ROUND((ST_Distance(rl.geom::geography, os.geom::geography)/1609.34)::NUMERIC,2),0) AS "nearestParkDistance"
      FROM rental_listings rl
      LEFT JOIN LATERAL (
        SELECT os.id, os.geom FROM open_street os WHERE os.leisure='park' ORDER BY rl.geom <-> os.geom LIMIT 1
      ) os ON TRUE
      WHERE rl.state IN ('DC','MD','VA')
    )
    """

    # Determine which joins/CTEs matter (CTEs are always present; we just select columns)
    source_map = {
        "airQualityScore": 'rb."airQualityScore"',
        "walkScore": 'rb."walkScore"',
        "price": "rb.price",
        "busStopsNumber": 'bsc."busStopsNumber"',
        "openStreetNumber": 'pc."openStreetNumber"',
        "nearestBusStopDistance": 'nb."nearestBusStopDistance"',
        "nearestParkDistance": 'np."nearestParkDistance"',
    }
    for feat in active_features:
        col = feature_columns[feat]
        source_expr = source_map[feat]
        select_cols.append(f'COALESCE({source_expr},0) AS "{col}"')

    sql = (
        base_cte
        + "\nSELECT "
        + ", ".join(select_cols)
        + "\nFROM RentalBase rb\nLEFT JOIN NearestBus nb ON rb.listing_db_id = nb.listing_db_id\nLEFT JOIN BusStopCount bsc ON rb.listing_db_id = bsc.listing_db_id\nLEFT JOIN ParkCount pc ON rb.listing_db_id = pc.listing_db_id\nLEFT JOIN NearestPark np ON rb.listing_db_id = np.listing_db_id\nORDER BY rb.listing_db_id;"
    )
    db = DBEngine()
    engine = db.get_engine()
    df = pd.read_sql(sql, engine)
    print(df.columns)

    if df.empty:
        return []
    # Log transforms
    df["price"] = np.log1p(df["price"])
    df["nearestBusStopDistance"] = np.log1p(df["nearestBusStopDistance"])
    df["busStopsNumber"] = np.log1p(df["busStopsNumber"])
    df["nearestParkDistance"] = np.log1p(df["nearestParkDistance"])

    # features
    features = df.columns.tolist()[1:]
    X = df[features]

    # Standardize the features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    df_scaled = pd.DataFrame(X_scaled, columns=features, index=df.index)

    # Invert direction of the features
    df_scaled["airQualityScore"] *= -1
    df_scaled["nearestBusStopDistance"] *= -1
    df_scaled["nearestParkDistance"] *= -1

    weight_vector = np.array([v for v in norm_weights.values()])
    feature_matrix = np.array(df_scaled)
    raw_scores = feature_matrix.dot(weight_vector)
    ids = df["id"].tolist()
    # Min-max normalize to 0-100
    mn, mx = raw_scores.min(), raw_scores.max()
    if mx == mn:
        norm_scores = np.zeros_like(raw_scores)
    else:
        norm_scores = (raw_scores - mn) / (mx - mn) * 100

    response = [QoLScore(id=i, qolScore=round(s, 2)) for i, s in zip(ids, norm_scores)]
    return response
