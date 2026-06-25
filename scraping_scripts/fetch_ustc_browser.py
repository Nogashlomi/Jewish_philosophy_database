#!/usr/bin/env python3
"""
Fetch USTC quantitative data using a headless browser
"""

import time
import csv
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

def setup_driver():
    """Setup Chrome WebDriver"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def get_edition_count(driver, from_year, to_year):
    """Fetch edition count for a year range"""
    try:
        url = f"https://www.ustc.ac.uk/explore?fqyf={from_year}&fqyt={to_year}"
        driver.get(url)

        # Wait for the page to load and find the results text
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Showing')]"))
        )

        # Get page text
        page_text = driver.find_element(By.TAG_NAME, "body").text

        # Extract count from "Showing 1-20 of XXXXXX results"
        match = re.search(r'Showing \d+-\d+ of ([\d,]+) results', page_text)
        if match:
            count_str = match.group(1).replace(',', '')
            return int(count_str)
        else:
            print(f"  Warning: Could not find count in page for {from_year}-{to_year}")
            # Try alternative pattern
            match = re.search(r'of (\d+) results', page_text)
            if match:
                return int(match.group(1))
        return None

    except Exception as e:
        print(f"  Error fetching data for {from_year}-{to_year}: {e}")
        return None

def main():
    print("Fetching USTC data for European editions (1470-1650)...")
    print("=" * 70)

    driver = setup_driver()

    try:
        data = []

        # 20-year intervals from 1470 to 1650
        start_year = 1470
        end_year = 1650
        interval = 20

        for year in range(start_year, end_year, interval):
            from_year = year
            to_year = min(year + interval - 1, end_year)

            print(f"\nFetching data for {from_year:4d}-{to_year:4d}...", end=" ", flush=True)

            count = get_edition_count(driver, from_year, to_year)

            if count is not None:
                print(f"✓ {count:>10,} editions")
                data.append({
                    'period': f"{from_year}-{to_year}",
                    'from_year': from_year,
                    'to_year': to_year,
                    'count': count
                })
            else:
                print("✗ Failed to retrieve")

            # Wait a bit between requests to avoid overloading the server
            time.sleep(1)

        # Save to CSV
        output_file = '/Users/nogashlomi/projects/yossi/RDF_project_copy/ustc_europe_1470_1650.csv'

        print("\n" + "=" * 70)
        print(f"\nSaving data to {output_file}...")

        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['period', 'from_year', 'to_year', 'count'])
            writer.writeheader()
            writer.writerows(data)

        print(f"✓ Data saved successfully!")

        print("\n" + "=" * 70)
        print("Summary:")
        print("-" * 70)
        for row in data:
            print(f"{row['period']}: {row['count']:>10,} editions")

        total = sum(row['count'] for row in data)
        print("-" * 70)
        print(f"{'TOTAL':20}: {total:>10,} editions")
        print("=" * 70)

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
