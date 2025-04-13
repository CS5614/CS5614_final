import logging
import json
import psycopg2
from utils.db_connection import DatabaseConnection


def ugm3_to_ppb(c_ugm3, molecular_weight):
    """
    Convert concentration from µg/m³ to ppb.

    Args:
        c_ugm3 (float): Concentration in µg/m³.
        molecular_weight (float): Molecular weight of the gas in g/mol.

    Returns:
        float: Concentration in ppb.
    """
    return c_ugm3 * (24.45 / molecular_weight)


def ugm3_to_ppm(c_ugm3, molecular_weight):
    """
    Convert concentration from µg/m³ to ppm.

    Args:
        c_ugm3 (float): Concentration in µg/m³.
        molecular_weight (float): Molecular weight of the gas in g/mol.

    Returns:
        float: Concentration in ppm.
    """
    return ugm3_to_ppb(c_ugm3, molecular_weight) / 1000


def calculate_aqi(concentrations):
    """
    Calculate total AQI from concentrations in µg/m³, converting to EPA units.
    Output: Total AQI, category, dominant pollutant
    """
    # Define the AQI breakpoints for each pollutant
    # AQI breakpoints (O3, SO2, NO2 in ppb; CO in ppm; PM2.5, PM10 in µg/m³)
    breakpoints = {
        'pm2_5': [
            (0.0, 12.0, 0, 50), (12.1, 35.4, 51, 100), (35.5, 55.4, 101, 150),
            (55.5, 150.4, 151, 200), (150.5, 250.4, 201, 300), (250.5, 500.4, 301, 500)
        ],
        'pm10': [
            (0, 54, 0, 50), (55, 154, 51, 100), (155, 254, 101, 150),
            (255, 354, 151, 200), (355, 424, 201, 300), (425, 604, 301, 500)
        ],
        'o3': [  # 8-hour, ppb
            (0, 54, 0, 50), (55, 70, 51, 100), (71, 85, 101, 150),
            (86, 105, 151, 200), (106, 200, 201, 300)
        ],
        'co': [  # ppm
            (0.0, 4.4, 0, 50), (4.5, 9.4, 51, 100), (9.5, 12.4, 101, 150),
            (12.5, 15.4, 151, 200), (15.5, 30.4, 201, 300), (30.5, 50.4, 301, 500)
        ],
        'so2': [  # ppb
            (0, 35, 0, 50), (36, 75, 51, 100), (76, 185, 101, 150),
            (186, 304, 151, 200), (305, 604, 201, 300), (605, 1004, 301, 500)
        ],
        'no2': [  # ppb
            (0, 53, 0, 50), (54, 100, 51, 100), (101, 360, 101, 150),
            (361, 649, 151, 200), (650, 1249, 201, 300), (1250, 2049, 301, 500)
        ]
    }

    # AQI categories
    categories = [
        (0, 50, "Good"), (51, 100, "Moderate"), (101, 150, "Unhealthy for Sensitive Groups"),
        (151, 200, "Unhealthy"), (201, 300, "Very Unhealthy"), (301, 500, "Hazardous")
    ]

    def get_aqi(cp, pollutant):
        """Calculate AQI for a pollutant, converting µg/m³ to EPA units."""
        # Convert from µg/m³ to EPA units
        if pollutant == "o3":
            cp = ugm3_to_ppb(cp, 48)  # to ppb
        elif pollutant == "co":
            cp = ugm3_to_ppm(cp, 28)  # to ppm
        elif pollutant == "so2":
            cp = ugm3_to_ppb(cp, 64)  # to ppb
        elif pollutant == "no2":
            cp = ugm3_to_ppb(cp, 46)  # to ppb
        # PM2.5, PM10 are already in µg/m³

        # Calculate AQI
        for c_lo, c_hi, i_lo, i_hi in breakpoints[pollutant]:
            if c_lo <= cp <= c_hi:
                return ((i_hi - i_lo) / (c_hi - c_lo)) * (cp - c_lo) + i_lo
        return 0  # Return 0 if below range

    # Calculate individual AQIs
    aqi_values = {}
    for pollutant, conc in concentrations.items():
        if pollutant in breakpoints:
            aqi = get_aqi(conc, pollutant)
            aqi_values[pollutant] = round(aqi)

    # Determine total AQI
    if not aqi_values:
        return None, None, None
    total_aqi = max(aqi_values.values())
    dominant_pollutant = max(aqi_values, key=aqi_values.get)

    # Determine category
    category = "Unknown"
    for aqi_lo, aqi_hi, cat in categories:
        if aqi_lo <= total_aqi <= aqi_hi:
            category = cat
            break

    return total_aqi, category, dominant_pollutant


def process_air_quality_data(api_response):
    """
    Process the air quality data from the API response format

    Parameters:
    api_response (list): The API response data

    Returns:
    dict: Dictionary containing extracted data
    """
    result = {}
    data = api_response[0]
    aqi, category, _ = calculate_aqi(data["components"])

    result["aqi"] = aqi
    result["category"] = category
    return result

def read_and_import():
    # Read file
    with open("../raw_data/air_quality_data.json", "r") as f:
        data = json.load(f)

    # Connect to the database
    db_connection = DatabaseConnection()
    insert_sql = """
    INSERT INTO cluster_air_quality (
        cluster_id, aqi, category
    )
    VALUES(%s, %s, %s)
    """
    try:
        with db_connection as conn:
            with conn.cursor() as cursor:
                for item in data:
                    cluster_id = item.get("cluster_id")
                    air_quality_data = item.get("air_quality_data")
                    output_json = process_air_quality_data(air_quality_data)

                    try:
                        cursor.execute(
                            insert_sql,
                            (
                                cluster_id,
                                output_json["aqi"],
                                output_json["category"]
                            )
                        )
                        logging.info(f"Inserted air quality data for cluster ID {cluster_id} into the database.")
                    except psycopg2.Error as e:
                        logging.error(f"Error inserting data for cluster ID {cluster_id}: {e}")
                        # Rollback the transaction for this item
                        conn.rollback()
                        continue  # Continue with the next item

                # Commit all successful inserts at once
                conn.commit()

    except psycopg2.Error as e:
        logging.error(f"Database connection error: {e}")
    finally:
        # Ensure connection is closed properly
        db_connection.__exit__(None, None, None)


def main():
    read_and_import()


if __name__ == "__main__":
    main()