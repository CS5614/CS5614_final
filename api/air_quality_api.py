import requests
import json
import os
from dotenv import load_dotenv
import logging
import psycopg2
from utils.db_connection import DatabaseConnection

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def load_coordinates_from_db():
    """
    Query the database for rental clusters and coordinates of centroids.
    """
    db_connector = DatabaseConnection()
    rows = []
    sql_search = """
    SELECT DISTINCT(lc.cluster_id), rc.centroid_lat, rc.centroid_lon
    FROM rental_listings rl
    JOIN listing_clusters lc ON rl.listing_db_id = lc.listing_db_id
    JOIN rental_clusters rc ON lc.cluster_id = rc.cluster_id
    ORDER BY lc.cluster_id;
    """
    try:
        with db_connector as conn:
            with conn.cursor() as cur:
                cur.execute(sql_search)
                rows = cur.fetchall()
                if not rows:
                    print("No data found in the database.")
                    return []

                print(f"Fetched {len(rows)} records from the database.")
                return rows
    except psycopg2.Error as db_err:
        logging.error(f"Error fetching data from the database: {db_err}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return None

def fetch_air_quality_data(lat, lon):
    """
    Fetch air quality data from the AirNow API.

    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.

    Returns:
        dict: Air quality data.
    """
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={os.getenv("AIR_QUALITY_KEY")}"

    response = requests.get(url)

    if response.status_code != 200:
        logging.error(f"An unexpected error occurred status code: {response.status_code}")
        logging.error(f"message: {response.text}")
        return None
    data = response.json()
    return data



def main():
    result = load_coordinates_from_db()
    if not result:
        logging.error("No data found in the database.")
        return

    output = []
    for row in result:
        cluster_id, lat, lon = row[0], float(row[1]), float(row[2])
        air_quality_data = fetch_air_quality_data(lat, lon)
        if air_quality_data is None:
            logging.error(f"Failed to fetch air quality data for coordinates: {lat}, {lon}")
            continue
        output.append(
            {
                "cluster_id": cluster_id,
                "air_quality_data": air_quality_data.get("list")
            }
        )
        logging.info(f"Air quality data for cluster ID {cluster_id} obtained successfully.")

    with open("../raw_data/air_quality_data.json", "w") as f:
        json.dump(output, f, indent=4)

if __name__ == "__main__":
    main()

