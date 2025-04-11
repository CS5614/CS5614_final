import os
import psycopg2
from psycopg2.extras import execute_values
import json
from dotenv import load_dotenv


def import_open_street_parks():
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
        INSERT INTO open_street (lat, lon, name, leisure, geom)
        VALUES %s
        ON CONFLICT (lat, lon) DO NOTHING;
    """

    with open("../raw_data/openstreet_parks.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        elements = data["elements"]
        print(f"Number of Parks: {len(elements)}")
        # Prepare data for batch insert
        # print(elements)
        values = [
            (
                ele.get("lat"),
                ele.get("lon"),
                ele["tags"].get("name"),
                ele["tags"].get("leisure"),
                ele.get("lon"),
                ele.get("lat"),
            )
            for ele in elements
            if ele.get("tags") is not None
            and ele.get("lat") is not None
            and ele.get("lon") is not None
        ]
        print(f"Number of Parks with valid data: {len(values)}")
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
