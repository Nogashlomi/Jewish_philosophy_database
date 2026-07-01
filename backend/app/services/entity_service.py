from typing import List, Optional, Dict, Any
import math
from app.core.rdf_store import rdf_store, JP, RDF, RDFS
from app.schemas.person import PersonList, PersonDetail, RelatedWork, PlaceRelation, TimeRelation
from app.schemas.work import WorkList, WorkDetail, WorkAuthor
from app.schemas.place import PlaceList, PlaceDetail, PersonAtPlace
from app.schemas.subject import SubjectList, SubjectDetail, SubjectWorkInfo
from app.schemas.language import LanguageList, LanguageDetail, LanguagePersonInfo
from app.schemas.network import NetworkData, NetworkNode, NetworkEdge
from rdflib import URIRef, Literal, BNode
from rdflib.namespace import OWL
from app.core import queries
from app.core.queries import PREFIXES

class EntityService:
    """
    Core service class responsible for fetching and transforming RDF graph data 
    into application-specific schemas (Pydantic models). It acts as the bridge 
    between the SPARQL queries in `rdf_store` and the REST API.
    """

    def list_persons(self, page: int = 1, page_size: int = 100, source: str = None, search: str = None) -> Dict[str, Any]:
        """
        Retrieves a paginated list of historical persons with optional search filtering.
        """
        offset = (page - 1) * page_size
        pagination = f"LIMIT {page_size} OFFSET {offset}"

        search_filter = ""
        if search:
            safe_search = search.replace('"', '\\"')
            search_filter = f'FILTER(CONTAINS(LCASE(?label), LCASE("{safe_search}")))'

        # Single combined query — persons + birth/death years in one pass
        q = queries.LIST_PERSONS.format(pagination=pagination, search_filter=search_filter)
        items = []
        for row in rdf_store.query(q):
            uri = str(row.uri)
            uri_ref = URIRef(uri)

            # Extra places list
            places_list = []
            for prow in rdf_store.query(queries.GET_PERSON_PLACES, initBindings={'person': uri_ref}):
                p_label = str(prow.placeLabel)
                p_type = str(prow.type).capitalize() if prow.type else "Unknown"
                places_list.append(f"{p_label} ({p_type})")

            # Extra times list
            times_list = []
            for trow in rdf_store.query(queries.GET_PERSON_TIMES, initBindings={'person': uri_ref}):
                t_label = str(trow.label) if trow.label else None
                if t_label:
                    times_list.append(t_label)
                else:
                    start = str(trow.start) if trow.start else ""
                    end = str(trow.end) if trow.end else ""
                    t_type = str(trow.type).capitalize() if trow.type else "Time"
                    if start or end:
                        time_str = start
                        if end:
                            time_str += f"-{end}"
                        times_list.append(f"{time_str} ({t_type})")
                        
            # Time buckets
            buckets = []
            for bucket_uri in rdf_store.g.objects(uri_ref, JP.inTimeBucket):
                lbl = rdf_store.g.value(bucket_uri, JP.bucketLabel)
                if lbl: buckets.append(str(lbl))

            # Subjects
            subjects = []
            for subj_uri in rdf_store.g.objects(uri_ref, JP.hasSubject):
                lbl = rdf_store.g.value(subj_uri, RDFS.label) or subj_uri.split("#")[-1]
                subjects.append(str(lbl))

            items.append(PersonList(
                id=uri.strip("/").split("/")[-1].split("#")[-1],
                uri=uri,
                label=str(row.label),
                birth_year=str(row.birthYear) if getattr(row, 'birthYear', None) else None,
                death_year=str(row.deathYear) if getattr(row, 'deathYear', None) else None,
                places=", ".join(list(set(places_list))) if places_list else None,
                times=", ".join(list(set(times_list))) if times_list else None,
                time_buckets=", ".join(list(set(buckets))) if buckets else None,
                subjects=", ".join(list(set(subjects))) if subjects else None
            ))

        # Get total count (cached after first call if no search)
        count_q = queries.COUNT_PERSONS.format(search_filter=search_filter)
        total = 0
        for row in rdf_store.query(count_q):
            total = int(row.total)

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if page_size else 1,
        }

    def get_person_detail(self, person_id: str) -> Optional[PersonDetail]:
        # Try finding the person with the ontology namespace first
        uri = URIRef(f"{JP}{person_id}")
        
        # If not found (no label), try the ID namespace
        if not rdf_store.g.value(uri, RDFS.label):
            uri = URIRef(f"http://jewish_philosophy.org/id/{person_id}")
            
        # 1. Basic Info
        label = rdf_store.g.value(uri, RDFS.label)
        if not label:
            return None

        # 2. Authority Links
        authorities = [str(obj) for obj in rdf_store.g.objects(uri, JP.authorityLink)]
        
        # 3. Authored Works
        authored_works = []
        for row in rdf_store.query(queries.GET_PERSON_WORKS, initBindings={'person': uri}):
            authored_works.append(RelatedWork(
                uri=str(row.work),
                id=row.work.split("#")[-1],
                title=str(row.title)
            ))
            
        # 5. Place Relations
        places_map = {}
        for row in rdf_store.query(queries.GET_PERSON_PLACES, initBindings={'person': uri}):
            p_id = row.place.split("#")[-1]
            p_type = str(row.type).lower() if row.type else ""
            key = f"{p_id}_{p_type}"
            if key not in places_map:
                places_map[key] = PlaceRelation(
                    place_uri=str(row.place),
                    place_id=p_id,
                    label=str(row.placeLabel),
                    type=str(row.type) if row.type else None
                )
        places = list(places_map.values())

        # 6. Time Relations
        times_map = {}
        for row in rdf_store.query(queries.GET_PERSON_TIMES, initBindings={'person': uri}):
            start = str(row.start) if row.start else None
            end = str(row.end) if row.end else None
            rel_type = str(row.type) if row.type else "Life"
            label_val = str(row.label) if row.label else None
            if start or end or label_val:
                key = f"{rel_type.lower()}_{start}_{end}_{label_val}"
                if key not in times_map:
                    times_map[key] = TimeRelation(
                        type=rel_type,
                        start=start,
                        end=end,
                        label=label_val
                    )
        times = list(times_map.values())

        # Time Buckets
        time_buckets = []
        for bucket_uri in rdf_store.g.objects(uri, JP.inTimeBucket):
            b_lbl = rdf_store.g.value(bucket_uri, JP.bucketLabel)
            if b_lbl:
                time_buckets.append(str(b_lbl))

        # 7. Subjects & Languages
        subjects = []
        for subj_uri in rdf_store.g.objects(uri, JP.hasSubject):
            lbl = rdf_store.g.value(subj_uri, RDFS.label) or subj_uri.split("#")[-1]
            subjects.append(str(lbl))

        languages = []
        for lang_uri in rdf_store.g.objects(uri, JP.writtenInLanguage):
            lbl = rdf_store.g.value(lang_uri, RDFS.label) or lang_uri.split("#")[-1]
            languages.append(str(lbl))

        # 8. Source Attribution
        sources = []
        for source_uri in rdf_store.g.objects(uri, JP.hasSource):
            source_label = rdf_store.g.value(source_uri, RDFS.label)
            sources.append(str(source_label) if source_label else str(source_uri).split("#")[-1])

        return PersonDetail(
            id=person_id,
            uri=str(uri),
            label=str(label),
            works=authored_works,
            places=places,
            times=times,
            time_buckets=time_buckets,
            subjects=subjects,
            languages=languages
        )


    def list_works(self, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        offset = (page - 1) * page_size
        pagination = f"LIMIT {page_size} OFFSET {offset}"

        q = queries.LIST_WORKS.format(pagination=pagination, search_filter="")
        items = []
        for row in rdf_store.query(q):
            uri = str(row.uri)
            uri_ref = URIRef(uri)
            
            creation_year = str(row.creationYear) if getattr(row, 'creationYear', None) else None
            
            # Fetch Authors
            authors = []
            for arow in rdf_store.query(queries.GET_WORK_AUTHORS, initBindings={'work': uri_ref}):
                authors.append(str(arow.name))
                
            # Fetch Subjects
            subjects = []
            for subj_uri in rdf_store.g.objects(uri_ref, JP.hasSubject):
                lbl = rdf_store.g.value(subj_uri, RDFS.label) or subj_uri.split("#")[-1]
                subjects.append(str(lbl))
                
            # Fetch Languages
            languages = []
            for lang_uri in rdf_store.g.objects(uri_ref, JP.writtenInLanguage):
                lbl = rdf_store.g.value(lang_uri, RDFS.label) or lang_uri.split("#")[-1]
                languages.append(str(lbl))

            items.append(WorkList(
                id=uri.strip("/").split("/")[-1].split("#")[-1],
                uri=uri,
                title=str(row.title),
                creation_year=creation_year,
                authors=", ".join(authors) if authors else None,
                subjects=", ".join(subjects) if subjects else None,
                languages=", ".join(languages) if languages else None
            ))

        # Get total count (cached after first call)
        count_q = queries.COUNT_WORKS.format(search_filter="")
        total = 0
        for row in rdf_store.query(count_q):
            total = int(row.total)

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if page_size else 1,
        }

    def get_work_detail(self, work_id: str) -> Optional[WorkDetail]:
        uri = URIRef(f"{JP}{work_id}")
        
        # 1. Basic Info
        title = rdf_store.g.value(uri, JP.title)
        if not title:
            return None
            
        # 2. Authors
        authors = []
        for row in rdf_store.query(queries.GET_WORK_AUTHORS, initBindings={'work': uri}):
            authors.append(WorkAuthor(
                id=row.author.split("#")[-1],
                uri=str(row.author),
                label=str(row.name)
            ))

        # 3. Subjects
        subjects = []
        for subj_uri in rdf_store.g.objects(uri, JP.hasSubject):
            label = rdf_store.g.value(subj_uri, RDFS.label) or subj_uri.split("#")[-1]
            subjects.append(str(label))

        # 4. Languages
        languages = []
        for lang_uri in rdf_store.g.objects(uri, JP.writtenInLanguage):
            label = rdf_store.g.value(lang_uri, RDFS.label) or lang_uri.split("#")[-1]
            languages.append(str(label))

        # 7. Places
        places_map = {}
        for row in rdf_store.query(queries.GET_PERSON_PLACES, initBindings={'person': uri}):
            p_id = row.place.split("#")[-1]
            p_type = str(row.type).lower() if row.type else ""
            key = f"{p_id}_{p_type}"
            if key not in places_map:
                places_map[key] = PlaceRelation(
                    place_uri=str(row.place),
                    place_id=p_id,
                    label=str(row.placeLabel),
                    type=str(row.type) if row.type else None
                )
        places = list(places_map.values())

        # 8. Times
        times_map = {}
        for row in rdf_store.query(queries.GET_PERSON_TIMES, initBindings={'person': uri}):
            start = str(row.start) if row.start else None
            end = str(row.end) if row.end else None
            rel_type = str(row.type) if row.type else "Time"
            if start or end:
                key = f"{rel_type.lower()}_{start}_{end}"
                if key not in times_map:
                    times_map[key] = TimeRelation(
                        type=rel_type,
                        start=start,
                        end=end
                    )
        times = list(times_map.values())

        return WorkDetail(
            id=work_id,
            uri=str(uri),
            title=str(title),
            authors=authors,
            subjects=subjects,
            languages=languages,
            places=places,
            times=times
        )

    
    def list_places(self) -> List[PlaceList]:
        # For places, we filter by the people/works associated with the place in the source?
        # Or does the place itself have a source?
        # The query LIST_PLACES joins with optional person.
        # If we filter by source, we likely mean "show me places connected to people from this source"
        # Or "places that have source X" (unlikely for Places themselves often).
        # Let's assume we filter the related PERSONS by source, and count those.
        
        # BUT, the query structure for LIST_PLACES has an OPTIONAL block for persons.
        # If I inject source_filter into that optional block, it will filter the persons.
        # `queries.LIST_PLACES` has `{source_filter}` inside the OPTIONAL block for person relations.
        
        q = queries.LIST_PLACES.format(search_filter="")
        
        results = []
        for row in rdf_store.query(q):
            results.append(PlaceList(
                id=row.uri.split("#")[-1],
                uri=str(row.uri),
                label=str(row.label),
                lat=str(row.lat) if row.lat else None,
                long=str(row.long) if row.long else None,
                personCount=int(row.total)
            ))
        return results

    def get_place_detail(self, place_id: str) -> Optional[PlaceDetail]:
        uri = URIRef(f"{JP}{place_id}")
        
        # 1. Basic Info
        label = rdf_store.g.value(uri, RDFS.label)
        if not label:
            return None
            
        lat = rdf_store.g.value(uri, JP.latitude)
        long = rdf_store.g.value(uri, JP.longitude)
        
        # 2. People
        # Note: No source filtering on detail page for now unless requested.
        # The user said "filter by source in each entity page", implying list view.
        # But if they meant detail view too... complex. Sticking to list for now.
        
        people = []
        for row in rdf_store.query(queries.GET_PLACE_PEOPLE.format(), initBindings={'place': uri}):
            people.append(PersonAtPlace(
                id=row.person.split("#")[-1],
                uri=str(row.person),
                label=str(row.personLabel),
                type=str(row.type) if row.type else None
            ))
            
        return PlaceDetail(
            id=place_id,
            uri=str(uri),
            label=str(label),
            lat=str(lat) if lat else None,
            long=str(long) if long else None,
            people=people
        )

    # --- SUBJECTS ---

    def list_subjects(self) -> List[SubjectList]:
        q = queries.LIST_SUBJECTS.format(search_filter="")

        results = []
        for row in rdf_store.query(q):
             results.append(SubjectList(
                id=row.uri.split("#")[-1],
                label=str(row.label),
                count=int(row.total)
            ))
        return results

    def get_subject_detail(self, subject_id: str) -> Optional[SubjectDetail]:
        uri = URIRef(f"{JP}{subject_id}")
        
        # 1. Basic Info
        label = rdf_store.g.value(uri, RDFS.label)
        if not label:
            return None
        
        description = rdf_store.g.value(uri, JP.subjectDescription)
        
        # 2. Works
        works = []
        # GET_SUBJECT_WORKS likely has source_filter placeholder
        
        # Using format just in case
        q = queries.GET_SUBJECT_WORKS.format()
            
        for row in rdf_store.query(q, initBindings={'subject': uri}):
            t = str(row.title) if row.title else (str(row.label) if row.label else str(row.work).split("#")[-1])
            works.append(SubjectWorkInfo(
                id=row.work.split("#")[-1],
                uri=str(row.work),
                title=t
            ))
            
        return SubjectDetail(
            id=subject_id,
            uri=str(uri),
            label=str(label),
            description=str(description) if description else None,
            works=works
        )

    # --- SOURCES ---

    def list_sources(self) -> List[dict]:
        """List all sources with counts."""
        q = queries.LIST_SOURCES
        results = []
        for row in rdf_store.query(q):
            source_id = row.source.split("#")[-1]
            count_val = int(row.total)
            results.append({
                "id": source_id,
                "label": str(row.label),
                "description": f"Data source containing {count_val} entities",
                "count": count_val
            })
        
        return results


    # --- Languages ---
    def list_languages(self) -> List[LanguageList]:
        q = queries.LIST_LANGUAGES.format(search_filter="")
        results = []
        for row in rdf_store.query(q):
            label = str(row.label) if row.label else str(row.uri).split("#")[-1]
            results.append(LanguageList(
                id=row.uri.split("#")[-1],
                label=label,
                count=int(row.total)
            ))
        return results

    def get_language_detail(self, lang_id: str) -> Optional[LanguageDetail]:
        uri = URIRef(f"{JP}{lang_id}")
        
        label = rdf_store.g.value(uri, RDFS.label)
        if not label:
            label = lang_id
            
        persons = []
        q = queries.GET_LANGUAGE_PERSONS.format()
        for row in rdf_store.query(q, initBindings={'lang': uri}):
            p_name = str(row.label) if row.label else str(row.person).split("#")[-1]
            persons.append(LanguagePersonInfo(
                id=row.person.split("#")[-1],
                name=p_name
            ))

        return LanguageDetail(
            label=str(label),
            persons=persons
        )

    # --- Scholarly Works ---
    # --- Network ---
    def get_network_data(self, source: str = None) -> NetworkData:
        nodes = []
        edges = []

        def mk_id(uri): return uri.strip("/").split("/")[-1].split("#")[-1]
        
        person_buckets = {}
        q_all_buckets = "SELECT ?person ?b_lbl WHERE { ?person jp:hasTimeRelation ?tr . ?tr jp:inTimeBucket ?b . ?b jp:bucketLabel ?b_lbl }"
        for row in rdf_store.query(queries.PREFIXES + q_all_buckets):
            pid = mk_id(row.person)
            blbl = str(row.b_lbl)
            if pid not in person_buckets:
                person_buckets[pid] = []
            person_buckets[pid].append(blbl)

        # 1. Nodes - Get source-filtered entities (persons, works, etc.)
        sf_nodes = self._get_source_filter(source, "s")
        q_nodes = queries.GET_NETWORK_NODES.format(search_filter=sf_nodes)

        node_ids = set()
        node_types = {}

        for row in rdf_store.query(q_nodes):
            nid = mk_id(row.s)
            etype = mk_id(row.type)
            label = row.label or nid
            # Fix potential source error: check if attribute exists on row
            source_id = None
            if hasattr(row, 'source') and row.source:
                source_id = mk_id(row.source)

            nodes.append(NetworkNode(
                id=nid,
                label=str(label),
                group=etype,
                buckets=person_buckets.get(nid, []) if etype == 'HistoricalPerson' else []
            ))
            node_ids.add(nid)
            node_types[nid] = etype

        # Dictionary to map Person ID -> set of connected non-person entity IDs
        person_connections = {}

        # 2. Edges
        sf_edges = "" # No source filter on edges query for now, relies on node filtering
        q_direct = queries.GET_NETWORK_EDGES_DIRECT.format()

        for row in rdf_store.query(q_direct):
            s_id = mk_id(row.s)
            o_id = mk_id(row.o)
            p_id = mk_id(row.p)
            if s_id in node_ids and o_id in node_ids:
                edges.append({"from": s_id, "to": o_id, "relation": p_id})
                
                # Track for cross connections
                if node_types.get(s_id) == 'HistoricalPerson':
                    if s_id not in person_connections:
                        person_connections[s_id] = set()
                    person_connections[s_id].add(o_id)
                elif node_types.get(o_id) == 'HistoricalPerson':
                    if o_id not in person_connections:
                        person_connections[o_id] = set()
                    person_connections[o_id].add(s_id)

        q_places = queries.GET_NETWORK_EDGES_PLACES.format()
        for row in rdf_store.query(q_places):
            p_id = mk_id(row.person)
            pl_id = mk_id(row.place)
            if p_id in node_ids:
                # Add place node if person is in filtered nodes, even if place isn't
                if pl_id not in node_ids:
                    try:
                        label = str(row.place_label) if row.place_label else pl_id
                    except:
                        label = pl_id
                    nodes.append(NetworkNode(
                        id=pl_id,
                        label=label,
                        group="Place",
                        
                    ))
                    node_ids.add(pl_id)
                    node_types[pl_id] = "Place"
                    
                edges.append({"from": p_id, "to": pl_id})
                
                # Track for cross connections
                if p_id not in person_connections:
                    person_connections[p_id] = set()
                person_connections[p_id].add(pl_id)

        # 3. Generate implicit cross-connections (e.g. Place <-> Subject via Person)
        existing_edges = set()
        for edge in edges:
            t = tuple(sorted([edge['from'], edge['to']]))
            existing_edges.add(t)

        for p_id, connected_entities in person_connections.items():
            ent_list = list(connected_entities)
            for i in range(len(ent_list)):
                for j in range(i + 1, len(ent_list)):
                    e1 = ent_list[i]
                    e2 = ent_list[j]
                    # Only cross-connect if neither is a Person just to be safe
                    if node_types.get(e1) != 'HistoricalPerson' and node_types.get(e2) != 'HistoricalPerson':
                        t = tuple(sorted([e1, e2]))
                        if t not in existing_edges:
                            edges.append({"from": e1, "to": e2, "dashes": True})
                            existing_edges.add(t)



        return NetworkData(nodes=nodes, edges=edges)


    # --- Stats ---

    def _get_source_filter(self, source: str, var_name: str = "uri") -> str:
        if not source:
            return ""
        return f"?{var_name} jp:hasSource <{JP}{source}> ."

    def get_sources(self) -> List[dict]:
        results = []
        for row in rdf_store.query(queries.GET_SOURCES):
            results.append({
                "id": str(row.uri).split("#")[-1],
                "label": str(row.label) if row.label else str(row.uri).split("#")[-1]
            })
        results.sort(key=lambda x: x["label"])
        return results

    def get_global_stats(self, source: str = None) -> Dict[str, int]:
        stats_queries = queries.STATS_QUERIES
        PREFIXES = queries.PREFIXES
        
        
        stats = {}
        sf = self._get_source_filter(source, "s")
        for key, q in stats_queries.items():
            # Format the query with source_filter if applicable
            if "{search_filter}" in q:
                formatted_q = q.format(search_filter=sf)
            else:
                # If there are braces in q that aren't variables, format() will fail, so just don't format if not needed.
                formatted_q = q
            full_q = PREFIXES + formatted_q
            
            for row in rdf_store.query(full_q):
                stats[key] = int(row.total)
                
        return stats


    def get_geo_json(self, source: str = None) -> Dict[str, Any]:
        """
        Return GeoJSON FeatureCollection for places associated with historical persons.
        """
        sf = self._get_source_filter(source, "person")
        q = queries.GET_GEO_JSON.format(search_filter=sf)
        
        features = []
        for row in rdf_store.query(q):
            try:
                lat = float(row.lat)
                long = float(row.long)
                
                # Time handling
                bucket_label = str(row.bucketLabel) if getattr(row, 'bucketLabel', None) else None
                
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [long, lat]
                    },
                    "properties": {
                        "person_id": row.person.split("#")[-1],
                        "person_label": str(row.personLabel),
                        "place_label": str(row.placeLabel),
                        "type": str(row.placeType) if getattr(row, 'placeType', None) else "Unknown",
                        "bucket": bucket_label,
                        "source": str(row.sourceLabel) if getattr(row, 'sourceLabel', None) else "Unknown"
                    }
                })
            except (ValueError, TypeError):
                continue

        return {
            "type": "FeatureCollection",
            "features": features
        }

    def get_translation_flows(self) -> List[Dict[str, Any]]:
        """
        Return a list of translation flows between places for map visualization.
        """
        q = queries.GET_TRANSLATION_FLOWS
        flows = []
        for row in rdf_store.query(q):
            try:
                t_lat = float(row.translatorLat)
                t_long = float(row.translatorLong)
                a_lat = float(row.authorLat)
                a_long = float(row.authorLong)
                
                flows.append({
                    "translator_id": row.translator.split("#")[-1],
                    "translator_label": str(row.translatorLabel),
                    "author_id": row.author.split("#")[-1],
                    "author_label": str(row.authorLabel),
                    "path": [[t_lat, t_long], [a_lat, a_long]]
                })
            except (ValueError, TypeError):
                continue
        return flows


    def get_ontology_graph(self) -> Dict[str, Any]:
        """
        Return nodes (Classes) and edges (Properties) for ontology visualization.
        """
        nodes = []
        edges = []
        
        # 1. Classes -> Nodes
        classes = set()
        for row in rdf_store.query(queries.GET_ONTOLOGY_CLASSES):
            uri = str(row.uri)
            label = str(row.label) if row.label else uri.split("#")[-1]
            nodes.append({
                "id": uri,
                "label": label,
                "title": str(row.comment) if row.comment else None,
                "group": "Class"
            })
            classes.add(uri)
            
        # 2. Properties -> Edges

        def get_class_uris(node):
            if isinstance(node, URIRef):
                return [str(node)]
            elif isinstance(node, BNode):
                # Try to resolve owl:unionOf
                union_list = rdf_store.g.value(node, OWL.unionOf)
                if not union_list:
                    return []
                # Traverse the RDF list
                uris = []
                current = union_list
                while current and current != RDF.nil:
                    first = rdf_store.g.value(current, RDF.first)
                    if isinstance(first, URIRef):
                        uris.append(str(first))
                    current = rdf_store.g.value(current, RDF.rest)
                return uris
            return []

        for row in rdf_store.query(queries.GET_ONTOLOGY_PROPERTIES):
            if row.domain and row.range:
                domains = get_class_uris(row.domain)
                ranges = get_class_uris(row.range)
                
                label = str(row.label) if row.label else str(row.uri).split("#")[-1]
                
                for d in domains:
                    for r in ranges:
                        if d in classes and r in classes:
                            edges.append({
                                "from": d,
                                "to": r,
                                "label": label,
                                "arrows": "to",
                                "font": {"align": "middle"}
                            })
                    
        return {"nodes": nodes, "edges": edges}

    def get_ontology_audit(self) -> Dict[str, Any]:
        """
        Compare defined ontology (vocabulary.ttl) with actual data.
        """
        # 1. Get defined classes/properties from ontology
        defined_classes = set()
        for row in rdf_store.query(queries.GET_ONTOLOGY_CLASSES):
            defined_classes.add(str(row.uri))
            
        defined_properties = set()
        for row in rdf_store.query(queries.GET_ONTOLOGY_PROPERTIES):
            defined_properties.add(str(row.uri))
            
        # 2. Get actual classes/properties used in data
        actual_classes = set()
        for row in rdf_store.query(queries.GET_DATA_CLASSES):
            actual_classes.add(str(row.type))
            
        actual_properties = set()
        for row in rdf_store.query(queries.GET_DATA_PROPERTIES):
            actual_properties.add(str(row.p))
            
        return {
            "classes": {
                "defined_count": len(defined_classes),
                "actual_count": len(actual_classes),
                "unused": list(defined_classes - actual_classes),
                "undefined": list(actual_classes - defined_classes)
            },
            "properties": {
                "defined_count": len(defined_properties),
                "actual_count": len(actual_properties),
                "unused": list(defined_properties - actual_properties),
                "undefined": list(actual_properties - defined_properties)
            }
        }


entity_service = EntityService()
