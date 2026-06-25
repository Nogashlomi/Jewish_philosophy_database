#!/usr/bin/env python3
"""
Extract USTC data by CITY and COUNTRY for complete picture
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

def extract_filter_data(driver, filter_name):
    """Click on a filter and extract its data"""

    try:
        # Find the filter element
        filter_elements = [elem for elem in driver.find_elements(By.XPATH, "//*")
                          if elem.text.strip().upper() == filter_name.upper()]

        if not filter_elements:
            print(f"Could not find {filter_name} filter")
            return {}

        print(f"Found {filter_name} filter, clicking...")
        elem = filter_elements[0]
        elem.click()
        time.sleep(2)

        # Extract all visible data
        body_text = driver.find_element(By.TAG_NAME, "body").text
        lines = body_text.split('\n')

        data = {}
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Check if this looks like a filter item (name with a count)
            if (line and line[0].isupper() and
                not line.isupper() and
                i + 1 < len(lines) and
                filter_name.upper() not in line.upper() and
                'Settings' not in line and
                'Filters' not in line and
                'Total' not in line and
                'From' not in line and
                'To' not in line and
                'Showing' not in line and
                len(line) > 2):

                next_line = lines[i + 1].strip()

                # Check if next line is a number
                if next_line.isdigit():
                    item_name = line
                    count = int(next_line)

                    if item_name not in data:
                        data[item_name] = count

                    i += 2
                    continue

            i += 1

        print(f"  Extracted {len(data)} entries")

        # Click again to collapse
        elem.click()
        time.sleep(1)

        return data

    except Exception as e:
        print(f"Error extracting {filter_name}: {e}")
        return {}

def main():
    print("Extracting USTC data by CITY and COUNTRY")
    print("=" * 70)

    driver = setup_driver()

    try:
        # Load the page
        url = "https://www.ustc.ac.uk/explore?fqyf=1470&fqyt=1650"
        driver.get(url)

        print("Page loading...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        time.sleep(3)

        # Extract city data
        print("\nExtracting CITY data...")
        cities = extract_filter_data(driver, "PLACE")

        # Extract country data
        print("\nExtracting COUNTRY data...")
        countries = extract_filter_data(driver, "COUNTRY")

        # Extract region data
        print("\nExtracting REGION data...")
        regions = extract_filter_data(driver, "REGION")

        # Display results
        print("\n" + "=" * 70)
        print("CITIES (Places)")
        print("=" * 70)

        if cities:
            sorted_cities = sorted(cities.items(), key=lambda x: x[1], reverse=True)
            for idx, (city, count) in enumerate(sorted_cities, 1):
                print(f"{idx:3}. {city:45} {count:>10,}")

            # Save cities
            with open('/Users/nogashlomi/projects/yossi/RDF_project_copy/ustc_cities_1470_1650.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['city', 'count'])
                for city, count in sorted_cities:
                    writer.writerow([city, count])
            print(f"\n✓ Saved {len(cities)} cities")

        print("\n" + "=" * 70)
        print("COUNTRIES")
        print("=" * 70)

        if countries:
            sorted_countries = sorted(countries.items(), key=lambda x: x[1], reverse=True)
            for idx, (country, count) in enumerate(sorted_countries, 1):
                print(f"{idx:3}. {country:45} {count:>10,}")

            # Save countries
            with open('/Users/nogashlomi/projects/yossi/RDF_project_copy/ustc_countries_1470_1650.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['country', 'count'])
                for country, count in sorted_countries:
                    writer.writerow([country, count])
            print(f"\n✓ Saved {len(countries)} countries")

        print("\n" + "=" * 70)
        print("REGIONS")
        print("=" * 70)

        if regions:
            sorted_regions = sorted(regions.items(), key=lambda x: x[1], reverse=True)
            for idx, (region, count) in enumerate(sorted_regions[:30], 1):
                print(f"{idx:3}. {region:45} {count:>10,}")

            if len(regions) > 30:
                print(f"... and {len(regions) - 30} more regions")

            # Save regions
            with open('/Users/nogashlomi/projects/yossi/RDF_project_copy/ustc_regions_1470_1650.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['region', 'count'])
                for region, count in sorted_regions:
                    writer.writerow([region, count])
            print(f"\n✓ Saved {len(regions)} regions")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
