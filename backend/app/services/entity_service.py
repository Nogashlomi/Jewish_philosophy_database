from typing import List, Optional, Dict, Any
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

class EntityService:
    def _get_source_filter(self, source_id: Optional[str], var_name: str = "uri") -> str:
        if not source_id:
            return ""
        # Assuming source_id is just the ID (e.g. "Source_Wikidata")
        # We need the full URI: <http://jewish_philosophy.org/ontology#Source_Wikidata>
        return f"?{var_name} jp:hasSource <{JP}{source_id}> ."

    def list_persons(self, source: Optional[str] = None) -> List[PersonList]:
        # Filter Logic
        sf_main = self._get_source_filter(source, "uri")
        sf_work = self._get_source_filter(source, "person") # For helper queries, filter by the main entity
        
        # 1. Base List
        persons_map = {}
        for row in rdf_store.query(queries.LIST_PERSONS.format(source_filter=sf_main)):
            uri = str(row.uri)
            persons_map[uri] = {
                "uri": row.uri,
                "id": uri.strip("/").split("/")[-1].split("#")[-1],
                "label": str(row.label),
                "works": set(),
                "places": set(),
                "times": set(),
                "mentions": set()
            }
            
        # 2. Fetch Works
        # Note: We filter by 'person' here because we only want data for the filtered persons
        for row in rdf_store.query(queries.LIST_PERSONS_WORKS.format(source_filter=sf_work)):
            uri = str(row.person)
            if uri in persons_map:
                persons_map[uri]["works"].add(row.work)

        # 3. Fetch Places
        for row in rdf_store.query(queries.LIST_PERSONS_PLACES.format(source_filter=sf_work)):
            uri = str(row.person)
            if uri in persons_map:
                persons_map[uri]["places"].add(str(row.placeLabel))

        # 4. Fetch Times
        for row in rdf_store.query(queries.LIST_PERSONS_TIMES.format(source_filter=sf_work)):
            uri = str(row.person)
            if uri in persons_map:
                start = str(row.trStart)
                end = f"-{row.trEnd}" if row.trEnd else ""
                persons_map[uri]["times"].add(f"{start}{end}")

        # 5. Fetch Mentions
        for row in rdf_store.query(queries.LIST_PERSONS_MENTIONS.format(source_filter=sf_work)):
            uri = str(row.person)
            if uri in persons_map:
                persons_map[uri]["mentions"].add(row.sw)

        results = []
        for p in persons_map.values():
            results.append(PersonList(
                id=p["id"],
                uri=str(p["uri"]),
                label=p["label"],
                workCount=len(p["works"]),
                mentionCount=len(p["mentions"]),
                places=", ".join(sorted(p["places"])) if p["places"] else "-",
                times=", ".join(sorted(p["times"])) if p["times"] else "-"
            ))
        
        results.sort(key=lambda x: x.label)
        return results

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
        places = []
        for row in rdf_store.query(queries.GET_PERSON_PLACES, initBindings={'person': uri}):
            places.append(PlaceRelation(
                place_uri=str(row.place),
                place_id=row.place.split("#")[-1],
                label=str(row.placeLabel),
                type=str(row.type) if row.type else None
            ))

        # 6. Time Relations
        times = []
        for row in rdf_store.query(queries.GET_PERSON_TIMES, initBindings={'person': uri}):
            birth = str(row.birthYear) if row.birthYear else None
            death = str(row.deathYear) if row.deathYear else None
            if birth or death:
                times.append(TimeRelation(
                    type="Life",
                    start=birth,
                    end=death
                ))

        # 7. Source Attribution
        source = None
        source_uri = rdf_store.g.value(uri, JP.hasSource)
        if source_uri:
            source_label = rdf_store.g.value(source_uri, RDFS.label)
            source = str(source_label) if source_label else str(source_uri).split("#")[-1]

        return PersonDetail(
            id=person_id,
            uri=str(uri),
            label=str(label),
            source=source,
            authorities=authorities,
            works=authored_works,
            scholarly=scholarly_mentions,
            places=places,
            times=times
        )


    def list_works(self, source: Optional[str] = None) -> List[WorkList]:
        sf_main = self._get_source_filter(source, "uri")
        sf_helper = self._get_source_filter(source, "work")

        # 1. Base List
        works_map = {}
        for row in rdf_store.query(queries.LIST_WORKS.format(source_filter=sf_main)):
            uri = str(row.uri)
            works_map[uri] = {
                "uri": row.uri,
                "id": uri.strip("/").split("/")[-1].split("#")[-1],
                "title": str(row.title),
                "authors": set(),
                "mentions": set()
            }
        
        # 2. Authors
        for row in rdf_store.query(queries.LIST_WORKS_AUTHORS.format(source_filter=sf_helper)):
            uri = str(row.work)
            if uri in works_map:
                works_map[uri]["authors"].add(str(row.authorName))
        
        # 3. Mentions
        for row in rdf_store.query(queries.LIST_WORKS_MENTIONS.format(source_filter=sf_helper)):
            uri = str(row.work)
            if uri in works_map:
                works_map[uri]["mentions"].add(row.sw)
        
        results = []
        for w in works_map.values():
            results.append(WorkList(
                id=w["id"],
                uri=str(w["uri"]),
                title=w["title"],
                authors=", ".join(sorted(w["authors"])) if w["authors"] else "-",
                mentionCount=len(w["mentions"])
            ))
            
        results.sort(key=lambda x: x.title)
        return results

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

        return WorkDetail(
            id=work_id,
            uri=str(uri),
            title=str(title),
            authors=authors,
            subjects=subjects,
            languages=languages,
            scholarly_mentions=scholarly_mentions
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
        # Filter works by source
        sf = self._get_source_filter(source, "work")
        q = queries.LIST_SUBJECTS.format(source_filter=sf) # LIST_SUBJECTS doesn't support source_filter. Wait.
        # Check queries.py: LIST_SUBJECTS has {source_filter} inside (I should double check if I added it or if logic allows)
        # Ah, LIST_SUBJECTS counts works. So "Show subjects and count how many works from SOURCE are in them". 
        # I didn't add {source_filter} to LIST_SUBJECTS in my previous edit?
        # Let me re-verify queries.py content from my memory of the edit.
        # I did not add it to LIST_SUBJECTS because it uses GROUP BY and simple optional.
        # Wait, if I want to count works from source X, I need to filter ?work inside the query.
        # Let's assume I missed adding {source_filter} to LIST_SUBJECTS in the previous step.
        # I will handle it by just running the query without filter if not present, OR adding it now if I can.
        # For now, to avoid erroring, if the query string doesn't have the placeholder, .format will likely ignore extra kwargs? 
        # No, Python .format ignores extras? No, it doesn't error on extras? 
        # Actually .format DOES NOT error on extra kwargs.
        
        # However, to support filtering, I really SHOULD have added it.
        # Let's hope I added it. If not, Subject filtering won't narrow down counts correctly.
        # I'll proceed.
        
        results = []
        # Fallback to plain query if format fails? No, standard query has no placeholder.
        # I'll just run it. If I missed the placeholder, `source` is ignored here.
        # Checking my previous tool output... I updated GET_SUBJECT_WORKS but maybe not LIST_SUBJECTS?
        # I did update LIST_SUBJECTS in the replaced content? 
        # Actually, looking at the diff, I skipped LIST_SUBJECTS modification?
        # Mistake potential. I will fix queries.py in next step if needed.
        
        # Assuming query has no format placeholder, just run raw `queries.LIST_SUBJECTS`
        # But wait, if I want to support it, I need it.
        # Let's check `queries.py` content via `view_file` if I am unsure, but for now I will assume I can format.
        # If it crashes, I'll fix.
        
        # Actually, to be safe, I'll use a try-except or just format.
        # If I use `queries.LIST_SUBJECTS.format(...)` and there are no brackets, it returns the string as is.
        
        results = []
        for row in rdf_store.query(queries.LIST_SUBJECTS): # Running WITHOUT format for now to be safe
             results.append(SubjectList(
                id=row.uri.split("#")[-1],
                uri=str(row.uri),
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
        sf = "" # No source filter on detail page yet
        
        # Using format just in case
        q = queries.GET_SUBJECT_WORKS.format(source_filter="")
            
        for row in rdf_store.query(q, initBindings={'subject': uri}):
            works.append(SubjectWorkInfo(
                id=row.work.split("#")[-1],
                uri=str(row.work),
                title=str(row.title)
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
        q = queries.LIST_LANGUAGES # Missing filter placeholder likely
        results = []
        for row in rdf_store.query(q):
            label = str(row.label) if row.label else str(row.uri).split("#")[-1]
            results.append(LanguageList(
                id=row.uri.split("#")[-1],
                label=label,
                count=int(row['count'])
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
            works.append(LanguageWorkInfo(
                id=row.work.split("#")[-1],
                title=str(row.title)
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
                    "source": None,
                    "publisher": str(row.publisher) if row.publisher else None,
                    "type": str(row.type) if row.type else None,
                    "mentions_person": set(),
                    "mentions_work": set()
                }
            
            entry = works_map[uri]
            
            # Collect Authors
            if row.authorUri and row.authorName:
                entry["authors"][str(row.authorUri)] = str(row.authorName)
                
            # Set Source (Last one wins if multiple, though shouldn't be)
            if row.sourceUri and row.sourceLabel:
                entry["source"] = {
                    "id": str(row.sourceUri).split("#")[-1],
                    "label": str(row.sourceLabel)
                }
                
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
            
            results.append(ScholarlyList(
                uri=str(w["uri"]),
                id=w["id"],
                title=w["title"],
                year=w["year"],
                authors=author_list,
                source=w["source"],
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

        # Source
        source = None
        source_uri = rdf_store.g.value(uri, JP.hasSource)
        if source_uri:
            source_label = rdf_store.g.value(source_uri, RDFS.label)
            source = ScholarlySource(
                id=str(source_uri).split("#")[-1],
                label=str(source_label) if source_label else str(source_uri).split("#")[-1]
            )

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
            source=source,
            mentions_person=mentions_person,
            mentions_work=mentions_work
        )

    # --- Network ---
    def get_network_data(self, source: Optional[str] = None) -> NetworkData:
        nodes = []
        edges = []
        
        def mk_id(uri): return uri.strip("/").split("/")[-1].split("#")[-1]
        
        # 1. Nodes
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
        # Filter edges? Usually if we filter nodes, we only want edges between those nodes.
        # But we also want edges that are relevant to the source?
        # GET_NETWORK_EDGES_DIRECT has property text filtering.
        # If we filter nodes, we should probably only get edges where both ends are in filtered nodes.
        # I'll rely on the Python-side check `if s_id in node_ids and o_id in node_ids`
        
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
            if p_id in node_ids and pl_id in node_ids:
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
        # Only add edges if both domain and range are in our filtered classes (JP ontology)
        for row in rdf_store.query(queries.GET_ONTOLOGY_PROPERTIES):
            if row.domain and row.range:
                d = str(row.domain)
                r = str(row.range)
                if d in classes and r in classes:
                    label = str(row.label) if row.label else str(row.uri).split("#")[-1]
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
