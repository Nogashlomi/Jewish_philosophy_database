#!/usr/bin/env python3
"""
Import Wikidata persons and works into RDF database.
Processes CSV files from Wikidata SPARQL query and generates TTL files.
"""
import csv
import re
from datetime import datetime
from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import XSD

# Namespaces
JP = Namespace("http://jewish_philosophy.org/ontology#")

# Source URI
WIKIDATA_SOURCE = URIRef(f"{JP}Source_Wikidata")

# Input CSVs
PERSONS_CSV = "/Users/nogashlomi/projects/yossi/wikidata persons/jewish_intellectuals_20260215_120845.csv"
WORKS_CSV = "/Users/nogashlomi/projects/yossi/wikidata persons/jewish_intellectual_works_20260215_120845.csv"

# Output TTL files
PERSONS_TTL = "data/wikidata_persons.ttl"
WORKS_TTL = "data/wikidata_works.ttl"
PLACES_TTL = "data/wikidata_places.ttl"
PLACE_RELATIONS_TTL = "data/wikidata_place_relations.ttl"

def parse_date(iso_date):
    """Extract year from ISO 8601 date string."""
    if not iso_date or iso_date.strip() == '':
        return None
    try:
        # Format: 1882-06-18T00:00:00Z
        year = iso_date.split('-')[0]
        return int(year)
    except:
        return None

def sanitize_name(name):
    """Clean up person/work names."""
    if not name:
        return ""
    # Remove leading quotes/apostrophes
    name = name.lstrip("'\"")
    return name.strip()

def import_persons():
    """Import persons from Wikidata CSV."""
    print("\n=== IMPORTING WIKIDATA PERSONS ===")
    
    persons_g = Graph()
    persons_g.bind("jp", JP)
    persons_g.bind("rdfs", RDFS)
    persons_g.bind("xsd", XSD)
    
    place_relations_g = Graph()
    place_relations_g.bind("jp", JP)
    place_relations_g.bind("rdfs", RDFS)
    place_relations_g.bind("xsd", XSD)
    
    places_g = Graph()
    places_g.bind("jp", JP)
    places_g.bind("rdfs", RDFS)
    
    # Load existing places to avoid duplicates
    try:
        places_g.parse("data/places.ttl", format="turtle")
        print(f"  Loaded {len(list(places_g.subjects(RDF.type, JP.Place)))} existing places")
    except:
        print("  No existing places.ttl found")
    
    person_count = 0
    place_relation_count = 0
    new_place_count = 0
    
    with open(PERSONS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            qid = row['QID'].strip()
            name = sanitize_name(row['Name'])
            birth_date = row.get('Birth Date', '').strip()
            death_date = row.get('Death Date', '').strip()
            birth_place = row.get('Birth Place', '').strip()
            birth_place_qid = row.get('Birth Place QID', '').strip()
            death_place = row.get('Death Place', '').strip()
            death_place_qid = row.get('Death Place QID', '').strip()
            wikidata_uri = row.get('Wikidata URI', '').strip()
            
            if not qid or not name:
                continue
            
            # Create person URI
            person_uri = URIRef(f"{JP}Person_{qid}")
            
            # Add person triples
            persons_g.add((person_uri, RDF.type, JP.HistoricalPerson))
            persons_g.add((person_uri, RDFS.label, Literal(name)))
            persons_g.add((person_uri, JP.hasSource, WIKIDATA_SOURCE))
            
            if wikidata_uri:
                persons_g.add((person_uri, JP.authorityLink, Literal(wikidata_uri)))
            
            # Parse dates
            birth_year = parse_date(birth_date)
            death_year = parse_date(death_date)
            
            # Create birth place relation
            if birth_place_qid and birth_year:
                # Create place if needed
                place_uri = URIRef(f"{JP}Place_{birth_place_qid}")
                if not list(places_g.triples((place_uri, RDF.type, JP.Place))):
                    places_g.add((place_uri, RDF.type, JP.Place))
                    if birth_place:
                        places_g.add((place_uri, RDFS.label, Literal(birth_place)))
                    places_g.add((place_uri, JP.authorityLink, Literal(f"https://www.wikidata.org/wiki/{birth_place_qid}")))
                    new_place_count += 1
                
                # Create place relation
                relation_uri = URIRef(f"{JP}PlaceRelation_{qid}_Birth")
                place_relations_g.add((relation_uri, RDF.type, JP.PlaceRelation))
                place_relations_g.add((relation_uri, JP.relatedPlace, place_uri))
                place_relations_g.add((relation_uri, JP.placeType, Literal("Birth")))
                place_relations_g.add((relation_uri, JP.timeFrom, Literal(birth_year, datatype=XSD.gYear)))
                
                # Link person to relation
                persons_g.add((person_uri, JP.hasPlaceRelation, relation_uri))
                place_relation_count += 1
            
            # Create death place relation
            if death_place_qid and death_year:
                # Create place if needed
                place_uri = URIRef(f"{JP}Place_{death_place_qid}")
                if not list(places_g.triples((place_uri, RDF.type, JP.Place))):
                    places_g.add((place_uri, RDF.type, JP.Place))
                    if death_place:
                        places_g.add((place_uri, RDFS.label, Literal(death_place)))
                    places_g.add((place_uri, JP.authorityLink, Literal(f"https://www.wikidata.org/wiki/{death_place_qid}")))
                    new_place_count += 1
                
                # Create place relation
                relation_uri = URIRef(f"{JP}PlaceRelation_{qid}_Death")
                place_relations_g.add((relation_uri, RDF.type, JP.PlaceRelation))
                place_relations_g.add((relation_uri, JP.relatedPlace, place_uri))
                place_relations_g.add((relation_uri, JP.placeType, Literal("Death")))
                place_relations_g.add((relation_uri, JP.timeFrom, Literal(death_year, datatype=XSD.gYear)))
                
                # Link person to relation
                persons_g.add((person_uri, JP.hasPlaceRelation, relation_uri))
                place_relation_count += 1
            
            person_count += 1
            
            if person_count % 1000 == 0:
                print(f"  Processed {person_count} persons...")
    
    print(f"  Imported {person_count} persons")
    print(f"  Created {place_relation_count} place relations")
    print(f"  Created {new_place_count} new places")
    
    # Save TTL files
    persons_g.serialize(destination=PERSONS_TTL, format="turtle")
    place_relations_g.serialize(destination=PLACE_RELATIONS_TTL, format="turtle")
    places_g.serialize(destination=PLACES_TTL, format="turtle")
    
    return person_count, place_relation_count, new_place_count

def import_works():
    """Import works from Wikidata CSV."""
    print("\n=== IMPORTING WIKIDATA WORKS ===")
    
    works_g = Graph()
    works_g.bind("jp", JP)
    works_g.bind("rdfs", RDFS)
    works_g.bind("xsd", XSD)
    
    work_count = 0
    linked_count = 0
    
    with open(WORKS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            work_qid = row['Work QID'].strip()
            title = sanitize_name(row['Title'])
            author_qid = row.get('Author QID', '').strip()
            pub_date = row.get('Publication Date', '').strip()
            wikidata_uri = row.get('Wikidata URI', '').strip()
            
            if not work_qid or not title:
                continue
            
            # Create work URI
            work_uri = URIRef(f"{JP}Work_{work_qid}")
            
            # Add work triples
            works_g.add((work_uri, RDF.type, JP.HistoricalWork))
            works_g.add((work_uri, RDFS.label, Literal(title)))
            works_g.add((work_uri, JP.title, Literal(title)))
            works_g.add((work_uri, JP.hasSource, WIKIDATA_SOURCE))
            
            if wikidata_uri:
                works_g.add((work_uri, JP.authorityLink, Literal(wikidata_uri)))
            
            # Link to author if available
            if author_qid:
                author_uri = URIRef(f"{JP}Person_{author_qid}")
                works_g.add((work_uri, JP.writtenBy, author_uri))
                linked_count += 1
            
            # Parse publication year
            pub_year = parse_date(pub_date)
            if pub_year:
                works_g.add((work_uri, JP.publicationYear, Literal(pub_year, datatype=XSD.gYear)))
            
            work_count += 1
            
            if work_count % 1000 == 0:
                print(f"  Processed {work_count} works...")
    
    print(f"  Imported {work_count} works")
    print(f"  Linked {linked_count} works to authors")
    
    # Save TTL file
    works_g.serialize(destination=WORKS_TTL, format="turtle")
    
    return work_count, linked_count

def main():
    print("=" * 70)
    print("WIKIDATA IMPORT")
    print("=" * 70)
    
    # Import persons
    person_count, place_relation_count, new_place_count = import_persons()
    
    # Import works
    work_count, linked_count = import_works()
    
    print("\n" + "=" * 70)
    print("IMPORT COMPLETE!")
    print("=" * 70)
    print(f"\nWikidata Import Summary:")
    print(f"  - {person_count} persons")
    print(f"  - {work_count} works")
    print(f"  - {place_relation_count} place relations")
    print(f"  - {new_place_count} new places")
    print(f"  - {linked_count} works linked to authors")
    print(f"\nGenerated TTL files:")
    print(f"  - {PERSONS_TTL}")
    print(f"  - {WORKS_TTL}")
    print(f"  - {PLACES_TTL}")
    print(f"  - {PLACE_RELATIONS_TTL}")
    print("\nRestart the backend to load the new data.")

if __name__ == "__main__":
    main()
