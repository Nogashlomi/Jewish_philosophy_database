#!/usr/bin/env python3
"""
Fetch USTC data using direct API calls
"""

import requests
import json
import csv
from urllib.parse import urlencode

def fetch_ustc_data(filters=None):
    """
    Try to fetch USTC data using various API endpoints
    """

    # Try different potential API endpoints
    api_endpoints = [
        "https://www.ustc.ac.uk/api/explore",
        "https://www.ustc.ac.uk/api/editions",
        "https://www.ustc.ac.uk/api/search",
        "https://www.ustc.ac.uk/search",
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json',
    }

    params = {
        'fqyf': 1470,
        'fqyt': 1650,
        'sort_by': 'place',  # Try to sort by place
    }

    # Try each endpoint
    for endpoint in api_endpoints:
        print(f"Trying {endpoint}...")
        try:
            response = requests.get(endpoint, params=params, headers=headers, timeout=10)
            print(f"  Status: {response.status_code}")

            if response.status_code == 200:
                # Try to parse as JSON
                try:
                    data = response.json()
                    print(f"  Got JSON response with {len(data)} items")
                    return data
                except:
                    print(f"  Got response but not JSON")

        except Exception as e:
            print(f"  Error: {e}")

    return None

def get_cities_by_request(from_year, to_year):
    """
    Try to get city data by making a search request with a place filter
    """

    print(f"Fetching edition count by place for {from_year}-{to_year}...")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://www.ustc.ac.uk/explore',
    }

    # Try to search with a query that returns all results grouped by place
    urls = [
        # Try with just the explore page
        f"https://www.ustc.ac.uk/explore?fqyf={from_year}&fqyt={to_year}",

        # Try with sort parameter
        f"https://www.ustc.ac.uk/explore?fqyf={from_year}&fqyt={to_year}&sort_by=place",
    ]

    for url in urls:
        print(f"\nTrying: {url}")
        try:
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                # Look for place/city data in the response
                text = response.text

                # Look for patterns with place names and counts
                import re

                # Pattern: "place": "CityName", "count": 123
                patterns = [
                    r'"place"\s*:\s*"([^"]+)"\s*[,}].*?"count"\s*:\s*(\d+)',
                    r'"city"\s*:\s*"([^"]+)"\s*[,}].*?"count"\s*:\s*(\d+)',
                    r'"place"\s*:\s*"([^"]+)"\s*[,}].*?"editions"\s*:\s*(\d+)',
                ]

                for pattern in patterns:
                    matches = re.findall(pattern, text)
                    if matches:
                        print(f"Found {len(matches)} matches with pattern")
                        return matches

                # Alternative: look for ANY place data
                if 'place' in text.lower():
                    print("Found 'place' in response")

                    # Try to extract the JSON data structure
                    # Look for props or data structures
                    if 'props' in text or 'data' in text:
                        print("Found data structure in response")

        except Exception as e:
            print(f"Error: {e}")

    return None

def main():
    print("USTC API Data Fetcher")
    print("=" * 70)

    # Try direct API
    data = fetch_ustc_data()

    if not data:
        print("\nNo direct API found. Trying request method...")
        cities = get_cities_by_request(1470, 1650)

        if cities:
            print("\n" + "=" * 70)
            print("Cities found:")
            for city, count in cities[:20]:
                print(f"  {city}: {count}")
        else:
            print("\nNo city data extracted from requests")

    print("\n" + "=" * 70)
    print("Note: USTC website appears to use JavaScript rendering.")
    print("Recommend using Selenium or accessing through the web interface.")

if __name__ == '__main__':
    main()
