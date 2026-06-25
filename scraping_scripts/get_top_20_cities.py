#!/usr/bin/env python3
"""
Search for the top 20 European printing centers (1470-1650)
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

def get_count_for_city(driver, city_name):
    """Get edition count for a specific city"""
    try:
        # Navigate to USTC with place filter
        url = f"https://www.ustc.ac.uk/explore?fqp={city_name}&fqyf=1470&fqyt=1650"
        driver.get(url)

        time.sleep(2)

        # Get page text to extract count
        body_text = driver.find_element(By.TAG_NAME, "body").text

        # Look for "Showing 1-20 of XXXXX results"
        match = re.search(r'Showing \d+-\d+ of ([\d,]+) results', body_text)
        if match:
            count = int(match.group(1).replace(',', ''))
            return count

        # Alternative pattern
        match = re.search(r'of ([\d,]+) results', body_text)
        if match:
            count = int(match.group(1).replace(',', ''))
            return count

        return 0

    except Exception as e:
        print(f"      Error: {e}")
        return -1

def main():
    print("=" * 80)
    print("FINDING TOP 20 EUROPEAN PRINTING CENTERS (1470-1650)")
    print("=" * 80)

    # Major European printing centers of the period
    # We already have data for the top 5, so let's get more
    cities_to_search = [
        # Already confirmed (top 5)
        ("Paris", 81115),
        ("London", 58862),
        ("Venezia", 45461),
        ("Lyon", 29395),
        ("Antwerpen", 25789),

        # Other major Italian centers
        ("Roma", None),
        ("Milano", None),
        ("Firenze", None),
        ("Bologna", None),
        ("Napoli", None),

        # Other French centers
        ("Rouen", None),
        ("Toulouse", None),
        ("Strasbourg", None),

        # German/HRE centers
        ("Köln", None),
        ("Frankfurt", None),
        ("Basel", None),
        ("Wittenberg", None),

        # Low Countries
        ("Amsterdam", None),
        ("Leiden", None),
        ("Leuven", None),

        # Spanish centers
        ("Salamanca", None),
        ("Alcalá de Henares", None),
    ]

    driver = setup_driver()

    try:
        print(f"\nSearching for {len(cities_to_search)} printing centers...\n")

        results = {}

        for idx, (city, known_count) in enumerate(cities_to_search, 1):
            if known_count:
                # We already have this data
                print(f"{idx:2}. {city:30} (known) {known_count:>10,} editions")
                results[city] = known_count
            else:
                # Search for this city
                print(f"{idx:2}. {city:30} searching...", end=" ", flush=True)

                count = get_count_for_city(driver, city)

                if count > 0:
                    print(f"✓ {count:>10,}")
                    results[city] = count
                elif count == 0:
                    print("0 results")
                else:
                    print("ERROR")

                time.sleep(1)

        # Sort by count
        print("\n" + "=" * 80)
        print("TOP PRINTING CENTERS (1470-1650):")
        print("=" * 80)

        sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)

        total = 0
        for idx, (city, count) in enumerate(sorted_results, 1):
            print(f"{idx:2}. {city:35} {count:>10,} editions")
            total += count

        print("=" * 80)
        print(f"{'TOTAL':38} {total:>10,} editions")
        print(f"Coverage: {(total/843983)*100:.1f}% of all European editions\n")

        # Save to CSV
        output_file = '/Users/nogashlomi/projects/yossi/RDF_project_copy/ustc_top_20_cities.csv'

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['rank', 'city', 'count'])
            for idx, (city, count) in enumerate(sorted_results, 1):
                writer.writerow([idx, city, count])

        print(f"✓ Saved to {output_file}")

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
