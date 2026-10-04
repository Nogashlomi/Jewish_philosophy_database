# SPARQL Queries for Entity Service

# Prefix definitions (often used in queries)
PREFIXES = """
PREFIX jp: <http://jewish_philosophy.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""

# --- PERSONS ---

LIST_PERSONS = PREFIXES + """
SELECT ?uri (MIN(?label) AS ?name) (SAMPLE(?by) AS ?birthYear) (SAMPLE(?dy) AS ?deathYear)
WHERE {{
    ?uri a jp:HistoricalPerson ;
         rdfs:label ?label .
    OPTIONAL {{ ?uri jp:birthYear ?by }}
    OPTIONAL {{ ?uri jp:deathYear ?dy }}
    
    {source_filter}
    {search_filter}
}}
GROUP BY ?uri
ORDER BY ?name
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
SELECT ?work (SAMPLE(COALESCE(?title_prop, ?label_prop, STR(?work))) AS ?title)
WHERE {
    ?work jp:writtenBy ?person .
    OPTIONAL { ?work jp:title ?title_prop }
    OPTIONAL { ?work rdfs:label ?label_prop }
}
GROUP BY ?work
ORDER BY ?title
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
SELECT ?author (MIN(?label) AS ?name)
WHERE {
    ?work jp:writtenBy ?author .
    ?author rdfs:label ?label .
}
GROUP BY ?author
"""



# --- PLACES ---

LIST_PLACES = PREFIXES + """
SELECT ?uri (MIN(?l) AS ?label) (SAMPLE(?la) AS ?lat) (SAMPLE(?lo) AS ?long) (COUNT(DISTINCT ?person) as ?total)
WHERE {{
    ?uri a jp:Place ;
         rdfs:label ?l .
    OPTIONAL {{ ?uri jp:latitude ?la ; jp:longitude ?lo }}
    OPTIONAL {{
        ?person jp:hasPlaceRelation ?pr .
        ?pr jp:relatedPlace ?uri .
        
    }}
    {search_filter}
}}
GROUP BY ?uri
ORDER BY ?label
"""

GET_PLACE_PEOPLE = PREFIXES + """
SELECT ?person (MIN(?label) AS ?personLabel) ?type
WHERE {
    ?person jp:hasPlaceRelation ?rel .
    ?person rdfs:label ?label .
    ?rel jp:relatedPlace ?place ;
         jp:placeType ?type .
    
}
GROUP BY ?person ?type
ORDER BY ?type ?personLabel
"""

# --- SUBJECTS ---

LIST_SUBJECTS = PREFIXES + """
SELECT ?uri (MIN(?l) AS ?label) (COUNT(DISTINCT ?person) as ?total)
WHERE {{
    ?uri a jp:Subject .
    OPTIONAL {{ ?uri rdfs:label ?l }}
    OPTIONAL {{
        ?person jp:hasSubject ?uri .
        ?person a jp:HistoricalPerson .
        
    }}
    {search_filter}
}}
GROUP BY ?uri
ORDER BY ?label
"""

GET_SUBJECT_WORKS = PREFIXES + """
SELECT ?work (SAMPLE(?t) AS ?title) (MIN(?l) AS ?label)
WHERE {
    ?work jp:hasSubject ?subject ;
          a jp:HistoricalWork .
    OPTIONAL { ?work jp:title ?t }
    OPTIONAL { ?work rdfs:label ?l }
    
}
GROUP BY ?work
ORDER BY ?label
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

    ?pr jp:relatedPlace ?place .
    ?place rdfs:label ?placeLabel ;
           jp:latitude ?lat ;
           jp:longitude ?long .
    
    OPTIONAL {{ ?pr jp:placeType ?placeType }}
    
    OPTIONAL {{
        ?person jp:hasSource ?source .
        ?source rdfs:label ?sourceLabel .
    }}
           
    # Time data from TimeBucket
    OPTIONAL {{
        ?person jp:hasTimeRelation ?tr .
        ?tr jp:inTimeBucket ?bucket .
        ?bucket jp:bucketLabel ?bucketLabel .
    }}
}}
"""

# --- LANGUAGES ---

LIST_LANGUAGES = PREFIXES + """
SELECT ?uri (MIN(?l) AS ?label) (COUNT(DISTINCT ?person) as ?total)
WHERE {{
    ?uri a jp:Language .
    OPTIONAL {{ ?uri rdfs:label ?l }}
    OPTIONAL {{
        ?person jp:hasLanguage ?uri .
        ?person a jp:HistoricalPerson .
    }}
    {search_filter}
}}
GROUP BY ?uri
ORDER BY ?label
"""

GET_LANGUAGE_PERSONS = PREFIXES + """
SELECT ?person (MIN(?l) AS ?label)
WHERE {
    ?person jp:hasLanguage ?lang .
    ?person a jp:HistoricalPerson .
    OPTIONAL { ?person rdfs:label ?l }
}
GROUP BY ?person
ORDER BY ?label
"""

# --- SCHOLARLY WORKS ---



# --- NETWORK ---

GET_NETWORK_NODES = PREFIXES + """
SELECT ?s (MIN(?l) AS ?label) ?type
WHERE {{
    ?s a ?type .
    OPTIONAL {{ ?s rdfs:label ?l }}
    {search_filter}
    FILTER (?type IN (jp:HistoricalPerson, jp:HistoricalWork, jp:Place, jp:Subject, jp:Language))
    
}}
GROUP BY ?s ?type
"""

NETWORK_EDGE_PREDICATES = [
    "writtenBy",
    "hasSubject",
    "hasLanguage",
    "translated",
    "isTranslationOf",
    "translatedBy",
]

GET_NETWORK_EDGES_PLACES = PREFIXES + """
SELECT DISTINCT ?person ?place (MIN(?l) AS ?place_label)
WHERE {{
    ?person jp:hasPlaceRelation ?rel .
    ?rel jp:relatedPlace ?place .
    OPTIONAL {{ ?place rdfs:label ?l }}
    
}}
GROUP BY ?person ?place
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

# List sources with counts
LIST_SOURCES = PREFIXES + """
SELECT ?source (MIN(?l) AS ?label) (COUNT(DISTINCT ?s) AS ?total) WHERE {
    ?s jp:hasSource ?source .
    OPTIONAL { ?source rdfs:label ?l }
} GROUP BY ?source ORDER BY ?label
"""

# --- STATS ---
# These are fragments used in get_global_stats
STATS_QUERIES = {
    "persons": "SELECT (COUNT(?s) as ?total) WHERE {{ ?s a jp:HistoricalPerson . {search_filter} }}",
    "works": "SELECT (COUNT(?s) as ?total) WHERE {{ ?s a jp:HistoricalWork . {search_filter} }}",
    
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
    
    {source_filter}
    {search_filter}
}}
"""

COUNT_WORKS = PREFIXES + """
SELECT (COUNT(DISTINCT ?uri) as ?total)
WHERE {{
    ?uri a jp:HistoricalWork .
    
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
