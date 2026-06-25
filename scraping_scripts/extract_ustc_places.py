#!/usr/bin/env python3
"""
Extract USTC places by interacting with the SETTINGS filter panel
"""

import time
import csv
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
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

def extract_places(driver):
    """Extract all places and their counts from USTC"""

    try:
        # Load the explore page with year filter
        url = "https://www.ustc.ac.uk/explore?fqyf=1470&fqyt=1650"
        driver.get(url)

        print("Page loaded. Waiting for dynamic content...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        time.sleep(3)

        # Find the SETTINGS section
        settings_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'SETTINGS') or contains(text(), 'Settings')]")
        print(f"Found {len(settings_buttons)} SETTINGS elements")

        # Try to find the place filter input or expander
        # First, let's look for any input field that might be for searching places
        place_inputs = driver.find_elements(By.XPATH, "//input[contains(@placeholder, 'place') or contains(@placeholder, 'Place')]")
        print(f"Found {len(place_inputs)} place input fields")

        # Try to find checkboxes or buttons with place names
        # Look for all li elements that might contain filter options
        all_text = driver.find_element(By.TAG_NAME, "body").text

        # Parse the text to find place-like entries
        lines = all_text.split('\n')

        # Look for patterns that might be places with counts
        places = {}

        # Try to find a section that lists places
        in_place_section = False
        for i, line in enumerate(lines):
            line = line.strip()

            # Check if this line starts a place section
            if 'place' in line.lower() and ('filter' in line.lower() or 'options' in line.lower() or i > 20):
                print(f"Potential place section starting at line {i}: {line}")
                in_place_section = True

            # Look for lines that look like "Name (number)" pattern
            if in_place_section:
                match = re.match(r'^([A-Z][A-Za-z\s\-\']+?)\s*\((\d+)\)$', line)
                if match:
                    place_name = match.group(1).strip()
                    count = int(match.group(2))
                    if place_name and count > 0:
                        places[place_name] = count
                        if len(places) <= 20:
                            print(f"  Found: {place_name} ({count})")

        print(f"\nExtracted {len(places)} places from page text")

        if not places:
            print("\nTrying to extract from page HTML...")

            # Get the page source
            page_html = driver.page_source

            # Look for data attributes or hidden elements
            # Try to find all potential place entries in the HTML
            place_pattern = r'>([A-Z][A-Za-z\s\-\']+?)\s*\((\d+)\)<'
            matches = re.findall(place_pattern, page_html)

            if matches:
                print(f"Found {len(matches)} place patterns in HTML")
                for place, count in matches[:20]:
                    place = place.strip()
                    if len(place) > 2:
                        places[place] = int(count)
                        print(f"  {place}: {count}")

        # Try scrolling to see if there's more content
        if not places:
            print("\nScrolling to find more content...")

            driver.execute_script("window.scrollBy(0, window.innerHeight);")
            time.sleep(2)

            # Try extracting again after scroll
            page_html = driver.page_source
            place_pattern = r'>([A-Z][A-Za-z\s\-\']+?)\s*\((\d+)\)<'
            matches = re.findall(place_pattern, page_html)

            print(f"After scroll, found {len(matches)} place patterns")

            for place, count in matches[:30]:
                place = place.strip()
                if len(place) > 2 and place not in places:
                    places[place] = int(count)

        return places

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return {}

def main():
    print("Extracting USTC places data")
    print("=" * 70)

    driver = setup_driver()

    try:
        places = extract_places(driver)

        if places:
            print("\n" + "=" * 70)
            print("Places found:")
            print("=" * 70)

            # Sort by count (descending)
            sorted_places = sorted(places.items(), key=lambda x: x[1], reverse=True)

            for idx, (place, count) in enumerate(sorted_places, 1):
                print(f"{idx:3}. {place:40} {count:>10,} editions")

            # Save to CSV
            output_file = '/Users/nogashlomi/projects/yossi/RDF_project_copy/ustc_cities_1470_1650.csv'

            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['city', 'count'])
                for city, count in sorted_places:
                    writer.writerow([city, count])

            print(f"\n✓ Data saved to {output_file}")

            total = sum(count for _, count in sorted_places)
            print(f"\nTotal: {len(sorted_places)} cities, {total:,} editions")

        else:
            print("No places extracted from page")

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
