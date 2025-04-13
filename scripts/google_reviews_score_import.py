import os
import asyncio
import aiohttp
import asyncpg
import json
from dotenv import load_dotenv


async def fetch_place_id(session, listing_name):
    url = "https://places.googleapis.com/v1/places:searchText"
    payload = json.dumps({"textQuery": listing_name})
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": os.getenv("GOOGLE_API_KEY"),
        "X-Goog-FieldMask": "places.id",
    }
    async with session.post(url, headers=headers, data=payload) as response:
        response_json = await response.json()
        if "places" in response_json and response_json["places"]:
            return response_json["places"][0]["id"]
    return None


async def fetch_rating(session, place_id):
    url = f"https://places.googleapis.com/v1/places/{place_id}"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": os.getenv("GOOGLE_API_KEY"),
        "X-Goog-FieldMask": "rating",
    }
    async with session.get(url, headers=headers) as response:
        json_response = await response.json()
        return json_response.get("rating")


async def import_google_reviews_score():
    load_dotenv()
    # Create a connection pool
    pool = await asyncpg.create_pool(
        host=os.getenv("db_host"),
        database=os.getenv("db_name"),
        user=os.getenv("db_user"),
        password=os.getenv("db_password"),
        min_size=1,
        max_size=10,  # Adjust based on your workload
    )

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT DISTINCT listing_db_id, listing_name FROM rental_listings;
            """
        )
        print(f"Number of listings: {len(rows)}")

    async with aiohttp.ClientSession() as session:
        tasks = []
        for row in rows:
            listing_id = row["listing_db_id"]
            listing_name = row["listing_name"]
            tasks.append(process_listing(session, pool, listing_id, listing_name))

        await asyncio.gather(*tasks)

    await pool.close()
    print("Google reviews score imported successfully.")


async def process_listing(session, pool, listing_id, listing_name):
    # Fetch place ID
    place_id = await fetch_place_id(session, listing_name)
    if not place_id:
        return

    # Fetch rating
    rating = await fetch_rating(session, place_id)
    if rating is None:
        return

    # Insert into database using a connection from the pool
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO place_review (place_name, place_id, listing_id, rating)
            VALUES ($1, $2, $3, $4)
            """,
            listing_name,
            place_id,
            listing_id,
            rating,
        )
