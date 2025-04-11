import os
import psycopg2
from psycopg2.extras import execute_values
import json
from dotenv import load_dotenv


def import_bus_stops():
    load_dotenv()

    # Database connection
    conn = psycopg2.connect(
        host=os.getenv("db_host"),  # update as needed
        dbname=os.getenv("db_name"),  # update as needed
        user=os.getenv("db_user"),  # update as needed
        password=os.getenv("db_password"),  # update as needed,
    )
    cur = conn.cursor()

    # Prepare INSERT query
    query = """
        INSERT INTO bus_stops (id, name, lon, lat, geom)
        VALUES %s
        ON CONFLICT (id) DO NOTHING;
    """

    with open("../raw_data/bus_stops.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        stops = data["Stops"]
        print(f"Number of stops: {len(stops)}")
        # Prepare data for batch insert
        values = [
            (
                int(stop["StopID"]),
                stop["Name"],
                stop["Lon"],
                stop["Lat"],
                stop["Lon"],
                stop["Lat"],
            )
            for stop in stops
        ]
        print("Prepared data for batch insert")
        # Use execute_values for batch insert
        execute_values(
            cur,
            query,
            [(v[0], v[1], v[2], v[3], v[4], v[5]) for v in values],
            template="(%s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))",
        )
        print("Batch insert executed")

    conn.commit()
    cur.close()
    conn.close()
