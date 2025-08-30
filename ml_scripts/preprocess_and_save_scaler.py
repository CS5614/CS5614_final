import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import joblib
import os
import sys

# Add the parent directory to the sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.append(PROJECT_ROOT)


from server.utils.database import engine
from server.config.features_config import FEATURES_CONFIG, DB_COLUMN_NAMES

def load_rental_listings():
    load_sql = """
    SELECT
      rl.listing_db_id,
      rl.latitude,
      rl.longitude,
      rl.price,
      aq.aqi,
      gn.nwi_score
    FROM public.rental_listings rl
    JOIN public.listing_clusters    lc ON rl.listing_db_id = lc.listing_db_id
    JOIN public.cluster_air_quality aq ON lc.cluster_id    = aq.cluster_id
    JOIN public.listings_geo        lg ON rl.listing_db_id = lg.listing_db_id
    JOIN public.geo_nwi             gn ON lg.geo_id        = gn.geo_id
    WHERE
      rl.state = 'DC'
      OR (rl.state = 'MD' AND rl.county IN ('Montgomery', 'Prince George''s'))
      OR (rl.state = 'VA' AND (rl.county IN ('Arlington', 'Fairfax', 'Loudoun')
                               OR rl.city IN ('Alexandria', 'Fairfax', 'Falls Church')))
    ORDER BY rl.listing_db_id;
    """
    return pd.read_sql(load_sql, engine)


def load_nearest_bus_stops():
    load_sql = """
    SELECT
      rl.listing_db_id,
      ROUND(
        (extensions.ST_Distance(rl.geom::extensions.geography,
                                bs.geom::extensions.geography) / 1609.34)::numeric,
        2
      ) AS nearest_bus_stop_miles
    FROM public.rental_listings rl
    JOIN LATERAL (
      SELECT bs.id, bs.name, bs.geom
      FROM public.bus_stops bs
      ORDER BY
        (rl.geom::extensions.geometry)
        OPERATOR(extensions.<->)
        (bs.geom::extensions.geometry)
      LIMIT 1
    ) bs ON TRUE
    WHERE
      rl.state = 'DC'
      OR (rl.state = 'MD' AND rl.county IN ('Montgomery', 'Prince George''s'))
      OR (rl.state = 'VA' AND (rl.county IN ('Arlington', 'Fairfax', 'Loudoun')
                               OR rl.city IN ('Alexandria', 'Fairfax', 'Falls Church')));
    """
    return pd.read_sql(load_sql, engine)


def load_count_bus_stops():
    # 1 英里 = 1609.34m；先 bbox（吃 GiST 索引）再用 geography 精算
    load_sql = """
    SELECT
      rl.listing_db_id,
      COALESCE(bs_cnt.nearby_bus_stops, 0) AS nearby_bus_stops
    FROM public.rental_listings rl
    LEFT JOIN LATERAL (
      SELECT COUNT(*) AS nearby_bus_stops
      FROM public.bus_stops bs
      WHERE
        bs.geom OPERATOR(extensions.&&) extensions.ST_Expand(rl.geom, 0.02)
        AND extensions.ST_DWithin(
              rl.geom::extensions.geography,
              bs.geom::extensions.geography,
              1609.34
            )
    ) bs_cnt ON TRUE
    WHERE
      rl.state = 'DC'
      OR (rl.state = 'MD' AND rl.county IN ('Montgomery', 'Prince George''s'))
      OR (rl.state = 'VA' AND (rl.county IN ('Arlington', 'Fairfax', 'Loudoun')
                               OR rl.city IN ('Alexandria', 'Fairfax', 'Falls Church')))
    ORDER BY nearby_bus_stops DESC;
    """
    return pd.read_sql(load_sql, engine)


def load_nearest_parks():
    load_sql = """
    SELECT
      rl.listing_db_id,
      ROUND(
        (extensions.ST_Distance(rl.geom::extensions.geography,
                                os.geom::extensions.geography) / 1609.34)::numeric,
        2
      ) AS nearest_park_miles
    FROM public.rental_listings rl
    JOIN LATERAL (
      SELECT os.id, os.name, os.geom
      FROM public.open_street os
      WHERE os.leisure = 'park'
      ORDER BY
        (rl.geom::extensions.geometry)
        OPERATOR(extensions.<->)
        (os.geom::extensions.geometry)
      LIMIT 1
    ) os ON TRUE
    WHERE
      rl.state = 'DC'
      OR (rl.state = 'MD' AND rl.county IN ('Montgomery', 'Prince George''s'))
      OR (rl.state = 'VA' AND (rl.county IN ('Arlington', 'Fairfax', 'Loudoun')
                               OR rl.city IN ('Alexandria', 'Fairfax', 'Falls Church')));
    """
    return pd.read_sql(load_sql, engine)


def load_count_parks():
    load_sql = """
    SELECT
      rl.listing_db_id,
      COALESCE(pk_cnt.nearby_parks, 0) AS nearby_parks
    FROM public.rental_listings rl
    LEFT JOIN LATERAL (
      SELECT COUNT(*) AS nearby_parks
      FROM public.open_street os
      WHERE
        os.leisure = 'park'
        AND os.geom OPERATOR(extensions.&&) extensions.ST_Expand(rl.geom, 0.02)
        AND extensions.ST_DWithin(
              rl.geom::extensions.geography,
              os.geom::extensions.geography,
              1609.34
            )
    ) pk_cnt ON TRUE
    WHERE
      rl.state = 'DC'
      OR (rl.state = 'MD' AND rl.county IN ('Montgomery', 'Prince George''s'))
      OR (rl.state = 'VA' AND (rl.county IN ('Arlington', 'Fairfax', 'Loudoun')
                               OR rl.city IN ('Alexandria', 'Fairfax', 'Falls Church')))
    ORDER BY nearby_parks DESC;
    """
    return pd.read_sql(load_sql, engine)

def merge_dataframes() -> pd.DataFrame:
    rental_df = load_rental_listings()
    nearest_bus_df = load_nearest_bus_stops()
    count_bus_df = load_count_bus_stops()
    nearest_park_df = load_nearest_parks()
    count_park_df = load_count_parks()

    # Merge all dataframes
    merged_df = rental_df.merge(nearest_bus_df, on="listing_db_id", how="left")
    merged_df = merged_df.merge(count_bus_df, on="listing_db_id", how="left")
    merged_df = merged_df.merge(nearest_park_df, on="listing_db_id", how="left")
    merged_df = merged_df.merge(count_park_df, on="listing_db_id", how="left")

    merged_df.fillna(0, inplace=True)
    return merged_df


def main():
    df = merge_dataframes()
    if df.empty:
        raise Exception("No data found")

    # Log Transformation
    for feature in FEATURES_CONFIG:
        if feature.apply_log:
            df[feature.db_col] = np.log1p(df[feature.db_col])

    X = df[DB_COLUMN_NAMES]
    scaler = StandardScaler()
    scaler.fit(X)

    output_dir = os.path.join(PROJECT_ROOT, "server", "ml_models")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "scaler.gz")
    joblib.dump(scaler, output_path)
    print(f"Scaler saved to {output_path}")


if __name__ == "__main__":
    main()