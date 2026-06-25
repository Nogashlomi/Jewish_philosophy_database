#!/usr/bin/env python3
"""
Fetch USTC quantitative data by city - Version 2
Uses the filter API and page interactions
"""

import time
import csv
import json
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
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--start-maximized')

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def get_cities_from_page(driver):
    """Extract cities and counts from the USTC page"""

    try:
        # Load the USTC explore page with year filter
        url = "https://www.ustc.ac.uk/explore?fqyf=1470&fqyt=1650"
        driver.get(url)

        # Wait for page to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        time.sleep(3)  # Extra wait for dynamic content

        print("Page loaded. Analyzing structure...")

        # Get the full page HTML
        page_html = driver.page_source

        # Look for any data embedded in the page
        # Check if there's a JSON structure with place/location data
        if 'place' in page_html.lower():
            print("Found 'place' reference in page")

        # Try to find all buttons/links in the filters section
        all_links = driver.find_elements(By.TAG_NAME, "a")
        all_buttons = driver.find_elements(By.TAG_NAME, "button")

        print(f"Found {len(all_links)} links and {len(all_buttons)} buttons")

        # Look for the place filter section
        print("\nSearching for place filter...")

        # Try to find the SETTINGS section
        settings_section = None
        try:
            settings_section = driver.find_element(By.XPATH, "//*[contains(text(), 'SETTINGS')]")
            print("Found SETTINGS section")
        except:
            print("SETTINGS section not found")

        # Try to find all elements with "place" in their text or attributes
        place_elements = driver.find_elements(By.XPATH, "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'place')]")
        print(f"Found {len(place_elements)} elements containing 'place'")

        # Try a different approach: search for a filter input or button
        # Look for input fields or expandable sections
        try:
            # Scroll down to find more content
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        except:
            pass

        # Look for list items that might contain city names
        list_items = driver.find_elements(By.TAG_NAME, "li")
        print(f"Found {len(list_items)} list items")

        # Extract text from list items looking for city patterns
        cities = {}
        for item in list_items:
            try:
                text = item.text.strip()
                if text and len(text) > 2:
                    # Look for patterns with numbers
                    parts = text.rsplit('(', 1) if '(' in text else [text, '']
                    if len(parts) == 2 and parts[1].strip().endswith(')'):
                        try:
                            city = parts[0].strip()
                            count_str = parts[1].replace(')', '').replace(',', '').strip()
                            count = int(count_str)

                            if city and count > 0:
                                cities[city] = count
                                if len(cities) <= 10:  # Print first 10
                                    print(f"  Found: {city} ({count})")
                        except:
                            pass
            except:
                pass

        if cities:
            print(f"\nSuccessfully extracted {len(cities)} cities from page")
            return cities

        else:
            print("\nNo cities found in list items. Trying to access page data...")

            # Try to get data from JavaScript variables
            try:
                # Look for any JSON data in script tags
                scripts = driver.find_elements(By.TAG_NAME, "script")
                for script in scripts:
                    content = script.get_attribute("textContent")
                    if content and 'place' in content.lower() and len(content) < 50000:
                        print(f"Found script with 'place' ({len(content)} chars)")
                        # Try to parse JSON from script
                        if '{' in content and '"' in content:
                            try:
                                # Extract JSON-like structures
                                import re
                                json_matches = re.findall(r'\{[^{}]*"place"[^{}]*\}', content)
                                if json_matches:
                                    print(f"  Found {len(json_matches)} potential JSON matches")
                            except:
                                pass
            except:
                pass

            print("\nPage HTML preview (first 2000 chars):")
            print(page_html[:2000])
            print("\n...")
            print(page_html[-1000:])

            return {}

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return {}

def main():
    print("Fetching USTC data by city - Version 2")
    print("=" * 70)

    driver = setup_driver()

    try:
        cities = get_cities_from_page(driver)

        if cities:
            print("\n" + "=" * 70)
            print("Cities with edition counts (1470-1650):")
            print("=" * 70)

            # Sort by edition count (descending)
            sorted_cities = sorted(cities.items(), key=lambda x: x[1], reverse=True)

            for idx, (city, count) in enumerate(sorted_cities, 1):
                print(f"{idx:3}. {city:40} {count:>10,} editions")

            # Save to CSV
            output_file = '/Users/nogashlomi/projects/yossi/RDF_project_copy/ustc_cities_1470_1650.csv'

            print(f"\nSaving {len(sorted_cities)} cities to {output_file}...")

            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['city', 'count'])
                for city, count in sorted_cities:
                    writer.writerow([city, count])

            print("✓ Data saved successfully!")

            # Print summary
            total = sum(count for _, count in sorted_cities)
            print(f"\nSummary: {len(sorted_cities)} cities, {total:,} total editions")

        else:
            print("\nFailed to extract city data")

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
