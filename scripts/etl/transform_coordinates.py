from rdflib import Graph, Namespace, Literal, XSD
import re

JP = Namespace("http://jewish_philosophy.org/ontology#")

def transform_coords():
    file_path = "data/wikidata_place_coordinates.ttl"
    g = Graph()
    g.parse(file_path, format="turtle")
    
    new_g = Graph()
    new_g.bind("jp", JP)
    
    count = 0
    
    # Iterate over all coordinates
    for s, p, o in g.triples((None, JP.coordinates, None)):
        wkt = str(o)
        # Format: Point(LONG LAT)
        match = re.search(r"Point\(([-\d\.]+) ([-\d\.]+)\)", wkt)
        if match:
            long = float(match.group(1))
            lat = float(match.group(2))
            
            new_g.add((s, JP.latitude, Literal(lat)))
            new_g.add((s, JP.longitude, Literal(long)))
            count += 1
            
    print(f"Transformed {count} coordinate points to lat/long pairs.")
    new_g.serialize(destination="data/wikidata_place_coordinates.ttl", format="turtle")

if __name__ == "__main__":
    transform_coords()
