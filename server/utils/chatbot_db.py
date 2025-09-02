from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine
from ..config.general_config import settings


def get_db_connection():
    """
    建立 LangChain 的 SQLDatabase 物件，
    明確指定 schema 並提供要載入欄位結構的資料表清單。
    """
    engine = create_engine(settings.database_url)

    included_tables = [
        "bus_stops",
        "cluster_air_quality",
        "crime_reports",
        "geo_nwi",
        "listing_clusters",
        "listings_geo",
        "listings_qol",
        "open_street",
        "place_review",
        "rental_clusters",
        "rental_listings"
    ]
    db = SQLDatabase(
        engine=engine,
        schema="public",
        include_tables=included_tables,
        sample_rows_in_table_info=2
    )

    print(f"Usable tables initialized for LangChain: {db.get_usable_table_names()}")

    return db