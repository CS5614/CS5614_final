import requests
import json
import os
import logging
import psycopg2
from dotenv import load_dotenv
from typing import List, Optional
from utils.db_connection import DatabaseConnection

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_coordinates_from_db(batch_size: int, last_processed_id: int) -> Optional[List[tuple]]:
    db_connector = DatabaseConnection()
    rows = []
    logging.debug(f"Fetching batch of size {batch_size} after ID {last_processed_id}...")
    search_sql = """
    SELECT listing_db_id, latitude, longitude
    FROM rental_listings
    WHERE listing_db_id > %s
        AND latitude IS NOT NULL
        AND longitude IS NOT NULL
    ORDER BY listing_db_id
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

    output_json = []

    while True:
        batch_coordinates = load_coordinates_from_db(batch_size, last_id)

        for id, lat, lon in batch_coordinates:
            air_quality_data = fetch_air_quality_helper(id, lat, lon)
            if air_quality_data:
                output_json.append({
                    "latitude": lat,
                    "longitude": lon,
                    "air_quality": air_quality_data
                })

        if batch_coordinates is None:
            logging.error("Failed to get batch from database. Stopping...")
            break

        if not batch_coordinates:
            logging.info("No more coordinates to process. Stopping...")
            break

        logging.info(f"Processing batch of {len(batch_coordinates)} coordinates...")

        last_id = batch_coordinates[-1][0]
        total_processed += len(batch_coordinates)

    logging.info(f"Total processed coordinates: {total_processed}")
    return output_json


def fetch_air_quality_helper(listing_db_id: int, lat: float, lon: float, distance: int = 25):
    try:
        uri = f"https://www.airnowapi.org/aq/observation/latLong/current/?format=application/json&latitude={lat}&longitude={lon}&distance={distance}&API_KEY={os.getenv("AIR_QUALITY_KEY")}"
        response = requests.get(uri)
        response.raise_for_status()

        # Parse the response
        data = response.json()

        if not data:
            logging.info(f"No air quality data found for listing ID {id}.")
            return None

        air_quality = {}
        # Iterate through returned parameters to find the ones we want
        for reading in data:
            param = reading.get("ParameterName")
            aqi = reading.get("AQI")
            if param == "O3":
                air_quality["o3"] = aqi
            elif param == "PM2.5":
                air_quality["pm25"] = aqi
            elif param == "PM10": # Note: PM10 might not always be present
                air_quality["pm10"] = aqi

        # Check if we found at least one relevant measurement
        if not air_quality or all(v is None for v in air_quality.values()):
             logging.debug(f"Relevant AQI parameters (O3, PM2.5, PM10) not found for listing ID {listing_db_id} ({lat},{lon}). Full data: {data}")
             return None

        logging.debug(f"Successfully fetched AQ data for listing ID {listing_db_id}: {air_quality}")
        return air_quality

    except requests.exceptions.RequestException as e:
        logging.error(f"Request error: {e}")



def main():
    result = fetch_air_quality()
    print(result)

if __name__ == "__main__":
    main()