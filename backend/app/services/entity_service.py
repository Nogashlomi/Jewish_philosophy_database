from typing import List, Optional, Dict, Any
import math
from app.core.rdf_store import rdf_store, JP, RDF, RDFS
from app.schemas.person import PersonList, PersonDetail, RelatedWork, ScholarlyMention, PlaceRelation, TimeRelation
from app.schemas.work import WorkList, WorkDetail, WorkAuthor, ScholarlyWorkRef
from app.schemas.place import PlaceList, PlaceDetail, PersonAtPlace
from app.schemas.subject import SubjectList, SubjectDetail, SubjectWorkInfo
from app.schemas.language import LanguageList, LanguageDetail, LanguageWorkInfo
from app.schemas.scholarly import ScholarlyList, ScholarlyDetail, MentionedPerson, MentionedWork, Scholar, Source as ScholarlySource
from app.schemas.network import NetworkData, NetworkNode, NetworkEdge
from app.schemas.source import Source
from rdflib import URIRef, Literal, BNode
from app.core import queries
from app.core.queries import PREFIXES

class EntityService:
    def _get_source_filter(self, source_id: Optional[str], var_name: str = "uri") -> str:
        if not source_id:
            return ""
        # Assuming source_id is just the ID (e.g. "Source_Wikidata")
        # We need the full URI: <http://jewish_philosophy.org/ontology#Source_Wikidata>
        return f"?{var_name} jp:hasSource <{JP}{source_id}> ."

    def list_persons(self, source: Optional[str] = None, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        sf = self._get_source_filter(source, "uri")
        offset = (page - 1) * page_size
        pagination = f"LIMIT {page_size} OFFSET {offset}"

        # Single combined query — persons + birth/death years in one pass
        q = queries.LIST_PERSONS.format(source_filter=sf, pagination=pagination)
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
                start = str(trow.start) if trow.start else ""
                end = str(trow.end) if trow.end else ""
                t_type = str(trow.type).capitalize() if trow.type else "Time"
                if start or end:
                    time_str = start
                    if end:
                        time_str += f"-{end}"
                    times_list.append(f"{time_str} ({t_type})")

            items.append(PersonList(
                id=uri.strip("/").split("/")[-1].split("#")[-1],
                uri=uri,
                label=str(row.label),
                birth_year=str(row.birthYear) if getattr(row, 'birthYear', None) else None,
                death_year=str(row.deathYear) if getattr(row, 'deathYear', None) else None,
                places=", ".join(list(set(places_list))) if places_list else None,
                times=", ".join(list(set(times_list))) if times_list else None
            ))

        # Get total count (cached after first call)
        count_q = queries.COUNT_PERSONS.format(source_filter=sf)
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
            
        # 4. Scholarly Works about this person
        scholarly_mentions = []
        for row in rdf_store.query(queries.GET_PERSON_SCHOLARLY, initBindings={'person': uri}):
            title = str(row.title) if row.title else str(row.label) if row.label else row.sw.split("#")[-1]
            scholarly_mentions.append(ScholarlyMention(
                uri=str(row.sw),
                id=row.sw.split("#")[-1],
                title=title,
                year=str(row.year) if row.year else None
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
            if start or end:
                key = f"{rel_type.lower()}_{start}_{end}"
                if key not in times_map:
                    times_map[key] = TimeRelation(
                        type=rel_type,
                        start=start,
                        end=end
                    )
        times = list(times_map.values())

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
            sources=sources,
            authorities=authorities,
            works=authored_works,
            scholarly=scholarly_mentions,
            places=places,
            times=times,
            subjects=subjects,
            languages=languages
        )


    def list_works(self, source: Optional[str] = None, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        sf = self._get_source_filter(source, "uri")
        offset = (page - 1) * page_size
        pagination = f"LIMIT {page_size} OFFSET {offset}"

        q = queries.LIST_WORKS.format(source_filter=sf, pagination=pagination)
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
        count_q = queries.COUNT_WORKS.format(source_filter=sf)
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

        # 5. Scholarly Mentions
        scholarly_mentions = []
        for row in rdf_store.query(queries.GET_WORK_SCHOLARLY, initBindings={'work': uri}):
            scholarly_mentions.append(ScholarlyWorkRef(
                id=row.sw.split("#")[-1],
                uri=str(row.sw),
                title=str(row.title),
                year=str(row.year) if row.year else None
            ))

        # 6. Source Attribution
        sources = []
        for source_uri in rdf_store.g.objects(uri, JP.hasSource):
            source_label = rdf_store.g.value(source_uri, RDFS.label)
            sources.append(str(source_label) if source_label else str(source_uri).split("#")[-1])

        # 7. Places
        places_map = {}
        for row in rdf_store.query(queries.GET_PERSON_PLACES, initBindings={'person': uri}):
            p_id = row.place.split("#")[-1]
            p_type = str(row.type).lower() if row.type else ""
            key = f"{p_id}_{p_type}"
            if key not in places_map:
                from app.schemas.person import PlaceRelation
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
                    from app.schemas.person import TimeRelation
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
            sources=sources,
            authors=authors,
            subjects=subjects,
            languages=languages,
            scholarly_mentions=scholarly_mentions,
            places=places,
            times=times
        )

    
    def list_places(self, source: Optional[str] = None) -> List[PlaceList]:
        # For places, we filter by the people/works associated with the place in the source?
        # Or does the place itself have a source?
        # The query LIST_PLACES joins with optional person.
        # If we filter by source, we likely mean "show me places connected to people from this source"
        # Or "places that have source X" (unlikely for Places themselves often).
        # Let's assume we filter the related PERSONS by source, and count those.
        
        # BUT, the query structure for LIST_PLACES has an OPTIONAL block for persons.
        # If I inject source_filter into that optional block, it will filter the persons.
        # `queries.LIST_PLACES` has `{source_filter}` inside the OPTIONAL block for person relations.
        
        sf = self._get_source_filter(source, "person")
        q = queries.LIST_PLACES.format(source_filter=sf)
        
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
        for row in rdf_store.query(queries.GET_PLACE_PEOPLE.format(source_filter=""), initBindings={'place': uri}):
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

    def list_subjects(self, source: Optional[str] = None) -> List[SubjectList]:
        sf = self._get_source_filter(source, "work")
        q = queries.LIST_SUBJECTS.format(source_filter=sf)

        results = []
        for row in rdf_store.query(q):
             results.append(SubjectList(
                id=row.uri.split("#")[-1],
                label=str(row.label),
                count=int(row.total),
                works=int(row.total),
                authors=int(row.author_count) if hasattr(row, 'author_count') and row.author_count else 0
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
        sf = "" # No source filter on detail page yet
        
        # Using format just in case
        q = queries.GET_SUBJECT_WORKS.format(source_filter="")
            
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
    def list_languages(self, source: Optional[str] = None) -> List[LanguageList]:
        sf = self._get_source_filter(source, "work")
        q = queries.LIST_LANGUAGES.format(source_filter=sf)
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
            
        works = []
        q = queries.GET_LANGUAGE_WORKS.format(source_filter="")
        for row in rdf_store.query(q, initBindings={'lang': uri}):
            t = str(row.title) if row.title else (str(row.label) if row.label else str(row.work).split("#")[-1])
            works.append(LanguageWorkInfo(
                id=row.work.split("#")[-1],
                title=t
            ))

        return LanguageDetail(
            label=str(label),
            works=works
        )

    # --- Scholarly Works ---
    def list_scholarly_works(self, source: Optional[str] = None) -> List[ScholarlyList]:
        sf = self._get_source_filter(source, "uri")
        q = queries.LIST_SCHOLARLY_WORKS.format(source_filter=sf)
        
        works_map = {}
        
        for row in rdf_store.query(q):
            uri = str(row.uri)
            title = str(row.title) if row.title else str(row.label) if row.label else uri.split("#")[-1]
            if uri not in works_map:
                works_map[uri] = {
                    "uri": row.uri,
                    "id": uri.split("#")[-1],
                    "title": title,
                    "year": str(row.year) if row.year else None,
                    "authors": {}, # uri -> name map to dedup
                    "sources": {}, # uri -> label map
                    "publisher": str(row.publisher) if row.publisher else None,
                    "type": str(row.type) if row.type else None,
                    "mentions_person": set(),
                    "mentions_work": set()
                }
            
            entry = works_map[uri]
            
            # Collect Authors
            if row.authorUri and row.authorName:
                entry["authors"][str(row.authorUri)] = str(row.authorName)
                
            # Set Source
            if row.sourceUri and row.sourceLabel:
                entry["sources"][str(row.sourceUri)] = str(row.sourceLabel)
                
            if row.person: entry["mentions_person"].add(row.person)
            if row.work: entry["mentions_work"].add(row.work)

        results = []
        for w in works_map.values():
            # Convert authors dict to list of Scholar objects
            author_list = [
                Scholar(id=uri.split("#")[-1], name=name)
                for uri, name in w["authors"].items()
            ]
            # Sort authors by name
            author_list.sort(key=lambda x: x.name)
            # Convert sources dict to list of Source objects
            from app.schemas.scholarly import Source as ScholarlySource
            source_list = [
                ScholarlySource(id=suri.split("#")[-1], label=slabel)
                for suri, slabel in w["sources"].items()
            ]
            source_list.sort(key=lambda x: x.label)

            results.append(ScholarlyList(
                uri=str(w["uri"]),
                id=w["id"],
                title=w["title"],
                year=w["year"],
                authors=author_list,
                sources=source_list,
                publisher=w["publisher"],
                type=w["type"],
                mentions_person_count=len(w["mentions_person"]),
                mentions_work_count=len(w["mentions_work"])
            ))
            
        # Sort by Year (descending), then Title
        results.sort(key=lambda x: (x.year or "0", x.title), reverse=True)
        return results

    def get_scholarly_detail(self, work_id: str) -> Optional[ScholarlyDetail]:
        uri = URIRef(f"{JP}{work_id}")
        
        title = rdf_store.g.value(uri, JP.title)
        if not title:
            return None

        # Standardized year
        year = rdf_store.g.value(uri, JP.publicationYear)
        if not year:
             year = rdf_store.g.value(uri, JP.year)

        # Sources
        sources = []
        for source_uri in rdf_store.g.objects(uri, JP.hasSource):
            source_label = rdf_store.g.value(source_uri, RDFS.label)
            sources.append(ScholarlySource(
                id=str(source_uri).split("#")[-1],
                label=str(source_label) if source_label else str(source_uri).split("#")[-1]
            ))
        sources.sort(key=lambda x: x.label)

        # Authors
        authors = []
        for author_uri in rdf_store.g.objects(uri, JP.hasAuthor):
            author_name = rdf_store.g.value(author_uri, RDFS.label)
            authors.append(Scholar(
                id=str(author_uri).split("#")[-1],
                name=str(author_name) if author_name else str(author_uri).split("#")[-1]
            ))
        authors.sort(key=lambda x: x.name)

        mentions_person = []
        for p in rdf_store.g.objects(uri, JP.aboutPerson):
            label = rdf_store.g.value(p, RDFS.label)
            mentions_person.append(MentionedPerson(
                id=p.split("#")[-1],
                label=str(label) if label else p.split("#")[-1]
            ))
            
        mentions_work = []
        for w in rdf_store.g.objects(uri, JP.aboutWork):
            w_title = rdf_store.g.value(w, JP.title)
            mentions_work.append(MentionedWork(
                id=w.split("#")[-1],
                title=str(w_title) if w_title else w.split("#")[-1]
            ))

        return ScholarlyDetail(
            uri=str(uri),
            title=str(title),
            year=str(year) if year else None,
            authors=authors,
            sources=sources,
            mentions_person=mentions_person,
            mentions_work=mentions_work
        )

    # --- Network ---
    def get_network_data(self, source: Optional[str] = None) -> NetworkData:
        nodes = []
        edges = []

        def mk_id(uri): return uri.strip("/").split("/")[-1].split("#")[-1]

        # 1. Nodes - Get source-filtered entities (persons, works, etc.)
        sf_nodes = self._get_source_filter(source, "s")
        q_nodes = queries.GET_NETWORK_NODES.format(source_filter=sf_nodes)

        node_ids = set()

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
                source=source_id  # Add source to node
            ))
            node_ids.add(mk_id(row.s)) # Use mk_id for safe checking


        # 2. Edges
        sf_edges = "" # No source filter on edges query for now, relies on node filtering
        q_direct = queries.GET_NETWORK_EDGES_DIRECT.format(source_filter=sf_edges)

        for row in rdf_store.query(q_direct):
            s_id = mk_id(row.s)
            o_id = mk_id(row.o)
            if s_id in node_ids and o_id in node_ids:
                edges.append({"from": s_id, "to": o_id})

        q_places = queries.GET_NETWORK_EDGES_PLACES.format(source_filter="")
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
                        source=None
                    ))
                    node_ids.add(pl_id)
                edges.append({"from": p_id, "to": pl_id})

        return NetworkData(nodes=nodes, edges=edges)


    # --- Stats ---
    def get_global_stats(self, source: Optional[str] = None) -> Dict[str, int]:
        stats_queries = queries.STATS_QUERIES
        PREFIXES = queries.PREFIXES
        
        sf = self._get_source_filter(source, "s")
        
        stats = {}
        for key, q in stats_queries.items():
            # Format the query with source_filter
            # Note: "s" is hardcoded in STATS_QUERIES
            formatted_q = q.format(source_filter=sf)
            full_q = PREFIXES + formatted_q
            
            for row in rdf_store.query(full_q):
                stats[key] = int(row.total)
                
        return stats


    def get_geo_json(self, source: Optional[str] = None) -> Dict[str, Any]:
        """
        Return a GeoJSON FeatureCollection of Persons at Places.
        Matches frontend expectation: person_id, person_label, place_label, start, end.
        """
        # Filter persons by source
        sf = self._get_source_filter(source, "person")
        q = queries.GET_GEO_JSON.format(source_filter=sf)
        
        features = []
        for row in rdf_store.query(q):
            try:
                lat = float(row.lat)
                long = float(row.long)
                
                # Time handling
                start_year = int(row.start) if row.start else None
                end_year = int(row.end) if row.end else None
                
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
                        "type": str(row.placeType) if row.placeType else "Unknown",
                        "start": start_year,
                        "end": end_year
                    }
                })
            except (ValueError, TypeError):
                continue

        return {
            "type": "FeatureCollection",
            "features": features
        }

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
        from rdflib import BNode, URIRef
        from rdflib.namespace import OWL, RDF

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
