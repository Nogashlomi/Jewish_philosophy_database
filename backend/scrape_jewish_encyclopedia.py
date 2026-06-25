import requests
from bs4 import BeautifulSoup
import csv
import time
import re
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

BASE_URL = "https://www.jewishencyclopedia.com"
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "../data/jewish_encyclopedia_raw.csv")

BORN_PATTERN = re.compile(r'born\s+(?:in|at)\s+([^,;]+)(?:,|\s)([^;]*?\d{3,4})', re.IGNORECASE)
DIED_PATTERN = re.compile(r'died\s+(?:in|at|after|before)\s+([^,;]+)(?:,|\s)([^;]*?\d{3,4})', re.IGNORECASE)
PERSON_FILTER_PATTERN = re.compile(r'(?:born|died)\s+.*?(\d{3,4})', re.IGNORECASE)

def extract_bio_data(snippet):
    data = {
        'Birth Place': '',
        'Birth Year': '',
        'Death Place': '',
        'Death Year': ''
    }
    born_match = BORN_PATTERN.search(snippet)
    if born_match:
        data['Birth Place'] = born_match.group(1).strip()
        data['Birth Year'] = born_match.group(2).strip()
        
    died_match = DIED_PATTERN.search(snippet)
    if died_match:
        data['Death Place'] = died_match.group(1).strip()
        data['Death Year'] = died_match.group(2).strip()
        
    if not born_match and 'born' in snippet.lower():
        fallback_born = re.search(r'born\s+([^;]+)', snippet, re.IGNORECASE)
        if fallback_born:
            data['Birth Year'] = fallback_born.group(1).strip()
            
    if not died_match and 'died' in snippet.lower():
        fallback_died = re.search(r'died\s+([^;]+)', snippet, re.IGNORECASE)
        if fallback_died:
            data['Death Year'] = fallback_died.group(1).strip()
            
    return data

def scrape_encyclopedia():
    logging.info("Fetching homepage to find directory links...")
    res = requests.get(BASE_URL)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # Find all directory links
    dir_links = []
    nav = soup.find('ul', id='nav')
    if nav:
        for a in nav.find_all('a', href=re.compile(r'^/directory/')):
            dir_links.append(a['href'])
            
    logging.info(f"Found {len(dir_links)} base directory sections.")
    
    all_records = []
    
    # We will just scrape the first few to test, or we can do all. 
    # Let's do a fast scrape by following all links.
    for dir_link in dir_links:
        current_url = BASE_URL + dir_link
        
        while current_url:
            logging.info(f"Scraping {current_url}")
            try:
                page_res = requests.get(current_url, timeout=10)
                page_soup = BeautifulSoup(page_res.text, 'html.parser')
                
                table = page_soup.find('table', class_='searchresults')
                if table:
                    rows = table.find_all('tr')
                    for row in rows:
                        td = row.find('td')
                        if not td: continue
                        
                        a_tag = td.find('a')
                        if not a_tag: continue
                        
                        name = a_tag.text.strip()
                        article_url = BASE_URL + a_tag['href']
                        
                        snippet = td.text.replace(name, '', 1).strip()
                        snippet = snippet.lstrip("–").lstrip("-").strip()
                        
                        # Only keep if it looks like a person
                        if PERSON_FILTER_PATTERN.search(snippet):
                            bio_data = extract_bio_data(snippet)
                            all_records.append({
                                'Name': name,
                                'Birth Year': bio_data['Birth Year'],
                                'Death Year': bio_data['Death Year'],
                                'Birth Place': bio_data['Birth Place'],
                                'Death Place': bio_data['Death Place'],
                                'Article URL': article_url,
                                'Raw Text Snippet': snippet
                            })
                
                # Check for next page
                next_span = page_soup.find('span', class_='next')
                if next_span and next_span.find('a'):
                    next_href = next_span.find('a')['href']
                    current_url = BASE_URL + next_href
                else:
                    current_url = None
                    
            except Exception as e:
                logging.error(f"Failed on {current_url}: {e}")
                current_url = None
                
            time.sleep(0.2) # be polite

    logging.info(f"Writing {len(all_records)} records to {OUTPUT_CSV}")
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Name', 'Birth Year', 'Death Year', 'Birth Place', 'Death Place', 'Article URL', 'Raw Text Snippet'])
        writer.writeheader()
        writer.writerows(all_records)
        
    logging.info("Done.")

if __name__ == "__main__":
    scrape_encyclopedia()
