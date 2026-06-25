#!/usr/bin/env python3
"""
Search for places using the USTC place filter search box
"""

import time
import csv
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

def main():
    print("=" * 80)
    print("SEARCHING FOR PLACES USING PLACE FILTER SEARCH")
    print("=" * 80)

    driver = setup_driver()

    try:
        # Load page
        print("\n1. Loading USTC explore page (1470-1650)...")
        driver.get("https://www.ustc.ac.uk/explore?fqyf=1470&fqyt=1650")

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )

        time.sleep(3)

        # Click Settings to expand
        print("\n2. Expanding Settings...")
        try:
            settings_btn = driver.find_element(By.XPATH, "//*[contains(text(), 'Settings')]")
            driver.execute_script("arguments[0].click();", settings_btn)
            time.sleep(2)
        except:
            print("   Could not find Settings button")

        # Click PLACE filter
        print("\n3. Clicking PLACE filter...")
        try:
            place_elem = None
            selectors = ["//*[text()='place']", "//label[contains(text(), 'place')]", "//div[contains(text(), 'place')]"]

            for selector in selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        if 'place' in elem.text.lower():
                            place_elem = elem
                            break
                    if place_elem:
                        break
                except:
                    pass

            if place_elem:
                driver.execute_script("arguments[0].click();", place_elem)
                time.sleep(2)
                print("   PLACE filter expanded")
            else:
                print("   Could not find PLACE filter")

        except Exception as e:
            print(f"   Error: {e}")

        # Look for search input
        print("\n4. Looking for search input in place filter...")
        search_input = None

        try:
            # Find all input elements
            inputs = driver.find_elements(By.TAG_NAME, "input")
            print(f"   Found {len(inputs)} input elements")

            for inp in inputs:
                try:
                    placeholder = inp.get_attribute("placeholder")
                    aria_label = inp.get_attribute("aria-label")

                    if placeholder:
                        print(f"     - Input with placeholder: {placeholder}")
                    if aria_label:
                        print(f"     - Input with aria-label: {aria_label}")

                    if (placeholder and ("search" in placeholder.lower() or "filter" in placeholder.lower() or "place" in placeholder.lower())) or \
                       (aria_label and ("search" in aria_label.lower() or "filter" in aria_label.lower())):
                        search_input = inp
                        print(f"   ✓ Found search input!")
                        break
                except:
                    pass

        except Exception as e:
            print(f"   Error finding search input: {e}")

        if not search_input:
            print("   ✗ Could not find search input - let me check the page structure...")

            # Print available elements
            page_structure = driver.execute_script("""
                const inputs = document.querySelectorAll('input');
                const results = [];

                inputs.forEach((inp, idx) => {
                    results.push({
                        type: inp.type,
                        placeholder: inp.placeholder,
                        value: inp.value,
                        visible: inp.offsetParent !== null,
                        class: inp.className
                    });
                });

                return results;
            """)

            print(f"   Page has {len(page_structure)} inputs:")
            for idx, inp in enumerate(page_structure):
                print(f"     {idx}: type={inp['type']}, placeholder='{inp['placeholder']}', visible={inp['visible']}")

        else:
            print("\n5. Testing place search...")

            # Test with a few search terms
            test_searches = ["Paris", "London", "Venice", "Rome", "Berlin", "Amsterdam"]

            place_results = {}

            for search_term in test_searches:
                print(f"\n   Searching for '{search_term}'...")

                # Clear input
                search_input.clear()
                time.sleep(0.5)

                # Type search term
                search_input.send_keys(search_term)
                time.sleep(2)

                # Extract results
                results = driver.execute_script("""
                    const results = [];

                    // Look for buttons or divs that show search results
                    const elements = document.querySelectorAll('button, [role="button"], div');

                    elements.forEach(elem => {
                        const text = elem.textContent.trim();

                        // Look for patterns like "CityName 1234"
                        const match = text.match(/^([A-Z][^\\d]*?)\\s+(\\d+(?:,\\d+)*)$/);

                        if (match) {
                            results.push({
                                name: match[1].trim(),
                                count: parseInt(match[2].replace(/,/g, ''))
                            });
                        }
                    });

                    return results;
                """)

                if results:
                    for res in results[:5]:
                        print(f"     - {res['name']}: {res['count']:,}")
                        place_results[res['name']] = res['count']
                else:
                    print(f"     - No results found")

            if place_results:
                print("\n" + "=" * 80)
                print("FOUND PLACES:")
                print("=" * 80)

                sorted_places = sorted(place_results.items(), key=lambda x: x[1], reverse=True)
                for idx, (place, count) in enumerate(sorted_places, 1):
                    print(f"{idx}. {place:40} {count:>10,}")

                # Save to CSV
                output_file = '/Users/nogashlomi/projects/yossi/RDF_project_copy/ustc_places_searched.csv'

                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['place', 'count'])
                    for place, count in sorted_places:
                        writer.writerow([place, count])

                print(f"\n✓ Saved to {output_file}")

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
