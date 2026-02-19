import time
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.core.rdf_store import rdf_store
from app.core.config import settings
from app.services.entity_service import entity_service

def benchmark():
    print("Loading data...")
    start_load = time.time()
    # Load data if empty
    if len(rdf_store.g) == 0:
        rdf_store.load_data()
    print(f"Data load took: {time.time() - start_load:.2f} seconds")

    print("Benchmarking list_persons()...")
    start_time = time.time()
    persons = entity_service.list_persons()
    end_time = time.time()
    
    print(f"Time taken: {end_time - start_time:.4f} seconds")
    print(f"Number of persons: {len(persons)}")

if __name__ == "__main__":
    benchmark()
