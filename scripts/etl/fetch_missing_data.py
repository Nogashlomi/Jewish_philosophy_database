#!/usr/bin/env python3
"""
Fetch missing place and time data from Wikidata for all persons.
Queries for birth/death dates and birth/death places.
"""
import time
import re
from rdflib import Graph, Namespace, RDF, RDFS, Literal, URIRef
from SPARQLWrapper import SPARQLWrapper, JSON

JP = Namespace("http://jewish_philosophy.org/ontology#")

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"

def extract_wikidata_qid(url):
    """Extract QID from Wikidata URL."""
    if not url:
        return None
    match = re.search(r'Q\d+', str(url))
    return match.group(0) if match else None

def load_persons_with_wikidata():
    """Load all persons with Wikidata IDs."""
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
        except Exception as e:
            print(f"Warning: Could not load {file_path}: {e}")
    
    persons = []
    for person_uri in g.subjects(RDF.type, JP.HistoricalPerson):
        for auth in g.objects(person_uri, JP.authorityLink):
            qid = extract_wikidata_qid(auth)
            if qid:
                person_id = str(person_uri).split("#")[-1]
                label = g.value(person_uri, RDFS.label)
                persons.append({
                    'uri': person_uri,
                    'id': person_id,
                    'qid': qid,
                    'label': str(label) if label else person_id
                })
                break
    
    return persons, g

def fetch_wikidata_batch(qids):
    """Fetch birth/death data for a batch of QIDs from Wikidata."""
    qid_values = " ".join([f"wd:{qid}" for qid in qids])
    
    query = f"""
    SELECT ?person ?personLabel 
           ?birthDate ?birthPlace ?birthPlaceLabel ?birthPlaceCoords
           ?deathDate ?deathPlace ?deathPlaceLabel ?deathPlaceCoords
    WHERE {{
      VALUES ?person {{ {qid_values} }}
      
      OPTIONAL {{ 
        ?person wdt:P569 ?birthDate .
      }}
      OPTIONAL {{ 
        ?person wdt:P19 ?birthPlace .
        OPTIONAL {{ ?birthPlace wdt:P625 ?birthPlaceCoords . }}
      }}
      OPTIONAL {{ 
        ?person wdt:P570 ?deathDate .
      }}
      OPTIONAL {{ 
        ?person wdt:P20 ?deathPlace .
        OPTIONAL {{ ?deathPlace wdt:P625 ?deathPlaceCoords . }}
      }}
      
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,he". }}
    }}
    """
    
    sparql = SPARQLWrapper(WIKIDATA_ENDPOINT)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    sparql.addCustomHttpHeader("User-Agent", "RDF-Research-Explorer/1.0")
    
    try:
        results = sparql.query().convert()
        return results["results"]["bindings"]
    except Exception as e:
        print(f"Error querying Wikidata: {e}")
        return []

def create_time_relations(g_time, persons_data, qid_to_uri):
    """Create time relations TTL file."""
    g = Graph()
    g.bind("jp", JP)
    g.bind("rdfs", RDFS)
    
    time_relations_created = 0
    
    for qid, data in persons_data.items():
        if not data.get('birthDate') and not data.get('deathDate'):
            continue
        
        # Find person URI from map
        person_uri = qid_to_uri.get(qid)
        
        if not person_uri:
            continue
        
        person_id = str(person_uri).split("#")[-1]
        
        # Create time relation
        time_rel_id = f"TimeRelation_{person_id}"
        time_rel_uri = JP[time_rel_id]
        
        g.add((time_rel_uri, RDF.type, JP.TimeRelation))
        g.add((time_rel_uri, RDFS.label, Literal(f"Time Relation for {data.get('label', person_id)}")))
        g.add((time_rel_uri, JP.relatedPerson, person_uri))
        
        if data.get('birthDate'):
            try:
                year_str = str(data['birthDate'])[:4]
                if year_str.isdigit():
                    g.add((time_rel_uri, JP.birthYear, Literal(int(year_str))))
            except:
                pass
        
        if data.get('deathDate'):
            try:
                year_str = str(data['deathDate'])[:4]
                if year_str.isdigit():
                    g.add((time_rel_uri, JP.deathYear, Literal(int(year_str))))
            except:
                pass
        
        # Link person to time relation
        g.add((person_uri, JP.hasTimeRelation, time_rel_uri))
        
        time_relations_created += 1
    
    return g, time_relations_created

def create_place_relations(g_places, persons_data, existing_places, qid_to_uri):
    """Create place relations TTL file and new places."""
    g_relations = Graph()
    g_relations.bind("jp", JP)
    g_relations.bind("rdfs", RDFS)
    
    # Graph for just coordinates (to enrich existing places)
    g_coords = Graph()
    g_coords.bind("jp", JP)

    g_new_places = Graph()
    g_new_places.bind("jp", JP)
    g_new_places.bind("rdfs", RDFS)
    
    place_relations_created = 0
    new_places_created = 0
    coords_added = 0
    place_qid_to_uri = {}
    
    for qid, data in persons_data.items():
        if not data.get('birthPlace') and not data.get('deathPlace'):
            continue
        
        # Find person URI from map
        person_uri = qid_to_uri.get(qid)
        
        if not person_uri:
            continue
        
        person_id = str(person_uri).split("#")[-1]
        
        # Process birth place
        if data.get('birthPlace'):
            place_qid = data['birthPlace']
            
            # Check if place exists or create it
            if place_qid not in place_qid_to_uri:
                if place_qid in existing_places:
                    place_uri = existing_places[place_qid]
                    place_qid_to_uri[place_qid] = place_uri
                    
                    # Add coordinates for EXISTING place
                    if data.get('birthPlaceCoords'):
                        g_coords.add((place_uri, JP.coordinates, Literal(data['birthPlaceCoords'])))
                        coords_added += 1
                else:
                    # Create new place
                    place_uri = JP[f"Place_{place_qid}"]
                    g_new_places.add((place_uri, RDF.type, JP.Place))
                    g_new_places.add((place_uri, RDFS.label, Literal(data.get('birthPlaceLabel', place_qid))))
                    g_new_places.add((place_uri, JP.authorityLink, Literal(f"http://www.wikidata.org/entity/{place_qid}")))
                    
                    if data.get('birthPlaceCoords'):
                        g_new_places.add((place_uri, JP.coordinates, Literal(data['birthPlaceCoords'])))
                        # Also add to coords graph for completeness/redundancy or just keep in new_places
                        # Let's keep new places self-contained, but g_coords is for enrichment.
                    
                    place_qid_to_uri[place_qid] = place_uri
                    new_places_created += 1
            
            # Create birth relation
            rel_id = f"Relation_{person_id}_Birth"
            rel_uri = JP[rel_id]
            g_relations.add((rel_uri, RDF.type, JP.PlaceRelation))
            g_relations.add((rel_uri, RDFS.label, Literal(f"Birth of {data.get('label', person_id)}")))
            g_relations.add((rel_uri, JP.relatedPerson, person_uri))
            g_relations.add((rel_uri, JP.relatedPlace, place_qid_to_uri[place_qid]))
            g_relations.add((rel_uri, JP.relationType, Literal("Birth")))
            
            g_relations.add((person_uri, JP.hasPlaceRelation, rel_uri))
            place_relations_created += 1
        
        # Process death place
        if data.get('deathPlace'):
            place_qid = data['deathPlace']
            
            # Check if place exists or create it
            if place_qid not in place_qid_to_uri:
                if place_qid in existing_places:
                    place_uri = existing_places[place_qid]
                    place_qid_to_uri[place_qid] = place_uri
                    
                    # Add coordinates for EXISTING place
                    if data.get('deathPlaceCoords'):
                        g_coords.add((place_uri, JP.coordinates, Literal(data['deathPlaceCoords'])))
                        coords_added += 1
                else:
                    # Create new place
                    place_uri = JP[f"Place_{place_qid}"]
                    g_new_places.add((place_uri, RDF.type, JP.Place))
                    g_new_places.add((place_uri, RDFS.label, Literal(data.get('deathPlaceLabel', place_qid))))
                    g_new_places.add((place_uri, JP.authorityLink, Literal(f"http://www.wikidata.org/entity/{place_qid}")))
                    
                    if data.get('deathPlaceCoords'):
                        g_new_places.add((place_uri, JP.coordinates, Literal(data['deathPlaceCoords'])))
                    
                    place_qid_to_uri[place_qid] = place_uri
                    new_places_created += 1
            
            # Create death relation
            rel_id = f"Relation_{person_id}_Death"
            rel_uri = JP[rel_id]
            g_relations.add((rel_uri, RDF.type, JP.PlaceRelation))
            g_relations.add((rel_uri, RDFS.label, Literal(f"Death of {data.get('label', person_id)}")))
            g_relations.add((rel_uri, JP.relatedPerson, person_uri))
            g_relations.add((rel_uri, JP.relatedPlace, place_qid_to_uri[place_qid]))
            g_relations.add((rel_uri, JP.relationType, Literal("Death")))
            
            g_relations.add((person_uri, JP.hasPlaceRelation, rel_uri))
            place_relations_created += 1
    
    return g_relations, g_new_places, g_coords, place_relations_created, new_places_created, coords_added

def load_existing_places():
    """Load existing places to avoid duplicates."""
    g = Graph()
    try:
        g.parse("data/wikidata_places.ttl", format="turtle")
    except:
        pass
    
    places = {}
    for place_uri in g.subjects(RDF.type, JP.Place):
        for auth in g.objects(place_uri, JP.authorityLink):
            qid = extract_wikidata_qid(auth)
            if qid:
                places[qid] = place_uri
                break
    
    return places

def main():
    print("=== FETCHING MISSING PLACE AND TIME DATA FROM WIKIDATA ===\n")
    
    # Load persons
    print("Loading persons with Wikidata IDs...")
    persons, g_all = load_persons_with_wikidata()
    print(f"Found {len(persons)} persons with Wikidata IDs\n")
    
    # Load existing places
    existing_places = load_existing_places()
    print(f"Loaded {len(existing_places)} existing places\n")
    
    # Fetch data in batches
    print("Fetching data from Wikidata...")
    batch_size = 50
    all_data = {}
    
    for i in range(0, len(persons), batch_size):
        batch = persons[i:i+batch_size]
        qids = [p['qid'] for p in batch]
        
        print(f"  Batch {i//batch_size + 1}/{(len(persons)-1)//batch_size + 1} ({len(qids)} persons)...")
        results = fetch_wikidata_batch(qids)
        
        for result in results:
            qid = result['person']['value'].split('/')[-1]
            
            # Find person label
            person_label = None
            for p in batch:
                if p['qid'] == qid:
                    person_label = p['label']
                    break
            
            all_data[qid] = {
                'label': person_label,
                'birthDate': result.get('birthDate', {}).get('value'),
                'birthPlace': result.get('birthPlace', {}).get('value', '').split('/')[-1] if result.get('birthPlace') else None,
                'birthPlaceLabel': result.get('birthPlaceLabel', {}).get('value'),
                'birthPlaceCoords': result.get('birthPlaceCoords', {}).get('value'),
                'deathDate': result.get('deathDate', {}).get('value'),
                'deathPlace': result.get('deathPlace', {}).get('value', '').split('/')[-1] if result.get('deathPlace') else None,
                'deathPlaceLabel': result.get('deathPlaceLabel', {}).get('value'),
                'deathPlaceCoords': result.get('deathPlaceCoords', {}).get('value'),
            }
        
        time.sleep(1)  # Be nice to Wikidata
    
    print(f"\n✅ Fetched data for {len(all_data)} persons\n")
    
    # Create QID to URI map
    qid_to_uri = {p['qid']: p['uri'] for p in persons}
    
    # Create time relations
    print("Creating time relations...")
    g_time, time_count = create_time_relations(g_all, all_data, qid_to_uri)
    g_time.serialize(destination="data/wikidata_time_relations.ttl", format="turtle")
    print(f"✅ Created {time_count} time relations\n")
    
    # Create place relations and new places
    # Create place relations and new places
    print("Creating place relations...")
    g_place_rels, g_new_places, g_coords, place_count, new_place_count, coords_count = create_place_relations(g_all, all_data, existing_places, qid_to_uri)
    g_place_rels.serialize(destination="data/wikidata_place_relations_new.ttl", format="turtle")
    g_coords.serialize(destination="data/wikidata_place_coordinates.ttl", format="turtle")
    
    print(f"✅ Added coordinates for {coords_count} existing places")
    
    if new_place_count > 0:
        g_new_places.serialize(destination="data/wikidata_places_new.ttl", format="turtle")
        print(f"✅ Created {place_count} place relations and {new_place_count} new places\n")
    else:
        print(f"✅ Created {place_count} place relations (no new places needed)\n")
    
    print("✅ Done!")

if __name__ == "__main__":
    main()
