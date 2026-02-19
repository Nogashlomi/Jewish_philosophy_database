import csv
import json
import sys
import os
from pathlib import Path
from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import XSD

# Namespaces
JP = Namespace("http://jewish_philosophy.org/ontology#")
WIKIDATA_SOURCE = URIRef(f"{JP}Source_Wikidata")

# Paths (Hardcoded to user's specific files)
PERSONS_CSV = "/Users/nogashlomi/projects/yossi/wikidata persons/jewish_intellectuals_20260215_120845.csv"
WORKS_CSV = "/Users/nogashlomi/projects/yossi/wikidata persons/jewish_intellectual_works_20260215_120845.csv"

# Output
OUTPUT_DIR = "data/cleaned"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def parse_date(date_str):
    if not date_str: return None
    # Handle "1882-06-18T00:00:00Z" -> 1882
    try:
        return int(date_str.split('-')[0])
    except:
        return None

def clean_name(name):
    if not name: return ""
    return name.strip().strip("'").strip('"')

def run_import():
    print(f"Importing from:\n  {PERSONS_CSV}\n  {WORKS_CSV}")
    
    g_persons = Graph()
    g_works = Graph()
    g_places = Graph()
    
    # Bind prefixes
    for g in [g_persons, g_works, g_places]:
        g.bind("jp", JP)
        g.bind("rdfs", RDFS)
        g.bind("xsd", XSD)

    # 1. Import Persons
    print("Processing Persons...")
    count_p = 0
    with open(PERSONS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            qid = row.get('QID', '').strip()
            if not qid: continue
            
            uri = URIRef(f"{JP}Person_{qid}")
            name = clean_name(row.get('Name', ''))
            
            g_persons.add((uri, RDF.type, JP.HistoricalPerson))
            g_persons.add((uri, RDFS.label, Literal(name)))
            g_persons.add((uri, JP.hasSource, WIKIDATA_SOURCE))
            
            if row.get('Wikidata URI'):
                 g_persons.add((uri, JP.authorityLink, Literal(row['Wikidata URI'])))
            
            birth_year = parse_date(row.get('Birth Date'))
            if birth_year:
                g_persons.add((uri, JP.birthYear, Literal(birth_year, datatype=XSD.gYear)))
                
            death_year = parse_date(row.get('Death Date'))
            if death_year:
                g_persons.add((uri, JP.deathYear, Literal(death_year, datatype=XSD.gYear)))
                
            # Places (Simple linking for now)
            b_place = row.get('Birth Place')
            b_qid = row.get('Birth Place QID')
            if b_qid:
                p_uri = URIRef(f"{JP}Place_{b_qid}")
                g_places.add((p_uri, RDF.type, JP.Place))
                g_places.add((p_uri, RDFS.label, Literal(b_place if b_place else b_qid)))
                
                # Create relation node
                rel_uri = URIRef(f"{JP}PlaceRelation_{qid}_Birth")
                g_persons.add((uri, JP.hasPlaceRelation, rel_uri))
                g_persons.add((rel_uri, RDF.type, JP.PlaceRelation))
                g_persons.add((rel_uri, JP.relatedPlace, p_uri))
                g_persons.add((rel_uri, JP.placeType, Literal("Birth")))
                
            d_place = row.get('Death Place')
            d_qid = row.get('Death Place QID')
            if d_qid:
                p_uri = URIRef(f"{JP}Place_{d_qid}")
                g_places.add((p_uri, RDF.type, JP.Place))
                g_places.add((p_uri, RDFS.label, Literal(d_place if d_place else d_qid)))
                
                # Create relation node
                rel_uri = URIRef(f"{JP}PlaceRelation_{qid}_Death")
                g_persons.add((uri, JP.hasPlaceRelation, rel_uri))
                g_persons.add((rel_uri, RDF.type, JP.PlaceRelation))
                g_persons.add((rel_uri, JP.relatedPlace, p_uri))
                g_persons.add((rel_uri, JP.placeType, Literal("Death")))

            count_p += 1
            
    # 2. Import Works
    print("Processing Works...")
    count_w = 0
    with open(WORKS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            qid = row.get('Work QID', '').strip()
            if not qid: continue
            
            uri = URIRef(f"{JP}Work_{qid}")
            title = clean_name(row.get('Title', ''))
            
            g_works.add((uri, RDF.type, JP.HistoricalWork))
            g_works.add((uri, RDFS.label, Literal(title)))
            g_works.add((uri, JP.title, Literal(title)))
            g_works.add((uri, JP.hasSource, WIKIDATA_SOURCE))
            
            author_qid = row.get('Author QID')
            if author_qid:
                author_uri = URIRef(f"{JP}Person_{author_qid}")
                g_works.add((uri, JP.writtenBy, author_uri))
                
            pub_year = parse_date(row.get('Publication Date'))
            if pub_year:
                 g_works.add((uri, JP.publicationYear, Literal(pub_year, datatype=XSD.gYear)))
            
            count_w += 1

    # Save
    print(f"Saving {count_p} persons to data/cleaned/cleaned_persons.ttl")
    g_persons.serialize(f"{OUTPUT_DIR}/cleaned_persons.ttl", format="turtle")
    
    print(f"Saving {count_w} works to data/cleaned/cleaned_works.ttl")
    g_works.serialize(f"{OUTPUT_DIR}/cleaned_works.ttl", format="turtle")
    
    print(f"Saving places to data/cleaned/cleaned_places.ttl")
    g_places.serialize(f"{OUTPUT_DIR}/cleaned_places.ttl", format="turtle")

if __name__ == "__main__":
    run_import()
