import pyshacl
from app.core.rdf_store import rdf_store

def validate_graph():
    """
    Run SHACL validation on the current in-memory graph.
    Returns: (conforms, results_graph, results_text)
    """
    conforms, v_graph, v_text = pyshacl.validate(
        rdf_store.g,
        shacl_graph="shacl/shapes.ttl",
        inference='rdfs',
        abort_on_first=False,
        allow_warnings=True,
        meta_shacl=False,
        advanced=True,
        js=False,
        debug=False
    )
    return conforms, v_text
