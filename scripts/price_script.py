import requests
import json

import load_dotenv
import os
load_dotenv.load_dotenv()

limit = 500
offset = 0
data_list = []

while True:
    url = f"https://api.rentcast.io/v1/listings/rental/long-term?state=DC&status=Active&limit={limit}&offset={offset}"
    headers = {
        "accept": "application/json",
        "X-Api-Key": os.getenv("RENTAL_API_KEY"),
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        break

    data = response.json()

    data_list.extend(data)

    if len(data) < limit:
        break

    offset += limit


# Save the data to a JSON file
output_file = "dc_rental_listings.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(data_list, f, ensure_ascii=False, indent=4)