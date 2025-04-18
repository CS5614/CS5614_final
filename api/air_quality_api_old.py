import requests
import json
import os
import logging
import psycopg2
from dotenv import load_dotenv
from typing import List, Optional
from utils.db_connection import DatabaseConnection
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_coordinates_from_db(batch_size: int, last_processed_id: int) -> Optional[List[tuple]]:
    db_connector = DatabaseConnection()
    rows = []
    logging.debug(f"Fetching batch of size {batch_size} after ID {last_processed_id}...")
    search_sql = """
    SELECT cluster_id, centroid_lat, centroid_lon
    FROM rental_clusters
    WHERE cluster_id > %s
        AND centroid_lat IS NOT NULL
        AND centroid_lon IS NOT NULL
    ORDER BY cluster_id
    LIMIT %s;
    """

    try:
        with db_connector as conn:
            with conn.cursor() as cur:
                cur.execute(search_sql, (last_processed_id, batch_size))
                rows = cur.fetchall()

        if rows:
            logging.info(f"Fetched {len(rows)} rows from the database.")
        else:
            logging.debug("No more rows to fetch from the database.")
        return rows

    except psycopg2.Error as db_err:
        logging.error(f"Error fetching data from the database: {db_err}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return None



def fetch_air_quality():
    load_dotenv()
    batch_size = 1000
    last_id = 0
    total_processed = 0

    # Rate Limiting Variables
    request_count = 0          # Counter for API requests made
    api_call_limit = 500       # Pause after this many requests
    sleep_duration_minutes = 60
    sleep_duration_seconds = sleep_duration_minutes * 60

    output_json = []

    while True:
        batch_coordinates = load_coordinates_from_db(batch_size, last_id)

        # Handle potential database errors
        if batch_coordinates is None:
            logging.error("Failed to get batch from database. Stopping...")
            break

        # Stop if no more coordinates are returned
        if not batch_coordinates:
            logging.info("No more coordinates to process. Successfully completed.")
            break

        for cluster_id, lat, lon in batch_coordinates:

            # Rate limiting logic
            if request_count > 0 and request_count % api_call_limit == 0:
                 logging.warning(f"Reached {request_count} API requests. Pausing for {sleep_duration_minutes} minutes...")
                 time.sleep(sleep_duration_seconds)
                 logging.info("Resuming API requests...")

            # Increment request counter
            request_count += 1

            air_quality_data = fetch_air_quality_helper(cluster_id, lat, lon)
            if air_quality_data:
                output_json.append({
                    "cluster_id": cluster_id,
                    "centroid_lat": lat,
                    "centroid_lon": lon,
                    "air_quality": air_quality_data
                })

        last_id = batch_coordinates[-1][0]
        total_processed += len(batch_coordinates)
        logging.info(f"Batch finished. Total processed so far: {total_processed}. Total API calls: {request_count}")


    logging.info(f"Total processed coordinates: {total_processed}")
    logging.info(f"Total API requests made: {request_count}")
    return output_json


def fetch_air_quality_helper(cluster_id: int, lat: float, lon: float, distance: int = 25):
    try:
        uri = f"https://www.airnowapi.org/aq/observation/latLong/current/?format=application/json&latitude={lat}&longitude={lon}&distance={distance}&API_KEY={os.getenv("AIR_QUALITY_KEY")}"
        response = requests.get(uri)
        response.raise_for_status()

        # Parse the response
        data = response.json()

        if not data:
            logging.info(f"No air quality data found for cluster_id ID {cluster_id}.")
            return None

        air_quality = {
            "o3": 0,
            "pm25": 0,
            "pm10": 0
        }
        # Iterate through returned parameters to find the ones we want
        for reading in data:
            param = reading.get("ParameterName")
            aqi = reading.get("AQI")
            if aqi:
                if param == "O3":
                    air_quality["o3"] = aqi
                elif param == "PM2.5":
                    air_quality["pm25"] = aqi
                elif param == "PM10": # Note: PM10 might not always be present
                    air_quality["pm10"] = aqi

        # Check if we found at least one relevant measurement
        if not air_quality or all(v is None for v in air_quality.values()):
             logging.debug(f"Relevant AQI parameters (O3, PM2.5, PM10) not found for listing ID {cluster_id} ({lat},{lon}). Full data: {data}")
             return None

        logging.debug(f"Successfully fetched AQ data for listing ID {cluster_id}: {air_quality}")
        return air_quality

    except requests.exceptions.RequestException as e:
        logging.error(f"Request error: {e}")



def main():
    logging.warning(f"Initial pause due to recent API limit. Sleeping for {70} minutes...")
    time.sleep(70 * 60)
    logging.info("Initial pause finished. Starting fetch process...")
    results = fetch_air_quality()
    if results:
        with open("../raw_data/air_quality_results_old.json", "w") as f:
            json.dump(results, f, indent=4)
        logging.info("Results saved to air_quality_results_old.json")

if __name__ == "__main__":
    main()