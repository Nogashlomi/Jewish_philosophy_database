import re

with open('app/core/queries.py', 'r') as f:
    content = f.read()

# Remove specific queries
queries_to_remove = [
    r'LIST_PERSONS_MENTIONS\s*=\s*PREFIXES\s*\+\s*"""[\s\S]*?"""',
    r'GET_PERSON_SCHOLARLY\s*=\s*PREFIXES\s*\+\s*"""[\s\S]*?"""',
    r'LIST_WORKS_MENTIONS\s*=\s*PREFIXES\s*\+\s*"""[\s\S]*?"""',
    r'GET_WORK_SCHOLARLY\s*=\s*PREFIXES\s*\+\s*"""[\s\S]*?"""',
    r'LIST_SCHOLARLY_WORKS\s*=\s*PREFIXES\s*\+\s*"""[\s\S]*?"""',
    r'LIST_SOURCES\s*=\s*PREFIXES\s*\+\s*"""[\s\S]*?"""'
]

for q in queries_to_remove:
    content = re.sub(q, '', content)

# Remove source_filter
content = content.replace('{source_filter}', '')

# Update LIST_LANGUAGES
list_lang = """LIST_LANGUAGES = PREFIXES + \"\"\"
SELECT ?uri ?label (COUNT(DISTINCT ?person) as ?total)
WHERE {{
    ?uri a jp:Language .
    OPTIONAL {{ ?uri rdfs:label ?label }}
    OPTIONAL {{
        ?person jp:hasLanguage ?uri .
        ?person a jp:HistoricalPerson .
    }}
    {search_filter}
}}
GROUP BY ?uri ?label
ORDER BY ?label
\"\"\""""
content = re.sub(r'LIST_LANGUAGES\s*=\s*PREFIXES\s*\+\s*"""[\s\S]*?"""', list_lang, content)

# Update GET_LANGUAGE_WORKS to GET_LANGUAGE_PERSONS
get_lang_persons = """GET_LANGUAGE_PERSONS = PREFIXES + \"\"\"
SELECT DISTINCT ?person ?label
WHERE {{
    ?person jp:hasLanguage ?lang .
    ?person a jp:HistoricalPerson .
    OPTIONAL {{ ?person rdfs:label ?label }}
}}
ORDER BY ?label
\"\"\""""
content = re.sub(r'GET_LANGUAGE_WORKS\s*=\s*PREFIXES\s*\+\s*"""[\s\S]*?"""', get_lang_persons, content)

# Update stats queries
content = re.sub(r'"scholarly":.*?,', '', content)
content = re.sub(r'"sources":.*?', '', content)
content = content.replace('jp:HistoricalLanguage', 'jp:Language')

# Update GET_NETWORK_NODES to remove ScholarlyWork and Source and change HistoricalLanguage
content = content.replace('jp:ScholarlyWork, ', '')
content = content.replace('jp:HistoricalLanguage', 'jp:Language')
content = content.replace('OPTIONAL {{ ?s jp:hasSource ?source }}', '')

# Update GET_NETWORK_EDGES_DIRECT to remove aboutPerson, aboutWork, mentionsPerson, mentionsWork, and change writtenInLanguage to hasLanguage
content = content.replace('        jp:aboutPerson, \n', '')
content = content.replace('        jp:aboutWork, \n', '')
content = content.replace('        jp:mentionsPerson,\n', '')
content = content.replace('        jp:mentionsWork\n', '')
content = content.replace('jp:writtenInLanguage,', 'jp:hasLanguage')

# Fix dangling commas in network edges
content = re.sub(r',\s*\)\)', '))', content)

with open('app/core/queries.py', 'w') as f:
    f.write(content)
