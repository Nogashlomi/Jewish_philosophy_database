#!/usr/bin/env python3
"""
Search USTC for a comprehensive list of European printing cities (1470-1650)
Using detailed URL parameters to get data for each city
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

def get_count_for_place(driver, place_name):
    """Get edition count for a specific place using URL search"""
    try:
        # Try different URL parameter formats
        urls_to_try = [
            f"https://www.ustc.ac.uk/search?place={place_name}&start_year=1470&end_year=1650",
            f"https://www.ustc.ac.uk/search?p={place_name}&sy=1470&ey=1650",
            f"https://www.ustc.ac.uk/search?q={place_name}&year_from=1470&year_to=1650",
        ]

        for url in urls_to_try:
            try:
                driver.get(url)
                time.sleep(1)

                body_text = driver.find_element(By.TAG_NAME, "body").text

                # Look for result counts
                patterns = [
                    r'(\d+(?:,\d+)*)\s+results?',
                    r'Showing.*?of.*?(\d+(?:,\d+)*)',
                    r'Total.*?(\d+(?:,\d+)*)',
                ]

                for pattern in patterns:
                    match = re.search(pattern, body_text, re.IGNORECASE)
                    if match:
                        count = int(match.group(1).replace(',', ''))
                        if count > 0:
                            return count

            except:
                pass

        return 0

    except:
        return -1

def main():
    print("=" * 80)
    print("COMPREHENSIVE EUROPEAN PRINTING CITIES SEARCH (1470-1650)")
    print("=" * 80)

    # Comprehensive list of known European printing centers from the period
    cities = {
        # Already known top 5
        'Paris': None,
        'London': None,
        'Venice': None,
        'Lyon': None,
        'Antwerp': None,

        # Italy
        'Milan': None,
        'Rome': None,
        'Florence': None,
        'Bologna': None,
        'Padua': None,
        'Naples': None,
        'Genoa': None,
        'Perugia': None,
        'Siena': None,
        'Turin': None,
        'Modena': None,
        'Ferrara': None,
        'Mantua': None,
        'Brescia': None,
        'Como': None,

        # France (beyond Paris and Lyon)
        'Rouen': None,
        'Toulouse': None,
        'Marseille': None,
        'Dijon': None,
        'Troyes': None,
        'Angers': None,
        'Caen': None,
        'Nantes': None,
        'Orleans': None,
        'Amiens': None,
        'Strasbourg': None,

        # Germany/HRE
        'Cologne': None,
        'Frankfurt': None,
        'Nuremberg': None,
        'Augsburg': None,
        'Wittenberg': None,
        'Leipzig': None,
        'Mainz': None,
        'Speyer': None,
        'Heidelberg': None,
        'Erfurt': None,
        'Basil': None,

        # Low Countries
        'Amsterdam': None,
        'Brussels': None,
        'Bruges': None,
        'Ghent': None,
        'Haarlem': None,
        'Mechelen': None,
        'Leuven': None,
        'Maastricht': None,
        'Deventer': None,
        'Middleburg': None,

        # Spain/Portugal
        'Seville': None,
        'Toledo': None,
        'Madrid': None,
        'Barcelona': None,
        'Valencia': None,
        'Granada': None,
        'Salamanca': None,
        'Valladolid': None,
        'Lisbon': None,
        'Covilha': None,
        'Evora': None,
        'Porto': None,

        # Switzerland
        'Basel': None,
        'Bern': None,
        'Lucerne': None,
        'Geneva': None,
        'Zurich': None,

        # Central Europe
        'Vienna': None,
        'Prague': None,
        'Krakow': None,
        'Budapest': None,

        # Special locations
        '[S.l.]': None,
        's.l.': None,
        'No place': None,
    }

    driver = setup_driver()

    try:
        print(f"\nSearching for {len(cities)} cities...\n")

        results = {}
        found_count = 0

        for idx, (city, _) in enumerate(cities.items(), 1):
            print(f"{idx:2}. Searching for {city:30}", end=" ... ", flush=True)

            count = get_count_for_place(driver, city)

            if count > 0:
                results[city] = count
                print(f"✓ {count:>10,}")
                found_count += 1
            elif count == 0:
                print("0 results")
            else:
                print("ERROR")

            time.sleep(0.5)

        print("\n" + "=" * 80)
        print(f"RESULTS: {found_count} cities found with data")
        print("=" * 80)

        if results:
            sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)

            total = 0
            for idx, (city, count) in enumerate(sorted_results, 1):
                print(f"{idx:3}. {city:35} {count:>10,} editions")
                total += count

            print("-" * 80)
            print(f"{'TOTAL':38} {total:>10,} editions")
            coverage = (total / 843983) * 100
            print(f"Coverage: {coverage:.1f}% of all editions\n")

            # Save to CSV
            output_file = '/Users/nogashlomi/projects/yossi/RDF_project_copy/ustc_cities_searched.csv'

            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['city', 'count'])
                for city, count in sorted_results:
                    writer.writerow([city, count])

            print(f"✓ Saved to {output_file}")

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
