
import pandas as pd
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS
import glob
import os
import sys

# --- Configuration ---
INPUT_FILE = "Niran_data.xlsx" 
SCHOLARLY_WORK_TITLE = "The Popularization of Philosophy in Medieval Islam, Judaism, and Christianity"
SCHOLARLY_WORK_EDITOR = "Marieke Abram et al."
SCHOLARLY_WORK_PUBLISHER = "Brepols Publishers"
SCHOLARLY_WORK_YEAR = "2022"

JP = Namespace("http://jewish_philosophy.org/ontology#")
SCHOLARLY_URI = URIRef("http://jewish_philosophy.org/scholarly/SW_Abram_2022")

def main():
    print(f"Starting import from {INPUT_FILE}...")
    
    # 1. Load Existing Data for Duplicate Checks
    print("Loading existing RDF data...")
    g_existing = Graph()
    for file in glob.glob("data/*.ttl"):
        try:
            g_existing.parse(file, format="turtle")
        except Exception as e:
            print(f"Warning: Could not parse {file}: {e}")
    
    print(f"Loaded {len(g_existing)} existing triples.")
    
    # Extract existing labels to URIs mapping
    existing_people = {}
    for s, p, o in g_existing.triples((None, RDF.type, JP.HistoricalPerson)):
        labels = list(g_existing.objects(s, RDFS.label))
        if labels:
            label = str(labels[0]).lower().strip()
            existing_people[label] = s

    print(f"Found {len(existing_people)} existing people involved in duplicates check.")

    # 2. Setup New Graph
    g_new = Graph()
    g_new.bind("jp", JP)
    g_new.bind("rdfs", RDFS)

    # 3. Create the Scholarly Work Entity
    g_new.add((SCHOLARLY_URI, RDF.type, JP.ScholarlyWork))
    g_new.add((SCHOLARLY_URI, RDFS.label, Literal(SCHOLARLY_WORK_TITLE)))
    g_new.add((SCHOLARLY_URI, JP.creatorName, Literal(SCHOLARLY_WORK_EDITOR))) # Using creatorName for editor/author
    g_new.add((SCHOLARLY_URI, JP.year, Literal(SCHOLARLY_WORK_YEAR)))
    # If we had a publisher property we would add it, but using label/creatorName/year for now based on ontology

    # 4. Read Input Data
    try:
        df = pd.read_excel(INPUT_FILE)
        print("Columns found:", df.columns.tolist())
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # iterate
    for index, row in df.iterrows():
        # Heuristic to find relevant columns if names vary
        # We look for the first column as Author and others as Works, or by name
        
        # specific logic for this file if we knew the columns, but let's try to be smart or generic
        # Assuming column 0 is Author Name
        author_name = str(row.iloc[0]).strip()
        
        if not author_name or author_name.lower() == 'nan':
            continue

        # -- Author --
        author_uri = None
        # Check duplicate
        if author_name.lower() in existing_people:
            author_uri = existing_people[author_name.lower()]
            print(f"Matched existing person: {author_name} -> {author_uri}")
        else:
            # Create new
            safe_name = author_name.replace(" ", "_").replace("'", "").replace('"', "")
            author_uri = URIRef(f"http://jewish_philosophy.org/id/{safe_name}")
            g_new.add((author_uri, RDF.type, JP.HistoricalPerson))
            g_new.add((author_uri, RDFS.label, Literal(author_name)))
            existing_people[author_name.lower()] = author_uri # Update local cache check

        # Link Scholarly Work -> Author
        g_new.add((SCHOLARLY_URI, JP.aboutPerson, author_uri))

        # -- Works --
        # Assuming other columns might contain works, or a column named 'Work'
        # Let's check for 'Work' or 'Title' columns, or just iterate rest
        
        work_candidates = []
        if 'Work' in df.columns:
             work_candidates.append(str(row['Work']))
        elif 'Title' in df.columns:
             work_candidates.append(str(row['Title']))
        else:
            # If no obvious column, assume column 1 is work
            if len(row) > 1:
                work_candidates.append(str(row.iloc[1]))

        for work_name in work_candidates:
            work_name = work_name.strip()
            if work_name and work_name.lower() != 'nan':
                # Create Work
                safe_work = work_name.replace(" ", "_").replace("'", "").replace('"', "")[:50] 
                work_uri = URIRef(f"http://jewish_philosophy.org/work/{safe_work}")
                
                g_new.add((work_uri, RDF.type, JP.HistoricalWork))
                g_new.add((work_uri, RDFS.label, Literal(work_name)))
                g_new.add((work_uri, JP.writtenBy, author_uri))
                
                # Link Scholarly Work -> Historical Work
                g_new.add((SCHOLARLY_URI, JP.aboutWork, work_uri))

    # 5. Save
    output_path = "data/imported_scholarly_data.ttl"
    g_new.serialize(destination=output_path, format="turtle")
    print(f"Success! Imported data saved to {output_path}")
    print(f"Triples added: {len(g_new)}")

if __name__ == "__main__":
    main()
