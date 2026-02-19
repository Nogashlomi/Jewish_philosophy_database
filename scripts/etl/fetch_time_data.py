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

# Output File
TIME_DATA_TTL = "data/time_data.ttl"

def load_persons():
    """Load persons with Wikidata IDs from person-historical.ttl"""
    g = Graph()
    g.parse("data/person-historical.ttl", format="ttl")
    
    persons = []
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

def fetch_time_data(qid):
    """Fetch birth and death dates for a single QID from Wikidata"""
    
    # P569 = date of birth
    # P570 = date of death
    query = f"""
    SELECT ?birth ?death WHERE {{
      wd:{qid} wdt:P569 ?birth .
      OPTIONAL {{ wd:{qid} wdt:P570 ?death }}
    }}
    """
    
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    params = urllib.parse.urlencode({'format': 'json', 'query': query})
    headers = {
        "User-Agent": "RDF_Explorer_Bot/1.0 (internal research project)", 
        "Accept": "application/json"
    }
    
    try:
        conn = http.client.HTTPSConnection("query.wikidata.org", context=context, timeout=30)
        conn.request("GET", f"/sparql?{params}", headers=headers)
        response = conn.getresponse()
        
        if response.status != 200:
            print(f"  Error: {response.status} {response.reason}")
            return None
            
        data = json.loads(response.read().decode())
        conn.close()
        
        bindings = data.get('results', {}).get('bindings', [])
        if bindings:
            return bindings[0]
        return None
        
    except Exception as e:
        print(f"  Error fetching {qid}: {e}")
        return None

def extract_year(date_str):
    """Extract year from Wikidata date string (e.g., '1138-03-30T00:00:00Z' -> 1138)"""
    if not date_str:
        return None
    try:
        # Wikidata dates can be: +1138-03-30T00:00:00Z or -0500-01-01T00:00:00Z
        # Remove leading + or -
        cleaned = date_str.lstrip('+-')
        # Extract year part
        year = int(cleaned.split('-')[0])
        # Check if original was negative (BCE)
        if date_str.startswith('-'):
            year = -year
        return year
    except:
        return None

def main():
    print("Loading persons...")
    persons = load_persons()
    print(f"Found {len(persons)} persons with Wikidata IDs.")
    
    # Map QID to URI
    qid_to_uri = {}
    for uri, qid in persons:
        qid_to_uri[qid] = URIRef(uri)
    
    time_graph = Graph()
    time_graph.bind("jp", JP)
    time_graph.bind("rdfs", RDFS)
    time_graph.bind("xsd", XSD)
    
    success_count = 0
    
    for i, (uri, qid) in enumerate(persons, 1):
        print(f"Processing {qid} ({i}/{len(persons)})...")
        
        result = fetch_time_data(qid)
        
        if result:
            birth_str = result.get('birth', {}).get('value')
            death_str = result.get('death', {}).get('value')
            
            birth_year = extract_year(birth_str)
            death_year = extract_year(death_str)
            
            if birth_year or death_year:
                person_uri = URIRef(uri)
                
                # Create TimeRelation for this person
                time_rel_uri = URIRef(f"{JP}TimeRelation_{qid}")
                time_graph.add((time_rel_uri, RDF.type, JP.TimeRelation))
                time_graph.add((time_rel_uri, JP.aboutPerson, person_uri))
                
                if birth_year:
                    time_graph.add((time_rel_uri, JP.timeFrom, Literal(birth_year, datatype=XSD.gYear)))
                    print(f"  Birth: {birth_year}")
                
                if death_year:
                    time_graph.add((time_rel_uri, JP.timeUntil, Literal(death_year, datatype=XSD.gYear)))
                    print(f"  Death: {death_year}")
                
                # Link person to time relation
                time_graph.add((person_uri, JP.hasTimeRelation, time_rel_uri))
                
                success_count += 1
            else:
                print(f"  No valid dates found")
        else:
            print(f"  No data returned")
        
        # Be nice to Wikidata
        time.sleep(1)
    
    print(f"\nSuccessfully fetched time data for {success_count}/{len(persons)} persons")
    print(f"Saving {len(time_graph)} triples to {TIME_DATA_TTL}...")
    time_graph.serialize(destination=TIME_DATA_TTL, format="turtle")
    
    print("Done.")

if __name__ == "__main__":
    main()
