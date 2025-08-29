from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator
import numpy as np
from ..utils.db_connection import DatabaseConnection
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


@router.post("", response_model=List[QoLScore])
def compute_dynamic_qol(weights: QoLWeightRequest):
    """Recalculate QoL scores with custom feature weights sent by frontend."""
    try:
        norm_weights = weights.normalized()
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

    # For distance features we will invert later (closer is better)
    invert_features = {"nearestBusStopDistance", "nearestParkDistance"}

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

    try:
        with DatabaseConnection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")

    if not rows:
        return []

    # Build arrays for weighted score
    # rows come back as tuples in column order we built: id + active feature columns in same sequence
    ids = [r[0] for r in rows]
    # Build matrix by slicing row elements 1.. for each row
    feature_matrix: List[List[float]] = []
    for r in rows:
        values = []
        for idx, feat in enumerate(active_features):
            val = float(r[1 + idx])
            if feat in invert_features:
                val = -val
            values.append(val)
        feature_matrix.append(values)

    feature_matrix = np.array(feature_matrix)
    weight_vector = np.array([norm_weights[f] for f in active_features])
    feature_matrix_np = np.array(feature_matrix)
    raw_scores = feature_matrix_np.dot(weight_vector)

    # Min-max normalize to 0-100
    mn, mx = raw_scores.min(), raw_scores.max()
    if mx == mn:
        norm_scores = np.zeros_like(raw_scores)
    else:
        norm_scores = (raw_scores - mn) / (mx - mn) * 100

    response = [QoLScore(id=i, qolScore=round(s, 2)) for i, s in zip(ids, norm_scores)]
    return response
