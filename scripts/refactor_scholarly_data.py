import rdflib
from rdflib import Graph, Namespace, RDF, RDFS, Literal, URIRef
from rdflib.namespace import XSD
import re
import os

# Namespaces
JP = Namespace("http://jewish_philosophy.org/ontology#")
SCHOLARLY = Namespace("http://jewish_philosophy.org/scholarly/")
ID = Namespace("http://jewish_philosophy.org/id/")

def sanitize_name(name):
    # Remove dots, spaces, etc for URI
    s = str(name).strip()
    s = re.sub(r'[^a-zA-Z0-9_\-]', '_', s)
    s = re.sub(r'_+', '_', s) # collapse multiple underscores
    return s.strip('_')

def run_migration():
    print("Starting migration...")
    
    # 1. Load Data
    g = Graph()
    data_dir = "data"
    files = ["scholarly-work.ttl", "imported_scholarly_data.ttl", "mentions-scholarly-works-to-people-and-works.ttl"]
    
    for f in files:
        path = os.path.join(data_dir, f)
        if os.path.exists(path):
            print(f"Loading {f}...")
            g.parse(path, format="turtle")
        else:
            print(f"Warning: {f} not found.")

    # 2. Output Graphs
    g_scholars = Graph()
    g_sources = Graph()
    g_works = Graph()
    
    # Bind prefixes
    for graph in [g_scholars, g_sources, g_works]:
        graph.bind("jp", JP)
        graph.bind("rdfs", RDFS)
        graph.bind("xsd", XSD)

    # 3. Create Sources
    source_legacy = JP["Source_Legacy_Import"]
    source_bib = JP["Source_Bibliography"]
    
    g_sources.add((source_legacy, RDF.type, JP.Source))
    g_sources.add((source_legacy, RDFS.label, Literal("Legacy Import Data")))
    
    g_sources.add((source_bib, RDF.type, JP.Source))
    g_sources.add((source_bib, RDFS.label, Literal("General Bibliography")))

    # 4. Migrate Works & Extract Scholars
    scholars_cache = {} # name -> uri

    def get_scholar_uri(name):
        if name not in scholars_cache:
            safe_id = sanitize_name(name)
            uri = JP[f"Scholar_{safe_id}"]
            scholars_cache[name] = uri
            g_scholars.add((uri, RDF.type, JP.Scholar))
            g_scholars.add((uri, RDFS.label, Literal(name)))
        return scholars_cache[name]

    # Iterate over all ScholarlyWorks
    for work_uri in g.subjects(RDF.type, JP.ScholarlyWork):
        # -- Metadata Extraction --
        title = g.value(work_uri, JP.title) or g.value(work_uri, RDFS.label)
        year = g.value(work_uri, JP.year)
        
        # Handle "Island B" URIs (SW_Author_Year) to extract missing data if needed
        if "scholarly/SW_" in str(work_uri):
             # Try to parse properties from URI if missing
             pass 

        # -- Creators processing --
        # Collect all creators (authorName, creatorName, etc.)
        creators = set()
        for p in [JP.creatorName, JP.authorName, JP.editorName]:
             for c in g.objects(work_uri, p):
                 creators.add(str(c))
        
        # Also check URI for authors in "SW_" series if no properties exist? 
        # For now, let's stick to explicit properties and the 'Island B' extraction logic if implemented.
        
        # -- Create New Work Entry --
        # Use existing URI or canonicalize? Let's keep existing URIs for stability for now.
        new_work_uri = work_uri 
        
        g_works.add((new_work_uri, RDF.type, JP.ScholarlyWork))
        
        if title:
            g_works.add((new_work_uri, JP.title, Literal(str(title), datatype=XSD.string)))
            # Also keep rdfs:label for generic tools
            g_works.add((new_work_uri, RDFS.label, Literal(str(title))))

        if year:
             # Standardize to publicationYear
             g_works.add((new_work_uri, JP.publicationYear, year))

        # Assign Source (Default to Legacy for now)
        g_works.add((new_work_uri, JP.hasSource, source_legacy))

        # Link Authors
        for creator_name in creators:
            scholar_uri = get_scholar_uri(creator_name)
            g_works.add((new_work_uri, JP.hasAuthor, scholar_uri))

        # Preserve Mentions
        for p in [JP.aboutPerson, JP.aboutWork]:
            for target in g.objects(work_uri, p):
                 g_works.add((new_work_uri, p, target))

    # 5. Save Output
    print(f"Extracted {len(scholars_cache)} scholars.")
    print(f"Processed {len(list(g_works.subjects(RDF.type, JP.ScholarlyWork)))} works.")
    
    g_scholars.serialize(os.path.join(data_dir, "scholars.ttl"), format="turtle")
    g_sources.serialize(os.path.join(data_dir, "sources.ttl"), format="turtle")
    g_works.serialize(os.path.join(data_dir, "scholarly-works-v2.ttl"), format="turtle")
    
    print("Migration complete. Check scholarly-works-v2.ttl, scholars.ttl, sources.ttl")

if __name__ == "__main__":
    run_migration()
