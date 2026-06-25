#!/usr/bin/env python3
"""
Inspect the actual place filter links to understand USTC's URL format
"""

import time
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
    options.add_argument('--window-size=1920,1200')

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def main():
    print("=" * 80)
    print("INSPECTING PLACE FILTER LINKS IN USTC")
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

        # Click Settings
        print("\n2. Expanding Settings...")
        try:
            settings_btn = driver.find_element(By.XPATH, "//*[contains(text(), 'Settings')]")
            driver.execute_script("arguments[0].click();", settings_btn)
            time.sleep(2)
        except:
            pass

        # Click PLACE
        print("\n3. Expanding PLACE filter...")
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
        except:
            pass

        # Extract all links and buttons in the place filter area
        print("\n4. Extracting place filter links...")

        links_data = driver.execute_script("""
            const data = {
                buttons: [],
                links: [],
                hrefs: []
            };

            // Get all buttons and their attributes
            const buttons = document.querySelectorAll('button, [role="button"], a');

            buttons.forEach((elem, idx) => {
                const text = elem.textContent.trim();
                const href = elem.href || '';
                const onclick = elem.onclick ? 'has onclick' : '';

                // Look for city names (capitalized, reasonable length)
                if (text && text.length > 2 && text.length < 80 && text[0] === text[0].toUpperCase()) {
                    // Skip UI elements
                    if (!text.match(/^(Total|Showing|Settings|Filters|Hide|Clear|Sort|Download|From|To|Results?|Editions?|Next|Previous|Page|Home|Search|Place|PLACE)$/i)) {
                        data.buttons.push({
                            text: text,
                            tag: elem.tagName,
                            href: href,
                            class: elem.className
                        });

                        if (href) {
                            data.hrefs.push(href);
                        }
                    }
                }
            });

            return data;
        """)

        print(f"\n   Found {len(links_data['buttons'])} potential place buttons/links:")
        print("   " + "-" * 70)

        for idx, item in enumerate(links_data['buttons'][:15]):
            print(f"   {idx+1}. {item['text']:30} | href: {item['href'][:80] if item['href'] else 'none'}")

        if links_data['hrefs']:
            print("\n   Sample URLs from place filter:")
            print("   " + "-" * 70)
            for url in links_data['hrefs'][:5]:
                print(f"   {url}")

                # Extract the place filter parameter
                match = re.search(r'fqr=([^&]+)', url)
                if match:
                    print(f"      → fqr parameter: {match.group(1)}")

        # Try clicking on a city button and seeing the URL change
        print("\n5. Testing city selection...")

        try:
            # Find buttons that might be city names
            buttons = driver.find_elements(By.TAG_NAME, "button")

            for btn in buttons:
                text = btn.text.strip()
                if text in ['Paris', 'London', 'Venice', 'Lyon', 'Antwerp']:
                    print(f"\n   Found '{text}' button, clicking...")

                    # Get current URL
                    current_url = driver.current_url
                    print(f"   Current URL: {current_url}")

                    # Click the button
                    btn.click()
                    time.sleep(2)

                    # Get new URL
                    new_url = driver.current_url
                    print(f"   New URL: {new_url}")

                    # Extract the difference
                    if current_url != new_url:
                        print(f"   ✓ URL changed!")

                        # Parse parameters
                        import urllib.parse
                        parsed_new = urllib.parse.parse_qs(urllib.parse.urlparse(new_url).query)
                        parsed_old = urllib.parse.parse_qs(urllib.parse.urlparse(current_url).query)

                        for key in parsed_new:
                            if key not in parsed_old or parsed_new[key] != parsed_old[key]:
                                print(f"   Changed: {key}={parsed_new[key]}")

                    break

        except Exception as e:
            print(f"   Error: {e}")

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
