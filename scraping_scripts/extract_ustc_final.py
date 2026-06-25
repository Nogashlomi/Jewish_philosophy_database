#!/usr/bin/env python3
"""
Final approach: Try to click PLACE and extract visible content
"""

import time
import csv
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
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
    print("Final approach: Clicking PLACE filter")
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

        # Try to find all elements on the page
        all_elements = driver.find_elements(By.XPATH, "//*")
        print(f"Total elements on page: {len(all_elements)}")

        # Try to find elements with "place" in text or attributes
        place_elements = []
        for elem in all_elements:
            try:
                text = elem.text.strip().upper()
                if text == "PLACE":
                    place_elements.append(elem)
                    print(f"Found PLACE element: tag={elem.tag_name}, class={elem.get_attribute('class')}")
            except:
                pass

        if place_elements:
            elem = place_elements[0]
            print("\nAttempting to click PLACE element...")

            # Try different click strategies
            strategies = [
                ("Direct click", lambda e: e.click()),
                ("Action click", lambda e: ActionChains(driver).click(e).perform()),
                ("Parent click", lambda e: e.find_element(By.XPATH, "..").click()),
                ("Grandparent click", lambda e: e.find_element(By.XPATH, "../..").click()),
            ]

            clicked = False
            for name, strategy in strategies:
                try:
                    print(f"  Trying {name}...")
                    strategy(elem)
                    time.sleep(1)
                    clicked = True
                    print(f"  ✓ {name} succeeded!")
                    break
                except Exception as e:
                    print(f"  ✗ {name} failed: {str(e)[:50]}")

            if clicked:
                # Try to scroll to ensure content is visible
                driver.execute_script("window.scrollBy(0, 200);")
                time.sleep(2)

                # Extract visible text
                body_text = driver.find_element(By.TAG_NAME, "body").text
                lines = body_text.split('\n')

                print(f"\nPage now has {len(lines)} lines of text")

                # Look for place patterns in visible text
                # Places and counts might be on separate lines: PlaceName \n Number
                places = {}
                i = 0
                while i < len(lines):
                    line = lines[i].strip()

                    # Check if this line looks like a place name (starts with capital letter)
                    if line and line[0].isupper() and not line.isupper() and i + 1 < len(lines):
                        # Check if next line is a number
                        next_line = lines[i + 1].strip()
                        if next_line.isdigit():
                            place = line
                            count = int(next_line)
                            # Filter out common non-place words
                            if len(place) > 2 and count > 0 and 'PLACE' not in place.upper():
                                places[place] = count
                            i += 2
                            continue

                    # Also try the single-line pattern: "CityName (number)"
                    match = re.match(r'^([A-Z][A-Za-z\s\-\'\.]+?)\s*\((\d+)\)$', line)
                    if match:
                        place = match.group(1).strip()
                        count = int(match.group(2))
                        if len(place) > 2 and count > 0:
                            places[place] = count

                    i += 1

                if places:
                    print(f"\nExtracted {len(places)} places!")
                    print("=" * 70)

                    sorted_places = sorted(places.items(), key=lambda x: x[1], reverse=True)

                    for idx, (place, count) in enumerate(sorted_places[:30], 1):
                        print(f"{idx:3}. {place:45} {count:>10,}")

                    if len(sorted_places) > 30:
                        print(f"... and {len(sorted_places) - 30} more")

                    # Save to CSV
                    output_file = '/Users/nogashlomi/projects/yossi/RDF_project_copy/ustc_cities_1470_1650.csv'

                    with open(output_file, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(['city', 'count'])
                        for city, count in sorted_places:
                            writer.writerow([city, count])

                    print(f"\n✓ Saved {len(sorted_places)} cities to {output_file}")
                    print(f"Total editions: {sum(c for _, c in sorted_places):,}")

                else:
                    print("No places found after clicking")
                    print("\nFirst 50 lines after click:")
                    for i, line in enumerate(lines[:50]):
                        print(f"{i}: {line}")

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
