import re

with open('data/ontology/vocabulary.ttl', 'r') as f:
    lines = f.readlines()

new_lines = []
skip_mode = False
for line in lines:
    # Entities to completely skip
    if re.match(r'^jp:(ScholarlyWork|ExternalAuthority|HistoricalReference|Scholar|Source)\b', line):
        skip_mode = True
        continue
    
    # Properties to completely skip
    if re.match(r'^jp:(aboutPerson|aboutWork|authorityLink|referenceSource|referenceTarget|referenceType|year|label|creatorName|authorName|editorName|publisher|resourceType|hasSource|hasAuthor|hasEditor|publicationYear)\b', line):
        skip_mode = True
        continue
        
    if skip_mode:
        if line.strip() == '' or line.endswith('.\n'):
            skip_mode = False
        continue

    # Rename HistoricalLanguage to Language
    line = re.sub(r'jp:HistoricalLanguage', 'jp:Language', line)
    line = re.sub(r'"Historical Language"', '"Language"', line)

    # Update hasSubject domain
    if line.startswith('    rdfs:domain jp:HistoricalWork ;'):
        if 'has subject' in ''.join(new_lines[-2:]):
            line = '    rdfs:domain [ owl:unionOf ( jp:HistoricalWork jp:HistoricalPerson ) ] ;\n'

    # Update inTimeBucket domain
    if line.startswith('    rdfs:domain [ owl:unionOf ( jp:HistoricalPerson jp:HistoricalWork jp:TimeRelation ) ] ;'):
        line = '    rdfs:domain jp:TimeRelation ;\n'
        
    new_lines.append(line)

# Add hasLanguage property
new_lines.append("""
jp:hasLanguage a owl:ObjectProperty ;
    rdfs:label "has language" ;
    rdfs:domain jp:HistoricalPerson ;
    rdfs:range jp:Language ;
    rdfs:comment "Associates a historical person with a language they spoke or wrote in." .
""")

with open('data/ontology/vocabulary.ttl', 'w') as f:
    f.writelines(new_lines)
