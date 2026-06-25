#!/usr/bin/env python3
"""
Search for top 20 cities using alternative names and spellings
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

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def get_count_for_city(driver, city_name):
    """Get edition count for a specific city - try multiple spellings"""
    try:
        # Try different URL parameter names
        for param_name in ['fqp', 'place', 'fqplace']:
            for city_variant in [city_name, city_name.replace(' ', '%20')]:
                try:
                    url = f"https://www.ustc.ac.uk/explore?{param_name}={city_variant}&fqyf=1470&fqyt=1650"
                    driver.get(url)
                    time.sleep(1)

                    body_text = driver.find_element(By.TAG_NAME, "body").text

                    # Look for result count
                    match = re.search(r'Showing \d+-\d+ of ([\d,]+) results', body_text)
                    if match:
                        count = int(match.group(1).replace(',', ''))
                        if count > 0:
                            return count, param_name

                except:
                    pass

        return 0, None

    except:
        return -1, None

def main():
    print("=" * 80)
    print("TOP 20 EUROPEAN PRINTING CENTERS (1470-1650)")
    print("=" * 80)

    # Known top 5 + alternatives for others
    cities_with_variants = [
        # Top 5 (confirmed)
        ("Paris", ["Paris"], 81115),
        ("London", ["London"], 58862),
        ("Venice", ["Venezia", "Venice"], 45461),
        ("Lyon", ["Lyon", "Lyons"], 29395),
        ("Antwerp", ["Antwerpen", "Antwerp"], 25789),

        # Other major centers - with multiple spelling variants
        ("Rome", ["Roma", "Rome"], None),
        ("Milan", ["Milano", "Milan"], None),
        ("Florence", ["Firenze", "Florence"], None),
        ("Bologna", ["Bologna"], None),
        ("Naples", ["Napoli", "Naples", "Neapoli"], None),
        ("Rouen", ["Rouen"], None),
        ("Toulouse", ["Toulouse"], None),
        ("Strasbourg", ["Strasbourg", "Strassburg", "Straßburg"], None),
        ("Cologne", ["Köln", "Cologne", "Koeln", "Cologn"], None),
        ("Frankfurt", ["Frankfurt", "Frankfort"], None),
        ("Basel", ["Basel", "Basle", "Bale"], None),
        ("Wittenberg", ["Wittenberg"], None),
        ("Amsterdam", ["Amsterdam"], None),
        ("Leiden", ["Leiden", "Leyden"], None),
        ("Leuven", ["Leuven", "Louvain"], None),
        ("Salamanca", ["Salamanca"], None),
        ("Alcalá", ["Alcalá de Henares", "Alcala"], None),
    ]

    driver = setup_driver()

    try:
        print(f"\nSearching for major printing centers...\n")

        results = {}

        for idx, (city, variants, known_count) in enumerate(cities_with_variants, 1):
            if known_count:
                print(f"{idx:2}. {city:30} (confirmed) {known_count:>10,} editions")
                results[city] = known_count
            else:
                print(f"{idx:2}. {city:30} trying variants...", end=" ", flush=True)

                found_count = 0
                found_variant = None

                for variant in variants:
                    count, param = get_count_for_city(driver, variant)
                    if count > 0:
                        found_count = count
                        found_variant = variant
                        break

                if found_count > 0:
                    print(f"✓ {found_count:>10,} ('{found_variant}')")
                    results[city] = found_count
                else:
                    print("0 results")

                time.sleep(0.5)

        # Sort and display
        print("\n" + "=" * 80)
        print("RESULTS (sorted by edition count):")
        print("=" * 80)

        sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)

        total = 0
        for idx, (city, count) in enumerate(sorted_results, 1):
            if count > 0:
                print(f"{idx:2}. {city:35} {count:>10,} editions")
                total += count

        print("=" * 80)
        print(f"{'TOTAL':38} {total:>10,} editions")
        print(f"Coverage: {(total/843983)*100:.1f}%\n")

        # Save to CSV
        output_file = '/Users/nogashlomi/projects/yossi/RDF_project_copy/ustc_top_centers.csv'

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['rank', 'city', 'count'])
            for idx, (city, count) in enumerate(sorted_results, 1):
                if count > 0:
                    writer.writerow([idx, city, count])

        print(f"✓ Saved to {output_file}")

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
