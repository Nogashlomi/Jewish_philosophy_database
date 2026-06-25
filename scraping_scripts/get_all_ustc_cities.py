#!/usr/bin/env python3
"""
Comprehensive script to extract ALL USTC cities using multiple approaches
"""

import time
import csv
import json
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
    options.add_argument('--window-size=1920,1200')

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def extract_cities_from_page(driver):
    """Extract all visible city data from the current page"""
    cities = {}

    try:
        body_text = driver.find_element(By.TAG_NAME, "body").text
        lines = body_text.split('\n')

        # Parse the text to find city-count pairs
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Check if this looks like a city name (starts with capital letter, not all caps, reasonable length)
            if (line and
                len(line) > 2 and
                len(line) < 50 and
                line[0].isupper() and
                not line.isupper() and
                i + 1 < len(lines)):

                next_line = lines[i + 1].strip()

                # Check if next line is a number
                if next_line.isdigit() or (next_line.replace(',', '').isdigit()):
                    city = line
                    count = int(next_line.replace(',', ''))

                    # Filter out common UI elements
                    if city not in ['Place', 'Settings', 'Hide', 'Clear', 'Sort', 'List', 'Table',
                                   'Editions', 'Total', 'From', 'To', 'PLACE', 'SETTINGS',
                                   'ACTIVE FILTERS', 'Showing', 'results', 'Download',
                                   'Total Editions per Decade'] and count > 0:
                        cities[city] = count
                    i += 2
                    continue

            i += 1

    except Exception as e:
        print(f"Error extracting cities from page: {e}")

    return cities

def try_expand_place_filter(driver):
    """Try to expand the PLACE filter to see all options"""
    try:
        print("Attempting to expand PLACE filter...")

        # Find all clickable elements that might be the PLACE filter
        all_elements = driver.find_elements(By.XPATH, "//*")

        place_element = None
        for elem in all_elements:
            try:
                if elem.text.strip() == "place" or elem.text.strip().upper() == "PLACE":
                    place_element = elem
                    break
            except:
                pass

        if place_element:
            print("  Found PLACE filter, clicking...")
            place_element.click()
            time.sleep(2)
            return True
        else:
            print("  Could not find PLACE filter element")
            return False

    except Exception as e:
        print(f"  Error expanding PLACE filter: {e}")
        return False

def try_load_more_buttons(driver):
    """Try clicking any 'Load More' or 'View All' buttons"""
    try:
        load_more_buttons = driver.find_elements(By.XPATH,
            "//*[contains(text(), 'Load More') or contains(text(), 'View All') or contains(text(), 'More')]")

        clicked_any = False
        for btn in load_more_buttons:
            try:
                print(f"  Clicking button: {btn.text}")
                btn.click()
                time.sleep(1)
                clicked_any = True
            except:
                pass

        return clicked_any

    except:
        return False

def try_extract_from_javascript(driver):
    """Try to extract data from JavaScript state/localStorage"""
    try:
        print("Attempting to extract from JavaScript state...")

        # Try to access any data in window object
        result = driver.execute_script("""
            // Look for data in various common locations
            let data = {};

            // Check window object for any relevant data
            for (let key in window) {
                if (key.toLowerCase().includes('place') ||
                    key.toLowerCase().includes('data') ||
                    key.toLowerCase().includes('filter')) {
                    try {
                        let val = window[key];
                        if (typeof val === 'object' && val !== null) {
                            data[key] = typeof val === 'string' ? val.substring(0, 500) : JSON.stringify(val).substring(0, 500);
                        }
                    } catch(e) {}
                }
            }

            // Check localStorage
            try {
                for (let i = 0; i < localStorage.length; i++) {
                    let key = localStorage.key(i);
                    if (key.toLowerCase().includes('place') || key.toLowerCase().includes('filter')) {
                        data['localStorage_' + key] = localStorage.getItem(key).substring(0, 500);
                    }
                }
            } catch(e) {}

            return data;
        """)

        if result:
            print(f"  Found data: {json.dumps(result, indent=2)[:500]}")
            return result

    except Exception as e:
        print(f"  Error extracting from JavaScript: {e}")

    return {}

def main():
    print("=" * 80)
    print("COMPREHENSIVE USTC CITY EXTRACTION")
    print("=" * 80)

    driver = setup_driver()

    try:
        # Load the explore page with year filter
        print("\n1. Loading USTC explore page with year filter (1470-1650)...")
        driver.get("https://www.ustc.ac.uk/explore?fqyf=1470&fqyt=1650")

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        print("   Page loaded successfully")

        # Give the page time to fully render
        time.sleep(3)

        all_cities = {}

        # Method 1: Extract currently visible data
        print("\n2. Extracting currently visible cities...")
        visible_cities = extract_cities_from_page(driver)
        print(f"   Found {len(visible_cities)} visible cities")
        all_cities.update(visible_cities)
        for city, count in sorted(visible_cities.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"     - {city}: {count:,}")

        # Method 2: Try to expand PLACE filter
        print("\n3. Trying to expand PLACE filter...")
        if try_expand_place_filter(driver):
            time.sleep(2)
            expanded_cities = extract_cities_from_page(driver)
            print(f"   After expanding: {len(expanded_cities)} cities visible")
            all_cities.update(expanded_cities)

        # Method 3: Try to load more
        print("\n4. Trying to load more results...")
        if try_load_more_buttons(driver):
            loaded_cities = extract_cities_from_page(driver)
            print(f"   After loading more: {len(loaded_cities)} cities visible")
            all_cities.update(loaded_cities)

        # Method 4: Try JavaScript extraction
        print("\n5. Trying JavaScript extraction...")
        js_data = try_extract_from_javascript(driver)

        # Method 5: Try scrolling in filter panel
        print("\n6. Trying to scroll within filter panel...")
        try:
            filter_panels = driver.find_elements(By.XPATH, "//*[contains(@class, 'max-h-')]")
            print(f"   Found {len(filter_panels)} potential filter panels")

            for idx, panel in enumerate(filter_panels[:3]):
                for scroll_attempt in range(5):
                    driver.execute_script("arguments[0].scrollTop += 500;", panel)
                    time.sleep(0.5)

                scrolled_cities = extract_cities_from_page(driver)
                print(f"   Panel {idx} after scrolling: {len(scrolled_cities)} cities")
                all_cities.update(scrolled_cities)
        except:
            pass

        # Summary
        print("\n" + "=" * 80)
        print(f"TOTAL CITIES FOUND: {len(all_cities)}")
        print("=" * 80)

        if all_cities:
            sorted_cities = sorted(all_cities.items(), key=lambda x: x[1], reverse=True)

            for idx, (city, count) in enumerate(sorted_cities, 1):
                print(f"{idx:4}. {city:40} {count:>10,} editions")

            # Save to CSV
            output_file = '/Users/nogashlomi/projects/yossi/RDF_project_copy/ustc_all_cities_comprehensive.csv'

            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['city', 'count'])
                for city, count in sorted_cities:
                    writer.writerow([city, count])

            total = sum(count for _, count in sorted_cities)
            coverage = (total / 843983) * 100

            print(f"\n✓ Saved {len(all_cities)} cities to {output_file}")
            print(f"Total editions: {total:,}")
            print(f"Coverage: {coverage:.1f}% of all editions (1470-1650)")

        else:
            print("✗ No cities found!")

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
