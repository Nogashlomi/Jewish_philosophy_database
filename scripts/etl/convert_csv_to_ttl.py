import csv
import sys
import re
from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import XSD
from pathlib import Path

# Namespaces
JP = Namespace("http://jewish_philosophy.org/ontology#")
QB = Namespace("http://purl.org/linked-data/cube#")

def clean_id(text):
    if not text:
        return "Unknown"
    # Remove non-alphanumeric characters except underscore
    s = re.sub(r'[^a-zA-Z0-9_]', '', text)
    return s if s else "Unknown"

def create_person_historical(csv_path: str, output_path: str):
    g = Graph()
    g.bind("jp", JP)
    g.bind("rdfs", RDFS)
    
    print(f"Converting {csv_path} to {output_path}...")
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row['id']: continue
            
            uri = URIRef(f"{JP}Person_{row['id']}")
            
            g.add((uri, RDF.type, JP.HistoricalPerson))
            g.add((uri, RDFS.label, Literal(row['label'])))
            
            if row.get('wikidata_url'):
                g.add((uri, JP.authorityLink, Literal(row['wikidata_url'])))
                
            if row.get('birth_year'):
                try:
                    g.add((uri, JP.birthDate, Literal(row['birth_year'], datatype=XSD.gYear)))
                except: pass
                
            if row.get('death_year'):
                try:
                    g.add((uri, JP.deathDate, Literal(row['death_year'], datatype=XSD.gYear)))
                except: pass
                
    g.serialize(destination=output_path, format="turtle")
    print("Done Persons.")

def create_work_historical(csv_path: str, output_path: str):
    g = Graph()
    g.bind("jp", JP)
    g.bind("rdfs", RDFS)
    
    print(f"Converting {csv_path} to {output_path}...")
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row['id']: continue

            uri = URIRef(f"{JP}Work_{clean_id(row['id'])}")
            
            g.add((uri, RDF.type, JP.HistoricalWork))
            g.add((uri, JP.title, Literal(row['title'])))
            g.add((uri, RDFS.label, Literal(row['title'])))
            
            if row.get('author_id'):
                author_uri = URIRef(f"{JP}Person_{row['author_id']}")
                g.add((uri, JP.writtenBy, author_uri))

    g.serialize(destination=output_path, format="turtle")
    print("Done Works.")

def create_scholars_and_works(csv_path: str, scholars_out: str, works_out: str):
    g_works = Graph()
    g_works.bind("jp", JP)
    g_works.bind("rdfs", RDFS)
    
    g_scholars = Graph()
    g_scholars.bind("jp", JP)
    g_scholars.bind("rdfs", RDFS)
    
    print(f"Converting {csv_path}...")
    
    seen_scholars = set()

    with open(csv_path, 'r', encoding='utf-8') as f:
        # Check for empty lines or issues
        lines = (line.replace('\0', '') for line in f)
        reader = csv.DictReader(lines)
        
        for i, row in enumerate(reader):
            try:
                if not row.get('id'): 
                    # Try to generate ID if missing but title exists? 
                    # Or skip. Let's skip empty IDs.
                    continue

                work_uri = URIRef(f"{JP}ScholarlyWork_{clean_id(row['id'])}")
                
                g_works.add((work_uri, RDF.type, JP.ScholarlyWork))
                g_works.add((work_uri, JP.title, Literal(row['title'])))
                g_works.add((work_uri, RDFS.label, Literal(row['title'])))
                
                creator_name = row.get('creator_name', '').strip()
                if creator_name:
                    safe_id = clean_id(creator_name)
                    scholar_uri = URIRef(f"{JP}Scholar_{safe_id}")
                    
                    g_works.add((work_uri, JP.hasAuthor, scholar_uri))
                    
                    if scholar_uri not in seen_scholars:
                        g_scholars.add((scholar_uri, RDF.type, JP.Scholar))
                        g_scholars.add((scholar_uri, RDFS.label, Literal(creator_name)))
                        seen_scholars.add(scholar_uri)

                if row.get('year'):
                    try:
                        g_works.add((work_uri, JP.publicationYear, Literal(row['year'], datatype=XSD.gYear)))
                    except: pass
                
                if row.get('topic_id'):
                    # Can be multiple? CSV usually single val. Assuming single for now.
                    topic_uri = URIRef(f"{JP}Person_{row['topic_id']}")
                    g_works.add((work_uri, JP.aboutPerson, topic_uri))
                    # Also add mentionsPerson for compatibility
                    g_works.add((work_uri, JP.mentionsPerson, topic_uri))

            except Exception as e:
                print(f"Error on row {i}: {e}")
                continue

    g_works.serialize(destination=works_out, format="turtle")
    g_scholars.serialize(destination=scholars_out, format="turtle")
    print("Done Scholarly Works.")

if __name__ == "__main__":
    base_csv = "/Users/nogashlomi/projects/yossi/SIEPM_mateirals_and_data"
    
    try:
        create_person_historical(
            f"{base_csv}/persons.csv", 
            "data/person-historical.ttl"
        )
        
        create_work_historical(
            f"{base_csv}/works.csv", 
            "data/work-historical.ttl"
        )
        
        create_scholars_and_works(
            f"{base_csv}/scholarly_works.csv",
            "data/scholars.ttl",
            "data/scholarly-works.ttl"
        )
    except Exception as e:
        print(f"Critical Error: {e}")
        import traceback
        traceback.print_exc()

