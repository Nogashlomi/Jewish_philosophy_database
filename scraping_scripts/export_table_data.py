#!/usr/bin/env python3
"""
Switch to TABLE view and extract all filtered records by city
"""

import time
import csv
import json
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
    print("EXTRACTING ALL RECORDS IN TABLE VIEW")
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

        # Click TABLE button
        print("\n2. Switching to TABLE view...")
        try:
            table_btns = driver.find_elements(By.XPATH, "//*[contains(text(), 'Table')]")
            if table_btns:
                table_btn = table_btns[0]
                driver.execute_script("arguments[0].click();", table_btn)
                time.sleep(3)
                print("   Switched to TABLE view")
            else:
                print("   Could not find TABLE button")
        except Exception as e:
            print(f"   Error: {e}")

        # Look for export options
        print("\n3. Looking for export/download options...")
        page_text = driver.find_element(By.TAG_NAME, "body").text

        export_options = []
        if 'download' in page_text.lower():
            export_options.append("Download option found")
        if 'export' in page_text.lower():
            export_options.append("Export option found")
        if 'csv' in page_text.lower():
            export_options.append("CSV option found")

        for opt in export_options:
            print(f"   ✓ {opt}")

        # Try to find and click a download/export button
        print("\n4. Attempting to download/export data...")
        found_export = False

        for button_text in ['Download CSV', 'Export', 'Download', 'CSV']:
            try:
                btns = driver.find_elements(By.XPATH, f"//*[contains(text(), '{button_text}')]")
                if btns:
                    print(f"   Found '{button_text}' button, clicking...")
                    btns[0].click()
                    time.sleep(2)
                    found_export = True
                    print(f"   ✓ Clicked {button_text}")
                    break
            except:
                pass

        if not found_export:
            print("   No export button found, will extract from visible table rows...")

        # Extract table data
        print("\n5. Extracting table data by city...")

        # Get all visible rows and extract place/city information
        cities_count = {}

        # Try multiple extraction strategies
        all_rows_text = driver.execute_script("""
            const rows = [];

            // Try to find all table rows
            const tableRows = document.querySelectorAll('tr, [role="row"]');
            console.log(`Found ${tableRows.length} rows`);

            tableRows.forEach(row => {
                const cells = row.querySelectorAll('td, [role="cell"]');
                if (cells.length > 0) {
                    const rowData = [];
                    cells.forEach(cell => {
                        rowData.push(cell.textContent.trim());
                    });
                    rows.push(rowData);
                }
            });

            return rows;
        """)

        print(f"   Found {len(all_rows_text)} table rows")

        if all_rows_text and len(all_rows_text) > 0:
            # Parse rows to find city/place column
            for row_idx, row in enumerate(all_rows_text[:10]):
                print(f"   Row {row_idx}: {row[:3]}...")  # Print first 3 cells

            # Look for city/place data in rows
            for row in all_rows_text:
                for cell in row:
                    # Check if this looks like a city name
                    if (cell and len(cell) > 3 and len(cell) < 60 and
                        cell[0].isupper() and cell.lower() != cell and
                        cell not in ['No.', 'Author', 'Title', 'Place', 'Date', 'Country']):

                        if cell in cities_count:
                            cities_count[cell] += 1
                        else:
                            cities_count[cell] = 1

            print(f"\n   Found {len(cities_count)} potential cities in table")

        else:
            print("   Could not extract table rows, trying alternative method...")

            # Alternative: look at all visible text that might be cities
            body_text = driver.find_element(By.TAG_NAME, "body").text
            lines = body_text.split('\n')

            for line in lines:
                line = line.strip()
                if (line and len(line) > 5 and len(line) < 50 and
                    line[0].isupper() and
                    'Paris' in line or 'London' in line or 'Venice' in line):
                    print(f"   Found city reference: {line}")

        # Try to get the actual data by scrolling through paginated results
        print("\n6. Scrolling through paginated results...")

        for scroll_num in range(5):
            print(f"   Scroll {scroll_num + 1}...", end=" ", flush=True)

            # Scroll down
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(1)

            # Look for "Load more" or "Next" button
            try:
                next_btn = driver.find_element(By.XPATH, "//*[contains(text(), 'Next')]")
                if next_btn.is_enabled():
                    print("Found Next button, clicking...")
                    next_btn.click()
                    time.sleep(2)
            except:
                print("End of results or no Next button")
                break

        # Final summary
        print("\n" + "=" * 80)

        if cities_count:
            sorted_cities = sorted(cities_count.items(), key=lambda x: x[1], reverse=True)
            print(f"FOUND {len(sorted_cities)} CITIES IN TABLE:")
            print("=" * 80)

            for city, count in sorted_cities[:20]:
                print(f"  {city:40} {count:>5} occurrences")

        else:
            print("Could not extract detailed city counts from table")
            print("\nTry manually clicking the TABLE button and looking for export options")

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
