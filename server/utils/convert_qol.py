import os
import decimal
from typing import List, Dict
from psycopg2.extras import RealDictCursor
from .db_connection import DatabaseConnection


class QualityOfLifeConverter:
    def __init__(self):
        pass

    def _normalize_qol_score(self, score: float, min_score: float, max_score: float) -> float:
        """Normalize a score to 0–1 scale."""
        if max_score == min_score:
            return 0.0
        return (score - min_score) / (max_score - min_score)

    def _convert_decimals(self, value):
        """Convert decimal.Decimal to float for JSON serialization."""
        return float(value) if isinstance(value, decimal.Decimal) else value

    def fetch_rental_scores(self) -> List[Dict]:
        sql_main = """
        WITH RentalBase AS (
          SELECT
            rl.listing_db_id,
            COALESCE(rl.listing_name,'')   AS name,
            rl.latitude                     AS lat,
            rl.longitude                    AS long,
            COALESCE(rl.price,0)            AS price,
            COALESCE(rl.bedrooms,0)         AS bedroom,
            COALESCE(rl.bathrooms,0)        AS bathroom,
            COALESCE(rl.state,'')           AS state,
            COALESCE(aq.aqi,0)              AS "airQualityScore",
            COALESCE(gn.nwi_score,0)        AS "walkScore",
            COALESCE(pr.rating,0)           AS "reviewScore",
            COALESCE(lq.qol_score,0)        AS "qolScore"
          FROM rental_listings rl
          LEFT JOIN listing_clusters lc    ON rl.listing_db_id = lc.listing_db_id
          LEFT JOIN cluster_air_quality aq ON lc.cluster_id     = aq.cluster_id
          LEFT JOIN listings_geo lg        ON rl.listing_db_id = lg.listing_db_id
          LEFT JOIN geo_nwi gn             ON lg.geo_id         = gn.geo_id
          LEFT JOIN place_review pr        ON rl.listing_db_id = pr.listing_id
          LEFT JOIN listings_qol lq        ON rl.listing_db_id = lq.listing_db_id
          WHERE rl.state IN ('DC','MD','VA')
            AND (
              rl.state = 'DC'
              OR (rl.state = 'MD' AND rl.county IN ('Montgomery','Prince George''s'))
              OR (rl.state = 'VA' AND (
                rl.county IN ('Arlington','Fairfax','Loudoun') OR
                rl.city   IN ('Alexandria','Fairfax','Falls Church')
              ))
            )
        ),
        NearestBus AS (
          SELECT
            rl.listing_db_id,
            COALESCE(
              ROUND((ST_Distance(rl.geom::geography, bs.geom::geography)/1609.34)::NUMERIC,2)
            ,0) AS "nearestBusStopMiles"
          FROM rental_listings rl
          LEFT JOIN LATERAL (
            SELECT bs.id, bs.geom
            FROM bus_stops bs
            ORDER BY rl.geom <-> bs.geom
            LIMIT 1
          ) bs ON TRUE
          WHERE rl.state IN ('DC','MD','VA')
        ),
        BusStopCount AS (
          SELECT
            rl.listing_db_id,
            COUNT(DISTINCT bs.id) AS "busStopsNumber"
          FROM rental_listings rl
          LEFT JOIN bus_stops bs
            ON ST_DWithin(rl.geom, bs.geom, 0.0145)
          WHERE rl.state IN ('DC','MD','VA')
          GROUP BY rl.listing_db_id
        ),
        ParkCount AS (
          SELECT
            rl.listing_db_id,
            COUNT(DISTINCT os.id) AS "openStreetNumber"
          FROM rental_listings rl
          LEFT JOIN open_street os
            ON ST_DWithin(rl.geom, os.geom, 0.0145) AND os.leisure='park'
          WHERE rl.state IN ('DC','MD','VA')
          GROUP BY rl.listing_db_id
        ),
        NearestPark AS (
          SELECT
            rl.listing_db_id,
            COALESCE(
              ROUND((ST_Distance(rl.geom::geography, os.geom::geography)/1609.34)::NUMERIC,2)
            ,0) AS "nearestParkMiles"
          FROM rental_listings rl
          LEFT JOIN LATERAL (
            SELECT os.id, os.geom
            FROM open_street os
            WHERE os.leisure='park'
            ORDER BY rl.geom <-> os.geom
            LIMIT 1
          ) os ON TRUE
          WHERE rl.state IN ('DC','MD','VA')
        )
        SELECT
          rb.listing_db_id,
          rb.name,
          rb.lat,
          rb.long,
          rb.price,
          rb.bedroom,
          rb.bathroom,
          rb.state,
          rb."airQualityScore",
          rb."qolScore",
          rb."walkScore",
          rb."reviewScore",
          COALESCE(bsc."busStopsNumber",0)     AS "busStopsNumber",
          COALESCE(pc."openStreetNumber",0)    AS "openStreetNumber",
          COALESCE(nb."nearestBusStopMiles",0) AS "nearestBusStopMiles",
          COALESCE(np."nearestParkMiles",0)    AS "nearestParkMiles"
        FROM RentalBase rb
        LEFT JOIN NearestBus nb    ON rb.listing_db_id = nb.listing_db_id
        LEFT JOIN BusStopCount bsc ON rb.listing_db_id = bsc.listing_db_id
        LEFT JOIN ParkCount pc     ON rb.listing_db_id = pc.listing_db_id
        LEFT JOIN NearestPark np   ON rb.listing_db_id = np.listing_db_id
        ORDER BY rb.listing_db_id;
        """

        try:
            # 1) Open connection + real‐dict cursor
            with DatabaseConnection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # 2) Fetch min/max QoL with distinct aliases
                    cur.execute(
                        "SELECT "
                        "COALESCE(MIN(qol_score),0) AS min_qol, "
                        "COALESCE(MAX(qol_score),1) AS max_qol "
                        "FROM listings_qol WHERE qol_score IS NOT NULL;"
                    )
                    row = cur.fetchone()
                    min_qol, max_qol = float(row["min_qol"]), float(row["max_qol"])

                    # 3) Execute main rental‐score query
                    cur.execute(sql_main)
                    records: List[Dict] = cur.fetchall()

            # 4) Post‐process each record
            for rec in records:
                # decimal → float
                for k, v in rec.items():
                    rec[k] = self._convert_decimals(v)
                # normalize QoL
                rec["qolScore"] = round((self._normalize_qol_score(
                    rec.get("qolScore", 0), min_qol, max_qol
                ))*100, 2)
            return records

        except Exception as e:
            raise RuntimeError(f"Failed to fetch or process data: {e}")