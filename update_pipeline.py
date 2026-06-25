import re

with open('/Users/nogashlomi/projects/yossi/data_pipeline/process_general_list.py', 'r') as f:
    c = f.read()

# Add the source creation logic
source_logic = """
    # Create the data source
    source_uri = URIRef(JP["Source_General_List"])
    g.add((source_uri, RDF.type, JP.Source))
    g.add((source_uri, RDFS.label, Literal("General List", datatype=XSD.string)))

    for idx, row in df.iterrows():"""

c = re.sub(r'\s*for idx, row in df\.iterrows\(\):', source_logic, c)

person_logic = """
        person_uri = sanitize_uri(name)
        g.add((person_uri, RDF.type, JP.HistoricalPerson))
        g.add((person_uri, RDFS.label, Literal(name, datatype=XSD.string)))
        g.add((person_uri, JP.hasSource, source_uri))"""

c = re.sub(r'\s*person_uri = sanitize_uri\(name\)\n\s*g\.add\(\(person_uri, RDF\.type, JP\.HistoricalPerson\)\)\n\s*g\.add\(\(person_uri, RDFS\.label, Literal\(name, datatype=XSD\.string\)\)\)', person_logic, c)

with open('/Users/nogashlomi/projects/yossi/data_pipeline/process_general_list.py', 'w') as f:
    f.write(c)

