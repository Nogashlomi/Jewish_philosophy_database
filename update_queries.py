import re

with open('backend/app/core/queries.py', 'r') as f:
    c = f.read()

# Add GET_SOURCES query
get_sources_query = """
GET_SOURCES = PREFIXES + \"\"\"
SELECT DISTINCT ?uri ?label
WHERE {{
    ?uri a jp:Source .
    OPTIONAL {{ ?uri rdfs:label ?label }}
}}
\"\"\"

# --- STATS ---"""
if "GET_SOURCES" not in c:
    c = c.replace('# --- STATS ---', get_sources_query)

# Add source filtering to STATS_QUERIES for persons
# From: "persons": "SELECT (COUNT(?s) as ?total) WHERE {{ ?s a jp:HistoricalPerson .  }}",
# To:   "persons": "SELECT (COUNT(?s) as ?total) WHERE {{ ?s a jp:HistoricalPerson . {search_filter} }}",
c = re.sub(r'"persons": "SELECT \(COUNT\(\?s\) as \?total\) WHERE \{\{ \?s a jp:HistoricalPerson \.  \}\}",', '"persons": "SELECT (COUNT(?s) as ?total) WHERE {{ ?s a jp:HistoricalPerson . {search_filter} }}",', c)

# For Works, Places, etc., if we filter by source, we only apply source filter if they connect to HistoricalPerson.
# But for now, we just restore what was there. Originally STATS_QUERIES did not have {search_filter} in it.
# The user wants Data Source only for HistoricalPerson.
# COUNT_PERSONS already has {search_filter}
# LIST_PERSONS already has {search_filter}
# GET_NETWORK_NODES already has {search_filter}

with open('backend/app/core/queries.py', 'w') as f:
    f.write(c)

