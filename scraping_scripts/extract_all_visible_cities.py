#!/usr/bin/env python3
"""
Extract ALL visible cities by scrolling through the page
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
    print("EXTRACTING ALL VISIBLE CITIES - WITH SCROLLING")
    print("=" * 80)

    driver = setup_driver()

    try:
        # Load page
        print("\n1. Loading USTC explore page (1470-1650)...")
        driver.get("https://www.ustc.ac.uk/explore?fqyf=1470&fqyt=1650")

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )

        print("   Page loaded")
        time.sleep(3)

        # Click Settings
        print("\n2. Expanding Settings/Filters...")
        try:
            settings_btn = driver.find_element(By.XPATH, "//*[contains(text(), 'Settings')]")
            settings_btn.click()
            time.sleep(2)
        except:
            pass

        # Click PLACE filter
        print("\n3. Clicking PLACE filter...")
        try:
            place_elem = None
            selectors = [
                "//*[text()='place']",
                "//label[contains(text(), 'place')]",
                "//div[contains(text(), 'place')]"
            ]

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

        # Now scroll the page and capture all visible city data
        print("\n4. Scrolling page and extracting all cities...")

        all_cities = {}
        scroll_attempts = 0
        max_scrolls = 20

        while scroll_attempts < max_scrolls:
            # Extract visible cities
            cities_data = driver.execute_script("""
                const cities = {};
                const mainElement = document.querySelector('main');

                if (mainElement) {
                    const text = mainElement.innerText;
                    const lines = text.split('\\n');

                    for (let i = 0; i < lines.length - 1; i++) {
                        const line = lines[i].trim();
                        const nextLine = lines[i + 1].trim();

                        if (!line || !nextLine) continue;

                        const numberMatch = nextLine.match(/^(\\d+(?:,\\d+)*)$/);

                        if (numberMatch) {
                            if (line.length > 2 &&
                                line.length < 60 &&
                                line[0] === line[0].toUpperCase() &&
                                line.toLowerCase() !== line &&
                                !line.match(/^(Total|Showing|No\\.|Settings|Filters|Hide|Clear|Sort|Download|From|To|Results?|Editions?|SUBJECT|Place|Next|Previous)$/i) &&
                                !line.match(/^\\d/) &&
                                !line.includes('[') &&
                                !line.includes('(')) {

                                const city = line;
                                const count = parseInt(numberMatch[1].replace(/,/g, ''));

                                if (count > 0) {
                                    cities[city] = count;
                                }
                            }
                        }
                    }
                }

                return cities;
            """)

            # Update all_cities with new data
            for city, count in cities_data.items():
                if city not in all_cities:
                    all_cities[city] = count

            new_cities = len(cities_data)
            total_unique = len(all_cities)

            if new_cities > 0:
                print(f"   Scroll {scroll_attempts + 1}: Found {new_cities} cities (total unique: {total_unique})")

            # Scroll down
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(1)

            scroll_attempts += 1

        print(f"\n   Total unique cities found: {len(all_cities)}")

        if all_cities:
            # Sort by count
            sorted_cities = sorted(all_cities.items(), key=lambda x: x[1], reverse=True)

            print("\n   " + "=" * 70)
            print("   CITIES FOUND:")
            print("   " + "=" * 70)

            total = 0
            for idx, (city, count) in enumerate(sorted_cities, 1):
                print(f"   {idx:4}. {city:45} {count:>10,}")
                total += count

            print("   " + "=" * 70)
            print(f"   {'TOTAL':50} {total:>10,}")
            print(f"   Coverage: {(total/843983)*100:.1f}%\n")

            # Save to CSV
            output_file = '/Users/nogashlomi/projects/yossi/RDF_project_copy/ustc_all_cities_complete.csv'

            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['rank', 'city', 'count'])
                for idx, (city, count) in enumerate(sorted_cities, 1):
                    writer.writerow([idx, city, count])

            print(f"✓ Data saved to {output_file}\n")

        else:
            print("   ✗ No cities found")

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
