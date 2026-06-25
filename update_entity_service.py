import re

with open('backend/app/services/entity_service.py', 'r') as f:
    c = f.read()

# Add get_sources and _get_source_filter methods
methods = """
    def _get_source_filter(self, source: str, var_name: str = "uri") -> str:
        if not source:
            return ""
        return f"?{var_name} jp:hasSource <{JP}{source}> ."

    def get_sources(self) -> List[dict]:
        results = []
        for row in rdf_store.query(queries.GET_SOURCES):
            results.append({
                "id": str(row.uri).split("#")[-1],
                "label": str(row.label) if row.label else str(row.uri).split("#")[-1]
            })
        results.sort(key=lambda x: x["label"])
        return results

    def get_global_stats"""
c = c.replace("    def get_global_stats", methods)

# Add source to get_global_stats
c = re.sub(r'def get_global_stats\(self, \) -> dict:', 'def get_global_stats(self, source: str = None) -> dict:', c)
# In get_global_stats, replace search_filter="" with source_filter
stats_mod = """        sf = self._get_source_filter(source, "s")
        for key, q in queries.STATS_QUERIES.items():
            if "{search_filter}" in q:
                formatted_q = q.format(search_filter=sf)
            else:
                formatted_q = q
            for row in rdf_store.query(formatted_q):"""
c = re.sub(r'\s*for key, q in queries\.STATS_QUERIES\.items\(\):\n\s*for row in rdf_store\.query\(q\):', '\n' + stats_mod, c)

# Add source to list_persons
c = re.sub(r'def list_persons\(self,\s*page: int = 1,\s*page_size: int = 100\) -> PaginatedResponse\[PersonList\]:', 'def list_persons(self, page: int = 1, page_size: int = 100, source: str = None) -> PaginatedResponse[PersonList]:', c)
c = re.sub(r'q_count = queries\.COUNT_PERSONS\.format\(search_filter=""\)', 'sf = self._get_source_filter(source, "uri")\n        q_count = queries.COUNT_PERSONS.format(search_filter=sf)', c)
c = re.sub(r'q_data = queries\.LIST_PERSONS\.format\(\n\s*search_filter="",', 'q_data = queries.LIST_PERSONS.format(\n            search_filter=sf,', c)

# Add source to get_network_data
c = re.sub(r'def get_network_data\(self, \) -> NetworkData:', 'def get_network_data(self, source: str = None) -> NetworkData:', c)
c = re.sub(r'q_nodes = queries\.GET_NETWORK_NODES\.format\(search_filter=""\)', 'sf_nodes = self._get_source_filter(source, "s")\n        q_nodes = queries.GET_NETWORK_NODES.format(search_filter=sf_nodes)', c)

with open('backend/app/services/entity_service.py', 'w') as f:
    f.write(c)

