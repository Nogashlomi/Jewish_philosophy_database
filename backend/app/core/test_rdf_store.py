from rdflib import Literal, URIRef
from app.core.rdf_store import RDFStore, JP

QUERY = "SELECT ?o WHERE {{ <http://example.org/s> <http://example.org/p> ?o . FILTER(?o != {n}) }}"

def make_store(cache_size):
    store = RDFStore(cache_size=cache_size)
    store.g.add((URIRef("http://example.org/s"), URIRef("http://example.org/p"), Literal(1)))
    return store

def test_query_caches_results():
    store = make_store(cache_size=4)
    first = store.query(QUERY.format(n=0))
    second = store.query(QUERY.format(n=0))
    assert first is second
    assert [int(row.o) for row in first] == [1]

def test_query_cache_is_bounded():
    store = make_store(cache_size=2)
    for n in range(5):
        store.query(QUERY.format(n=n + 10))
    assert len(store._cache) == 2

def test_query_cache_evicts_least_recently_used():
    store = make_store(cache_size=2)
    store.query(QUERY.format(n=10))
    store.query(QUERY.format(n=11))
    store.query(QUERY.format(n=10))
    store.query(QUERY.format(n=12))
    assert QUERY.format(n=10) in store._cache
    assert QUERY.format(n=11) not in store._cache

def test_query_with_bindings():
    store = make_store(cache_size=2)
    rows = list(store.query("SELECT ?o WHERE { ?s <http://example.org/p> ?o }", initBindings={"s": URIRef("http://example.org/s")}))
    assert [int(row.o) for row in rows] == [1]
    assert len(store._cache) == 0

def test_load_data_loads_graph_and_clears_cache():
    store = RDFStore()
    store.query(QUERY.format(n=0))
    store.load_data()
    assert len(store.g) > 0
    assert len(store._cache) == 0
    assert (None, None, JP.HistoricalPerson) in store.g
