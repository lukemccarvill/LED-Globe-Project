import requests
import json
import pandas as pd


def fetch_all_countries():
    """
    Fetch all countries from OpenDataSoft API with pagination
    """
    base_url = "https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/world-administrative-boundaries-countries/records"

    all_countries = []
    offset = 0
    limit = 100  # Maximum limit per request

    print("Fetching countries from OpenDataSoft API...")

    while True:
        # Make request with pagination
        params = {
            'limit': limit,
            'offset': offset
        }

        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            records = data.get('results', [])

            if not records:
                break  # No more records to fetch

            all_countries.extend(records)
            print(f"Fetched {len(records)} countries (Total so far: {len(all_countries)})")

            # Check if we've fetched all records
            total_count = data.get('total_count', 0)
            if len(all_countries) >= total_count:
                break

            offset += limit

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            break

    print(f"\nTotal countries fetched: {len(all_countries)}")
    return all_countries


def save_to_json(countries, filename='countries.json'):
    """Save countries data to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(countries, f, indent=2, ensure_ascii=False)
    print(f"Data saved to {filename}")


def save_to_csv(countries, filename='countries.csv'):
    """Save countries data to CSV file"""
    if countries:
        # Flatten nested fields if needed
        df = pd.json_normalize(countries)
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"Data saved to {filename}")


def display_sample(countries, num=5):
    """Display sample of country data"""
    print(f"\n--- Sample of {min(num, len(countries))} countries ---")
    for i, country in enumerate(countries[:num]):
        # Try different field names that might contain country name
        name = (country.get('name') or
                country.get('country') or
                country.get('name_en') or
                country.get('label') or
                'N/A')
        iso3 = country.get('iso3', country.get('iso_3166_1_alpha_3', 'N/A'))
        print(f"{i + 1}. {name} ({iso3})")


def get_country_statistics(countries):
    """Display basic statistics about the data"""
    print(f"\n--- Data Statistics ---")
    print(f"Total countries: {len(countries)}")

    if countries:
        print(f"\nAvailable fields: {len(countries[0].keys())}")
        print("\nField names:")
        for field in sorted(countries[0].keys()):
            print(f"  - {field}")


if __name__ == "__main__":
    # Fetch all countries
    countries = fetch_all_countries()

    if countries:
        # Display sample
        display_sample(countries, num=10)

        # Show statistics
        get_country_statistics(countries)

        # Save to files
        save_to_json(countries)

        # Optionally save to CSV (requires pandas)
        try:
            save_to_csv(countries)
        except ImportError:
            print("Note: Install pandas to save as CSV (pip install pandas)")
        except Exception as e:
            print(f"Could not save CSV: {e}")
    else:
        print("\nNo countries were fetched. Please check your internet connection and try again.")