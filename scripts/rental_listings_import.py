import logging
import json
import psycopg2
from utils.db_connection import DatabaseConnection


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def import_rental_listings(json_path: str):
    db_connector = DatabaseConnection()
    processed_count = 0
    inserted_count = 0
    skipped_due_to_error = 0

    try:
        logging.info(f"Attempting to load data from {json_path}")
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logging.info(f"Successfully loaded {len(data)} records from JSON file.")

    except FileNotFoundError:
        logging.error(f"Error: JSON file not found at '{json_path}'")
        return
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON file '{json_path}': {e}")
        return
    except Exception as e:
        logging.error(f"Failed to read or parse JSON file '{json_path}': {e}")
        return

    sql_insert = """
    INSERT INTO rental_listings (
        listing_id, listing_name,
        formatted_address, address_line_1, address_line_2, city, state, zip_code, county, latitude, longitude, geom,
        property_type, bedrooms, bathrooms, square_footage, year_built,
        price, status, listing_type,
        listed_date, last_seen_date, removed_date, created_date, days_on_market
    ) VALUES %s
    ON CONFLICT (listing_id) DO NOTHING;
    """

    values = []

    for item in data:
        processed_count += 1
        try:
            listing_id = item.get("id")
            if not listing_id:
                logging.warning(f"Skipping record {processed_count} due to missing 'id'")
                skipped_due_to_error += 1
                continue

            formatted_address = item.get("formattedAddress", "")

            listing_office = item.get("listingOffice")
            listing_name = None
            if listing_office and isinstance(listing_office, dict):
                listing_name = listing_office.get("name")
            else:
                listing_name = formatted_address

            address_line_1 = item.get("addressLine1", "")
            address_line_2 = item.get("addressLine2", "")
            city = item.get("city", "")
            state = item.get("state", "")
            zip_code = item.get("zipCode", "")
            county = item.get("county", "")
            latitude = item.get("latitude")
            longitude = item.get("longitude")
            geom = f"SRID=4326;POINT({longitude} {latitude})" if latitude and longitude else None

            property_type = item.get("propertyType", "")
            bedrooms = item.get("bedrooms", 0)
            bathrooms = item.get("bathrooms", 0.0)
            square_footage = item.get("lotSize", 0)
            year_built = item.get("yearBuilt", 0)

            price = item.get("price", 0)
            status = item.get("status", "")
            listing_type = item.get("listingType", "")

            listed_date = item.get("listedDate", "")
            last_seen_date = item.get("lastSeenDate", "")
            remove_date = item.get("removedDate", "")
            created_date = item.get("createdDate", "")
            days_on_market = item.get("daysOnMarket", 0)

            values.append((
                listing_id, listing_name,
                formatted_address, address_line_1, address_line_2, city, state, zip_code, county, latitude, longitude, geom,
                property_type, bedrooms, bathrooms, square_footage, year_built,
                price, status, listing_type,
                listed_date, last_seen_date, remove_date, created_date, days_on_market
            ))

        except Exception as e:
            skipped_due_to_error += 1
            logging.error(f"Record {processed_count} (ID: {item.get('id', 'N/A')}): Failed processing item: {e}", exc_info=False)

    if not values:
        logging.info("No valid records to insert.")
        return

    try:
        with db_connector as conn:
            with conn.cursor() as cur:
                psycopg2.extras.execute_values(
                    cur,
                    sql_insert,
                    values,
                    page_size=1000
                )
                inserted_count = cur.rowcount
                conn.commit()
                logging.info(f"Inserted {inserted_count} records into the database.")

    except psycopg2.Error as db_err:
        logging.error(f"Database insertion failed: {db_err}", exc_info=True)

    finally:
        logging.info(f"--- Import Summary ---")
        logging.info(f"Processed: {processed_count} records from JSON.")
        logging.info(f"Prepared for DB: {len(values)} records.")
        logging.info(f"Skipped due to errors/missing critical data: {skipped_due_to_error} records.")
        # Note: inserted_count from execute_values with ON CONFLICT DO NOTHING might not be perfectly accurate
        # for the total number of *new* rows if some conflicts occurred. It reflects rows processed/attempted by the last batch.
        logging.info(f"Rows affected by final DB command (approx): {inserted_count}")
        logging.info("----------------------")



def main():
    path = "../raw_data/dmv_rental_listings.json"
    import_rental_listings(path)


if __name__ == "__main__":
    main()
