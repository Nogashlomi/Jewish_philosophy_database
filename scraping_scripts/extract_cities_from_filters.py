#!/usr/bin/env python3
"""
Extract all cities from USTC place filter - targeting the visible list below chart
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
    options.add_argument('--window-size=1920,1080')

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def main():
    print("=" * 80)
    print("EXTRACTING CITIES FROM USTC PLACE FILTER")
    print("=" * 80)

    driver = setup_driver()

    try:
        # Load page
        print("\n1. Loading USTC explore page (1470-1650)...")
        driver.get("https://www.ustc.ac.uk/explore?fqyf=1470&fqyt=1650")

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )

        print("   Page loaded\n")
        time.sleep(3)

        # Click on Settings to expand filters
        print("2. Looking for Settings/Filters section...")
        try:
            settings_btn = driver.find_element(By.XPATH, "//*[contains(text(), 'Settings')]")
            print("   Found Settings button, clicking...")
            settings_btn.click()
            time.sleep(2)
        except:
            print("   Settings button not found, continuing...")

        # Look for PLACE label and click it
        print("\n3. Finding and clicking PLACE filter...")
        try:
            place_elem = None
            # Try different selectors
            selectors = [
                "//*[text()='place']",
                "//*[text()='PLACE']",
                "//*[contains(text(), 'place')]",
                "//label[contains(text(), 'place')]",
                "//button[contains(text(), 'place')]",
                "//div[contains(text(), 'place')]"
            ]

            for selector in selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        if elem.is_displayed():
                            text = elem.text.strip().lower()
                            if text == 'place':
                                place_elem = elem
                                break
                    if place_elem:
                        break
                except:
                    pass

            if place_elem:
                print(f"   Found PLACE element, clicking...")
                driver.execute_script("arguments[0].click();", place_elem)
                time.sleep(2)
            else:
                print("   Could not find PLACE element")

        except Exception as e:
            print(f"   Error: {e}")

        # Now extract all visible city-number pairs
        print("\n4. Extracting city data from page...")

        cities_data = driver.execute_script("""
            const cities = {};

            // Get the main content text
            const mainElement = document.querySelector('main');
            if (!mainElement) return cities;

            const text = mainElement.innerText;
            const lines = text.split('\\n');

            // Parse through lines looking for city name + count pairs
            for (let i = 0; i < lines.length - 1; i++) {
                const line = lines[i].trim();
                const nextLine = lines[i + 1].trim();

                // Skip empty lines
                if (!line || !nextLine) continue;

                // Check if next line is a number
                const numberMatch = nextLine.match(/^(\\d+(?:,\\d+)*)$/);

                if (numberMatch) {
                    // Check if current line looks like a place name
                    // Should start with capital letter, not be all caps, reasonable length
                    if (line.length > 2 &&
                        line.length < 60 &&
                        line[0] === line[0].toUpperCase() &&
                        line.toLowerCase() !== line &&
                        !line.match(/^(Total|Showing|No\\.|Settings|Filters|Hide|Clear|Sort|Download|From|To|Results?|Editions?)$/i) &&
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

            return cities;
        """)

        print(f"   Found {len(cities_data)} cities\n")

        if cities_data:
            # Sort by count
            sorted_cities = sorted(cities_data.items(), key=lambda x: x[1], reverse=True)

            print("   Cities found:")
            print("   " + "-" * 70)

            total = 0
            for idx, (city, count) in enumerate(sorted_cities, 1):
                print(f"   {idx:3}. {city:45} {count:>10,} editions")
                total += count

            print("   " + "-" * 70)
            print(f"   {'TOTAL':48} {total:>10,} editions")
            print(f"   Coverage: {(total/843983)*100:.1f}% of all European editions\n")

            # Save to CSV
            output_file = '/Users/nogashlomi/projects/yossi/RDF_project_copy/ustc_cities_from_filter.csv'

            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['city', 'count'])
                for city, count in sorted_cities:
                    writer.writerow([city, count])

            print(f"✓ Data saved to {output_file}")

        else:
            print("   ✗ No cities found - filter may not be expanded properly")
            print("\n   Trying alternative extraction method...")

            # Try getting all button text that might contain city data
            buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"   Found {len(buttons)} buttons on page")

            city_buttons = []
            for btn in buttons:
                text = btn.text.strip()
                if text and len(text) > 5 and len(text) < 60 and text[0].isupper():
                    city_buttons.append(text)

            print(f"   Potential city buttons: {city_buttons[:20]}")

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
