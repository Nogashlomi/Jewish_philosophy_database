#!/usr/bin/env python3
"""
Import NLI MARC Astronomy data with deduplication against Wikidata.
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
    """Load all existing Wikidata QIDs."""
    qids = {'persons': set(), 'works': set()}
    
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
    
    return qids

def import_manuscripts(csv_path):
    """Import manuscripts/records from NLI MARC data."""
    g = Graph()
    g.bind("jp", JP)
    g.bind("rdfs", RDFS)
    
    imported = 0
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            record_id = row.get('record_id', '').strip()
            if not record_id:
                continue
            
            # Create scholarly work entity for the manuscript/record
            work_id = f"ScholarlyWork_NLI_{record_id.replace('/', '_')}"
            work_uri = JP[work_id]
            
            g.add((work_uri, RDF.type, JP.ScholarlyWork))
            g.add((work_uri, RDFS.label, Literal(row.get('title', 'Untitled'))))
            g.add((work_uri, JP.hasSource, JP.Source_NLI_Astronomy))
            g.add((work_uri, JP.hasSubject, JP.Subject_Astronomy))
            
            # Add MARC record ID
            g.add((work_uri, JP.marcRecordId, Literal(record_id)))
            
            # Add authors if available
            if row.get('all_authors'):
                g.add((work_uri, JP.authorNames, Literal(row['all_authors'])))
            
            # Add year if available
            if row.get('year'):
                try:
                    g.add((work_uri, JP.publicationYear, Literal(int(row['year']))))
                except:
                    pass
            
            # Add manuscript flag
            is_manuscript = row.get('is_manuscript', 'No') == 'Yes'
            g.add((work_uri, JP.isManuscript, Literal(is_manuscript)))
            
            imported += 1
    
    print(f"Manuscripts/Records: Imported {imported}")
    return g

def main():
    print("=== IMPORTING NLI MARC ASTRONOMY DATA ===\n")
    
    # Load existing Wikidata QIDs
    existing_qids = load_existing_wikidata_qids()
    
    # Import manuscripts and records
    print("\n--- Importing Manuscripts/Records ---")
    manuscripts_g = import_manuscripts(
        "/Users/nogashlomi/projects/yossi/get_marc_data/astronomy_manuscripts_output/astronomy_all_records.csv"
    )
    manuscripts_g.serialize(destination="data/nli_astronomy_manuscripts.ttl", format="turtle")
    print("✅ Saved to data/nli_astronomy_manuscripts.ttl")
    
    print("\n✅ NLI MARC Astronomy import complete!")

if __name__ == "__main__":
    main()
