#!/usr/bin/env python3
"""
Add source provenance to all RDF data files.
- Old data (scholarly-works.ttl, person-historical.ttl, work-historical.ttl) -> Steven Harvey Reports
- New book data (book_persons.ttl, book_works.ttl, translation_relations.ttl) -> Freudenthal 2012
"""
from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef

# Namespaces
JP = Namespace("http://jewish_philosophy.org/ontology#")

# Source URIs
HARVEY_SOURCE = URIRef(f"{JP}Source_Harvey")
FREUDENTHAL_SOURCE = URIRef(f"{JP}Source_Freudenthal")

def add_source_to_file(filename, source_uri, entity_types):
    """Add jp:hasSource to all entities of specified types in a file"""
    print(f"\nProcessing {filename}...")
    
    try:
        g = Graph()
        g.parse(filename, format="ttl")
        g.bind("jp", JP)
        g.bind("rdfs", RDFS)
        
        initial_count = len(g)
        added_count = 0
        
        # Find all entities of the specified types
        for entity_type in entity_types:
            for entity in g.subjects(RDF.type, entity_type):
                # Check if it already has a source
                existing_source = list(g.objects(entity, JP.hasSource))
                if not existing_source:
                    g.add((entity, JP.hasSource, source_uri))
                    added_count += 1
        
        print(f"  Added {added_count} source links")
        print(f"  Total triples: {initial_count} -> {len(g)}")
        
        # Save back
        g.serialize(destination=filename, format="turtle")
        return added_count
        
    except FileNotFoundError:
        print(f"  File not found, skipping")
        return 0
    except Exception as e:
        print(f"  Error: {e}")
        return 0

def main():
    print("=" * 60)
    print("Adding Source Provenance to RDF Data")
    print("=" * 60)
    
    total_added = 0
    
    # Old data -> Steven Harvey Reports
    print("\n--- OLD DATA (Steven Harvey Reports) ---")
    
    total_added += add_source_to_file(
        "data/scholarly-works.ttl",
        HARVEY_SOURCE,
        [JP.ScholarlyWork]
    )
    
    total_added += add_source_to_file(
        "data/person-historical.ttl",
        HARVEY_SOURCE,
        [JP.HistoricalPerson]
    )
    
    total_added += add_source_to_file(
        "data/work-historical.ttl",
        HARVEY_SOURCE,
        [JP.HistoricalWork]
    )
    
    # New book data -> Freudenthal 2012
    print("\n--- NEW DATA (Freudenthal 2012) ---")
    
    total_added += add_source_to_file(
        "data/book_persons.ttl",
        FREUDENTHAL_SOURCE,
        [JP.HistoricalPerson]
    )
    
    total_added += add_source_to_file(
        "data/book_works.ttl",
        FREUDENTHAL_SOURCE,
        [JP.HistoricalWork]
    )
    
    total_added += add_source_to_file(
        "data/translation_relations.ttl",
        FREUDENTHAL_SOURCE,
        [JP.TranslationRelation]
    )
    
    print("\n" + "=" * 60)
    print(f"Total source links added: {total_added}")
    print("=" * 60)
    print("\nRestart the backend to load the updated data.")

if __name__ == "__main__":
    main()
