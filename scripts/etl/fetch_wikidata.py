import sys
import time
import json
import urllib.parse
import http.client
import ssl
from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import XSD

# Namespaces
JP = Namespace("http://jewish_philosophy.org/ontology#")

# Output Files
PLACES_TTL = "data/places.ttl"
RELATIONS_TTL = "data/place_relations.ttl"

def load_persons():
    g = Graph()
    g.parse("data/person-historical.ttl", format="ttl")
    
    persons = []
    # Query for Persons with Wikidata Link
    q = """
    PREFIX jp: <http://jewish_philosophy.org/ontology#>
    SELECT ?person ?wiki
    WHERE {
        ?person a jp:HistoricalPerson ;
                jp:authorityLink ?wiki .
    }
    """
    for row in g.query(q):
        wiki_url = str(row.wiki)
        if "wikidata.org" in wiki_url:
            qid = wiki_url.split("/")[-1]
            persons.append((str(row.person), qid))
    
    return persons

def fetch_batch_data(qids):
    if not qids: return []
    
    values = " ".join(f"wd:{qid}" for qid in qids)
    
    query = f"""
    SELECT ?person ?personLabel ?place ?placeLabel ?lat ?long ?typeLabel WHERE {{
      VALUES ?person {{ {values} }}
      
      {{
        ?person wdt:P19 ?place .
        BIND("Birth" AS ?typeLabel)
      }} UNION {{
        ?person wdt:P20 ?place .
        BIND("Death" AS ?typeLabel)
      }} UNION {{
        ?person wdt:P551 ?place .
        BIND("Residence" AS ?typeLabel)
      }} UNION {{
        ?person wdt:P937 ?place .
        BIND("WorkLocation" AS ?typeLabel)
      }}
      
      ?place wdt:P625 ?loc .
      ?place rdfs:label ?placeLabel .
      FILTER(LANG(?placeLabel) = "en")
      
      BIND(STRAFTER(STR(?loc), "Point(") AS ?coords)
      BIND(STRBEFORE(?coords, ")") AS ?latlong)
      BIND(STRBEFORE(?latlong, " ") AS ?long)
      BIND(STRAFTER(?latlong, " ") AS ?lat)
      
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
    }}
    """
    
    # Use http.client with unsecured context
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    params = urllib.parse.urlencode({'format': 'json', 'query': query})
    headers = {"User-Agent": "RDF_Explorer_Bot/1.0 (internal research project)", "Accept": "application/json"}
    
    try:
        conn = http.client.HTTPSConnection("query.wikidata.org", context=context, timeout=30)
        conn.request("GET", f"/sparql?{params}", headers=headers)
        response = conn.getresponse()
        
        if response.status != 200:
            print(f"Error: {response.status} {response.reason}")
            print(response.read().decode())
            return []
            
        data = json.loads(response.read().decode())
        conn.close()
        
        return data.get('results', {}).get('bindings', [])
    except Exception as e:
        print(f"Error fetching batch: {e}")
        return []

def main():
    print("Loading persons...")
    persons = load_persons()
    print(f"Found {len(persons)} persons with Wikidata IDs.")
    
    qid_to_uri = {}
    qids = []
    
    for uri, qid in persons:
        qid_to_uri[qid] = URIRef(uri)
        qids.append(qid)
        
    BATCH_SIZE = 1
    
    places_graph = Graph()
    places_graph.bind("jp", JP)
    places_graph.bind("rdfs", RDFS)
    
    relations_graph = Graph()
    relations_graph.bind("jp", JP)
    relations_graph.bind("rdfs", RDFS)
    
    seen_places = set()
    
    for i in range(0, len(qids), BATCH_SIZE):
        batch = qids[i:i+BATCH_SIZE]
        if not batch: break
        
        print(f"Processing {batch[0]} ({i+1}/{len(qids)})...")
        
        results = fetch_batch_data(batch)
        if results:
            print(f"  Got {len(results)} relations.")
        else:
            print(f"  No relations found or error.")
        
        for row in results:
            wiki_uri = row['person']['value']
            person_qid = wiki_uri.split("/")[-1]
            if person_qid not in qid_to_uri: continue
            
            person_uri = qid_to_uri[person_qid]
            
            # Place
            place_url = row['place']['value']
            place_label = row['placeLabel']['value']
            lat = row['lat']['value']
            long = row['long']['value']
            relation_type = row['typeLabel']['value']
            
            clean_label = "".join(c for c in place_label if c.isalnum() or c == '_')
            place_uri = URIRef(f"{JP}Place_{clean_label}")
            place_qid = place_url.split("/")[-1]
            
            if place_uri not in seen_places:
                places_graph.add((place_uri, RDF.type, JP.Place))
                places_graph.add((place_uri, RDFS.label, Literal(place_label)))
                places_graph.add((place_uri, JP.latitude, Literal(lat)))
                places_graph.add((place_uri, JP.longitude, Literal(long)))
                places_graph.add((place_uri, JP.authorityLink, Literal(place_url)))
                seen_places.add(place_uri)
            
            rel_id = f"Rel_{person_qid}_{place_qid}_{relation_type}"
            rel_uri = URIRef(f"{JP}{rel_id}")
            
            relations_graph.add((rel_uri, RDF.type, JP.PlaceRelation))
            relations_graph.add((rel_uri, JP.relatedPlace, place_uri))
            relations_graph.add((rel_uri, JP.placeType, Literal(relation_type)))
            relations_graph.add((rel_uri, JP.aboutPerson, person_uri))
            
            relations_graph.add((person_uri, JP.hasPlaceRelation, rel_uri))
        
        time.sleep(1)

    print(f"Saving {len(places_graph)} triples to {PLACES_TTL}...")
    places_graph.serialize(destination=PLACES_TTL, format="turtle")
    
    print(f"Saving {len(relations_graph)} triples to {RELATIONS_TTL}...")
    relations_graph.serialize(destination=RELATIONS_TTL, format="turtle")
    
    print("Done.")

if __name__ == "__main__":
    main()
