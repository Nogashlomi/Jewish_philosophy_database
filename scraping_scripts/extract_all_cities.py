#!/usr/bin/env python3
"""
Extract ALL USTC cities by scrolling through the expanded PLACE filter
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

def main():
    print("Extracting ALL USTC cities with scrolling")
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

        # Find and click PLACE filter
        place_elements = [elem for elem in driver.find_elements(By.XPATH, "//*")
                         if elem.text.strip().upper() == "PLACE"]

        if place_elements:
            print(f"Found PLACE elements: {len(place_elements)}")
            elem = place_elements[0]
            print("Clicking PLACE...")
            elem.click()
            time.sleep(2)

            # Find the scrollable container for the place list
            # Usually it's a ul, div with overflow-y-auto, or similar
            scrollable_elements = driver.find_elements(By.XPATH,
                "//*[contains(@class, 'overflow') or contains(@class, 'scroll') or contains(@class, 'max-h')]")

            print(f"Found {len(scrollable_elements)} potentially scrollable elements")

            # Try to find the place list container
            place_container = None
            for elem in scrollable_elements:
                try:
                    # Check if this contains place names
                    text = elem.text
                    if 'Paris' in text or 'London' in text or 'Venezia' in text:
                        place_container = elem
                        print(f"Found place container: {elem.tag_name}, class={elem.get_attribute('class')}")
                        break
                except:
                    pass

            # If we didn't find a specific container, just scroll the body
            if not place_container:
                print("Using body for scrolling")
                place_container = driver.find_element(By.TAG_NAME, "body")

            # Scroll through the places
            print("\nScrolling through places...")
            previous_height = 0
            cities = {}
            scroll_count = 0

            while True:
                # Get current height
                current_height = driver.execute_script(
                    "return arguments[0].scrollHeight;",
                    place_container
                )

                print(f"  Scroll {scroll_count}: height={current_height}")

                # Extract visible text
                body_text = driver.find_element(By.TAG_NAME, "body").text
                lines = body_text.split('\n')

                # Extract cities (name on one line, count on next)
                i = 0
                while i < len(lines):
                    line = lines[i].strip()

                    # Check if this looks like a place name
                    if (line and line[0].isupper() and
                        not line.isupper() and
                        i + 1 < len(lines) and
                        'PLACE' not in line.upper() and
                        'Settings' not in line and
                        'Filters' not in line and
                        'Total' not in line and
                        'From' not in line and
                        'To' not in line and
                        'Showing' not in line):

                        next_line = lines[i + 1].strip()

                        # Check if next line is a number
                        if next_line.isdigit():
                            place = line
                            count = int(next_line)

                            # Add if we haven't seen it before or if it's new
                            if place not in cities:
                                cities[place] = count
                                if len(cities) % 10 == 0:
                                    print(f"    Found {len(cities)} cities so far...")

                            i += 2
                            continue

                    i += 1

                # Scroll down in the container
                driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollTop + 500;",
                    place_container
                )

                time.sleep(1)

                # Check if we've reached the bottom
                new_height = driver.execute_script(
                    "return arguments[0].scrollHeight;",
                    place_container
                )

                if new_height == previous_height:
                    print("  Reached end of places list")
                    break

                previous_height = new_height
                scroll_count += 1

                if scroll_count > 100:  # Safety limit
                    print("  Reached scroll limit")
                    break

            print(f"\n✓ Found {len(cities)} cities total!")
            print("=" * 70)

            # Sort by count
            sorted_cities = sorted(cities.items(), key=lambda x: x[1], reverse=True)

            for idx, (city, count) in enumerate(sorted_cities, 1):
                print(f"{idx:3}. {city:45} {count:>10,}")

            # Save to CSV
            output_file = '/Users/nogashlomi/projects/yossi/RDF_project_copy/ustc_cities_1470_1650.csv'

            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['city', 'count'])
                for city, count in sorted_cities:
                    writer.writerow([city, count])

            print(f"\n✓ Saved to {output_file}")

            total = sum(count for _, count in sorted_cities)
            print(f"Total editions across all cities: {total:,}")

        else:
            print("Could not find PLACE element")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
