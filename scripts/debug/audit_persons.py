#!/usr/bin/env python3
"""
Comprehensive data quality audit for historical persons.
Checks for:
- Wikidata authority links
- Place relations
- Time relations
- Source attribution
- Authored works
- Duplicates

Removes persons without Wikidata IDs and exports them to CSV for review.
"""
import csv
import re
from collections import defaultdict
from rdflib import Graph, Namespace, RDF, RDFS

JP = Namespace("http://jewish_philosophy.org/ontology#")

def extract_wikidata_qid(url):
    """Extract QID from Wikidata URL."""
    if not url:
        return None
    match = re.search(r'Q\d+', str(url))
    return match.group(0) if match else None

def load_all_persons():
    """Load all persons from all TTL files."""
    g = Graph()
    
    files = [
        "data/person-historical.ttl",
        "data/wikidata_persons.ttl",
        "data/book_persons.ttl",
        "data/books_reports_persons.ttl"
    ]
    
    for file_path in files:
        try:
            g.parse(file_path, format="turtle")
            print(f"Loaded {file_path}")
        except Exception as e:
            print(f"Warning: Could not load {file_path}: {e}")
    
    return g

def audit_persons(g):
    """Audit all persons and return detailed report."""
    report = {
        'total': 0,
        'with_wikidata': 0,
        'without_wikidata': 0,
        'with_places': 0,
        'with_times': 0,
        'with_source': 0,
        'with_works': 0,
        'duplicates': defaultdict(list),
        'persons_without_wikidata': []
    }
    
    # Track QIDs to find duplicates
    qid_to_persons = defaultdict(list)
    
    for person_uri in g.subjects(RDF.type, JP.HistoricalPerson):
        report['total'] += 1
        person_id = str(person_uri).split("#")[-1]
        label = g.value(person_uri, RDFS.label)
        
        # Check Wikidata authority link
        has_wikidata = False
        wikidata_qid = None
        for auth in g.objects(person_uri, JP.authorityLink):
            qid = extract_wikidata_qid(auth)
            if qid:
                has_wikidata = True
                wikidata_qid = qid
                qid_to_persons[qid].append((person_id, str(label)))
                break
        
        if has_wikidata:
            report['with_wikidata'] += 1
        else:
            report['without_wikidata'] += 1
        
        # Check place relations
        has_places = bool(list(g.objects(person_uri, JP.hasPlaceRelation)))
        if has_places:
            report['with_places'] += 1
        
        # Check time relations
        has_times = bool(list(g.objects(person_uri, JP.hasTimeRelation)))
        if has_times:
            report['with_times'] += 1
        
        # Check source
        has_source = bool(g.value(person_uri, JP.hasSource))
        if has_source:
            report['with_source'] += 1
            source_uri = g.value(person_uri, JP.hasSource)
            source_label = g.value(source_uri, RDFS.label)
        else:
            source_label = None
        
        # Check authored works
        has_works = bool(list(g.subjects(JP.hasAuthor, person_uri)))
        if has_works:
            report['with_works'] += 1
        
        # Store persons without Wikidata for export
        if not has_wikidata:
            report['persons_without_wikidata'].append({
                'id': person_id,
                'label': str(label) if label else '',
                'source': str(source_label) if source_label else '',
                'has_places': has_places,
                'has_times': has_times,
                'has_works': has_works
            })
    
    # Find duplicates (same QID, different person URIs)
    for qid, persons in qid_to_persons.items():
        if len(persons) > 1:
            report['duplicates'][qid] = persons
    
    return report

def remove_persons_without_wikidata(g):
    """Remove persons without Wikidata IDs from graph."""
    persons_to_remove = []
    
    for person_uri in g.subjects(RDF.type, JP.HistoricalPerson):
        has_wikidata = False
        for auth in g.objects(person_uri, JP.authorityLink):
            if extract_wikidata_qid(auth):
                has_wikidata = True
                break
        
        if not has_wikidata:
            persons_to_remove.append(person_uri)
    
    # Remove these persons and all their triples
    for person_uri in persons_to_remove:
        # Remove all triples where person is subject
        for p, o in g.predicate_objects(person_uri):
            g.remove((person_uri, p, o))
        # Remove all triples where person is object
        for s, p in g.subject_predicates(person_uri):
            g.remove((s, p, person_uri))
    
    return len(persons_to_remove)

def main():
    print("=== HISTORICAL PERSONS DATA QUALITY AUDIT ===\n")
    
    # Load all persons
    print("Loading all person data...")
    g = load_all_persons()
    
    # Audit
    print("\n--- Running Audit ---")
    report = audit_persons(g)
    
    # Print report
    print(f"\n=== AUDIT REPORT ===")
    print(f"Total Persons: {report['total']}")
    print(f"  With Wikidata ID: {report['with_wikidata']} ({report['with_wikidata']/report['total']*100:.1f}%)")
    print(f"  Without Wikidata ID: {report['without_wikidata']} ({report['without_wikidata']/report['total']*100:.1f}%)")
    print(f"\nData Completeness:")
    print(f"  With Place Relations: {report['with_places']} ({report['with_places']/report['total']*100:.1f}%)")
    print(f"  With Time Relations: {report['with_times']} ({report['with_times']/report['total']*100:.1f}%)")
    print(f"  With Source: {report['with_source']} ({report['with_source']/report['total']*100:.1f}%)")
    print(f"  With Authored Works: {report['with_works']} ({report['with_works']/report['total']*100:.1f}%)")
    
    if report['duplicates']:
        print(f"\n⚠️  DUPLICATES FOUND: {len(report['duplicates'])} QIDs with multiple person URIs")
        for qid, persons in list(report['duplicates'].items())[:5]:
            print(f"  {qid}: {persons}")
        if len(report['duplicates']) > 5:
            print(f"  ... and {len(report['duplicates']) - 5} more")
    else:
        print(f"\n✅ No duplicates found")
    
    # Export persons without Wikidata to CSV
    if report['persons_without_wikidata']:
        csv_path = "persons_without_wikidata.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'label', 'source', 'has_places', 'has_times', 'has_works'])
            writer.writeheader()
            writer.writerows(report['persons_without_wikidata'])
        print(f"\n✅ Exported {len(report['persons_without_wikidata'])} persons without Wikidata to {csv_path}")
    
    # Remove persons without Wikidata from each file
    print("\n--- Removing Persons Without Wikidata ---")
    
    files_to_clean = [
        "data/person-historical.ttl",
        "data/book_persons.ttl",
        "data/books_reports_persons.ttl"
    ]
    
    total_removed = 0
    for file_path in files_to_clean:
        try:
            g_file = Graph()
            g_file.parse(file_path, format="turtle")
            
            before = len(list(g_file.subjects(RDF.type, JP.HistoricalPerson)))
            removed = remove_persons_without_wikidata(g_file)
            after = len(list(g_file.subjects(RDF.type, JP.HistoricalPerson)))
            
            if removed > 0:
                g_file.serialize(destination=file_path, format="turtle")
                print(f"  {file_path}: Removed {removed} persons ({before} → {after})")
                total_removed += removed
            else:
                print(f"  {file_path}: No persons to remove")
        except Exception as e:
            print(f"  Warning: Could not process {file_path}: {e}")
    
    print(f"\n✅ Total persons removed: {total_removed}")
    print(f"✅ Audit complete!")

if __name__ == "__main__":
    main()
