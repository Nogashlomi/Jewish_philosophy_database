#!/usr/bin/env python3
"""
Import all clean CSV data and generate TTL files.
Replaces all existing data while maintaining TTL structure and ontology.
"""
import csv
import re
from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import XSD

# Namespaces
JP = Namespace("http://jewish_philosophy.org/ontology#")

# Source URIs
HARVEY_SOURCE = URIRef(f"{JP}Source_Harvey")
BOOK_SOURCE = URIRef(f"{JP}Source_Freudenthal")

# Input CSVs
BOOK_PERSONS_CSV = "/Users/nogashlomi/projects/yossi/SIEPM_mateirals_and_data/book_data_persons_clean.csv"
BOOK_WORKS_CSV = "/Users/nogashlomi/projects/yossi/SIEPM_mateirals_and_data/book_data_works_clean.csv"
BOOK_PLACES_CSV = "/Users/nogashlomi/projects/yossi/SIEPM_mateirals_and_data/book_data_places_clean.csv"
BOOK_RELATIONS_CSV = "/Users/nogashlomi/projects/yossi/SIEPM_mateirals_and_data/book_data_relations_clean.csv"

HARVEY_PERSONS_CSV = "/Users/nogashlomi/projects/yossi/SIEPM_mateirals_and_data/persons_clean.csv"
HARVEY_WORKS_CSV = "/Users/nogashlomi/projects/yossi/SIEPM_mateirals_and_data/works_clean.csv"
HARVEY_SCHOLARLY_CSV = "/Users/nogashlomi/projects/yossi/SIEPM_mateirals_and_data/scholarly_works_clean.csv"

# Output TTL files
PERSON_HISTORICAL_TTL = "data/person-historical.ttl"
WORK_HISTORICAL_TTL = "data/work-historical.ttl"
SCHOLARLY_WORKS_TTL = "data/scholarly-works.ttl"
BOOK_PERSONS_TTL = "data/book_persons.ttl"
BOOK_WORKS_TTL = "data/book_works.ttl"
PLACES_TTL = "data/places.ttl"
TRANSLATION_RELATIONS_TTL = "data/translation_relations.ttl"

def sanitize_id(text):
    """Create a safe URI fragment from text"""
    if not text:
        return "Unknown"
    safe = re.sub(r'[^a-zA-Z0-9_]', '_', str(text))
    safe = re.sub(r'_+', '_', safe)
    safe = safe.strip('_')
    return safe if safe else "Unknown"

def import_harvey_persons():
    """Import Harvey persons (id, label, wikidata_url, birth_year, death_year)"""
    print("\n=== HARVEY PERSONS ===")
    g = Graph()
    g.bind("jp", JP)
    g.bind("rdfs", RDFS)
    g.bind("xsd", XSD)
    
    count = 0
    with open(HARVEY_PERSONS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            person_id = row['id']
            label = row['label'].strip()
            wikidata_url = row.get('wikidata_url', '').strip()
            
            if not label:
                continue
            
            person_uri = URIRef(f"{JP}Person_{person_id}")
            
            g.add((person_uri, RDF.type, JP.HistoricalPerson))
            g.add((person_uri, RDFS.label, Literal(label)))
            g.add((person_uri, JP.hasSource, HARVEY_SOURCE))
            
            if wikidata_url:
                g.add((person_uri, JP.authorityLink, Literal(wikidata_url)))
            
            count += 1
    
    print(f"  Imported {count} persons")
    g.serialize(destination=PERSON_HISTORICAL_TTL, format="turtle")
    return count

def import_harvey_works():
    """Import Harvey historical works"""
    print("\n=== HARVEY WORKS ===")
    g = Graph()
    g.bind("jp", JP)
    g.bind("rdfs", RDFS)
    
    count = 0
    with open(HARVEY_WORKS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            work_id = row['id']
            title = row.get('title', '').strip()
            
            if not title:
                continue
            
            work_uri = URIRef(f"{JP}Work_{work_id}")
            
            g.add((work_uri, RDF.type, JP.HistoricalWork))
            g.add((work_uri, RDFS.label, Literal(title)))
            g.add((work_uri, JP.title, Literal(title)))
            g.add((work_uri, JP.hasSource, HARVEY_SOURCE))
            
            count += 1
    
    print(f"  Imported {count} works")
    g.serialize(destination=WORK_HISTORICAL_TTL, format="turtle")
    return count

def import_harvey_scholarly():
    """Import Harvey scholarly works (id, title, creator_name, year, topic_id)"""
    print("\n=== HARVEY SCHOLARLY WORKS ===")
    g = Graph()
    g.bind("jp", JP)
    g.bind("rdfs", RDFS)
    g.bind("xsd", XSD)
    
    # Load existing scholars.ttl to get scholar URIs
    scholars_g = Graph()
    try:
        scholars_g.parse("data/scholars.ttl", format="ttl")
    except:
        pass
    
    count = 0
    with open(HARVEY_SCHOLARLY_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            work_id = row['id']
            title = row['title'].strip()
            creator_name = row.get('creator_name', '').strip()
            year = row.get('year', '').strip()
            topic_id = row.get('topic_id', '').strip()
            
            if not title:
                continue
            
            work_uri = URIRef(f"{JP}ScholarlyWork_{work_id}")
            
            g.add((work_uri, RDF.type, JP.ScholarlyWork))
            g.add((work_uri, RDFS.label, Literal(title)))
            g.add((work_uri, JP.title, Literal(title)))
            g.add((work_uri, JP.hasSource, HARVEY_SOURCE))
            
            if year:
                try:
                    g.add((work_uri, JP.publicationYear, Literal(int(year), datatype=XSD.gYear)))
                except:
                    pass
            
            if creator_name:
                # Create or reference scholar
                scholar_id = sanitize_id(creator_name)
                scholar_uri = URIRef(f"{JP}Scholar_{scholar_id}")
                
                # Add scholar if not exists
                if not list(scholars_g.triples((scholar_uri, RDF.type, JP.Scholar))):
                    g.add((scholar_uri, RDF.type, JP.Scholar))
                    g.add((scholar_uri, RDFS.label, Literal(creator_name)))
                    g.add((scholar_uri, JP.name, Literal(creator_name)))
                
                g.add((work_uri, JP.hasAuthor, scholar_uri))
            
            if topic_id:
                # Link to person if topic_id is a person ID
                topic_uri = URIRef(f"{JP}Person_{topic_id}")
                g.add((work_uri, JP.aboutPerson, topic_uri))
            
            count += 1
    
    print(f"  Imported {count} scholarly works")
    g.serialize(destination=SCHOLARLY_WORKS_TTL, format="turtle")
    return count

def import_book_persons():
    """Import book persons (id, name, wikidata_id)"""
    print("\n=== BOOK PERSONS ===")
    g = Graph()
    g.bind("jp", JP)
    g.bind("rdfs", RDFS)
    
    count = 0
    with open(BOOK_PERSONS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            person_id = row['id']
            name = row['name'].strip()
            wikidata_id = row.get('wikidata_id', '').strip()
            
            if not name:
                continue
            
            safe_id = sanitize_id(person_id)
            person_uri = URIRef(f"{JP}BookPerson_{safe_id}")
            
            g.add((person_uri, RDF.type, JP.HistoricalPerson))
            g.add((person_uri, RDFS.label, Literal(name)))
            g.add((person_uri, JP.hasSource, BOOK_SOURCE))
            
            if wikidata_id:
                wiki_url = f"https://www.wikidata.org/wiki/{wikidata_id}"
                g.add((person_uri, JP.authorityLink, Literal(wiki_url)))
            
            count += 1
    
    print(f"  Imported {count} persons")
    g.serialize(destination=BOOK_PERSONS_TTL, format="turtle")
    return count

def import_book_works():
    """Import book works"""
    print("\n=== BOOK WORKS ===")
    g = Graph()
    g.bind("jp", JP)
    g.bind("rdfs", RDFS)
    
    count = 0
    with open(BOOK_WORKS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            work_id = row['id']
            title = row.get('title', '').strip()
            author_name = row.get('author', '').strip()
            language = row.get('language', '').strip()
            
            if not title:
                continue
            
            safe_id = sanitize_id(work_id)
            work_uri = URIRef(f"{JP}BookWork_{safe_id}")
            
            g.add((work_uri, RDF.type, JP.HistoricalWork))
            g.add((work_uri, RDFS.label, Literal(title)))
            g.add((work_uri, JP.title, Literal(title)))
            g.add((work_uri, JP.hasSource, BOOK_SOURCE))
            
            if language:
                g.add((work_uri, JP.language, Literal(language)))
            
            if author_name:
                g.add((work_uri, JP.authorName, Literal(author_name)))
            
            count += 1
    
    print(f"  Imported {count} works")
    g.serialize(destination=BOOK_WORKS_TTL, format="turtle")
    return count

def import_book_places():
    """Import book places"""
    print("\n=== BOOK PLACES ===")
    
    # Load existing places
    g = Graph()
    try:
        g.parse("data/places.ttl", format="ttl")
        print(f"  Loaded {len(g)} existing place triples")
    except:
        print("  No existing places.ttl found, creating new")
    
    g.bind("jp", JP)
    g.bind("rdfs", RDFS)
    
    count = 0
    with open(BOOK_PLACES_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            place_id = row['id']
            name = row['name'].strip()
            wikidata_qid = row.get('wikidata_qid', '').strip()
            coords = row.get('coordinates', '').strip()
            
            if not name:
                continue
            
            safe_name = sanitize_id(name)
            place_uri = URIRef(f"{JP}Place_{safe_name}")
            
            # Check if place already exists
            existing = list(g.triples((place_uri, RDF.type, JP.Place)))
            if existing:
                print(f"  Place {name} already exists, skipping")
                continue
            
            g.add((place_uri, RDF.type, JP.Place))
            g.add((place_uri, RDFS.label, Literal(name)))
            
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
            
            count += 1
    
    print(f"  Added {count} new places")
    print(f"  Total places: {len([s for s in g.subjects(RDF.type, JP.Place)])}")
    g.serialize(destination=PLACES_TTL, format="turtle")
    return count

def import_book_relations():
    """Import book translation relations"""
    print("\n=== BOOK TRANSLATION RELATIONS ===")
    g = Graph()
    g.bind("jp", JP)
    g.bind("rdfs", RDFS)
    
    count = 0
    with open(BOOK_RELATIONS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            translator_name = row.get('translator', '').strip()
            relation_type = row.get('relation', '').strip()
            work_title = row.get('work', '').strip()
            location = row.get('location', '').strip()
            source_lang = row.get('source_language', '').strip()
            
            if not (translator_name and work_title):
                continue
            
            rel_id = f"Translation_{i:04d}"
            rel_uri = URIRef(f"{JP}{rel_id}")
            
            g.add((rel_uri, RDF.type, JP.TranslationRelation))
            g.add((rel_uri, JP.translatorName, Literal(translator_name)))
            g.add((rel_uri, JP.workTitle, Literal(work_title)))
            g.add((rel_uri, JP.hasSource, BOOK_SOURCE))
            
            if relation_type:
                g.add((rel_uri, JP.relationType, Literal(relation_type)))
            
            if location:
                g.add((rel_uri, JP.locationName, Literal(location)))
            
            if source_lang:
                g.add((rel_uri, JP.sourceLanguage, Literal(source_lang)))
            
            count += 1
    
    print(f"  Imported {count} translation relations")
    g.serialize(destination=TRANSLATION_RELATIONS_TTL, format="turtle")
    return count

def main():
    print("=" * 70)
    print("CLEAN DATA IMPORT - REPLACING ALL DATA")
    print("=" * 70)
    
    # Harvey data (Steven Harvey Reports source)
    harvey_persons = import_harvey_persons()
    harvey_works = import_harvey_works()
    harvey_scholarly = import_harvey_scholarly()
    
    # Book data (Freudenthal source)
    book_persons = import_book_persons()
    book_works = import_book_works()
    book_places = import_book_places()
    book_relations = import_book_relations()
    
    print("\n" + "=" * 70)
    print("IMPORT COMPLETE!")
    print("=" * 70)
    print(f"\nHarvey Data (Steven Harvey Reports):")
    print(f"  - {harvey_persons} persons")
    print(f"  - {harvey_works} historical works")
    print(f"  - {harvey_scholarly} scholarly works")
    print(f"\nBook Data (Freudenthal 2012):")
    print(f"  - {book_persons} persons")
    print(f"  - {book_works} historical works")
    print(f"  - {book_places} places")
    print(f"  - {book_relations} translation relations")
    print(f"\nGenerated TTL files:")
    print(f"  - {PERSON_HISTORICAL_TTL}")
    print(f"  - {WORK_HISTORICAL_TTL}")
    print(f"  - {SCHOLARLY_WORKS_TTL}")
    print(f"  - {BOOK_PERSONS_TTL}")
    print(f"  - {BOOK_WORKS_TTL}")
    print(f"  - {PLACES_TTL}")
    print(f"  - {TRANSLATION_RELATIONS_TTL}")
    print("\nRestart the backend to load the new data.")

if __name__ == "__main__":
    main()
