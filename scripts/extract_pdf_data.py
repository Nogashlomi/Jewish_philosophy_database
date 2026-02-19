import os
import re
import sys
import difflib
from pathlib import Path
from pypdf import PdfReader
from rdflib import Graph, Namespace, RDF, RDFS, Literal, URIRef

# Setup Paths
PROJECT_ROOT = Path(os.getcwd())
DATA_DIR = PROJECT_ROOT / "data"
PDF_DIR = Path("/Users/nogashlomi/projects/yossi/SIEPM_mateirals_and_data")

# Namespaces
JP = Namespace("http://jewish_philosophy.org/ontology#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")

def load_historical_entities():
    """Load existing Historical Persons and Works for reconciliation"""
    print("Loading existing RDF data for reconciliation...")
    g = Graph()
    
    # Load core data files
    files = [
        DATA_DIR / "persons.ttl",
        DATA_DIR / "works.ttl",
        DATA_DIR / "person-historical.ttl",
        DATA_DIR / "work-historical.ttl" 
    ]
    
    for f in files:
        if f.exists():
            g.parse(f, format="turtle")
            
    persons = {}
    works = {}
    
    # query Persons
    for s, p, o in g.triples((None, RDF.type, JP.HistoricalPerson)):
        labels = []
        for _, _, label in g.triples((s, RDFS.label, None)):
            labels.append(str(label))
        # Also get names
        for _, _, name in g.triples((s, JP.name, None)):
            labels.append(str(name))
            
        pid = s.split("#")[-1]
        persons[pid] = labels

    # query Works
    for s, p, o in g.triples((None, RDF.type, JP.HistoricalWork)):
        titles = []
        for _, _, title in g.triples((s, JP.title, None)):
            titles.append(str(title))
        for _, _, label in g.triples((s, RDFS.label, None)):
            titles.append(str(label))
            
        wid = s.split("#")[-1]
        works[wid] = titles
        
    print(f"Loaded {len(persons)} Historical Persons and {len(works)} Historical Works.")
    return persons, works

def find_closest_match(name, entities_dict, threshold=0.85):
    """Find closest match in entities dictionary (id -> [labels])"""
    best_match = None
    best_score = 0
    
    name_lower = name.lower()
    
    for eid, labels in entities_dict.items():
        for label in labels:
            score = difflib.SequenceMatcher(None, name_lower, label.lower()).ratio()
            if score > best_score:
                best_score = score
                best_match = eid
                
    if best_score >= threshold:
        return best_match
    return None

def extract_from_pdf(pdf_path, persons_db, works_db):
    reader = PdfReader(pdf_path)
    extracted_entries = []
    
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() + "\n"
        
    # Split by lines, but try to reconstruct multi-line entries if needed
    # For now, simplistic line-by-line, assuming entries start on new lines
    lines = full_text.split('\n')
    
    current_source = "Steven Harvey Reports"
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 20: continue
        
        # Skip headers/footers roughly
        if "SIEPM" in line or line.isdigit(): continue

        # Logic from prototype
        entry = {
            "raw": line,
            "scholars": [],
            "mentioned_person_ids": [],
            "mentioned_work_ids": [],
            "title": None,
            "year": None
        }
        
        # 1. Year
        year_match = re.search(r'(\d{4})\.$', line) or re.search(r'(\d{4})', line)
        if year_match:
            entry["year"] = year_match.group(1)
            
        # 2. Historical Person (Subject)
        # Look for "NAME." at start
        subject_match = re.match(r'^([A-Z\s\-\’]+)\.', line)
        if subject_match:
            name_raw = subject_match.group(1).strip()
            if len(name_raw) > 3 and not "ISBN" in name_raw:
                # Try to match to existing DB
                matched_pid = find_closest_match(name_raw, persons_db)
                if matched_pid:
                    entry["mentioned_person_ids"].append(matched_pid)
                else:
                    # Fallback: Create ID from name if no match? 
                    # For now just use the raw name as ID/URI part logic handled later
                    pass
                
                # Remove subject from line for title processing
                line_content = line[len(subject_match.group(0)):]
        else:
            line_content = line

        # 3. Scholars
        scholar_matches = re.finditer(r'(?:ed\.|trans\.|by)\s+([A-Z][a-z]+\s+[A-Z]+)', line)
        for m in scholar_matches:
            entry["scholars"].append(m.group(1).title())
            
        # 4. Title & Mentioned Work
        # Everything before "ed." or "trans."
        title_part = re.split(r',?\s*(?:ed\.|trans\.|by)', line_content)[0]
        entry["title"] = title_part.strip().strip('.')
        
        # Check if title matches a Historical Work
        if entry["title"]:
            matched_wid = find_closest_match(entry["title"], works_db)
            if matched_wid:
                entry["mentioned_work_ids"].append(matched_wid)

        # Only add valid looking entries
        if entry["title"] and (entry["scholars"] or entry["year"]):
            extracted_entries.append(entry)
            
    return extracted_entries

def generate_ttl(entries):
    output = """@prefix jp: <http://jewish_philosophy.org/ontology#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# Sources
jp:Source_Steven_Harvey_Reports a jp:Source ;
    rdfs:label "Steven Harvey Reports" ;
    jp:title "SIEPM Reports on Jewish Philosophy" .

jp:Source_Popularization a jp:Source ;
    rdfs:label "The Popularization of Philosophy in Medieval Islam, Judaism, and Christianity" ;
    jp:title "The Popularization of Philosophy in Medieval Islam, Judaism, and Christianity" .

"""
    
    unique_scholars = set()
    
    for i, entry in enumerate(entries):
        # Create ID
        safe_title = re.sub(r'[^a-zA-Z0-9]', '_', entry["title"][:30])
        sw_id = f"SW_New_{i}_{safe_title}"
        
        entry_title = entry["title"].replace("\"", "\\\"")
        output += f"jp:{sw_id} a jp:ScholarlyWork ;\n"
        output += f'    jp:title "{entry_title}"^^xsd:string ;\n'
        if entry["year"]:
            output += f'    jp:publicationYear "{entry["year"]}"^^xsd:gYear ;\n'
            
        output += "    jp:hasSource jp:Source_Steven_Harvey_Reports ;\n"
        
        # Authors/Scholars
        for scholar in entry["scholars"]:
            s_id = f"Scholar_{scholar.replace(' ', '_')}"
            unique_scholars.add((s_id, scholar))
            output += f"    jp:hasAuthor jp:{s_id} ;\n"
            
        # Mentions Person
        for pid in entry["mentioned_person_ids"]:
            output += f"    jp:aboutPerson jp:{pid} ;\n"
            
        # Mentions Work
        for wid in entry["mentioned_work_ids"]:
            output += f"    jp:aboutWork jp:{wid} ;\n"
            
        output += "    .\n\n"
        
    # Add Scholar definitions
    for s_id, s_name in unique_scholars:
        output += f"jp:{s_id} a jp:Scholar ;\n"
        output += f'    rdfs:label "{s_name}" ;\n'
        output += f'    jp:name "{s_name}" .\n'
        
    return output

def main():
    persons_db, works_db = load_historical_entities()
    
    all_entries = []
    
    # Process all 4 PDFs
    # Assuming standard naming or just list existing
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.startswith("SIEPM") and f.endswith(".pdf")]
    pdf_files.sort()
    
    for pdf_file in pdf_files:
        path = PDF_DIR / pdf_file
        print(f"Processing {path}...")
        entries = extract_from_pdf(path, persons_db, works_db)
        print(f"  Extracted {len(entries)} entries.")
        all_entries.extend(entries)
        
    print(f"Total entries extracted: {len(all_entries)}")
    
    ttl_content = generate_ttl(all_entries)
    
    output_path = DATA_DIR / "scholarly-harvey.ttl"
    with open(output_path, "w") as f:
        f.write(ttl_content)
        
    print(f"Saved RDF data to {output_path}")

if __name__ == "__main__":
    main()
