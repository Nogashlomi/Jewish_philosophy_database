import rdflib
from rdflib import Graph, URIRef
g = Graph()
g.parse("data/general_list.ttl", format="turtle")
uri_ref = URIRef("http://jewish_philosophy.org/ontology#Person_Ben_Sira")
q = """
PREFIX jp: <http://jewish_philosophy.org/ontology#>
SELECT ?rel ?type ?start ?end
WHERE {
     ?person jp:hasTimeRelation ?rel .
     OPTIONAL { ?rel jp:timeType ?type }
     OPTIONAL { ?rel jp:timeFrom ?start }
     OPTIONAL { ?rel jp:timeUntil ?end }
}
"""
for row in g.query(q, initBindings={'person': uri_ref}):
    print(row)
