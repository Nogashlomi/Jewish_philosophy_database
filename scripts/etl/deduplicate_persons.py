#!/usr/bin/env python3
"""
Remove duplicate persons from person-historical.ttl that also exist in wikidata_persons.ttl.
Wikidata persons should take precedence.
"""
from rdflib import Graph, Namespace, RDF, RDFS
import re

JP = Namespace("http://jewish_philosophy.org/ontology#")

def extract_wikidata_qid(url):
    """Extract QID from Wikidata URL, handling both /wiki/ and /entity/ formats."""
    match = re.search(r'Q\d+', str(url))
    return match.group(0) if match else None

# Load both graphs
print("Loading graphs...")
historical_g = Graph()
historical_g.parse("data/person-historical.ttl", format="turtle")

wikidata_g = Graph()
wikidata_g.parse("data/wikidata_persons.ttl", format="turtle")

print(f"Historical persons: {len(list(historical_g.subjects(RDF.type, JP.HistoricalPerson)))}")
print(f"Wikidata persons: {len(list(wikidata_g.subjects(RDF.type, JP.HistoricalPerson)))}")

# Get all Wikidata QIDs from wikidata_persons.ttl
wikidata_qids = set()
for person in wikidata_g.subjects(RDF.type, JP.HistoricalPerson):
    for auth in wikidata_g.objects(person, JP.authorityLink):
        qid = extract_wikidata_qid(auth)
        if qid:
            wikidata_qids.add(qid)

print(f"Wikidata QIDs: {len(wikidata_qids)}")

# Find persons in historical that have matching Wikidata QIDs
persons_to_remove = []
for person in historical_g.subjects(RDF.type, JP.HistoricalPerson):
    for auth in historical_g.objects(person, JP.authorityLink):
        qid = extract_wikidata_qid(auth)
        if qid and qid in wikidata_qids:
            persons_to_remove.append(person)
            label = historical_g.value(person, RDFS.label)
            print(f"  Removing duplicate: {label} ({qid})")
            break

print(f"\nRemoving {len(persons_to_remove)} duplicate persons from person-historical.ttl...")

# Remove these persons and all their triples
for person in persons_to_remove:
    # Remove all triples where person is subject
    for p, o in historical_g.predicate_objects(person):
        historical_g.remove((person, p, o))
    # Remove all triples where person is object  
    for s, p in historical_g.subject_predicates(person):
        historical_g.remove((s, p, person))

print(f"Historical persons after dedup: {len(list(historical_g.subjects(RDF.type, JP.HistoricalPerson)))}")

# Save cleaned graph
historical_g.serialize(destination="data/person-historical.ttl", format="turtle")
print("✅ Deduplicated person-historical.ttl saved")

