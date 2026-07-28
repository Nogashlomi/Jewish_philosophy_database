import sys, os
sys.path.append('backend')
from app.core.rdf_store import rdf_store
try:
    rdf_store.load_data()
    print('Load successful, triples:', len(rdf_store.g))
except Exception as e:
    print('Error during load:', e)
