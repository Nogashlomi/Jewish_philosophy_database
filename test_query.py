from rdflib import Graph
import time
g = Graph()
g.parse("data/zonta_table_data.ttl", format="turtle")
q = """
PREFIX jp: <http://example.org/jewish_philosophy/>
SELECT ?s ?p ?o
WHERE {
    ?s ?p ?o .
    FILTER (?p IN (
        jp:translated,
        jp:isTranslationOf
    ))
}
"""
res = list(g.query(q))
print("Translations found:", len(res))
if res:
    print(res[0])
