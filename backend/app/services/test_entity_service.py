from app.core.rdf_store import JP
from app.services.entity_service import entity_service

def test_source_filter_empty_without_source():
    assert entity_service._get_source_filter(None) == ""

def test_source_filter_uses_source_iri():
    assert entity_service._get_source_filter("Source_Zonta", "s") == f"?s jp:hasSource <{JP}Source_Zonta> ."

def test_source_filter_escapes_iri_breaking_characters():
    sf = entity_service._get_source_filter("x> . ?s ?p ?o . <y", "s")
    assert sf.count("<") == 1 and sf.count(">") == 1
    assert " " not in sf[sf.index("<"):sf.index(">")]
