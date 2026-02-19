#!/usr/bin/env python3
"""
Clean book_persons.ttl by removing persons without Wikidata authority links.
"""
from rdflib import Graph, Namespace, RDF, RDFS

JP = Namespace("http://jewish_philosophy.org/ontology#")

# Load the graph
g = Graph()
g.parse("data/book_persons.ttl", format="turtle")

print("=== CLEANING BOOK PERSONS ===")
print(f"Total persons before: {len(list(g.subjects(RDF.type, JP.HistoricalPerson)))}")

# Find persons without authority links
persons_to_remove = []
for person in g.subjects(RDF.type, JP.HistoricalPerson):
    if not list(g.objects(person, JP.authorityLink)):
        persons_to_remove.append(person)
        
print(f"Persons without Wikidata links: {len(persons_to_remove)}")

# Remove these persons and all their triples
for person in persons_to_remove:
    # Remove all triples where person is subject
    for p, o in g.predicate_objects(person):
        g.remove((person, p, o))
    # Remove all triples where person is object
    for s, p in g.subject_predicates(person):
        g.remove((s, p, person))

print(f"Total persons after: {len(list(g.subjects(RDF.type, JP.HistoricalPerson)))}")

# Save cleaned graph
g.serialize(destination="data/book_persons.ttl", format="turtle")
print("✅ Cleaned book_persons.ttl saved")
