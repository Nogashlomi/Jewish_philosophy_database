import re
import json

sample_text = """
SOLOMON IBN GABIROL. Fons Vitae - Meqor hayyim, Edizione critica e traduzione dell’Epitome ebraica dell’opera, ed. and trans. Roberto GATTI. Genoa: il Melangolo, 2001.
ABRAHAM IBN EZRA. The Book of Reasons, A parallel Hebrew-English critical edition of the two versions of the text, ed. and trans. Shlomo SELA. Leiden: Brill Academic Publishers, 2007.
JOSEPH IBN SADDIQ. The Microcosm, trans. Jacob HABERMAN. Madison, New Jersey: Fairleigh Dickinson University Press, 2003.
MAIMONIDES. La Guida dei perplessi di Mosè Maimonide, trans. Mauro ZONTA. Turin: U.T.E.T., 2003.
SAMUEL IBN TIBBON. Glosses to Maimonides’ Guide of the Perplexed, in From Maimonides to Samuel ibn Tibbon: The Transformation of the Dalalat al-Ha‛irin into the Moreh ha-Nevukhim, ed. Carlos FRAENKEL. Jerusalem: Magnes Press, 2007.
CCM – The Cambridge Companion to Maimonides, ed. K. SEESKIN. Cambridge: Cambridge University Press, 2005.
"""

def parse_entry(line):
    # Regex to find ALL CAPS names (potential Historical Authors or Subjects) at start
    # format: NAME. Title...
    
    entry = {
        "raw": line.strip(),
        "scholars": [],
        "mentioned_persons": [],
        "title": None,
        "year": None
    }
    
    # 1. Extract Year (last 4 digits)
    year_match = re.search(r'(\d{4})\.$', line) or re.search(r'(\d{4})', line)
    if year_match:
        entry["year"] = year_match.group(1)

    # 2. Extract Historical Person (Subject) - Assumes starts with CAPS
    # Look for "NAME." at start
    subject_match = re.match(r'^([A-Z\s]+)\.', line)
    if subject_match:
        name = subject_match.group(1).strip()
        if len(name) > 3: # Avoid single letters
            entry["mentioned_persons"].append(name.title()) # Convert to Title Case
            # Remove subject from line for title extraction
            line = line[len(subject_match.group(0)):]

    # 3. Extract Scholars (Editors/Translators) - Look for "ed." or "trans." followed by Name
    # This is tricky, often names are CAPS in this text too: "Roberto GATTI"
    
    # Strategy: Look for specific keywords like "ed.", "trans." and capture following names
    # Heuristic: names often have CAPS surname in this specific text
    
    scholar_matches = re.finditer(r'(?:ed\.|trans\.|by)\s+([A-Z][a-z]+\s+[A-Z]+)', line)
    for m in scholar_matches:
        entry["scholars"].append(m.group(1).title())
        
    # Also catch "ed. K. SEESKIN"
    scholar_matches_initials = re.finditer(r'(?:ed\.|trans\.|by)\s+([A-Z]\.\s+[A-Z]+)', line)
    for m in scholar_matches_initials:
         entry["scholars"].append(m.group(1).title())

    # 4. Title
    # Assume distinct part before "ed." or "trans."
    # This is a rough heuristic
    title_part = re.split(r',?\s*(?:ed\.|trans\.|by)', line)[0]
    entry["title"] = title_part.strip().strip('.')

    return entry

results = []
for line in sample_text.strip().split('\n'):
    if line.strip():
        results.append(parse_entry(line))

print(json.dumps(results, indent=2))
