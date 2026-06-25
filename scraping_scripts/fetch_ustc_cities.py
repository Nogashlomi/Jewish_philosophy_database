#!/usr/bin/env python3
"""
Fetch USTC quantitative data by city for European editions (1470-1650)
"""

import time
import csv
import re
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

def setup_driver():
    """Setup Chrome WebDriver"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def get_cities_data(driver):
    """Fetch all cities and their edition counts for 1470-1650"""

    try:
        # Load the USTC explore page with year filter
        url = "https://www.ustc.ac.uk/explore?fqyf=1470&fqyt=1650"
        driver.get(url)

        # Wait for page to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        time.sleep(2)  # Extra wait for dynamic content

        # Try to expand the place filter
        print("Looking for place/city filter...")

        # Look for all filter buttons or expandable sections
        filter_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'place') or contains(text(), 'Place')]")
        print(f"Found {len(filter_elements)} place-related elements")

        # Try to find and click the place filter
        place_filter = None
        try:
            # Look for a button or link that says "place"
            place_filter = driver.find_element(By.XPATH, "//*[contains(text(), 'place')]/..")
            if place_filter:
                print("Found place filter, attempting to expand...")
                place_filter.click()
                time.sleep(2)
        except:
            print("Could not find place filter button")

        # Try alternative: Look for all list items that contain city names and counts
        page_text = driver.find_element(By.TAG_NAME, "body").text

        # Extract the full page HTML
        page_html = driver.page_source

        # Look for patterns like "CityName (number)" or similar
        # USTC might display this in a filter panel

        # Try to find any divs or lists with city data
        city_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'filter') or contains(@class, 'place') or contains(@class, 'facet')]")
        print(f"Found {len(city_elements)} potential city filter elements")

        if city_elements:
            for element in city_elements[:5]:  # Show first 5
                try:
                    text = element.text
                    if text:
                        print(f"  Element text: {text[:100]}")
                except:
                    pass

        # Try to find city names in the page HTML using regex
        # Pattern: City Name (number)
        city_pattern = r'([A-Z][a-zA-Z\s\-\']+)\s*\((\d+)\)'
        cities = {}

        matches = re.findall(city_pattern, page_html)
        for city, count in matches:
            city = city.strip()
            # Filter out common non-city strings
            if len(city) > 2 and not city.isupper() or city.isupper() and len(city) > 3:
                if city not in cities:
                    cities[city] = int(count)

        print(f"\nFound {len(cities)} potential cities via regex")

        # Also try to get data from the page's JavaScript
        try:
            # Execute JavaScript to find all text nodes with numbers
            script = """
            const items = [];
            const walker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );

            let node;
            while (node = walker.nextNode()) {
                const text = node.textContent.trim();
                // Look for patterns like "City (number)"
                if (/^[A-Z][a-zA-Z\\s\\-']+\\s*\\(\\d+\\)$/.test(text)) {
                    items.push(text);
                }
            }

            return items.slice(0, 100);  // Return first 100 matches
            """

            results = driver.execute_script(script)
            print(f"JavaScript found {len(results)} city patterns")

            for result in results[:20]:  # Show first 20
                print(f"  {result}")

        except Exception as e:
            print(f"JavaScript execution failed: {e}")

        return cities, page_text

    except Exception as e:
        print(f"Error fetching cities data: {e}")
        import traceback
        traceback.print_exc()
        return {}, ""

def main():
    print("Fetching USTC data by city for European editions (1470-1650)...")
    print("=" * 70)

    driver = setup_driver()

    try:
        cities, page_text = get_cities_data(driver)

        if cities:
            print("\nCities found:")
            print("-" * 70)

            # Sort by edition count (descending)
            sorted_cities = sorted(cities.items(), key=lambda x: x[1], reverse=True)

            for city, count in sorted_cities[:30]:  # Show top 30
                print(f"{city:40} {count:>10,} editions")

            if len(sorted_cities) > 30:
                print(f"... and {len(sorted_cities) - 30} more cities")

            # Save to CSV
            output_file = '/Users/nogashlomi/projects/yossi/RDF_project_copy/ustc_cities_1470_1650.csv'

            print(f"\nSaving {len(sorted_cities)} cities to {output_file}...")

            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['city', 'count'])
                for city, count in sorted_cities:
                    writer.writerow([city, count])

            print("✓ Data saved successfully!")

        else:
            print("\nNo cities found via regex. Trying alternative method...")
            print("\nPage text preview:")
            print(page_text[:1000])

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
