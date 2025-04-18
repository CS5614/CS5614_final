import requests
import logging
import psycopg2
from utils.db_connection import DatabaseConnection
import pyproj
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_listing_batch(connection, batch_size, last_id):
    """Fetch rental listings from the database in batches."""
    sql = """
        SELECT listing_db_id, latitude, longitude
        FROM rental_listings
        WHERE listing_db_id > %s
            AND latitude IS NOT NULL
            AND longitude IS NOT NULL
        ORDER BY listing_db_id
        LIMIT %s;
    """


    try:
        with connection as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (last_id, batch_size))
                rows = cur.fetchall()
                if not rows:
                    logging.info("No more listings to process.")
                    return []

                logging.info(f"Fetched {len(rows)} listings from the database.")
                return rows
    except psycopg2.Error as db_err:
        logging.error(f"Error fetching data from the database: {db_err}")
        return None

def get_walkability_index(lat, lon):
    """Calls EPA API for national walkability index and GEOID10 using latitude and longitude."""
    try:
        projector = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        x, y = projector.transform(lon, lat)

        url = "https://geodata.epa.gov/arcgis/rest/services/OA/WalkabilityIndex/MapServer/0/query"
        params = {
            "geometry": f"{x},{y}",
            "geometryType": "esriGeometryPoint",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "NatWalkInd,GEOID10",
            "returnGeometry": "false",
            "f": "json"
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data and data.get("features") and len(data["features"]) > 0:
            attributes = data["features"][0].get("attributes", {})
            if attributes:
                geo_id = attributes.get("GEOID10")
                nwi = attributes.get("NatWalkInd")
                return {"geo_id": str(geo_id), "nwi_score": nwi}
            else:
                logging.error("No attributes found in the response.")
                return None
        else:
            logging.error("No features found in the response.")
            return None
    except requests.RequestException as e:
        logging.error(f"Error fetching walkability index: {e}")
        return None

def bulk_insert_geo_nwi(connection, data_list):
    sql = """
        INSERT INTO geo_nwi (geo_id, nwi_score)
        VALUES %s
        ON CONFLICT (geo_id) DO NOTHING;
    """
    try:
        with connection as conn:
            with conn.cursor() as cur:
                psycopg2.extras.execute_values(cur, sql, data_list)
                conn.commit()
                logging.info(f"Inserted {len(data_list)} records into geo_nwi.")

    except psycopg2.Error as db_err:
        logging.error(f"Error inserting data into geo_nwi: {db_err}")
        conn.rollback()

def bulk_insert_assignments(connection, data_list):
    sql = """
        INSERT INTO listings_geo (listing_db_id, geo_id)
        VALUES %s
        ON CONFLICT (listing_db_id) DO NOTHING;
    """
    try:
        with connection as conn:
            with conn.cursor() as cur:
                psycopg2.extras.execute_values(cur, sql, data_list)
                conn.commit()
                logging.info(f"Inserted {len(data_list)} records into walkability_assignments.")

    except psycopg2.Error as db_err:
        logging.error(f"Error inserting data into walkability_assignments: {db_err}")
        conn.rollback()

def process_all_listings():
    """Main function to process all rental listings."""
    batch_size = 1000
    walkability_data = {}
    assignments_data = []

    last_processed_id = 0
    total_processed_count = 0
    db_connector = DatabaseConnection()

    try:
        with db_connector as conn:
            while True:
                batch = fetch_listing_batch(conn, batch_size, last_processed_id)

                if not batch: break

                logging.info(f"Processing batch of {len(batch)} listings after ID {last_processed_id}...")

                for listing_id, lat, lon in batch:
                    api_result = get_walkability_index(lat, lon)

                    if api_result:
                        fetched_geo_id = api_result.get("geo_id")
                        fetched_nwi = api_result.get("nwi_score")

                        if fetched_geo_id not in walkability_data:
                            walkability_data[fetched_geo_id] = fetched_nwi

                        assignments_data.append((listing_id, fetched_geo_id))
                        logging.info(f"Fetched walkability index for listing ID {listing_id}: {fetched_nwi}")
                    else:
                        logging.error(f"Failed to fetch walkability index for listing ID {listing_id} with lat {lat} and lon {lon}")

                    # Avoid too many API calls in a short time
                    time.sleep(0.01)

                # Bulk insert after processing each batch
                geo_nwi_list = list(walkability_data.items())
                bulk_insert_geo_nwi(conn, geo_nwi_list)
                bulk_insert_assignments(conn, assignments_data)

                # Update last processed ID
                last_processed_id = batch[-1][0]
                total_processed_count += len(batch)
                logging.info(f"Processed {total_processed_count} listings so far...")

    except psycopg2.Error as db_err:
        logging.error(f"Database error: {db_err}")


def main():
    process_all_listings()

if __name__ == "__main__":
    main()




