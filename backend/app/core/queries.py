# SPARQL Queries for Entity Service

# Prefix definitions (often used in queries)
PREFIXES = """
PREFIX jp: <http://jewish_philosophy.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""

# --- PERSONS ---

LIST_PERSONS = PREFIXES + """
SELECT ?uri ?label
WHERE {{
    ?uri a jp:HistoricalPerson ;
         rdfs:label ?label .
    {source_filter}
}}
ORDER BY ?label
"""

LIST_PERSONS_WORKS = PREFIXES + """
SELECT ?person ?work
WHERE {{
    ?work jp:writtenBy ?person .
    {source_filter}
}}
"""

LIST_PERSONS_PLACES = PREFIXES + """
SELECT ?person ?placeLabel
WHERE {{
    ?person jp:hasPlaceRelation ?pr .
    ?pr jp:relatedPlace ?place .
    ?place rdfs:label ?placeLabel .
    {source_filter}
}}
"""

LIST_PERSONS_TIMES = PREFIXES + """
SELECT ?person ?trStart ?trEnd
WHERE {{
    ?person jp:hasTimeRelation ?tr .
    ?tr jp:timeFrom ?trStart .
    OPTIONAL {{ ?tr jp:timeUntil ?trEnd }}
    {source_filter}
}}
"""

LIST_PERSONS_MENTIONS = PREFIXES + """
SELECT ?person ?sw
WHERE {{
    ?sw jp:aboutPerson ?person .
    {source_filter}
}}
"""

GET_PERSON_WORKS = PREFIXES + """
SELECT ?work ?title
WHERE {{
    ?work jp:writtenBy ?person ;
          jp:title ?title .
}}
"""

GET_PERSON_SCHOLARLY = PREFIXES + """
SELECT ?sw ?title ?label ?year
WHERE {
    ?sw jp:aboutPerson ?person .
    OPTIONAL { ?sw jp:title ?title }
    OPTIONAL { ?sw rdfs:label ?label }
    OPTIONAL { ?sw jp:year ?year }
}
"""

GET_PERSON_PLACES = PREFIXES + """
SELECT ?rel ?place ?placeLabel ?type
WHERE {
     ?person jp:hasPlaceRelation ?rel .
     ?rel jp:relatedPlace ?place ;
          jp:placeType ?type .
     ?place rdfs:label ?placeLabel .
}
"""

GET_PERSON_TIMES = PREFIXES + """
SELECT ?rel ?birthYear ?deathYear
WHERE {
     ?person jp:hasTimeRelation ?rel .
     OPTIONAL { ?rel jp:birthYear ?birthYear }
     OPTIONAL { ?rel jp:deathYear ?deathYear }
}
"""

# --- WORKS ---

LIST_WORKS = PREFIXES + """
SELECT ?uri ?title
WHERE {
    ?uri a jp:HistoricalWork ;
         jp:title ?title .
    {source_filter}
}}
ORDER BY ?title
"""

LIST_WORKS_AUTHORS = PREFIXES + """
SELECT ?work ?authorName
WHERE {{
    ?work jp:writtenBy ?author . 
    ?author rdfs:label ?authorName .
    {source_filter}
}}
"""

LIST_WORKS_MENTIONS = PREFIXES + """
SELECT ?work ?sw
WHERE {{
    ?sw jp:aboutWork ?work .
    {source_filter}
}}
"""

GET_WORK_AUTHORS = PREFIXES + """
SELECT ?author ?name
WHERE {
    ?work jp:writtenBy ?author .
    ?author rdfs:label ?name .
}
"""

GET_WORK_SCHOLARLY = PREFIXES + """
SELECT ?sw ?title ?year
WHERE {
    ?sw jp:aboutWork ?work ;
        jp:title ?title .
    OPTIONAL { ?sw jp:year ?year }
}
"""

# --- PLACES ---

LIST_PLACES = PREFIXES + """
SELECT ?uri ?label ?lat ?long (COUNT(DISTINCT ?person) as ?total)
WHERE {{
    ?uri a jp:Place ;
         rdfs:label ?label .
    OPTIONAL {{ ?uri jp:latitude ?lat ; jp:longitude ?long }}
    OPTIONAL {{
        ?person jp:hasPlaceRelation ?pr .
        ?pr jp:relatedPlace ?uri .
        {source_filter}
    }}
}}
GROUP BY ?uri ?label ?lat ?long
ORDER BY ?label
"""

GET_PLACE_PEOPLE = PREFIXES + """
SELECT ?person ?personLabel ?type
WHERE {{
    ?person jp:hasPlaceRelation ?rel .
    ?person rdfs:label ?personLabel .
    ?rel jp:relatedPlace ?place ;
         jp:placeType ?type .
    {source_filter}
}
ORDER BY ?type ?personLabel
"""

# --- SUBJECTS ---

LIST_SUBJECTS = PREFIXES + """
SELECT ?uri ?label (COUNT(?work) as ?total)
WHERE {
    ?uri a jp:Subject .
    OPTIONAL { ?uri rdfs:label ?label }
    OPTIONAL { ?work jp:hasSubject ?uri }
}
GROUP BY ?uri ?label
ORDER BY ?label
"""

GET_SUBJECT_WORKS = PREFIXES + """
SELECT ?work ?title ?label
WHERE {{
    ?work jp:hasSubject ?subject .
    OPTIONAL {{ ?work jp:title ?title }}
    OPTIONAL {{ ?work rdfs:label ?label }}
    {source_filter}
}}
ORDER BY ?title
"""

# --- SOURCES ---

LIST_SOURCES = PREFIXES + """
SELECT ?source ?label (COUNT(DISTINCT ?work) as ?total)
WHERE {{
    ?source a jp:Source ;
            rdfs:label ?label .
    FILTER(CONTAINS(STR(?source), "Source_"))
    OPTIONAL {{
        ?work jp:hasSource ?source .
    }
}
GROUP BY ?source ?label
ORDER BY ?label
"""

# --- GEOJSON ---

GET_GEO_JSON = PREFIXES + """
SELECT ?person ?personLabel ?place ?placeLabel ?lat ?long ?start ?end ?placeType
WHERE {{
    ?person a jp:HistoricalPerson ;
            rdfs:label ?personLabel ;
            jp:hasPlaceRelation ?pr .
    
    ?pr jp:relatedPlace ?place .
    OPTIONAL {{ ?pr jp:placeType ?placeType }}
    
    ?place rdfs:label ?placeLabel ;
           jp:latitude ?lat ;
           jp:longitude ?long .
           
    # Time data from TimeRelation (Wikidata style uses jp:birthYear / jp:deathYear)
    OPTIONAL {{
        ?person jp:hasTimeRelation ?tr .
        OPTIONAL {{ ?tr jp:birthYear ?by }}
        OPTIONAL {{ ?tr jp:deathYear ?dy }}
    }}
    
    # Time data from PlaceRelation (Legacy or other source style uses jp:timeFrom / jp:timeUntil)
    OPTIONAL {{ ?pr jp:timeFrom ?tf }}
    OPTIONAL {{ ?pr jp:timeUntil ?tu }}
    
    BIND(COALESCE(?by, ?tf) AS ?start)
    BIND(COALESCE(?dy, ?tu) AS ?end)

    # Filter out entries with no dates (User request: "dont show people with no dates")
    FILTER (BOUND(?start) || BOUND(?end))
    {source_filter}
}}
"""

# --- LANGUAGES ---

LIST_LANGUAGES = PREFIXES + """
SELECT ?uri ?label (COUNT(?work) as ?total)
WHERE {
    ?uri a jp:HistoricalLanguage .
    OPTIONAL { ?uri rdfs:label ?label }
    OPTIONAL { ?work jp:writtenInLanguage ?uri }
}
GROUP BY ?uri ?label
ORDER BY ?label
"""

GET_LANGUAGE_WORKS = PREFIXES + """
SELECT ?work ?title
WHERE {{
    ?work jp:writtenInLanguage ?lang ;
          jp:title ?title .
    {source_filter}
}}
ORDER BY ?title
"""

# --- SCHOLARLY WORKS ---

LIST_SCHOLARLY_WORKS = PREFIXES + """
SELECT ?uri ?title ?label ?year ?type 
       ?authorUri ?authorName 
       ?sourceUri ?sourceLabel
       ?publisher
       ?person ?work
WHERE {{
    ?uri a jp:ScholarlyWork .
    OPTIONAL {{ ?uri jp:title ?title }}
    OPTIONAL {{ ?uri rdfs:label ?label }}
    OPTIONAL {{ ?uri jp:publicationYear ?year }}
    OPTIONAL {{ ?uri jp:resourceType ?type }}
    OPTIONAL {{ ?uri jp:publisher ?publisher }}
    
    # Source
    OPTIONAL {{ 
        ?uri jp:hasSource ?sourceUri .
        ?sourceUri rdfs:label ?sourceLabel .
    }}

    # Authors (Scholars)
    OPTIONAL {{ 
        ?uri jp:hasAuthor ?authorUri .
        ?authorUri rdfs:label ?authorName .
    }}
    
    OPTIONAL {{ ?uri jp:aboutPerson ?person }}
    OPTIONAL {{ ?uri jp:aboutWork ?work }}
    
    {source_filter}
}}
"""

# --- NETWORK ---

GET_NETWORK_NODES = PREFIXES + """
SELECT ?s ?label ?type ?source
WHERE {{
    ?s a ?type .
    OPTIONAL {{ ?s rdfs:label ?label }}
    OPTIONAL {{ ?s jp:hasSource ?source }}
    FILTER (?type IN (jp:HistoricalPerson, jp:HistoricalWork, jp:ScholarlyWork, jp:Place, jp:Subject, jp:HistoricalLanguage))
    {source_filter}
}}
"""

GET_NETWORK_EDGES_DIRECT = PREFIXES + """
SELECT ?s ?o
WHERE {{
    ?s ?p ?o .
    FILTER (?p IN (
        jp:writtenBy, 
        jp:aboutPerson, 
        jp:aboutWork, 
        jp:hasSubject, 
        jp:writtenInLanguage,
        jp:mentionsPerson,
        jp:mentionsWork
    ))
    {source_filter}
}}
"""

GET_NETWORK_EDGES_PLACES = PREFIXES + """
SELECT ?person ?place
WHERE {{
    ?person jp:hasPlaceRelation ?rel .
    ?rel jp:relatedPlace ?place .
    {source_filter}
}}
"""


# --- ONTOLOGY ---

GET_ONTOLOGY_CLASSES = PREFIXES + """
SELECT ?uri ?label ?comment
WHERE {
    ?uri a owl:Class .
    OPTIONAL { ?uri rdfs:label ?label }
    OPTIONAL { ?uri rdfs:comment ?comment }
    FILTER(STRSTARTS(STR(?uri), "http://jewish_philosophy.org/ontology#"))
}
"""

GET_ONTOLOGY_PROPERTIES = PREFIXES + """
SELECT ?uri ?label ?domain ?range ?comment
WHERE {
    ?uri a owl:ObjectProperty .
    OPTIONAL { ?uri rdfs:label ?label }
    OPTIONAL { ?uri rdfs:domain ?domain }
    OPTIONAL { ?uri rdfs:range ?range }
    OPTIONAL { ?uri rdfs:comment ?comment }
    FILTER(STRSTARTS(STR(?uri), "http://jewish_philosophy.org/ontology#"))
}
"""

# --- STATS ---
# These are fragments used in get_global_stats
STATS_QUERIES = {
    "persons": "SELECT (COUNT(?s) as ?total) WHERE {{ ?s a jp:HistoricalPerson . {source_filter} }}",
    "works": "SELECT (COUNT(?s) as ?total) WHERE {{ ?s a jp:HistoricalWork . {source_filter} }}",
    "scholarly": "SELECT (COUNT(?s) as ?total) WHERE {{ ?s a jp:ScholarlyWork . {source_filter} }}",
    "places": "SELECT (COUNT(?s) as ?total) WHERE {{ ?s a jp:Place }}",
    "subjects": "SELECT (COUNT(?s) as ?total) WHERE {{ ?s a jp:Subject }}",
    "languages": "SELECT (COUNT(?s) as ?total) WHERE {{ ?s a jp:HistoricalLanguage }}",
    "sources": "SELECT (COUNT(?s) as ?total) WHERE {{ ?s a jp:Source }}"
}

# --- AUDIT (Data usage) ---
GET_DATA_CLASSES = PREFIXES + """
SELECT DISTINCT ?type
WHERE {
    ?s a ?type .
    FILTER(STRSTARTS(STR(?type), "http://jewish_philosophy.org/ontology#"))
}
"""

GET_DATA_PROPERTIES = PREFIXES + """
SELECT DISTINCT ?p
WHERE {
    ?s ?p ?o .
    FILTER(STRSTARTS(STR(?p), "http://jewish_philosophy.org/ontology#"))
}
"""
