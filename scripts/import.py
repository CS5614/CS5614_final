## call bus_stops_import.py, openstreet_map.py, and bus_stops_import.py

import asyncio
import bus_stops_import
import openstreet_parks_import
import crime_reports_import
from google_reviews_score_import import import_google_reviews_score


if __name__ == "__main__":
    bus_stops_import.import_bus_stops()
    openstreet_parks_import.import_open_street_parks()
    crime_reports_import.import_crime_reports()
    asyncio.run(import_google_reviews_score())

