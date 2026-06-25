#!/usr/bin/env python3
"""
Extract USTC places by clicking the place filter and extracting expanded content
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

def expand_place_filter(driver):
    """Click on PLACE filter to expand it"""

    try:
        # Wait for page to fully load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        time.sleep(2)

        # Look for the PLACE filter text/button
        place_labels = driver.find_elements(By.XPATH, "//*[text()='PLACE'] | //*[text()='Place']")
        print(f"Found {len(place_labels)} PLACE labels")

        if place_labels:
            place_label = place_labels[0]
            print(f"Found PLACE label, parent: {place_label.tag_name}")

            # Try to find the clickable parent element
            parent = place_label
            for _ in range(5):  # Go up max 5 levels
                parent = parent.find_element(By.XPATH, "..")
                print(f"  Parent level: {parent.tag_name}, text: {parent.text[:50] if parent.text else 'N/A'}")

                # Try to click on it
                try:
                    parent.click()
                    print("  Clicked on parent")
                    time.sleep(2)

                    # Check if something expanded
                    body_text = driver.find_element(By.TAG_NAME, "body").text
                    if '\n' in body_text:
                        lines = body_text.split('\n')
                        print(f"  Page has {len(lines)} lines now")
                        # Check if place content is visible
                        if any('(' in line and ')' in line for line in lines):
                            return True

                except:
                    pass

            # Try a different approach: look for any clickable element with "place"
            clickables = driver.find_elements(By.XPATH, "//button[contains(., 'place') or contains(., 'PLACE')] | //div[contains(@class, 'clickable') and contains(., 'place')]")
            print(f"Found {len(clickables)} clickable place elements")

            if clickables:
                clickables[0].click()
                print("Clicked on clickable place element")
                time.sleep(2)
                return True

        return False

    except Exception as e:
        print(f"Error expanding filter: {e}")
        import traceback
        traceback.print_exc()
        return False

def extract_places_from_expanded(driver):
    """Extract places from the expanded filter"""

    try:
        # Get all text
        body_text = driver.find_element(By.TAG_NAME, "body").text
        lines = body_text.split('\n')

        places = {}

        # Look for lines with place patterns
        # Usually in format: "PlaceName (number)"
        for line in lines:
            line = line.strip()

            # Match pattern: City/Place name followed by count in parentheses
            match = re.match(r'^([A-Z][A-Za-z\s\-\'\.]+?)\s*\((\d+)\)$', line)
            if match:
                place_name = match.group(1).strip()
                count = int(match.group(2))

                # Filter out unlikely place names
                if len(place_name) > 2 and count > 0:
                    # Avoid common non-place words
                    if place_name.upper() not in ['PLACE', 'CITY', 'COUNTRY', 'FROM', 'TO']:
                        places[place_name] = count

        return places

    except Exception as e:
        print(f"Error extracting places: {e}")
        return {}

def main():
    print("Extracting USTC places - Version 2")
    print("=" * 70)

    driver = setup_driver()

    try:
        # Load the page
        url = "https://www.ustc.ac.uk/explore?fqyf=1470&fqyt=1650"
        driver.get(url)

        print("Page loading...")
        time.sleep(3)

        # Try to expand the PLACE filter
        print("\nTrying to expand PLACE filter...")
        expanded = expand_place_filter(driver)

        if expanded:
            print("Filter expanded successfully!")
        else:
            print("Could not expand filter, trying to extract anyway...")

        # Extract places
        print("\nExtracting places...")
        places = extract_places_from_expanded(driver)

        if places:
            print(f"\nFound {len(places)} places!")
            print("=" * 70)

            # Sort by count
            sorted_places = sorted(places.items(), key=lambda x: x[1], reverse=True)

            for idx, (place, count) in enumerate(sorted_places, 1):
                print(f"{idx:3}. {place:45} {count:>10,}")

            # Save to CSV
            output_file = '/Users/nogashlomi/projects/yossi/RDF_project_copy/ustc_cities_1470_1650.csv'

            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['city', 'count'])
                for city, count in sorted_places:
                    writer.writerow([city, count])

            print(f"\n✓ Data saved to {output_file}")

            total = sum(count for _, count in sorted_places)
            print(f"Total: {total:,} editions")

        else:
            print("No places found")
            print("\nDebug - showing first 100 lines of page text:")
            body_text = driver.find_element(By.TAG_NAME, "body").text
            lines = body_text.split('\n')
            for i, line in enumerate(lines[:100]):
                print(f"{i}: {line}")

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
