import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

STATE = ["DC", "VA", "MD", "WV"]

def fetch_rental_listings(state, limit=500, offset=0) -> list:
    """
    Fetch rental listings from the RentCast API.

    Args:
        state (str): The state to filter listings by.
        limit (int): The number of listings to fetch.
        offset (int): The offset for pagination.

    Returns:
        list: A list of rental listings.
    """
    listings = []

    while True:
        url = f"https://api.rentcast.io/v1/listings/rental/long-term?state={state}&status=Active&limit={limit}&offset={offset}"
        headers = {
            "accept": "application/json",
            "X-Api-Key": os.getenv("RENTAL_API_KEY"),
        }
        
        print(f"Fetching {state} listings with offset {offset}...")
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            print(response.text)
            break
        
        data = response.json()
        listings.extend(data)
        print(f"Retrieved {len(data)} listings for {state}")
        
        # Check if we are at the last page
        if len(data) < limit:
            break
        
        # Move to the next page
        offset += limit
    
    return listings


def main():
    """
    Main function to fetch rental listings for multiple states and save them to a JSON file.
    """
    all_listings = []

    for state in STATE:
        # Fetch rental listings for each state
        print(f"Fetching rental listings for {state}...")
        rental_listings = fetch_rental_listings(state)
        all_listings.extend(rental_listings)
        print(f"Total listings fetched for {state}: {len(rental_listings)}")

    # Get the path to current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Go up one directory to parent directory
    parent_dir = os.path.dirname(current_dir)

    # Create the raw_data directory if it doesn't exist
    output_dir = os.path.join(parent_dir, "raw_data")

    # Create the output file path
    output_file = os.path.join(output_dir, "dmv_rental_listings.json")

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_listings, f, ensure_ascii=False, indent=4)
        print(f"Data successfully saved to {output_file}")
    except Exception as e:
        print(f"Error saving data: {e}")
        # Fallback to saving in the current directory
        fallback_file = os.path.join(current_dir, "dmv_rental_listings.json")
        print(f"Attempting to save to script directory as {fallback_file}")
        with open(fallback_file, "w", encoding="utf-8") as f:
            json.dump(all_listings, f, ensure_ascii=False, indent=4)
        print(f"Data saved to {fallback_file}")

if __name__ == "__main__":
    main()

