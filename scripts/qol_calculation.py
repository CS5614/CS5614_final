from itertools import count

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

from utils.db_engine import DBEngine

db = DBEngine()
engine = db.get_engine()

def load_rental_listings():
    load_sql = """
    SELECT rl.listing_db_id, rl.latitude, rl.longitude, rl.price, aq.aqi, gn.nwi_score
    FROM rental_listings rl
    JOIN listing_clusters lc on rl.listing_db_id = lc.listing_db_id
    JOIN cluster_air_quality aq on lc.cluster_id = aq.cluster_id
    JOIN listings_geo lg on rl.listing_db_id = lg.listing_db_id
    JOIN geo_nwi gn on lg.geo_id = gn.geo_id

    WHERE
      rl.state = 'DC'
      OR
      (rl.state = 'MD' AND rl.county IN ('Montgomery', 'Prince George''s'))
      OR
      (rl.state = 'VA' AND (rl.county IN ('Arlington', 'Fairfax', 'Loudoun')
                         OR rl.city IN ('Alexandria', 'Fairfax', 'Falls Church')
                        )
      )
    ORDER BY lc.listing_db_id;
    """

    rental_units = pd.read_sql(load_sql, engine)
    return rental_units

def load_nearest_bus_stops():
    load_sql = """
    SELECT
      rl.listing_db_id,
        ROUND((ST_Distance(rl.geom::geography, bs.geom::geography) / 1609.34)::numeric, 2) AS nearest_bus_stop_miles
    FROM
      public.rental_listings rl
    JOIN LATERAL (
      SELECT bs.id, bs.name, bs.geom
      FROM public.bus_stops bs
      ORDER BY rl.geom <-> bs.geom  -- KNN search: uses spatial index!
      LIMIT 1
    ) bs ON TRUE
    WHERE
      state = 'DC'
      OR
      (state = 'MD' AND county IN ('Montgomery', 'Prince George''s'))
      OR
      (state = 'VA' AND (county IN ('Arlington', 'Fairfax', 'Loudoun')
                         -- Assuming independent cities are stored in the 'county' or a similar field, adjust as needed:
                         OR city IN ('Alexandria', 'Fairfax', 'Falls Church')
                        )
      );
    """

    nearest_bus_stops = pd.read_sql(load_sql, engine)
    return nearest_bus_stops

def load_count_bus_stops():
    load_sql = """
    SELECT
      rl.listing_db_id,
      COUNT(bs.id) AS nearby_bus_stops
    FROM
      public.rental_listings rl
    LEFT JOIN
      public.bus_stops bs
      ON ST_DWithin(rl.geom, bs.geom, 0.0145)
    WHERE
      state = 'DC'
      OR
      (state = 'MD' AND county IN ('Montgomery', 'Prince George''s'))
      OR
      (state = 'VA' AND (county IN ('Arlington', 'Fairfax', 'Loudoun')
                         -- Assuming independent cities are stored in the 'county' or a similar field, adjust as needed:
                         OR city IN ('Alexandria', 'Fairfax', 'Falls Church')
                        )
      )
    GROUP BY
      rl.listing_db_id,
      rl.listing_name
    ORDER BY
      nearby_bus_stops DESC;
    """
    count_bus_stops = pd.read_sql(load_sql, engine)
    return count_bus_stops

def load_count_parks():
    load_sql = """
    SELECT
      rl.listing_db_id,
      COUNT(os.id) AS nearby_parks
    FROM
      rental_listings rl
    LEFT JOIN
      open_street os
      ON ST_DWithin(rl.geom, os.geom, 0.0145)
    WHERE
      state = 'DC'
      OR
      (state = 'MD' AND county IN ('Montgomery', 'Prince George''s'))
      OR
      (state = 'VA' AND (county IN ('Arlington', 'Fairfax', 'Loudoun')
                         -- Assuming independent cities are stored in the 'county' or a similar field, adjust as needed:
                         OR city IN ('Alexandria', 'Fairfax', 'Falls Church')
                        )
      )
    GROUP BY
      rl.listing_db_id
    ORDER BY
      nearby_parks DESC;
    """
    count_parks = pd.read_sql(load_sql, engine)
    return count_parks

def load_nearest_parks():
    load_sql = """
    SELECT
      rl.listing_db_id,
      ROUND((ST_Distance(rl.geom::geography, os.geom::geography) / 1609.34)::numeric, 2) AS nearest_park_miles
    FROM
      rental_listings rl
    JOIN LATERAL (
      SELECT os.id, os.name, os.geom
      FROM open_street os
      WHERE os.leisure = 'park'
      ORDER BY rl.geom <-> os.geom  -- fast KNN using index
      LIMIT 1
    ) os ON TRUE
    WHERE
      state = 'DC'
      OR
      (state = 'MD' AND county IN ('Montgomery', 'Prince George''s'))
      OR
      (state = 'VA' AND (county IN ('Arlington', 'Fairfax', 'Loudoun')
                         -- Assuming independent cities are stored in the 'county' or a similar field, adjust as needed:
                         OR city IN ('Alexandria', 'Fairfax', 'Falls Church')
                        )
      );
    """
    nearest_parks = pd.read_sql(load_sql, engine)
    return nearest_parks



def merge_dataframes():
    rental_df = load_rental_listings()
    nearest_bus_df = load_nearest_bus_stops()
    count_bus_df = load_count_bus_stops()
    count_parks_df = load_count_parks()
    nearest_parks_df = load_nearest_parks()
    # Merge all dataframes on listing_db_id
    merged_df = rental_df.merge(nearest_bus_df, on="listing_db_id", how="left")
    merged_df = merged_df.merge(count_bus_df, on="listing_db_id", how="left")
    merged_df = merged_df.merge(count_parks_df, on="listing_db_id", how="left")
    merged_df = merged_df.merge(nearest_parks_df, on="listing_db_id", how="left")
    return merged_df



def compute_qol():
    # Load the data
    df = merge_dataframes()

    # Log transforms
    df["price"] = np.log1p(df["price"])
    df["nearest_bus_stop_miles"] = np.log1p(df["nearest_bus_stop_miles"])
    df["nearest_park_miles"] = np.log1p(df["nearest_park_miles"])

    # features
    features = [
        "price",
        "aqi",
        "nwi_score",
        "nearest_bus_stop_miles",
        "nearby_bus_stops",
        "nearby_parks",
        "nearest_park_miles"
    ]
    X = df[features]

    # Standardize the features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    df_scaled = pd.DataFrame(X_scaled, columns=features)

    # Invert direction of the features
    df_scaled["aqi"] *= -1
    df_scaled["nearest_bus_stop_miles"] *= -1
    df_scaled["nearest_park_miles"] *= -1

    # Perform PCA
    pca = PCA(n_components=len(features))
    pca.fit(df_scaled)
    pc1 = pca.components_[0]
    abs_loadings = np.abs(pc1)
    weights = abs_loadings / np.sum(abs_loadings)

    # Calculate the Quality of Life (QoL) score
    df_qol = pd.DataFrame({
        "listing_db_id": df["listing_db_id"],
        "qol_score": np.dot(df_scaled, weights)
    })

    return df_qol



def main():
    df_qol = compute_qol()
    # Save the QoL scores to the database
    df_qol.to_sql(
        "listings_qol",
        engine,
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=1000
    )



if __name__ == "__main__":
    main()