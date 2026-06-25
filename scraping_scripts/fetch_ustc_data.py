#!/usr/bin/env python3
"""
Fetch USTC quantitative data for European editions (1470-1650) in 20-year intervals
"""

import requests
from bs4 import BeautifulSoup
import re
import csv
from datetime import datetime

# Base URL for USTC search
BASE_URL = "https://www.ustc.ac.uk/explore"

def get_edition_count(from_year, to_year):
    """
    Fetch the number of editions for a given year range
    """
    params = {
        'fqyf': from_year,
        'fqyt': to_year
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()

        # Parse HTML to find "Showing X-Y of Z results"
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()

        # Look for "Showing 1-20 of XXXXXX results" pattern
        match = re.search(r'Showing \d+-\d+ of ([\d,]+) results', text)
        if match:
            count_str = match.group(1).replace(',', '')
            return int(count_str)
        else:
            print(f"Could not find count in response for {from_year}-{to_year}")
            return None

    except Exception as e:
        print(f"Error fetching data for {from_year}-{to_year}: {e}")
        return None

def main():
    print("Fetching USTC data for European editions (1470-1650)...")
    print("=" * 60)

    data = []

    # 20-year intervals from 1470 to 1650
    start_year = 1470
    end_year = 1650
    interval = 20

    for year in range(start_year, end_year, interval):
        from_year = year
        to_year = min(year + interval - 1, end_year)

        print(f"\nFetching data for {from_year}-{to_year}...", end=" ", flush=True)

        count = get_edition_count(from_year, to_year)
        if count is not None:
            print(f"✓ {count:,} editions")
            data.append({
                'period': f"{from_year}-{to_year}",
                'from_year': from_year,
                'to_year': to_year,
                'count': count
            })
        else:
            print("✗ Failed to retrieve")

    # Save to CSV
    output_file = '/Users/nogashlomi/projects/yossi/RDF_project_copy/ustc_europe_1470_1650.csv'

    print("\n" + "=" * 60)
    print(f"\nSaving data to {output_file}...")

    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['period', 'from_year', 'to_year', 'count'])
        writer.writeheader()
        writer.writerows(data)

    print(f"✓ Data saved successfully!")
    print("\nSummary:")
    print("-" * 40)
    for row in data:
        print(f"{row['period']}: {row['count']:>8,} editions")

    total = sum(row['count'] for row in data)
    print("-" * 40)
    print(f"{'TOTAL':20}: {total:>8,} editions")

if __name__ == '__main__':
    main()
