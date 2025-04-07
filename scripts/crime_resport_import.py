import os
import psycopg2
from psycopg2.extras import execute_values
import json
from dotenv import load_dotenv
import csv
from datetime import datetime


def import_crime_reports():
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
        INSERT INTO crime_reports (name, date, lat, lon, geom)
        VALUES %s
        ON CONFLICT (id) DO NOTHING;
    """
    with open("../raw_data/Crime_Incidents_in_2023.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        ##REPORT_DAT 2023/03/24 06:36:26+00
        values = list(
            map(
                lambda row: (
                    row["OFFENSE"],
                    datetime.strptime(row["REPORT_DAT"], "%Y/%m/%d %H:%M:%S+00"),
                    row["LATITUDE"],
                    row["LONGITUDE"],
                    row["LONGITUDE"],
                    row["LATITUDE"],
                ),
                filter(
                    lambda row: row["LATITUDE"]
                    and row["LONGITUDE"],  # Filter out rows with null lat/lon
                    reader,
                ),
            )
        )
        print(f"Number of records: {len(values)}")
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
