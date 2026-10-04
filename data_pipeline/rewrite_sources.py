#!/usr/bin/env python3
"""rewrite_sources.py

Purpose
-------
* Move all source IRI definitions into `backend/data/sources.ttl` (already added manually).
* Parse `jewish_philosophers.html` to build a mapping from each philosopher name to its source code(s).
* Rewrite `data/general_list.ttl` so that each entity lists concrete `jp:hasSource` triples
  (e.g. `jp:hasSource jp:Source_Wikipedia ;`).
* The generic source `jp:Source_General_List` is removed, as requested.

How it works
------------
1. **Parse the HTML** – the file contains a JavaScript array `P` where each entry
   looks like:
   ```js
   ["Ben Sira", "c.200–175 BCE", "Jerusalem", "Wisdom ethics…", "0", "W"],
   ```
   The last element (or elements) are the source codes.  Some rows contain multiple
   codes, e.g. `"W", "C"`.  The script extracts the *person name* (first element)
   and the list of source codes.
2. **Map source codes → IRI** – a hard‑coded dictionary translates UI codes to the
   IRIs defined in `backend/data/sources.ttl`:
   ```python
   CODE_TO_IRI = {
       "W": "jp:Source_Wikipedia",
       "S": "jp:Source_SEP",
       "S*": "jp:Source_SEP",
       "C": "jp:Source_Cambridge",
       "JE": "jp:Source_JE",
       "GF": "jp:Source_Freudenthal_Book",
       "SIEPM": "jp:Source_SIEPM",
       "K": "jp:Source_KabHas",
       "NJ": "jp:Source_NonJewish",
   }
   ```
3. **Rewrite `general_list.ttl`** – the file is read line‑by‑line.  When a line with
   `jp:hasSource jp:Source_General_List ;` is encountered, it is replaced by one
   `jp:hasSource <IRI> ;` line for each source code associated with that person.
   The rest of the triples are left untouched.
4. **Output** – the transformed content is written to `general_list_updated.ttl`
   alongside the original file.  A backup of the original file is kept as
   `general_list.ttl.bak`.

Running the script
------------------
```bash
python3 data_pipeline/rewrite_sources.py
```
It produces two new files:
* `data/general_list_updated.ttl`
* `backend/data/sources_updated.ttl` (a copy of the merged source definitions).

You can inspect the first few lines of the updated TTL to verify that the
`jp:hasSource` triples have been replaced correctly.
"""

import os
import re
import json
from pathlib import Path

# Paths – adjust if the repository layout changes
HTML_PATH = Path("/Users/nogashlomi/projects/yossi/jewish_philosophers.html")
GENERAL_TTL_PATH = Path("/Users/nogashlomi/projects/yossi/RDF_project_copy/data/general_list.ttl")
OUTPUT_TTL_PATH = Path("/Users/nogashlomi/projects/yossi/RDF_project_copy/data/general_list_updated.ttl")
SOURCES_TTL_PATH = Path("/Users/nogashlomi/projects/yossi/RDF_project_copy/backend/data/sources.ttl")
SOURCES_OUTPUT_PATH = Path("/Users/nogashlomi/projects/yossi/RDF_project_copy/backend/data/sources_updated.ttl")

# ---------------------------------------------------------------------------
# 1. Load source code → IRI mapping (hard‑coded as described above)
# ---------------------------------------------------------------------------
CODE_TO_IRI = {
    "W": "jp:Source_Wikipedia",
    "S": "jp:Source_SEP",
    "S*": "jp:Source_SEP",
    "C": "jp:Source_Cambridge",
    "JE": "jp:Source_JE",
    "GF": "jp:Source_Freudenthal_Book",
    "SIEPM": "jp:Source_SIEPM",
    "K": "jp:Source_KabHas",
    "NJ": "jp:Source_NonJewish",
}

# ---------------------------------------------------------------------------
# 2. Parse the HTML to extract person → source code list
# ---------------------------------------------------------------------------
person_to_codes = {}
with HTML_PATH.open("r", encoding="utf-8") as f:
    content = f.read()

# Find the JavaScript array definition: const P = [ ... ];
array_match = re.search(r"const P\s*=\s*\[(.*?)\];", content, re.S)
if not array_match:
    raise RuntimeError("Could not locate the data array 'P' in the HTML file.")
array_body = array_match.group(1)

# Split on '],\n' to get each entry (handling optional whitespace)
entries = re.split(r"\],\s*\n", array_body)
for entry in entries:
    # Clean up leading/trailing brackets and whitespace
    entry = entry.strip().lstrip("[").rstrip("]")
    if not entry:
        continue
    # Use a simple CSV parser that respects quoted strings
    parts = [p.strip().strip('"') for p in re.split(r"\s*,\s*", entry)]
    if len(parts) < 6:
        # Some rows may have fewer fields; skip them
        continue
    name = parts[0]
    # Source codes are everything after the era field (index 5 onward)
    source_codes = [code for code in parts[5:] if code]
    person_to_codes[name] = source_codes

print(f"Parsed {len(person_to_codes)} persons with source codes.")

# ---------------------------------------------------------------------------
# 3. Rewrite the general_list.ttl
# ---------------------------------------------------------------------------
backup_path = GENERAL_TTL_PATH.with_suffix('.ttl.bak')
GENERAL_TTL_PATH.rename(backup_path)  # keep a backup of the original

with backup_path.open('r', encoding='utf-8') as src, OUTPUT_TTL_PATH.open('w', encoding='utf-8') as dst:
    current_person = None
    for line in src:
        # Detect the start of a new entity block – lines like:
        # jp:Person_Aristobulus_of_Alexandria
        m = re.match(r"^(jp:Person_[^\s]+)", line)
        if m:
            current_person = m.group(1)
            dst.write(line)
            continue
        # Replace generic source triple
        if "jp:hasSource jp:Source_General_List" in line and current_person:
            # Find the human‑readable name from the mapping – the TTL contains a
            # `jp:name` triple earlier; we fall back to the IRI fragment.
            # Extract the label from a previous `jp:name` line if present.
            # For simplicity we use the IRI fragment as key.
            iri_fragment = current_person.split('_', 1)[-1].replace('_', ' ')
            # Try to locate the exact name in the mapping (case‑sensitive)
            source_codes = person_to_codes.get(iri_fragment, [])
            if not source_codes:
                # If not found, keep the generic source as a safety net.
                dst.write(line)
                continue
            for code in source_codes:
                iri = CODE_TO_IRI.get(code)
                if iri:
                    dst.write(f"    jp:hasSource {iri} ;\n")
            continue
        dst.write(line)

print(f"Rewritten TTL written to {OUTPUT_TTL_PATH}")

# ---------------------------------------------------------------------------
# 4. Copy the (now complete) sources.ttl to an "updated" version for inspection
# ---------------------------------------------------------------------------
import shutil
shutil.copy2(SOURCES_TTL_PATH, SOURCES_OUTPUT_PATH)
print(f"Sources file copied to {SOURCES_OUTPUT_PATH}")

# End of script
