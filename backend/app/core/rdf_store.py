from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS, OWL, SH

# Define Namespaces
JP = Namespace("http://jewish_philosophy.org/ontology#")

class RDFStore:
    def __init__(self, store_type="Memory", store_path="db"):
        self.store_type = store_type
        self.store_path = store_path
        self.g = None
        self._init_graph()

    def _init_graph(self):
        """Initialize the graph with the selected store."""
        import os
        print(f"DEBUG: RDFStore CWD is {os.getcwd()}")
        try:
            if self.store_type == "Sleepycat":
                self.g = Graph(store="Sleepycat")
                path = Path(self.store_path).resolve()
                path.mkdir(parents=True, exist_ok=True)
                self.g.open(str(path), create=True)
                print(f"info: Opened persistent Sleepycat store at {path}")
            else:
                self.g = Graph(store="Memory")
        except Exception as e:
            print(f"warning: Failed to initialize {self.store_type} store: {e}. Falling back to Memory.")
            self.g = Graph(store="Memory")

        self.g.bind("jp", JP)
        self.g.bind("owl", OWL)
        self.g.bind("sh", SH)
        
    def load_data(self):
        """Load all TTL files into the graph."""
        from app.core.config import settings
        import os
        
        data_files = [
            "cleaned/cleaned_persons.ttl",
            "cleaned/cleaned_works.ttl",
            "cleaned/cleaned_places.ttl",
            "cleaned/cleaned_subjects.ttl",
            "cleaned/cleaned_scholarly.ttl",
            "cleaned/cleaned_sources.ttl",
            "ontology/vocabulary.ttl",
            "cleaned/cleaned_other.ttl",
            "wikidata_place_coordinates.ttl",
            "wikidata_place_relations_new.ttl",
            "wikidata_places_new.ttl",
            "wikidata_time_relations.ttl",
            "wikidata_persons.ttl",
            "wikidata_works.ttl",
            "place_relations.ttl",
            "time_data.ttl"
        ]
        
        for filename in data_files:
            try:
                file_path = os.path.join(settings.DATA_DIR, filename)
                print(f"Loading {file_path}...")
                self.g.parse(file_path, format="turtle")
            except Exception as e:
                print(f"Warning: Could not load {filename}: {e}")
        
        print(f"Graph loaded with {len(self.g)} triples.")

    def query(self, query_str: str, **kwargs):
        return self.g.query(query_str, **kwargs)

    def close(self):
        if self.store_type == "Sleepycat":
            self.g.close()

# Use 'Sleepycat' if available, otherwise 'Memory'
# We default to Memory for now to ensure stability if bsddb is missing, 
# but the structure is there to switch to "Sleepycat" by changing this argument.
rdf_store = RDFStore(store_type="Memory", store_path="db")
