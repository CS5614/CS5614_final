import json

input_file = "./raw_data/dmv_rental_listings.json"

# Read the JSON file
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Loop through listings and print specific fields
print(len(data))