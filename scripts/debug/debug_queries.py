from app.core.rdf_store import rdf_store, JP
from rdflib import URIRef
import os

print("Loading data...")
rdf_store.load_data(["data", "ontology"])
print(f"Data loaded. Triples: {len(rdf_store.g)}")

print("Testing Persons Query (Python Aggregation)...")
try:
    q_persons = """
    PREFIX jp: <http://jewish_philosophy.org/ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?uri ?label ?work ?placeLabel ?timeVal
    WHERE {
        ?uri a jp:HistoricalPerson ;
             rdfs:label ?label .
        
        OPTIONAL { ?work jp:writtenBy ?uri }
        
        OPTIONAL { 
            ?uri jp:hasPlaceRelation ?pr .
            ?pr jp:relatedPlace ?place .
            ?place rdfs:label ?placeLabel .
        }

        OPTIONAL {
            ?uri jp:hasTimeRelation ?tr .
            ?tr jp:timeFrom ?trStart .
            OPTIONAL { ?tr jp:timeUntil ?trEnd }
            BIND( CONCAT(STR(?trStart), IF(BOUND(?trEnd), CONCAT("-", STR(?trEnd)), "")) as ?timeVal )
        }
    }
    ORDER BY ?label
    """
    raw_results = list(rdf_store.query(q_persons))
    print(f"Persons Raw Query Success. Rows: {len(raw_results)}")
    
    # Simulate Python Aggregation
    persons = {}
    for row in raw_results:
        uri = str(row.uri)
        if uri not in persons:
            persons[uri] = {
                "label": row.label,
                "works": set(),
                "places": set(),
                "times": set()
            }
        if row.work: persons[uri]["works"].add(row.work)
        if row.placeLabel: persons[uri]["places"].add(str(row.placeLabel))
        if row.timeVal: persons[uri]["times"].add(str(row.timeVal))
    
    print(f"Aggregated Persons: {len(persons)}")
    sample_p = list(persons.values())[0] if persons else None
    print(f"Sample: {sample_p}")

except Exception as e:
    print(f"Persons Query Failed: {e}")

print("\nTesting Works Query (Python Aggregation)...")
try:
    q_works = """
    PREFIX jp: <http://jewish_philosophy.org/ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?uri ?title ?authorName ?sw
    WHERE {
        ?uri a jp:HistoricalWork ;
             jp:title ?title .
        OPTIONAL { 
            ?uri jp:writtenBy ?author . 
            ?author rdfs:label ?authorName .
        }
        OPTIONAL { ?sw jp:aboutWork ?uri }
    }
    ORDER BY ?title
    """
    raw_works = list(rdf_store.query(q_works))
    print(f"Works Raw Query Success. Rows: {len(raw_works)}")
    
    works = {}
    for row in raw_works:
        uri = str(row.uri)
        if uri not in works:
            works[uri] = {
                "title": row.title,
                "authors": set(),
                "mentions": set()
            }
        if row.authorName: works[uri]["authors"].add(str(row.authorName))
        if row.sw: works[uri]["mentions"].add(str(row.sw))

    print(f"Aggregated Works: {len(works)}")
    sample_w = list(works.values())[0] if works else None
    print(f"Sample: {sample_w}")

except Exception as e:
    print(f"Works Query Failed: {e}")
