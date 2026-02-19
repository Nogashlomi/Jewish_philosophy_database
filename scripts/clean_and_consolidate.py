
import sys
import os
from collections import defaultdict
from pathlib import Path

# Add backend to path for imports
sys.path.append(os.path.join(os.getcwd(), "backend"))

from rdflib import Graph, Namespace, RDF, RDFS, URIRef, Literal
from app.core.config import settings

# Define Namespaces
JP = Namespace("http://jewish_philosophy.org/ontology#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")

def clean_and_consolidate():
    print("Loading all data files...")
    
    # 1. Load EVERYTHING into one graph
    g = Graph()
    g.bind("jp", JP)
    g.bind("owl", OWL)
    
    data_dir = Path(settings.DATA_DIR)
    files_to_load = [
        "time_data.ttl", "wikidata_places.ttl", "wikidata_places_new.ttl",
        "wikidata_works.ttl", "wikidata_place_relations.ttl", "wikidata_place_relations_new.ttl",
        "wikidata_place_coordinates.ttl", "wikidata_time_relations.ttl", "scholars.ttl",
        "place_relations.ttl", "work-historical.ttl", "book_works.ttl", "book_persons.ttl",
        "books_reports_persons.ttl", "books_reports_works.ttl", "books_reports_places.ttl",
        "nli_astronomy_manuscripts.ttl", "languages.ttl", "sources.ttl", "subjects.ttl",
        "person-historical.ttl", "wikidata_persons.ttl", "translation_relations.ttl",
        "places.ttl", "scholarly-works.ttl", "data_sources.ttl",
        "ontology/prefixes.ttl", "ontology/vocabulary.ttl"
    ]

    for f in files_to_load:
        p = data_dir / f
        if p.exists():
            print(f"  Loading {f}...")
            try:
                g.parse(str(p), format="turtle")
            except Exception as e:
                print(f"  ERROR loading {f}: {e}")

    print(f"Total triples loaded: {len(g)}")

    # 2. Identify Canonical URIs for Persons (Label-based)
    print("identifying duplicate Persons...")
    person_label_map = defaultdict(list)
    # Find all things that are Persons
    # 1. By Type
    for s in g.subjects(RDF.type, JP.HistoricalPerson):
        label = g.value(s, RDFS.label)
        if label:
            person_label_map[str(label)].append(s)
            
    # Also check BookPerson
    for s in g.subjects(RDF.type, JP.BookPerson): 
         label = g.value(s, RDFS.label)
         if label: 
             person_label_map[str(label)].append(s)

    # 2. Heuristic: URIs starting with 'Person_Q' are likely persons
    # (Wikidata import might miss type decls)
    for s in g.subjects():
        if "Person_Q" in str(s):
            label = g.value(s, RDFS.label)
            if label:
                # Add if not already present to avoid dups in list
                if s not in person_label_map[str(label)]:
                    person_label_map[str(label)].append(s)

    redirect_map = {} # old_uri -> new_uri
    
    for label, uris in person_label_map.items():
        if len(uris) > 1:
            # Pick canonical: prefer QID (wikidata), then longest URI, or just first
            canonical = sorted(uris, key=lambda u: (
                0 if "wikidata" in str(u) or "_Q" in str(u) else 1, # Prefer QIDs
                len(str(u)) # Tie-break
            ))[0]
            
            for u in uris:
                if u != canonical:
                    redirect_map[u] = canonical

    print(f"Found {len(redirect_map)} duplicate Person URIs to redirect.")

    # 3. Identify Canonical URIs for Works (Title-based)
    print("Identifying duplicate Works...")
    work_title_map = defaultdict(list)
    for s in g.subjects(RDF.type, JP.HistoricalWork):
        title = g.value(s, JP.title)
        if not title:
            title = g.value(s, RDFS.label)
        
        if title:
            work_title_map[str(title)].append(s)
            
    for title, uris in work_title_map.items():
        if len(uris) > 1:
             # Pick canonical: prefer QID (wikidata)
            canonical = sorted(uris, key=lambda u: (
                0 if "wikidata" in str(u) or "_W" in str(u) else 1,
                len(str(u))
            ))[0]
            for u in uris:
                if u != canonical:
                    redirect_map[u] = canonical

    print(f"Found {len(redirect_map) - len([u for u in redirect_map if u in person_label_map])} duplicate Work URIs to redirect.") # Approx count

    # 4. Rewrite Graph with Canonical URIs
    print("Rewriting graph...")
    new_g = Graph()
    new_g.bind("jp", JP)
    new_g.bind("owl", OWL) 
    
    # Copy triples, substituting subjects and objects
    for s, p, o in g:
        new_s = redirect_map.get(s, s)
        new_o = redirect_map.get(o, o)
        
        # Don't add triple if it becomes self-referential identity (unless useful)
        # e.g. owl:sameAs
        
        # Explicitly ADD owl:sameAs for merged entities? Maybe not needed for clean DB.
        
        new_g.add((new_s, p, new_o))
        
    print(f"New graph size: {len(new_g)}")
    
    # 5. Split and Save to Cleaned Files
    print("Saving cleaned files...")
    
    graphs = {
        "cleaned_persons.ttl": Graph(),
        "cleaned_works.ttl": Graph(),
        "cleaned_places.ttl": Graph(),
        "cleaned_subjects.ttl": Graph(),
        "cleaned_scholarly.ttl": Graph(),
        "cleaned_sources.ttl": Graph(),
        "cleaned_ontology.ttl": Graph(),
        "cleaned_other.ttl": Graph() # For everything else
    }
    
    for gr in graphs.values():
        gr.bind("jp", JP)
        gr.bind("owl", OWL)
        gr.bind("rdfs", RDFS)

    # Helper to determine file for a subject
    def get_target_graph(s, type_uri=None):
        if not type_uri:
            type_uri = new_g.value(s, RDF.type)
            
        if type_uri == JP.HistoricalPerson or type_uri == JP.BookPerson:
            return graphs["cleaned_persons.ttl"]
        elif type_uri == JP.HistoricalWork:
            return graphs["cleaned_works.ttl"]
        elif type_uri == JP.Place:
            return graphs["cleaned_places.ttl"]
        elif type_uri == JP.Subject:
            return graphs["cleaned_subjects.ttl"]
        elif type_uri == JP.ScholarlyWork:
            return graphs["cleaned_scholarly.ttl"]
        elif type_uri == JP.Source:
            return graphs["cleaned_sources.ttl"]
        elif str(s).startswith(str(JP)) and "ontology" in str(s): # Heuristic for ontology defs
             return graphs["cleaned_ontology.ttl"]
        else:
             return graphs["cleaned_other.ttl"]

    # Iterate subjects
    for s in set(new_g.subjects()):
        # Determine target graph based on type
        target = get_target_graph(s)
        
        # Copy strict subject triples
        for p, o in new_g.predicate_objects(s):
            target.add((s, p, o))

    # Save files
    os.makedirs(data_dir / "cleaned", exist_ok=True)
    
    for fname, gr in graphs.items():
        if len(gr) > 0:
            out_path = data_dir / "cleaned" / fname
            print(f"  Writing {fname} ({len(gr)} triples)...")
            gr.serialize(destination=str(out_path), format="turtle")

    print("Consolidation Complete!")

if __name__ == "__main__":
    clean_and_consolidate()
