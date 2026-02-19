# Medieval Jewish Philosophy - RDF Explorer

A research-oriented web application for mapping and studying medieval Jewish philosophy.
Visualizes **Historical Persons**, **Works**, **Places**, and their connections from an RDF Knowledge Graph.

## Features
- **Exploration**: Browse lists of Persons, Works, and Scholarly Literature.
- **Detail Views**: See full properties, authority links, and mentions.
- **Geo-Explorer**: Interactive Leaflet map filtering entities by time.
- **Network Graph**: Force-directed graph of the entire knowledge base (Vis.js).
- **Editing**: Simple editing of Person labels (persists in-memory for session).

## Setup
The environment is already set up in the `venv` folder.

1. Activate the environment:
   ```bash
   source venv/bin/activate
   ```

2. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

3. Open **http://127.0.0.1:8000** in your browser.

## Data Flow
- **Loading**: On startup, the app loads all `.ttl` files recursively from `data/` and `ontology/`.
- **Querying**: The app uses `rdflib` and SPARQL to query the in-memory graph.
- **Architecture**: `FastAPI` (backend) -> `Jinja2` (templates) -> `Leaflet`/`Vis.js` (frontend).

## Extensibility
- **New Data**: Just drop new `.ttl` files into `data/` and restart the server.
- **Validation**: SHACL shapes in `shacl/shapes.ttl` guide data quality.
