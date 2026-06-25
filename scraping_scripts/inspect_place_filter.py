#!/usr/bin/env python3
"""
Directly inspect and interact with USTC's PLACE filter using JavaScript
"""

import time
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
    print("INSPECTING USTC PLACE FILTER")
    print("=" * 80)

    driver = setup_driver()

    try:
        # Load page
        print("\n1. Loading USTC explore page...")
        driver.get("https://www.ustc.ac.uk/explore?fqyf=1470&fqyt=1650")

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        time.sleep(3)

        print("   Page loaded\n")

        # Use JavaScript to deeply inspect the page structure
        print("2. Inspecting page structure with JavaScript...")

        result = driver.execute_script("""
            console.log("Starting inspection");

            let findings = {
                buttons: [],
                divs_with_place: [],
                all_text_with_numbers: [],
                react_data: {},
                vue_data: {},
                angular_data: {}
            };

            // Look for all buttons and their text content
            const buttons = document.querySelectorAll('button');
            console.log(`Found ${buttons.length} buttons`);

            buttons.forEach((btn, idx) => {
                const text = btn.textContent.trim();
                if (text && text.length < 100) {
                    findings.buttons.push({
                        idx: idx,
                        text: text,
                        class: btn.className,
                        onclick: btn.onclick ? 'has onclick' : 'no onclick'
                    });
                }
            });

            // Look for divs that might contain place data
            const allDivs = document.querySelectorAll('div');
            allDivs.forEach((div, idx) => {
                const text = div.textContent;
                if (text && text.toLowerCase().includes('place') && text.length < 500) {
                    findings.divs_with_place.push({
                        idx: idx,
                        text: text.substring(0, 200),
                        class: div.className,
                        id: div.id
                    });
                }
            });

            // Look for any React, Vue, or Angular component data
            if (window.__REACT_DEVTOOLS_GLOBAL_HOOK__) {
                findings.react_data.found = true;
            }
            if (window.__vue__) {
                findings.vue_data.found = true;
            }
            if (window.ng) {
                findings.angular_data.found = true;
            }

            // Look for all text nodes that contain both city names and numbers
            const walker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_TEXT,
                null
            );

            let node;
            const text_nodes = [];
            while (node = walker.nextNode()) {
                const text = node.textContent.trim();
                if (text && text.match(/^[A-Z][a-z]+\\s+\\d+/) && text.length < 100) {
                    text_nodes.push(text);
                }
            }

            if (text_nodes.length > 0) {
                findings.all_text_with_numbers = text_nodes.slice(0, 50);
            }

            return findings;
        """)

        print("   Findings:")
        print(f"     - Buttons found: {len(result['buttons'])}")
        print(f"     - Divs with 'place': {len(result['divs_with_place'])}")
        print(f"     - Text nodes with city patterns: {len(result['all_text_with_numbers'])}")
        print(f"     - React detected: {result['react_data']}")

        # Print sample buttons
        if result['buttons']:
            print("\n   Sample buttons:")
            for btn in result['buttons'][:10]:
                print(f"      - {btn['text'][:50]}")

        # Print sample text nodes with numbers
        if result['all_text_with_numbers']:
            print("\n   Sample text with city-number patterns:")
            for text in result['all_text_with_numbers'][:10]:
                print(f"      - {text}")

        # Now try to find the PLACE button and click it
        print("\n3. Interacting with PLACE filter...")

        click_result = driver.execute_script("""
            // Find and click the PLACE label/button
            const labels = Array.from(document.querySelectorAll('label, button, div'));

            for (let elem of labels) {
                if (elem.textContent.trim() === 'place' ||
                    elem.textContent.trim() === 'PLACE' ||
                    (elem.textContent.includes('place') && elem.textContent.length < 20)) {

                    console.log(`Found PLACE element: ${elem.tagName}`);
                    elem.click();

                    return {
                        success: true,
                        element_type: elem.tagName,
                        text: elem.textContent.trim()
                    };
                }
            }

            return { success: false };
        """)

        print(f"   PLACE click result: {click_result}")

        time.sleep(2)

        # Extract visible places after clicking
        print("\n4. Extracting visible places...")

        places = driver.execute_script("""
            const places = {};

            // Strategy 1: Look for visible text that matches city names with numbers
            const bodyText = document.body.innerText;
            const lines = bodyText.split('\\n');

            for (let i = 0; i < lines.length - 1; i++) {
                const line = lines[i].trim();
                const next = lines[i + 1].trim();

                // City name pattern: starts with capital, not all caps, reasonable length
                if (line &&
                    line.length > 2 &&
                    line.length < 50 &&
                    line[0] === line[0].toUpperCase() &&
                    line !== line.toUpperCase() &&
                    /^\\d+(?:,\\d+)*$/.test(next.replace(/[^\\d,]/g, ''))) {

                    const cityName = line;
                    const count = parseInt(next.replace(/[^\\d]/g, ''));

                    if (count > 0 && cityName !== 'Place' && cityName !== 'PLACE') {
                        places[cityName] = count;
                    }
                }
            }

            // Strategy 2: Look for button elements that might contain place data
            const buttons = document.querySelectorAll('button');
            buttons.forEach(btn => {
                const text = btn.textContent.trim();
                if (text && text.length > 5 && text.length < 50) {
                    const match = text.match(/^([A-Z][a-z]+(?:\\s+[A-Z][a-z]+)*)\\s+(\\d+(?:,\\d+)*)$/);
                    if (match) {
                        places[match[1]] = parseInt(match[2].replace(/,/g, ''));
                    }
                }
            });

            return places;
        """)

        print(f"   Found {len(places)} places:")
        sorted_places = sorted(places.items(), key=lambda x: x[1], reverse=True)
        for city, count in sorted_places:
            print(f"      - {city}: {count:,}")

        # Try scrolling and capturing more
        print("\n5. Attempting to scroll and capture more places...")

        driver.execute_script("""
            // Find and scroll any overflow containers
            const containers = document.querySelectorAll('[style*="overflow"], [class*="overflow"]');
            console.log(`Found ${containers.length} overflow containers`);

            containers.forEach((cont, idx) => {
                if (cont.scrollHeight > cont.clientHeight) {
                    console.log(`Scrolling container ${idx}`);
                    cont.scrollTop = cont.scrollHeight;
                }
            });
        """)

        time.sleep(2)

        # Capture again after scrolling
        places_after_scroll = driver.execute_script("""
            const places = {};

            const bodyText = document.body.innerText;
            const lines = bodyText.split('\\n');

            for (let i = 0; i < lines.length - 1; i++) {
                const line = lines[i].trim();
                const next = lines[i + 1].trim();

                if (line &&
                    line.length > 2 &&
                    line.length < 50 &&
                    line[0] === line[0].toUpperCase() &&
                    line !== line.toUpperCase() &&
                    /^\\d+(?:,\\d+)*$/.test(next.replace(/[^\\d,]/g, ''))) {

                    const cityName = line;
                    const count = parseInt(next.replace(/[^\\d]/g, ''));

                    if (count > 0 && cityName !== 'Place' && cityName !== 'PLACE') {
                        places[cityName] = count;
                    }
                }
            }

            return places;
        """)

        print(f"   After scrolling: {len(places_after_scroll)} places")
        if len(places_after_scroll) > len(places):
            sorted_places_2 = sorted(places_after_scroll.items(), key=lambda x: x[1], reverse=True)
            for city, count in sorted_places_2:
                print(f"      - {city}: {count:,}")

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
