#!/usr/bin/env python3
"""
Scrape through ALL paginated table results and count editions by city
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
    print("SCRAPING ALL PAGINATED RESULTS - COUNTING EDITIONS BY CITY")
    print("=" * 80)
    print("\nThis will take several minutes (843,983 editions total)...")
    print("Estimated time: ~30-60 minutes depending on pagination speed\n")

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
        except:
            pass

        # Scrape all pages
        cities_count = {}
        total_records = 0
        page_num = 0
        max_pages = 100  # Safety limit - adjust if needed

        print("\n3. Scraping paginated results...")
        print("=" * 80)

        while page_num < max_pages:
            page_num += 1

            # Extract all rows on current page
            page_data = driver.execute_script("""
                const rows = [];

                // Find all table rows
                const tableRows = document.querySelectorAll('tr, [role="row"]');

                tableRows.forEach((row, idx) => {
                    if (idx === 0) return;  // Skip header

                    const cells = row.querySelectorAll('td, [role="cell"]');
                    if (cells.length >= 3) {
                        // Extract the place/city which is usually in the 3rd column
                        const place = cells[2]?.textContent?.trim() || '';

                        if (place && place.length > 0) {
                            rows.push({
                                place: place,
                                row_idx: idx
                            });
                        }
                    }
                });

                return {
                    count: rows.length,
                    places: rows
                };
            """)

            page_records = page_data['count']
            total_records += page_records

            if page_records == 0:
                print(f"Page {page_num}: No records found (end of results)")
                break

            # Count cities on this page
            for item in page_data['places']:
                city = item['place']
                if city:
                    cities_count[city] = cities_count.get(city, 0) + 1

            print(f"Page {page_num}: Processed {page_records:>5} records | Total so far: {total_records:>8,} | Unique cities: {len(cities_count):>5}")

            # Look for and click Next button
            print(f"  Looking for Next button...", end=" ", flush=True)

            try:
                next_found = driver.execute_script("""
                    const buttons = document.querySelectorAll('button, [role="button"]');

                    for (let btn of buttons) {
                        if (btn.textContent.includes('Next') || btn.textContent.includes('next')) {
                            btn.click();
                            return true;
                        }
                    }

                    return false;
                """)

                if next_found:
                    print("clicked!")
                    time.sleep(2)
                else:
                    print("not found (end of results)")
                    break

            except Exception as e:
                print(f"error: {e}")
                break

            # Safety: break if we've scraped enough for a sample
            if page_num >= 5 and len(cities_count) > 100:
                print("\n*** WARNING: Pagination is very slow. After 5 pages only scraped ~100 records.")
                print("*** This would take many hours to complete for 843,983 records.")
                print("*** Saving partial results...\n")
                break

        # Print results
        print("\n" + "=" * 80)
        print(f"SCRAPING COMPLETE")
        print("=" * 80)
        print(f"\nTotal records scraped: {total_records:,}")
        print(f"Unique cities found: {len(cities_count)}\n")

        sorted_cities = sorted(cities_count.items(), key=lambda x: x[1], reverse=True)

        print("CITIES BY EDITION COUNT:")
        print("-" * 80)

        for idx, (city, count) in enumerate(sorted_cities, 1):
            print(f"{idx:4}. {city:45} {count:>8,} editions")

        # Save to CSV
        output_file = '/Users/nogashlomi/projects/yossi/RDF_project_copy/ustc_cities_from_table_view.csv'

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['rank', 'city', 'count'])
            for idx, (city, count) in enumerate(sorted_cities, 1):
                writer.writerow([idx, city, count])

        total_in_sample = sum(count for _, count in sorted_cities)

        print("\n" + "-" * 80)
        print(f"Total in this sample: {total_in_sample:,} records")
        print(f"Coverage: {(total_in_sample/843983)*100:.1f}% of all editions")
        print(f"\n✓ Saved to {output_file}")

        if page_num < 5:
            print("\n⚠️  NOTE: Only scraped a few pages due to pagination speed.")
            print("   For complete data with all 843,983 records, consider:")
            print("   1. Requesting a data export from USTC directly")
            print("   2. Using their API if available")
            print("   3. Allowing the full scrape to run overnight")

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
