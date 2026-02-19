import sys
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF, RDFS

jp = Namespace("http://jewish_philosophy.org/ontology#")
g = Graph()
g.parse("data/scholarly-gad.ttl", format="ttl")
g.parse("data/ontology/vocabulary.ttl", format="ttl")

print("Checking Scholarly Work -> Person connections:")

count = 0
for s, p, o in g.triples((None, jp.aboutPerson, None)):
    print(f"{s} -> aboutPerson -> {o}")
    count += 1

print(f"Total connections found: {count}")

print("\nChecking Node Types:")
for s in g.subjects(RDF.type, jp.ScholarlyWork):
    print(f"ScholarlyWork Node: {s}")

