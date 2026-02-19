#!/usr/bin/env python3
"""
Import book data from CSV files and convert to RDF format.
Handles persons, works, places, and translation relations.
"""
import csv
import re
from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import XSD

# Namespaces
JP = Namespace("http://jewish_philosophy.org/ontology#")

# Output files
PERSONS_TTL = "data/book_persons.ttl"
WORKS_TTL = "data/book_works.ttl"
PLACES_TTL_UPDATE = "data/places.ttl"  # Will merge with existing
RELATIONS_TTL = "data/translation_relations.ttl"

# Input CSVs
PERSONS_CSV = "/Users/nogashlomi/projects/yossi/SIEPM_mateirals_and_data/book_data_persons.csv"
WORKS_CSV = "/Users/nogashlomi/projects/yossi/SIEPM_mateirals_and_data/book_data_works.csv"
PLACES_CSV = "/Users/nogashlomi/projects/yossi/SIEPM_mateirals_and_data/book_data_places.csv"
RELATIONS_CSV = "/Users/nogashlomi/projects/yossi/SIEPM_mateirals_and_data/book_data_relations.csv"

def sanitize_id(text):
    """Create a safe URI fragment from text"""
    if not text:
        return "Unknown"
    # Remove special characters, keep alphanumeric and underscores
    safe = re.sub(r'[^a-zA-Z0-9_]', '_', str(text))
    # Remove multiple underscores
    safe = re.sub(r'_+', '_', safe)
    # Remove leading/trailing underscores
    safe = safe.strip('_')
    return safe if safe else "Unknown"

def import_persons():
    """Import persons from CSV"""
    print("Importing persons...")
    g = Graph()
    g.bind("jp", JP)
    g.bind("rdfs", RDFS)
    
    person_map = {}  # Map CSV ID to URI
    
    with open(PERSONS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            person_id = row['id']
            name = row['name'].strip()
            wikidata_id = row.get('wikidata_id', '').strip()
            
            if not name or name == '':
                continue
            
            # Create URI
            safe_id = sanitize_id(person_id)
            person_uri = URIRef(f"{JP}BookPerson_{safe_id}")
            person_map[person_id] = person_uri
            
            # Add triples
            g.add((person_uri, RDF.type, JP.HistoricalPerson))
            g.add((person_uri, RDFS.label, Literal(name)))
            
            if wikidata_id:
                wiki_url = f"https://www.wikidata.org/wiki/{wikidata_id}"
                g.add((person_uri, JP.authorityLink, Literal(wiki_url)))
    
    print(f"  Imported {len(person_map)} persons")
    g.serialize(destination=PERSONS_TTL, format="turtle")
    return person_map

def import_works(person_map):
    """Import works from CSV"""
    print("Importing works...")
    g = Graph()
    g.bind("jp", JP)
    g.bind("rdfs", RDFS)
    
    work_map = {}  # Map work title to URI
    
    with open(WORKS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            work_id = row['id']
            title = row['title'].strip()
            author_name = row.get('author', '').strip()
            language = row.get('language', '').strip()
            
            if not title:
                continue
            
            # Create URI
            safe_id = sanitize_id(work_id)
            work_uri = URIRef(f"{JP}BookWork_{safe_id}")
            work_map[title] = work_uri
            
            # Add triples
            g.add((work_uri, RDF.type, JP.HistoricalWork))
            g.add((work_uri, RDFS.label, Literal(title)))
            g.add((work_uri, JP.title, Literal(title)))
            
            if language:
                g.add((work_uri, JP.language, Literal(language)))
            
            # Try to link author if we can find them
            if author_name:
                # Store author name for now - we'll try to match later
                g.add((work_uri, JP.authorName, Literal(author_name)))
    
    print(f"  Imported {len(work_map)} works")
    g.serialize(destination=WORKS_TTL, format="turtle")
    return work_map

def import_places():
    """Import places from CSV and merge with existing places.ttl"""
    print("Importing places...")
    
    # Load existing places
    g = Graph()
    try:
        g.parse("data/places.ttl", format="ttl")
        print(f"  Loaded {len(g)} existing place triples")
    except:
        print("  No existing places.ttl found, creating new")
    
    g.bind("jp", JP)
    g.bind("rdfs", RDFS)
    
    place_map = {}  # Map place name to URI
    
    with open(PLACES_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            place_id = row['id']
            name = row['name'].strip()
            wikidata_qid = row.get('wikidata_qid', '').strip()
            coords = row.get('coordinates', '').strip()
            
            if not name:
                continue
            
            # Create URI
            safe_name = sanitize_id(name)
            place_uri = URIRef(f"{JP}Place_{safe_name}")
            place_map[name] = place_uri
            
            # Check if place already exists
            existing = list(g.triples((place_uri, RDF.type, JP.Place)))
            if existing:
                print(f"  Place {name} already exists, skipping")
                continue
            
            # Add triples
            g.add((place_uri, RDF.type, JP.Place))
            g.add((place_uri, RDFS.label, Literal(name)))
            
            # Parse coordinates
            if coords and ',' in coords:
                try:
                    lat, lon = coords.split(',')
                    g.add((place_uri, JP.latitude, Literal(lat.strip())))
                    g.add((place_uri, JP.longitude, Literal(lon.strip())))
                except:
                    print(f"  Warning: Invalid coordinates for {name}: {coords}")
            
            if wikidata_qid:
                wiki_url = f"https://www.wikidata.org/wiki/{wikidata_qid}"
                g.add((place_uri, JP.authorityLink, Literal(wiki_url)))
    
    print(f"  Total places in graph: {len([s for s in g.subjects(RDF.type, JP.Place)])}")
    g.serialize(destination=PLACES_TTL_UPDATE, format="turtle")
    return place_map

def import_relations(person_map, work_map, place_map):
    """Import translation relations from CSV"""
    print("Importing translation relations...")
    g = Graph()
    g.bind("jp", JP)
    g.bind("rdfs", RDFS)
    
    relation_count = 0
    
    with open(RELATIONS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            translator_name = row.get('translator', '').strip()
            relation_type = row.get('relation', '').strip()  # e.g., "translated"
            work_title = row.get('work', '').strip()
            location = row.get('location', '').strip()
            source_lang = row.get('source_language', '').strip()
            
            if not (translator_name and work_title):
                continue
            
            # Create relation URI
            rel_id = f"Translation_{i:04d}"
            rel_uri = URIRef(f"{JP}{rel_id}")
            
            g.add((rel_uri, RDF.type, JP.TranslationRelation))
            g.add((rel_uri, JP.translatorName, Literal(translator_name)))
            g.add((rel_uri, JP.workTitle, Literal(work_title)))
            
            if relation_type:
                g.add((rel_uri, JP.relationType, Literal(relation_type)))
            
            if location:
                g.add((rel_uri, JP.locationName, Literal(location)))
            
            if source_lang:
                g.add((rel_uri, JP.sourceLanguage, Literal(source_lang)))
            
            relation_count += 1
    
    print(f"  Imported {relation_count} translation relations")
    g.serialize(destination=RELATIONS_TTL, format="turtle")

def main():
    print("=" * 60)
    print("Book Data Import Script")
    print("=" * 60)
    
    person_map = import_persons()
    work_map = import_works(person_map)
    place_map = import_places()
    import_relations(person_map, work_map, place_map)
    
    print("\n" + "=" * 60)
    print("Import Complete!")
    print("=" * 60)
    print(f"Generated files:")
    print(f"  - {PERSONS_TTL}")
    print(f"  - {WORKS_TTL}")
    print(f"  - {PLACES_TTL_UPDATE} (merged)")
    print(f"  - {RELATIONS_TTL}")
    print("\nRestart the backend to load the new data.")

if __name__ == "__main__":
    main()
