from typing import Dict, List
from fastapi import APIRouter, HTTPException
from ..utils.db_connection import DatabaseConnection
from psycopg2.extras import RealDictCursor

# Fix the prefix - there's a typo in "listing_is" that should be "listing_id"
router = APIRouter(prefix="/api/busStopsInOneMiles", tags=["busStopsInOneMiles"])


# Add a proper path parameter in the route
@router.get("/{listing_id}", response_model=Dict)
async def get_bus_stops_within_miles(listing_id: str) -> Dict:
    try:
        # 1) Open connection + real-dict cursor
        with DatabaseConnection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                sql = """
                    SELECT
                    STRING_AGG(bs.name, ', ') AS nearby_bus_stops
                    FROM
                    public.rental_listings rl
                    JOIN
                    public.bus_stops bs
                    ON ST_DWithin(rl.geom, bs.geom, 0.0145)
                    WHERE rl.listing_db_id = %s
                    GROUP BY
                    rl.listing_db_id;
                    """
                # Use parameterized query for security
                cur.execute(sql, (listing_id,))
                records: Dict = cur.fetchone()

                if not records:
                    raise HTTPException(
                        status_code=404,
                        detail=f"No bus stops found for listing ID: {listing_id}",
                    )

        return records
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching bus stops: {str(e)}"
        )
