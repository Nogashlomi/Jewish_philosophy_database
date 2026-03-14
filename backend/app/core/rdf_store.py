from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS, OWL, SH

# Define Namespaces
JP = Namespace("http://jewish_philosophy.org/ontology#")

class RDFStore:
    def __init__(self, store_type="Memory", store_path="db"):
        self.store_type = store_type
        self.store_path = store_path
        self.g = None
        self._cache = {}  # query_str -> list of result rows
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
        """Load all TTL files from the data directory dynamically."""
        from app.core.config import settings
        import os
        from pathlib import Path

        data_dir = Path(settings.DATA_DIR)

        print(f"\n=== RDF Data Loading Started ===")
        print(f"DATA_DIR: {data_dir}")
        print(f"DATA_DIR exists: {data_dir.exists()}")

        # Find all TTL files recursively
        ttl_files = sorted(data_dir.rglob("*.ttl"))
        print(f"Found {len(ttl_files)} TTL files")

        if not ttl_files:
            print(f"ERROR: No TTL files found in {data_dir}")
            return

        loaded_count = 0
        for file_path in ttl_files:
            try:
                print(f"  Loading {file_path.name}...", end=" ")
                self.g.parse(str(file_path), format="turtle")
                loaded_count += 1
                print(f"OK ({len(self.g)} triples total)")
            except Exception as e:
                print(f"FAILED: {str(e)[:100]}")

        print(f"\n✓ Graph loaded with {len(self.g)} triples from {loaded_count}/{len(ttl_files)} files.")
        self._cache.clear()  # Invalidate cache after reload
        print("✓ Query cache cleared.")
        print("=== RDF Data Loading Complete ===\n")

    def query(self, query_str: str, **kwargs):
        # Only cache queries with no runtime bindings (list/stats queries)
        if not kwargs:
            if query_str not in self._cache:
                self._cache[query_str] = list(self.g.query(query_str))
            return self._cache[query_str]
        return self.g.query(query_str, **kwargs)

    def close(self):
        if self.store_type == "Sleepycat":
            self.g.close()

# Use 'Sleepycat' if available, otherwise 'Memory'
# We default to Memory for now to ensure stability if bsddb is missing, 
# but the structure is there to switch to "Sleepycat" by changing this argument.
rdf_store = RDFStore(store_type="Memory", store_path="db")
