#!/usr/bin/env python3
"""
Extract ALL USTC cities - try searching and scrolling to get complete list
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

def extract_all_cities(driver):
    """Try to extract ALL cities from the expanded PLACE filter"""

    try:
        # Find and click PLACE
        place_elements = [elem for elem in driver.find_elements(By.XPATH, "//*")
                         if elem.text.strip().upper() == "PLACE"]

        if not place_elements:
            print("Could not find PLACE filter")
            return {}

        place_elem = place_elements[0]
        print("Clicking PLACE filter...")
        place_elem.click()
        time.sleep(2)

        # Look for search input within the filter
        all_inputs = driver.find_elements(By.XPATH, "//input[@type='text'] | //input[@type='search']")
        print(f"Found {len(all_inputs)} input fields")

        search_input = None
        for inp in all_inputs:
            try:
                placeholder = inp.get_attribute("placeholder")
                if placeholder and ("search" in placeholder.lower() or "filter" in placeholder.lower()):
                    search_input = inp
                    print(f"Found search input with placeholder: {placeholder}")
                    break
            except:
                pass

        # Try to extract cities multiple times with different scrolling strategies
        all_cities = {}

        print("\nExtracting visible cities...")

        # Strategy 1: Extract what's currently visible
        body_text = driver.find_element(By.TAG_NAME, "body").text
        lines = body_text.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if (line and line[0].isupper() and
                not line.isupper() and
                i + 1 < len(lines) and
                'PLACE' not in line.upper() and
                'Setting' not in line and
                'Filter' not in line):

                next_line = lines[i + 1].strip()
                if next_line.isdigit():
                    city = line
                    count = int(next_line)
                    if city not in all_cities:
                        all_cities[city] = count
                    i += 2
                    continue

            i += 1

        print(f"Currently visible: {len(all_cities)} cities")

        # Strategy 2: Try to scroll within the filter panel to find more
        print("\nTrying to scroll filter panel...")

        # Find the filter container/list
        filter_lists = driver.find_elements(By.XPATH, "//*[contains(@class, 'max-h')]")
        print(f"Found {len(filter_lists)} potentially scrollable filter lists")

        if filter_lists:
            # Try scrolling the first one
            for idx, filter_list in enumerate(filter_lists[:3]):
                try:
                    print(f"\nScrolling filter list {idx}...")
                    original_height = driver.execute_script("return arguments[0].scrollHeight;", filter_list)
                    print(f"  Original height: {original_height}")

                    # Scroll down in the list
                    for scroll_attempt in range(20):
                        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollTop + 300;", filter_list)
                        time.sleep(0.5)

                        # Extract visible cities again
                        body_text = driver.find_element(By.TAG_NAME, "body").text
                        lines = body_text.split('\n')

                        i = 0
                        while i < len(lines):
                            line = lines[i].strip()

                            if (line and line[0].isupper() and
                                not line.isupper() and
                                i + 1 < len(lines)):

                                next_line = lines[i + 1].strip()
                                if next_line.isdigit():
                                    city = line
                                    count = int(next_line)
                                    all_cities[city] = count
                                    i += 2
                                    continue

                            i += 1

                        # Check if we've reached bottom
                        current_scroll = driver.execute_script("return arguments[0].scrollTop;", filter_list)
                        if current_scroll >= original_height - 10:
                            print(f"  Reached bottom of list at scroll attempt {scroll_attempt}")
                            break

                        if (scroll_attempt + 1) % 5 == 0:
                            print(f"  After scroll {scroll_attempt + 1}: {len(all_cities)} cities found")

                except Exception as e:
                    print(f"  Error scrolling list {idx}: {e}")

        print(f"\nTotal cities found: {len(all_cities)}")

        # Try clicking on some cities to see if that loads more
        print("\nTrying to click on cities to load more...")

        city_buttons = driver.find_elements(By.XPATH, "//button[contains(@class, 'flex')]")
        print(f"Found {len(city_buttons)} potential city buttons")

        for idx, btn in enumerate(city_buttons[:10]):
            try:
                text = btn.text.strip()
                if text and text[0].isupper() and not text.isupper():
                    print(f"  Clicking city button {idx}: {text[:30]}")
                    btn.click()
                    time.sleep(0.3)

                    # Extract again
                    body_text = driver.find_element(By.TAG_NAME, "body").text
                    lines = body_text.split('\n')

                    i = 0
                    while i < len(lines):
                        line = lines[i].strip()
                        if (line and line[0].isupper() and
                            not line.isupper() and
                            i + 1 < len(lines)):

                            next_line = lines[i + 1].strip()
                            if next_line.isdigit():
                                city = line
                                count = int(next_line)
                                all_cities[city] = count
                                i += 2
                                continue

                        i += 1

                    # Unclick to close submenu if any
                    btn.click()
                    time.sleep(0.2)

            except:
                pass

        return all_cities

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return {}

def main():
    print("Extracting ALL USTC cities - Complete approach")
    print("=" * 70)

    driver = setup_driver()

    try:
        # Load page
        url = "https://www.ustc.ac.uk/explore?fqyf=1470&fqyt=1650"
        driver.get(url)

        print("Page loading...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        time.sleep(3)

        # Extract all cities
        cities = extract_all_cities(driver)

        if cities:
            print("\n" + "=" * 70)
            print(f"FOUND {len(cities)} CITIES!")
            print("=" * 70)

            sorted_cities = sorted(cities.items(), key=lambda x: x[1], reverse=True)

            for idx, (city, count) in enumerate(sorted_cities, 1):
                print(f"{idx:4}. {city:45} {count:>10,}")

            # Save to CSV
            output_file = '/Users/nogashlomi/projects/yossi/RDF_project_copy/ustc_all_cities_1470_1650.csv'

            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['city', 'count'])
                for city, count in sorted_cities:
                    writer.writerow([city, count])

            print(f"\n✓ Saved {len(cities)} cities to {output_file}")

            total = sum(count for _, count in sorted_cities)
            print(f"Total editions: {total:,}")

        else:
            print("\nNo cities found")

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
