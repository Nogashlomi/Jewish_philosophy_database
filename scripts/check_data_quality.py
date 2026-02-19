
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.core.rdf_store import rdf_store, JP
from rdflib import RDF, RDFS

def check_quality():
    print("Loading data...")
    rdf_store.load_data()
    g = rdf_store.g
    
    # 1. Check Astronomy Links
    print("\n--- Checking Astronomy Links ---")
    astronomy_uri = JP.Subject_Astronomy
    works = list(g.subjects(JP.hasSubject, astronomy_uri))
    print(f"Found {len(works)} works linked to Astronomy.")
    for w in works[:5]:
        print(f"  - {w}")

    # 2. Check Person Duplicates (by Label)
    print("\n--- Checking Person Duplicates ---")
    persons = {}
    for s in g.subjects(RDF.type, JP.HistoricalPerson):
        label = str(g.value(s, RDFS.label))
        if label not in persons:
            persons[label] = []
        persons[label].append(s)
    
    dup_count = 0
    for label, uris in persons.items():
        if len(uris) > 1:
            dup_count += 1
            print(f"Duplicate Person: '{label}' -> {len(uris)} URIs")
            for u in uris:
                print(f"    {u}")
            if dup_count > 10:
                print("... (stopping list)")
                break
    print(f"Total Person Labels with Multiples: {dup_count}")

    # 3. Check Work Duplicates (by Title)
    print("\n--- Checking Work Duplicates ---")
    works_map = {}
    for s in g.subjects(RDF.type, JP.HistoricalWork):
        title = str(g.value(s, JP.title))
        if title == "None":
             title = str(g.value(s, RDFS.label))
        
        if title not in works_map:
            works_map[title] = []
        works_map[title].append(s)

    dup_count = 0
    for title, uris in works_map.items():
        if len(uris) > 1:
            dup_count += 1
            print(f"Duplicate Work: '{title}' -> {len(uris)} URIs")
            if dup_count > 10:
                print("... (stopping list)")
                break

    print(f"Total Work Titles with Multiples: {dup_count}")

if __name__ == "__main__":
    check_quality()
