# SPARQL Queries for Entity Service

# Prefix definitions (often used in queries)
PREFIXES = """
PREFIX jp: <http://jewish_philosophy.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""

# --- PERSONS ---

LIST_PERSONS = PREFIXES + """
SELECT ?uri ?label (SAMPLE(?by) AS ?birthYear) (SAMPLE(?dy) AS ?deathYear)
WHERE {{
    ?uri a jp:HistoricalPerson ;
         rdfs:label ?label .
    OPTIONAL {{ ?uri jp:birthYear ?by }}
    OPTIONAL {{ ?uri jp:deathYear ?dy }}
    
    {search_filter}
}}
GROUP BY ?uri ?label
ORDER BY ?label
{pagination}
"""

LIST_PERSONS_WORKS = PREFIXES + """
SELECT ?person ?work
WHERE {{
    ?work jp:writtenBy ?person .
    
}}
"""

LIST_PERSONS_PLACES = PREFIXES + """
SELECT ?person ?placeLabel
WHERE {{
    ?person jp:hasPlaceRelation ?pr .
    ?pr jp:relatedPlace ?place .
    ?place rdfs:label ?placeLabel .
    
}}
"""

LIST_PERSONS_TIMES = PREFIXES + """
SELECT ?person ?birthYear ?deathYear
WHERE {{
    ?person jp:hasTimeRelation ?tr .
    OPTIONAL {{ ?tr jp:hasTimeData ?td . ?td jp:timeFrom ?birthYear }}
    OPTIONAL {{ ?tr jp:deathYear|jp:timeUntil ?deathYear }}
    
}}
"""



GET_PERSON_WORKS = PREFIXES + """
SELECT ?work ?title
WHERE {{
    ?work jp:writtenBy ?person ;
          jp:title ?title .
}}
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
SELECT ?rel ?type ?start ?end ?label
WHERE {
     ?person jp:hasTimeRelation ?rel .
     OPTIONAL { ?rel jp:timeType ?type }
     OPTIONAL { ?rel jp:hasTimeData ?td . ?td jp:timeFrom ?start }
     OPTIONAL { ?rel jp:hasTimeData ?td . ?td jp:timeUntil ?end }
     OPTIONAL { ?rel jp:hasTimeData ?td . ?td jp:timeLabel ?label }
}
"""

# --- WORKS ---

LIST_WORKS = PREFIXES + """
SELECT ?uri ?title ?creationYear
WHERE {{
    ?uri a jp:HistoricalWork .
    OPTIONAL {{ ?uri jp:title ?title_prop }}
    OPTIONAL {{ ?uri rdfs:label ?label_prop }}
    BIND(COALESCE(?title_prop, ?label_prop, "Unknown Title") AS ?title)
    OPTIONAL {{ ?uri jp:creationYear|jp:publicationYear|jp:year ?creationYear }}
    
    {search_filter}
}}
ORDER BY ?title
{pagination}
"""

LIST_WORKS_AUTHORS = PREFIXES + """
SELECT ?work ?authorName
WHERE {{
    ?work jp:writtenBy ?author . 
    ?author rdfs:label ?authorName .
    
}}
"""



GET_WORK_AUTHORS = PREFIXES + """
SELECT ?author ?name
WHERE {
    ?work jp:writtenBy ?author .
    ?author rdfs:label ?name .
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
        
    }}
    {search_filter}
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
    
}
ORDER BY ?type ?personLabel
"""

# --- SUBJECTS ---

LIST_SUBJECTS = PREFIXES + """
SELECT ?uri ?label (COUNT(DISTINCT ?person) as ?total)
WHERE {{
    ?uri a jp:Subject .
    OPTIONAL {{ ?uri rdfs:label ?label }}
    OPTIONAL {{
        ?person jp:hasSubject ?uri .
        ?person a jp:HistoricalPerson .
        
    }}
    {search_filter}
}}
GROUP BY ?uri ?label
ORDER BY ?label
"""

GET_SUBJECT_WORKS = PREFIXES + """
SELECT ?work ?title ?label
WHERE {{
    ?work jp:hasSubject ?subject .
    OPTIONAL {{ ?work jp:title ?title }}
    OPTIONAL {{ ?work rdfs:label ?label }}
    
}}
ORDER BY ?title
"""

# --- SOURCES ---



# --- GEOJSON ---

GET_GEO_JSON = PREFIXES + """
SELECT DISTINCT ?person ?personLabel ?placeLabel ?lat ?long ?bucketLabel ?placeType ?sourceLabel
WHERE {{
    ?person a jp:HistoricalPerson ;
            rdfs:label ?personLabel ;
            jp:hasPlaceRelation ?pr .
    {search_filter}
    
    OPTIONAL {{
        ?person jp:hasSource ?source .
        ?source rdfs:label ?sourceLabel .
    }}

    ?pr jp:relatedPlace ?place .
    OPTIONAL {{ ?pr jp:placeType ?placeType }}
    
    ?place rdfs:label ?placeLabel ;
           jp:latitude ?lat ;
           jp:longitude ?long .
           
    # Time data from TimeBucket
    OPTIONAL {{
        ?person jp:hasTimeRelation ?tr .
        ?tr jp:inTimeBucket ?bucket .
        ?bucket jp:bucketLabel ?bucketLabel .
    }}
}}
"""

GET_TRANSLATION_FLOWS = PREFIXES + """
SELECT DISTINCT ?translator ?translatorLabel ?translatorLat ?translatorLong ?author ?authorLabel ?authorLat ?authorLong
WHERE {
    ?translator jp:translated ?author .
    
    ?translator rdfs:label ?translatorLabel ;
                jp:hasPlaceRelation ?tpr .
    ?tpr jp:relatedPlace ?tp .
    ?tp jp:latitude ?translatorLat ;
        jp:longitude ?translatorLong .
        
    ?author rdfs:label ?authorLabel ;
            jp:hasPlaceRelation ?apr .
    ?apr jp:relatedPlace ?ap .
    ?ap jp:latitude ?authorLat ;
        jp:longitude ?authorLong .
}
"""

# --- LANGUAGES ---

LIST_LANGUAGES = PREFIXES + """
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
"""

GET_LANGUAGE_PERSONS = PREFIXES + """
SELECT DISTINCT ?person ?label
WHERE {{
    ?person jp:hasLanguage ?lang .
    ?person a jp:HistoricalPerson .
    OPTIONAL {{ ?person rdfs:label ?label }}
}}
ORDER BY ?label
"""

# --- SCHOLARLY WORKS ---



# --- NETWORK ---

GET_NETWORK_NODES = PREFIXES + """
SELECT ?s ?label ?type ?source
WHERE {{
    ?s a ?type .
    OPTIONAL {{ ?s rdfs:label ?label }}
    
    FILTER (?type IN (jp:HistoricalPerson, jp:HistoricalWork, jp:Place, jp:Subject, jp:Language))
    
}}
"""

GET_NETWORK_EDGES_DIRECT = PREFIXES + """
SELECT ?s ?o
WHERE {{
    ?s ?p ?o .
    FILTER (?p IN (
        jp:writtenBy, 
        jp:hasSubject, 
        jp:hasLanguage,
        jp:translated,
        jp:isTranslationOf,
        <http://schema.org/author>
    ))
    
}}
"""

GET_NETWORK_EDGES_PLACES = PREFIXES + """
SELECT ?person ?place ?place_label
WHERE {{
    ?person jp:hasPlaceRelation ?rel .
    ?rel jp:relatedPlace ?place .
    OPTIONAL {{ ?place rdfs:label ?place_label }}
    
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
    { ?uri a owl:ObjectProperty } UNION { ?uri a owl:DatatypeProperty } .
    OPTIONAL { ?uri rdfs:label ?label }
    OPTIONAL { ?uri rdfs:domain ?domain }
    OPTIONAL { ?uri rdfs:range ?range }
    OPTIONAL { ?uri rdfs:comment ?comment }
    FILTER(STRSTARTS(STR(?uri), "http://jewish_philosophy.org/ontology#"))
}
"""


GET_SOURCES = PREFIXES + """
SELECT DISTINCT ?uri ?label
WHERE {{
    ?uri a jp:Source .
    OPTIONAL {{ ?uri rdfs:label ?label }}
}}
"""

# --- STATS ---
# These are fragments used in get_global_stats
STATS_QUERIES = {
    "persons": "SELECT (COUNT(?s) as ?total) WHERE {{ ?s a jp:HistoricalPerson . {search_filter} }}",
    "works": "SELECT (COUNT(?s) as ?total) WHERE {{ ?s a jp:HistoricalWork .  }}",
    
    "places": "SELECT (COUNT(?s) as ?total) WHERE {{ ?s a jp:Place }}",
    "subjects": "SELECT (COUNT(?s) as ?total) WHERE {{ ?s a jp:Subject }}",
    "languages": "SELECT (COUNT(?s) as ?total) WHERE {{ ?s a jp:Language }}",
    "sources": "SELECT (COUNT(?s) as ?total) WHERE {{ ?s a jp:Source }}"
}

COUNT_PERSONS = PREFIXES + """
SELECT (COUNT(DISTINCT ?uri) as ?total)
WHERE {{
    ?uri a jp:HistoricalPerson .
    OPTIONAL {{ ?uri rdfs:label ?label }}
    
    {search_filter}
}}
"""

COUNT_WORKS = PREFIXES + """
SELECT (COUNT(DISTINCT ?uri) as ?total)
WHERE {{
    ?uri a jp:HistoricalWork ;
         jp:title ?title .
    
    {search_filter}
}}
"""

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
