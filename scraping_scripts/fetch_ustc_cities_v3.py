#!/usr/bin/env python3
"""
Fetch USTC data by city - Version 3
Query each known major printing city individually
"""

import time
import csv
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

def setup_driver():
    """Setup Chrome WebDriver"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def get_city_count(driver, city_name, from_year=1470, to_year=1650):
    """Get the number of editions for a specific city"""

    try:
        # Build URL with place filter
        # Note: The place parameter might be fqp or similar
        url = f"https://www.ustc.ac.uk/explore?fqp={city_name}&fqyf={from_year}&fqyt={to_year}"

        driver.get(url)

        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        time.sleep(1)

        # Get page text and look for "Showing X-Y of Z results"
        page_text = driver.find_element(By.TAG_NAME, "body").text

        # Extract count
        match = re.search(r'Showing \d+-\d+ of ([\d,]+) results', page_text)
        if match:
            count_str = match.group(1).replace(',', '')
            return int(count_str)

        # Try alternative pattern
        match = re.search(r'of ([\d,]+) results', page_text)
        if match:
            count_str = match.group(1).replace(',', '')
            return int(count_str)

        return 0

    except Exception as e:
        print(f"  Error querying {city_name}: {e}")
        return 0

def main():
    print("Fetching USTC data by city - Version 3")
    print("Querying known European printing cities (1470-1650)")
    print("=" * 70)

    # Major European printing cities in the 15th-17th centuries
    major_cities = [
        # Italy
        "Venice",
        "Milan",
        "Florence",
        "Rome",
        "Naples",
        "Bologna",
        "Padua",

        # Germany
        "Strasbourg",
        "Cologne",
        "Frankfurt",
        "Nuremberg",
        "Augsburg",
        "Wittenberg",
        "Leipzig",
        "Mainz",

        # France
        "Paris",
        "Lyon",
        "Rouen",
        "Toulouse",

        # Low Countries
        "Antwerp",
        "Amsterdam",
        "Brussels",
        "Bruges",

        # Spain
        "Seville",
        "Toledo",
        "Salamanca",
        "Barcelona",

        # Portugal
        "Lisbon",

        # Other
        "Basel",
        "Zurich",
        "Geneva",
        "Prague",
        "Vienna",
        "London",
        "Edinburgh",
        "Dublin",
    ]

    driver = setup_driver()
    cities_data = {}

    try:
        for city in major_cities:
            print(f"Querying {city:20}", end=" ... ", flush=True)

            count = get_city_count(driver, city)

            if count > 0:
                cities_data[city] = count
                print(f"✓ {count:>8,} editions")
            else:
                print(f"✗ 0 editions")

            time.sleep(0.5)  # Small delay between requests

        # Save to CSV
        output_file = '/Users/nogashlomi/projects/yossi/RDF_project_copy/ustc_cities_1470_1650.csv'

        print("\n" + "=" * 70)
        print(f"Saving data to {output_file}...")

        # Sort by count (descending)
        sorted_cities = sorted(cities_data.items(), key=lambda x: x[1], reverse=True)

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['city', 'count'])
            for city, count in sorted_cities:
                writer.writerow([city, count])

        print("✓ Data saved successfully!")

        print("\n" + "=" * 70)
        print("Results:")
        print("=" * 70)

        for idx, (city, count) in enumerate(sorted_cities, 1):
            print(f"{idx:2}. {city:30} {count:>10,} editions")

        total = sum(count for _, count in sorted_cities)
        print("=" * 70)
        print(f"Total (selected cities): {total:,} editions")

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
