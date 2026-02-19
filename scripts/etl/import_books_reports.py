#!/usr/bin/env python3
"""
Import Books/Reports data with deduplication against Wikidata.
"""
import csv
import re
from rdflib import Graph, Namespace, RDF, RDFS, Literal, URIRef

JP = Namespace("http://jewish_philosophy.org/ontology#")

def extract_wikidata_qid(url_or_qid):
    """Extract QID from Wikidata URL or return QID if already in Q format."""
    if not url_or_qid:
        return None
    match = re.search(r'Q\d+', str(url_or_qid))
    return match.group(0) if match else None

def load_existing_wikidata_qids():
    """Load all existing Wikidata QIDs from wikidata_persons.ttl and wikidata_works.ttl."""
    qids = {'persons': set(), 'works': set(), 'places': set()}
    
    # Load persons
    g_persons = Graph()
    try:
        g_persons.parse("data/wikidata_persons.ttl", format="turtle")
        for person in g_persons.subjects(RDF.type, JP.HistoricalPerson):
            for auth in g_persons.objects(person, JP.authorityLink):
                qid = extract_wikidata_qid(auth)
                if qid:
                    qids['persons'].add(qid)
        print(f"Loaded {len(qids['persons'])} existing person QIDs")
    except Exception as e:
        print(f"Note: Could not load wikidata_persons.ttl: {e}")
    
    # Load works
    g_works = Graph()
    try:
        g_works.parse("data/wikidata_works.ttl", format="turtle")
        for work in g_works.subjects(RDF.type, JP.HistoricalWork):
            for auth in g_works.objects(work, JP.authorityLink):
                qid = extract_wikidata_qid(auth)
                if qid:
                    qids['works'].add(qid)
        print(f"Loaded {len(qids['works'])} existing work QIDs")
    except Exception as e:
        print(f"Note: Could not load wikidata_works.ttl: {e}")
    
    # Load places
    g_places = Graph()
    try:
        g_places.parse("data/wikidata_places.ttl", format="turtle")
        for place in g_places.subjects(RDF.type, JP.Place):
            for auth in g_places.objects(place, JP.authorityLink):
                qid = extract_wikidata_qid(auth)
                if qid:
                    qids['places'].add(qid)
        print(f"Loaded {len(qids['places'])} existing place QIDs")
    except Exception as e:
        print(f"Note: Could not load wikidata_places.ttl: {e}")
    
    return qids

def import_persons(csv_path, existing_qids):
    """Import persons from CSV, skipping those already in Wikidata."""
    g = Graph()
    g.bind("jp", JP)
    g.bind("rdfs", RDFS)
    
    imported = 0
    skipped = 0
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            qid = extract_wikidata_qid(row.get('wikidata_qid', ''))
            
            # Skip if already in Wikidata
            if qid and qid in existing_qids['persons']:
                skipped += 1
                print(f"  Skipping {row['name']} ({qid}) - already in Wikidata")
                continue
            
            # Create person entity
            if qid:
                person_id = f"Person_{qid}"
            else:
                # Create ID from name
                person_id = "Person_" + re.sub(r'[^a-zA-Z0-9]', '_', row['name'])
            
            person_uri = JP[person_id]
            g.add((person_uri, RDF.type, JP.HistoricalPerson))
            g.add((person_uri, RDFS.label, Literal(row['name'])))
            g.add((person_uri, JP.hasSource, JP.Source_BooksReports))
            
            # Add Wikidata link if available
            if qid:
                g.add((person_uri, JP.authorityLink, Literal(f"http://www.wikidata.org/entity/{qid}")))
            
            # Add birth/death years if available
            if row.get('birth_year'):
                g.add((person_uri, JP.birthYear, Literal(int(row['birth_year']))))
            if row.get('death_year'):
                g.add((person_uri, JP.deathYear, Literal(int(row['death_year']))))
            
            imported += 1
    
    print(f"\nPersons: Imported {imported}, Skipped {skipped} (already in Wikidata)")
    return g

def import_works(csv_path, existing_qids):
    """Import works from CSV, skipping those already in Wikidata."""
    g = Graph()
    g.bind("jp", JP)
    g.bind("rdfs", RDFS)
    
    imported = 0
    skipped = 0
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            qid = extract_wikidata_qid(row.get('wikidata_qid', ''))
            
            # Skip if already in Wikidata
            if qid and qid in existing_qids['works']:
                skipped += 1
                print(f"  Skipping {row['title']} ({qid}) - already in Wikidata")
                continue
            
            # Create work entity
            if qid:
                work_id = f"Work_{qid}"
            else:
                # Create ID from title
                work_id = "Work_" + re.sub(r'[^a-zA-Z0-9]', '_', row['title'][:50])
            
            work_uri = JP[work_id]
            g.add((work_uri, RDF.type, JP.HistoricalWork))
            g.add((work_uri, RDFS.label, Literal(row['title'])))
            g.add((work_uri, JP.hasSource, JP.Source_BooksReports))
            
            # Add Wikidata link if available
            if qid:
                g.add((work_uri, JP.authorityLink, Literal(f"http://www.wikidata.org/entity/{qid}")))
            
            # Add language if available
            if row.get('language'):
                g.add((work_uri, JP.language, Literal(row['language'])))
            
            imported += 1
    
    print(f"Works: Imported {imported}, Skipped {skipped} (already in Wikidata)")
    return g

def import_places(csv_path, existing_qids):
    """Import places from CSV, skipping those already in Wikidata."""
    g = Graph()
    g.bind("jp", JP)
    g.bind("rdfs", RDFS)
    
    imported = 0
    skipped = 0
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            qid = extract_wikidata_qid(row.get('wikidata_qid', ''))
            
            # Skip if already in Wikidata
            if qid and qid in existing_qids['places']:
                skipped += 1
                print(f"  Skipping {row['name']} ({qid}) - already in Wikidata")
                continue
            
            # Create place entity
            if qid:
                place_id = f"Place_{qid}"
            else:
                # Create ID from name
                place_id = "Place_" + re.sub(r'[^a-zA-Z0-9]', '_', row['name'])
            
            place_uri = JP[place_id]
            g.add((place_uri, RDF.type, JP.Place))
            g.add((place_uri, RDFS.label, Literal(row['name'])))
            g.add((place_uri, JP.hasSource, JP.Source_BooksReports))
            
            # Add Wikidata link if available
            if qid:
                g.add((place_uri, JP.authorityLink, Literal(f"http://www.wikidata.org/entity/{qid}")))
            
            # Add coordinates if available
            if row.get('coordinates'):
                coords = row['coordinates'].replace('"', '')
                g.add((place_uri, JP.coordinates, Literal(coords)))
            
            # Add type if available
            if row.get('type'):
                g.add((place_uri, JP.placeType, Literal(row['type'])))
            
            imported += 1
    
    print(f"Places: Imported {imported}, Skipped {skipped} (already in Wikidata)")
    return g

def main():
    print("=== IMPORTING BOOKS/REPORTS DATA ===\n")
    
    # Load existing Wikidata QIDs
    existing_qids = load_existing_wikidata_qids()
    
    # Import persons
    print("\n--- Importing Persons ---")
    persons_g = import_persons(
        "/Users/nogashlomi/projects/yossi/raw materials/persons_extracted.csv",
        existing_qids
    )
    persons_g.serialize(destination="data/books_reports_persons.ttl", format="turtle")
    print("✅ Saved to data/books_reports_persons.ttl")
    
    # Import works
    print("\n--- Importing Works ---")
    works_g = import_works(
        "/Users/nogashlomi/projects/yossi/raw materials/works_extracted.csv",
        existing_qids
    )
    works_g.serialize(destination="data/books_reports_works.ttl", format="turtle")
    print("✅ Saved to data/books_reports_works.ttl")
    
    # Import places
    print("\n--- Importing Places ---")
    places_g = import_places(
        "/Users/nogashlomi/projects/yossi/raw materials/places_extracted.csv",
        existing_qids
    )
    places_g.serialize(destination="data/books_reports_places.ttl", format="turtle")
    print("✅ Saved to data/books_reports_places.ttl")
    
    print("\n✅ Books/Reports import complete!")

if __name__ == "__main__":
    main()
