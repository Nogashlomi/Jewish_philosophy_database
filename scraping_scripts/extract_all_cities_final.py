#!/usr/bin/env python3
"""
Systematically extract ALL cities from USTC table view by going through all pages
"""

import time
import csv
from collections import defaultdict
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

def extract_cities_from_current_page(driver):
    """Extract all cities from the current visible page"""
    try:
        cities = []

        # Get all rows from the table
        rows_data = driver.execute_script("""
            const rows = [];

            // Find all table rows
            const tableRows = document.querySelectorAll('tr, [role="row"]');

            tableRows.forEach((row, idx) => {
                if (idx === 0) return;  // Skip header

                const cells = row.querySelectorAll('td, [role="cell"]');
                if (cells.length >= 3) {
                    // The place/city is typically in the 3rd column
                    const place = cells[2]?.textContent?.trim() || '';

                    if (place && place.length > 0 && place.length < 100) {
                        rows.push(place);
                    }
                }
            });

            return rows;
        """)

        return rows_data

    except Exception as e:
        print(f"Error extracting rows: {e}")
        return []

def main():
    print("=" * 80)
    print("EXTRACTING ALL CITIES FROM USTC TABLE VIEW")
    print("=" * 80)
    print("\nThis will systematically go through all pages...")
    print("Progress will be shown every 100 records\n")

    driver = setup_driver()

    try:
        # Load page in table view
        print("1. Loading USTC table view (1470-1650)...")
        driver.get("https://www.ustc.ac.uk/explore?fqyf=1470&fqyt=1650")

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )

        time.sleep(3)

        # Switch to table view
        print("2. Switching to TABLE view...")
        try:
            table_btns = driver.find_elements(By.XPATH, "//*[contains(text(), 'Table')]")
            if table_btns:
                driver.execute_script("arguments[0].click();", table_btns[0])
                time.sleep(3)
                print("   ✓ Switched to table view")
        except Exception as e:
            print(f"   Could not switch: {e}")

        # Extract all cities by going through pages
        print("\n3. Extracting cities from all pages...")
        print("=" * 80)

        cities_count = defaultdict(int)
        total_records = 0
        page_num = 0
        max_attempts = 50  # Safety limit
        consecutive_empty_pages = 0

        while page_num < max_attempts:
            page_num += 1

            # Extract cities from current page
            page_cities = extract_cities_from_current_page(driver)

            if not page_cities:
                consecutive_empty_pages += 1
                if consecutive_empty_pages >= 2:
                    print(f"\nPage {page_num}: No records found (2 consecutive empty pages - end of results)")
                    break
            else:
                consecutive_empty_pages = 0

                for city in page_cities:
                    cities_count[city] += 1
                    total_records += 1

                if total_records % 100 == 0:
                    print(f"  ✓ {total_records:>6,} records processed | {len(cities_count):>4} unique cities")

            # Try to find and click next button
            try:
                next_clicked = driver.execute_script("""
                    const buttons = document.querySelectorAll('button, [role="button"], a');

                    for (let btn of buttons) {
                        const text = btn.textContent.toLowerCase();
                        if (text.includes('next') || text.includes('→')) {
                            if (!btn.disabled && btn.offsetParent !== null) {
                                btn.click();
                                return true;
                            }
                        }
                    }

                    return false;
                """)

                if not next_clicked:
                    print(f"\nPage {page_num}: Next button not found (end of results)")
                    break

            except Exception as e:
                print(f"\nPage {page_num}: Error finding next button: {e}")
                break

            time.sleep(1.5)

        # Print results
        print("\n" + "=" * 80)
        print(f"SCRAPING COMPLETE")
        print("=" * 80)
        print(f"\nTotal records extracted: {total_records:,}")
        print(f"Unique cities found: {len(cities_count)}\n")

        # Sort by count
        sorted_cities = sorted(cities_count.items(), key=lambda x: x[1], reverse=True)

        print("CITIES BY NUMBER OF EDITIONS (Top 50):")
        print("-" * 80)

        for idx, (city, count) in enumerate(sorted_cities[:50], 1):
            print(f"{idx:3}. {city:45} {count:>8,} editions")

        if len(sorted_cities) > 50:
            print(f"\n... and {len(sorted_cities) - 50} more cities")

        # Calculate totals
        total_in_sample = sum(count for _, count in sorted_cities)
        coverage = (total_in_sample / 843983) * 100

        print("\n" + "-" * 80)
        print(f"Total in this extraction: {total_in_sample:,} editions")
        print(f"Coverage: {coverage:.1f}% of all 1470-1650 editions")

        # Save ALL to CSV
        output_file = '/Users/nogashlomi/projects/yossi/RDF_project_copy/USTC_ALL_CITIES_FINAL.csv'

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['rank', 'city', 'editions_count'])
            for idx, (city, count) in enumerate(sorted_cities, 1):
                writer.writerow([idx, city, count])

        print(f"\n✓ SAVED ALL {len(sorted_cities)} CITIES to {output_file}")

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
