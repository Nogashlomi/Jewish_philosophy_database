#!/usr/bin/env python3
"""
Search for individual cities to build comprehensive list
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
    options.add_argument('--window-size=1920,1080')

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def get_place_count(driver, city_name):
    """Get count for a specific city using the search/filter interface"""

    try:
        # Navigate with place parameter
        url = f"https://www.ustc.ac.uk/explore?fqp={city_name}&fqyf=1470&fqyt=1650"
        driver.get(url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        time.sleep(1)

        # Look for "Showing 1-20 of X results"
        body_text = driver.find_element(By.TAG_NAME, "body").text

        # Look for the result count
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
        return -1  # Error

def main():
    print("Searching for individual cities in USTC")
    print("=" * 70)

    driver = setup_driver()

    # Known major European printing cities of the period
    cities_to_search = [
        # Top 5 we already know
        "Paris", "London", "Venezia", "Lyon", "Antwerpen",

        # Other major Italian cities
        "Milano", "Milan", "Roma", "Rome", "Firenze", "Florence",
        "Bologna", "Padova", "Padua", "Napoli", "Naples",
        "Genova", "Genoa", "Perugia", "Siena", "Torino", "Turin",

        # Other German/HRE cities
        "Strasbourg", "Straßburg", "Cologne", "Köln", "Frankfurt",
        "Nuremberg", "Nürnberg", "Augsburg", "Wittenberg",
        "Leipzig", "Mainz", "Speyer", "Heidelberg", "Zurich",

        # Other French cities
        "Rouen", "Toulouse", "Marseille", "Dijon", "Troyes",
        "Angers", "Caen", "Nantes", "Orleans", "Amiens",

        # Other Low Countries
        "Amsterdam", "Brussels", "Bruges", "Ghent", "Haarlem",
        "Mechlin", "Mechelen", "Leuven", "Maastricht", "Deventer",

        # Spanish/Portuguese
        "Seville", "Sevilla", "Toledo", "Madrid", "Barcelona",
        "Valencia", "Granada", "Salamanca", "Valladolid", "Lisbon",
        "Covilhã", "Évora", "Porto",

        # Other regions
        "Basel", "Bern", "Lucerne", "Geneva", "Geneva", "Innsbruck",
        "Vienna", "Wien", "Prague", "Praha", "Krakow", "Kraków",
        "Venice", "Venetiae",  # Alternative spelling

        # Special cases
        "s.l.", "s.l. (sine loco)", "[s.l.]",  # No place specified
    ]

    driver_started = False
    results = {}

    try:
        driver.get("https://www.ustc.ac.uk/explore?fqyf=1470&fqyt=1650")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        driver_started = True

        print(f"Searching for {len(cities_to_search)} cities...\n")

        for i, city in enumerate(cities_to_search, 1):
            count = get_place_count(driver, city)

            if count > 0:
                results[city] = count
                print(f"{i:2}. {city:25} {count:>10,} editions")
            elif count == 0:
                print(f"{i:2}. {city:25} {'0':>10} editions (0 or filter not recognized)")
            else:
                print(f"{i:2}. {city:25} {'ERROR':>10}")

            # Small delay
            time.sleep(0.5)

        print("\n" + "=" * 70)
        print(f"Found {len(results)} cities with data")
        print("=" * 70)

        if results:
            sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)

            for idx, (city, count) in enumerate(sorted_results, 1):
                print(f"{idx:3}. {city:30} {count:>10,}")

            # Save to CSV
            output_file = '/Users/nogashlomi/projects/yossi/RDF_project_copy/ustc_searched_cities_1470_1650.csv'

            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['city', 'count'])
                for city, count in sorted_results:
                    writer.writerow([city, count])

            print(f"\n✓ Saved {len(results)} cities to {output_file}")

            total = sum(count for _, count in sorted_results)
            print(f"Total editions from searched cities: {total:,}")
            print(f"This represents ~{total/843983*100:.1f}% of all European editions (1470-1650)")

    finally:
        if driver_started:
            driver.quit()

if __name__ == '__main__':
    main()
