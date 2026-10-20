from typing import List, Optional, Dict, Any, Iterable
import math
import re
from app.core.db import db
from app.core.db_schema import COLLECTIONS, NAME_COLLATION, PREFIX_COLLECTIONS, SEARCH_FIELDS, SEARCH_INDEX_NAME, id_prefix, ref_targets
from app.schemas.person import PersonList, PersonDetail, RelatedWork, PlaceRelation, TimeRelation, IntellectualRelation
from app.schemas.work import WorkList, WorkDetail, WorkAuthor
from app.schemas.place import PlaceList, PlaceDetail, PersonAtPlace
from app.schemas.subject import SubjectList, SubjectDetail, SubjectWorkInfo
from app.schemas.language import LanguageList, LanguageDetail, LanguagePersonInfo
from app.schemas.network import NetworkData, NetworkNode

ENTITY_GROUPS = {
    "persons": "HistoricalPerson",
    "works": "HistoricalWork",
    "places": "Place",
    "subjects": "Subject",
    "languages": "Language",
}
OUTGOING_RELATIONS = {"influenced_by": "influenced_by", "cites": "cites", "interlocutor_of": "interlocutor"}
INCOMING_RELATIONS = {"influenced_by": "influenced", "cites": "cited_by", "interlocutor_of": "interlocutor"}
NETWORK_RELATIONS = {"influenced_by": "influencedBy", "cites": "cites", "interlocutor_of": "interlocutorOf"}
BUCKET_SIZE = 50


class ConflictError(Exception):
    pass


def bucket_starts(times: Iterable[dict]) -> List[int]:
    starts = set()
    for t in times:
        start = t["from"]
        until = t.get("until", start)
        starts.update(range(start // BUCKET_SIZE * BUCKET_SIZE, until // BUCKET_SIZE * BUCKET_SIZE + 1, BUCKET_SIZE))
    return sorted(starts)


def bucket_label(start: int) -> str:
    end = start + BUCKET_SIZE - 1
    return f"{-start}BCE-{-end}BCE" if start < 0 else f"{start}-{end}"


def time_buckets(times: Iterable[dict]) -> List[str]:
    return [bucket_label(start) for start in bucket_starts(times)]


def escape_wildcard(word: str) -> str:
    return re.sub(r"([\\*?])", r"\\\1", word)


def _year(value) -> Optional[str]:
    return str(value) if value is not None else None


def _unique(values: Iterable) -> list:
    return list(dict.fromkeys(values))


class EntityService:

    def _names(self, collection: str, ids: Iterable[str]) -> Dict[str, str]:
        ids = list(set(ids))
        if not ids:
            return {}
        field = "title" if collection == "works" else "name"
        return {doc["_id"]: doc[field] for doc in db[collection].find({"_id": {"$in": ids}}, {field: 1})}

    def _entity_names(self, ids: Iterable[str]) -> Dict[str, str]:
        by_collection = {}
        for entity_id in ids:
            by_collection.setdefault(PREFIX_COLLECTIONS.get(id_prefix(entity_id)), []).append(entity_id)
        names = {}
        for collection, collection_ids in by_collection.items():
            if collection:
                names.update(self._names(collection, collection_ids))
        return names

    def _source_query(self, source: Optional[str]) -> dict:
        return {"sources": source} if source else {}

    def _paginate(self, total: int, page: int, page_size: int, items: list) -> Dict[str, Any]:
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if page_size else 1,
        }

    def _time_text(self, t: dict) -> Optional[str]:
        if t.get("label"):
            return t["label"]
        text = str(t["from"])
        if t.get("until") is not None:
            text += f"-{t['until']}"
        return f"{text} ({t['type'].capitalize() if t.get('type') else 'Time'})"

    def _translation_pairs(self, person_ids: Optional[set] = None) -> List[tuple]:
        translations = list(db.works.find(
            {"translation_of": {"$exists": True}, "translators.0": {"$exists": True}},
            {"translation_of": 1, "translators": 1},
        ))
        originals = {
            doc["_id"]: doc["authors"]
            for doc in db.works.find({"_id": {"$in": [t["translation_of"] for t in translations]}}, {"authors": 1})
        }
        pairs = [
            (translator, author)
            for t in translations
            for translator in t["translators"]
            for author in originals.get(t["translation_of"], [])
        ]
        for doc in db.persons.find({"relations.type": "translated"}, {"relations": 1}):
            pairs += [(doc["_id"], r["target"]) for r in doc["relations"] if r["type"] == "translated"]
        pairs = _unique(pairs)
        if person_ids is not None:
            pairs = [p for p in pairs if p[0] in person_ids and p[1] in person_ids]
        return pairs

    def list_persons(self, page: int = 1, page_size: int = 100, source: str = None, search: str = None) -> Dict[str, Any]:
        query = self._source_query(source)
        if search:
            pattern = {"$regex": re.escape(search), "$options": "i"}
            query["$or"] = [{"name": pattern}, {"alt_names": pattern}]

        total = db.persons.count_documents(query)
        docs = list(
            db.persons.find(query, {"name": 1, "places": 1, "times": 1, "subjects": 1, "name_verified": 1, "viaf_id": 1, "viaf_suggestions": 1})
            .sort([("name", 1), ("_id", 1)])
            .collation(NAME_COLLATION)
            .skip((page - 1) * page_size)
            .limit(page_size)
        )
        place_names = self._names("places", (p["place"] for d in docs for p in d["places"]))
        subject_names = self._names("subjects", (s for d in docs for s in d["subjects"]))

        items = []
        for d in docs:
            places = _unique(
                f"{place_names.get(p['place'], p['place'])} ({p['type'].capitalize() if p.get('type') else 'Unknown'})"
                for p in d["places"]
            )
            times = _unique(self._time_text(t) for t in d["times"])
            buckets = time_buckets(d["times"])
            subjects = _unique(subject_names[s] for s in d["subjects"] if s in subject_names)
            items.append(PersonList(
                id=d["_id"],
                label=d["name"],
                **self._viaf_fields(d),
                places=", ".join(places) or None,
                times=", ".join(times) or None,
                time_buckets=", ".join(buckets) or None,
                subjects=", ".join(subjects) or None,
            ))

        return self._paginate(total, page, page_size, items)

    def get_person_detail(self, person_id: str) -> Optional[PersonDetail]:
        d = db.persons.find_one({"_id": person_id})
        if not d:
            return None

        works = [
            RelatedWork(id=w["_id"], title=w["title"])
            for w in db.works.find({"authors": person_id}, {"title": 1}).sort("title", 1).collation(NAME_COLLATION)
        ]

        place_names = self._names("places", (p["place"] for p in d["places"]))
        places_map = {}
        for i, p in enumerate(sorted(d["places"], key=lambda p: (p.get("from") is not None, p.get("from", 0)))):
            p_type = p.get("type", "")
            key = i if p.get("time_label") else f"{p['place']}_{p_type.lower()}"
            if key not in places_map:
                places_map[key] = PlaceRelation(
                    place_id=p["place"],
                    label=place_names.get(p["place"], p["place"]),
                    type=p.get("type"),
                    start=_year(p.get("from")),
                    end=_year(p.get("until")),
                    time_label=p.get("time_label"),
                    description=p.get("description"),
                )

        times_map = {}
        for t in d["times"]:
            time = TimeRelation(type=t.get("type") or "Life", start=_year(t["from"]), end=_year(t.get("until")), label=t.get("label"))
            times_map.setdefault((time.type.lower(), time.start, time.end, time.label), time)

        subject_names = self._names("subjects", d["subjects"])
        language_names = self._names("languages", d["languages"])

        related = [(r["target"], OUTGOING_RELATIONS[r["type"]]) for r in d["relations"] if r["type"] in OUTGOING_RELATIONS]
        for other in db.persons.find({"relations.target": person_id}, {"relations": 1}):
            related += [
                (other["_id"], INCOMING_RELATIONS[r["type"]])
                for r in other["relations"]
                if r["target"] == person_id and r["type"] in INCOMING_RELATIONS
            ]
        related = _unique(related)
        related_names = self._entity_names(other_id for other_id, _ in related)
        relations = sorted(
            (
                IntellectualRelation(
                    id=other_id,
                    label=related_names[other_id],
                    entity_type=ENTITY_GROUPS[PREFIX_COLLECTIONS[id_prefix(other_id)]],
                    relation=relation,
                )
                for other_id, relation in related
                if other_id in related_names
            ),
            key=lambda r: (r.relation, r.label),
        )

        return PersonDetail(
            id=person_id,
            label=d["name"],
            alt_names=d["alt_names"],
            **self._viaf_fields(d),
            works=works,
            places=list(places_map.values()),
            times=list(times_map.values()),
            time_buckets=time_buckets(d["times"]),
            subjects=[subject_names[s] for s in d["subjects"] if s in subject_names],
            languages=[language_names[l] for l in d["languages"] if l in language_names],
            relations=relations,
        )

    def _viaf_fields(self, d: dict) -> Dict[str, Any]:
        verified = d.get("name_verified", False)
        return {
            "name_verified": verified,
            "viaf_id": d.get("viaf_id"),
            "viaf_suggestions": [] if verified else d.get("viaf_suggestions", []),
        }

    def verify_name(self, person_id: str, name: Optional[str], viaf_id: Optional[str], alt_names: Optional[List[str]] = None) -> PersonDetail:
        d = db.persons.find_one({"_id": person_id}, {"name": 1, "alt_names": 1, "name_verified": 1, "viaf_suggestions": 1})
        if not d:
            raise LookupError("Person not found")
        if d.get("name_verified"):
            raise ConflictError("Person name is already verified")
        name = name.strip() if name else None
        if not name:
            suggestion = next((s for s in d.get("viaf_suggestions", []) if s["viaf_id"] == viaf_id), None)
            if not suggestion:
                raise ValueError("Provide a name, or a VIAF id that is one of the person's suggestions")
            name = suggestion["name"]

        if alt_names is None:
            alt_names = d["alt_names"] + [d["name"]]
        alt_names = _unique(n for n in (a.strip() for a in alt_names) if n and n != name)
        update = {"name": name, "alt_names": alt_names, "name_verified": True}
        if viaf_id:
            update["viaf_id"] = viaf_id
        result = db.persons.update_one(
            {"_id": person_id, "name": d["name"], "name_verified": {"$ne": True}},
            {"$set": update},
        )
        if not result.modified_count:
            raise ConflictError("Person was modified concurrently")
        return self.get_person_detail(person_id)

    def list_works(self, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        total = db.works.count_documents({})
        docs = list(
            db.works.find({}, {"title": 1, "authors": 1, "subjects": 1, "languages": 1})
            .sort([("title", 1), ("_id", 1)])
            .collation(NAME_COLLATION)
            .skip((page - 1) * page_size)
            .limit(page_size)
        )
        author_names = self._names("persons", (a for d in docs for a in d["authors"]))
        subject_names = self._names("subjects", (s for d in docs for s in d["subjects"]))
        language_names = self._names("languages", (l for d in docs for l in d["languages"]))

        items = []
        for d in docs:
            authors = [author_names[a] for a in d["authors"] if a in author_names]
            subjects = [subject_names[s] for s in d["subjects"] if s in subject_names]
            languages = [language_names[l] for l in d["languages"] if l in language_names]
            items.append(WorkList(
                id=d["_id"],
                title=d["title"],
                authors=", ".join(authors) or None,
                subjects=", ".join(subjects) or None,
                languages=", ".join(languages) or None,
            ))

        return self._paginate(total, page, page_size, items)

    def get_work_detail(self, work_id: str) -> Optional[WorkDetail]:
        d = db.works.find_one({"_id": work_id})
        if not d:
            return None

        author_names = self._names("persons", d["authors"])
        authors = [WorkAuthor(id=a, label=author_names[a]) for a in d["authors"] if a in author_names]
        cited_by = [
            WorkAuthor(id=p["_id"], label=p["name"])
            for p in db.persons.find(
                {"relations": {"$elemMatch": {"type": "cites", "target": work_id}}}, {"name": 1}
            ).sort("name", 1).collation(NAME_COLLATION)
        ]
        subject_names = self._names("subjects", d["subjects"])
        language_names = self._names("languages", d["languages"])

        return WorkDetail(
            id=work_id,
            title=d["title"],
            description=d.get("description"),
            authorship_status=d.get("authorship_status"),
            preservation_status=d.get("preservation_status"),
            authors=authors,
            cited_by=cited_by,
            subjects=[subject_names[s] for s in d["subjects"] if s in subject_names],
            languages=[language_names[l] for l in d["languages"] if l in language_names],
        )

    def _person_counts(self, field: str, collection: str = "persons") -> Dict[str, int]:
        return {
            row["_id"]: row["count"]
            for row in db[collection].aggregate([
                {"$unwind": f"${field}"},
                {"$group": {"_id": f"${field}", "entities": {"$addToSet": "$_id"}}},
                {"$project": {"count": {"$size": "$entities"}}},
            ])
        }

    def list_places(self) -> List[PlaceList]:
        counts = self._person_counts("places.place")
        results = []
        for p in db.places.find({}, {"name": 1, "location": 1}).sort("name", 1).collation(NAME_COLLATION):
            coordinates = p.get("location", {}).get("coordinates")
            results.append(PlaceList(
                id=p["_id"],
                label=p["name"],
                lat=str(coordinates[1]) if coordinates else None,
                long=str(coordinates[0]) if coordinates else None,
                personCount=counts.get(p["_id"], 0),
            ))
        return results

    def get_place_detail(self, place_id: str) -> Optional[PlaceDetail]:
        p = db.places.find_one({"_id": place_id})
        if not p:
            return None
        coordinates = p.get("location", {}).get("coordinates")

        people = {}
        for person in db.persons.find({"places.place": place_id}, {"name": 1, "places": 1}):
            for rel in person["places"]:
                if rel["place"] == place_id:
                    people.setdefault(
                        (person["_id"], rel.get("type")),
                        PersonAtPlace(id=person["_id"], label=person["name"], type=rel.get("type")),
                    )

        return PlaceDetail(
            id=place_id,
            label=p["name"],
            lat=str(coordinates[1]) if coordinates else None,
            long=str(coordinates[0]) if coordinates else None,
            people=sorted(people.values(), key=lambda person: (person.type or "", person.label)),
        )

    def list_subjects(self) -> List[SubjectList]:
        person_counts = self._person_counts("subjects")
        work_counts = self._person_counts("subjects", "works")
        return [
            SubjectList(
                id=s["_id"],
                label=s["name"],
                count=person_counts.get(s["_id"], 0),
                authors=person_counts.get(s["_id"], 0),
                works=work_counts.get(s["_id"], 0),
            )
            for s in db.subjects.find({}, {"name": 1}).sort("name", 1).collation(NAME_COLLATION)
        ]

    def get_subject_detail(self, subject_id: str) -> Optional[SubjectDetail]:
        s = db.subjects.find_one({"_id": subject_id})
        if not s:
            return None
        works = [
            SubjectWorkInfo(id=w["_id"], title=w["title"])
            for w in db.works.find({"subjects": subject_id}, {"title": 1}).sort("title", 1).collation(NAME_COLLATION)
        ]
        return SubjectDetail(label=s["name"], works=works)

    def list_sources(self) -> List[dict]:
        counts = {}
        for collection in ("persons", "works", "places", "subjects"):
            for source_id, count in self._person_counts("sources", collection).items():
                counts[source_id] = counts.get(source_id, 0) + count
        return [
            {
                "id": s["_id"],
                "label": s["name"],
                "description": f"Data source containing {counts.get(s['_id'], 0)} entities",
                "count": counts.get(s["_id"], 0),
            }
            for s in db.sources.find({}, {"name": 1}).sort("name", 1).collation(NAME_COLLATION)
        ]

    def list_languages(self) -> List[LanguageList]:
        counts = self._person_counts("languages")
        return [
            LanguageList(id=l["_id"], label=l["name"], count=counts.get(l["_id"], 0))
            for l in db.languages.find({}, {"name": 1}).sort("name", 1).collation(NAME_COLLATION)
        ]

    def get_language_detail(self, lang_id: str) -> Optional[LanguageDetail]:
        l = db.languages.find_one({"_id": lang_id})
        if not l:
            return None
        persons = [
            LanguagePersonInfo(id=p["_id"], name=p["name"])
            for p in db.persons.find({"languages": lang_id}, {"name": 1}).sort("name", 1).collation(NAME_COLLATION)
        ]
        return LanguageDetail(label=l["name"], persons=persons)

    def _search_pipeline(self, collection: str, text: str, limit: int) -> List[dict]:
        words = text.split()
        should = [{"phrase": {"query": text, "path": {"wildcard": "*"}, "score": {"boost": {"value": 8}}}}]
        for word in words:
            should.append({"text": {"query": word, "path": {"wildcard": "*"}}})
            should.append({"wildcard": {
                "query": f"*{escape_wildcard(word.lower())}*",
                "path": {"wildcard": "*"},
                "allowAnalyzedField": True,
            }})
        return [
            {"$search": {"index": SEARCH_INDEX_NAME, "compound": {"should": should, "minimumShouldMatch": 1}}},
            {"$limit": limit},
            {"$project": {
                "label": "$title" if collection == "works" else "$name",
                "entity_type": {"$literal": ENTITY_GROUPS[collection]},
                "_searchScore": {"$meta": "searchScore"},
            }},
        ]

    def search(self, text: str, limit: int = 20) -> List[Dict[str, Any]]:
        collections = list(SEARCH_FIELDS)
        pipeline = self._search_pipeline(collections[0], text, limit)
        for collection in collections[1:]:
            pipeline.append({"$unionWith": {"coll": collection, "pipeline": self._search_pipeline(collection, text, limit)}})
        pipeline += [{"$sort": {"_searchScore": -1}}, {"$limit": limit}]
        return [
            {"id": doc["_id"], "label": doc["label"], "entity_type": doc["entity_type"], "score": doc["_searchScore"]}
            for doc in db[collections[0]].aggregate(pipeline)
        ]

    def get_network_data(self, source: str = None) -> NetworkData:
        query = self._source_query(source)
        nodes = []
        edges = []
        node_types = {}

        def add_node(node_id: str, label: str, group: str, buckets: List[str] = None):
            node_types[node_id] = group
            nodes.append(NetworkNode(id=node_id, label=label, group=group, buckets=buckets or []))

        persons = list(db.persons.find(query, {"name": 1, "times": 1, "places": 1, "subjects": 1, "languages": 1, "relations": 1}))
        works = list(db.works.find(query, {"title": 1, "authors": 1, "translators": 1, "translation_of": 1, "subjects": 1, "languages": 1}))
        for p in persons:
            add_node(p["_id"], p["name"], ENTITY_GROUPS["persons"], time_buckets(p["times"]))
        for w in works:
            add_node(w["_id"], w["title"], ENTITY_GROUPS["works"])
        for collection in ("places", "subjects", "languages"):
            for doc in db[collection].find(query, {"name": 1}):
                add_node(doc["_id"], doc["name"], ENTITY_GROUPS[collection])

        person_connections = {}
        person_group = ENTITY_GROUPS["persons"]

        def add_edge(from_id: str, to_id: str, relation: str):
            if from_id not in node_types or to_id not in node_types:
                return
            edges.append({"from": from_id, "to": to_id, "relation": relation})
            if node_types[from_id] == person_group:
                person_connections.setdefault(from_id, set()).add(to_id)
            elif node_types[to_id] == person_group:
                person_connections.setdefault(to_id, set()).add(from_id)

        for w in works:
            for author in w["authors"]:
                add_edge(w["_id"], author, "writtenBy")
            for translator in w["translators"]:
                add_edge(w["_id"], translator, "translatedBy")
            if w.get("translation_of"):
                add_edge(w["_id"], w["translation_of"], "isTranslationOf")
        for doc in persons + works:
            for subject in doc["subjects"]:
                add_edge(doc["_id"], subject, "hasSubject")
            for language in doc["languages"]:
                add_edge(doc["_id"], language, "hasLanguage")
        for p in persons:
            for r in p["relations"]:
                if r["type"] in NETWORK_RELATIONS:
                    add_edge(p["_id"], r["target"], NETWORK_RELATIONS[r["type"]])
        for translator, author in self._translation_pairs():
            add_edge(translator, author, "translated")

        place_names = self._names("places", (rel["place"] for p in persons for rel in p["places"]))
        for p in persons:
            for place_id in _unique(rel["place"] for rel in p["places"]):
                if place_id not in node_types:
                    add_node(place_id, place_names.get(place_id, place_id), ENTITY_GROUPS["places"])
                edges.append({"from": p["_id"], "to": place_id})
                person_connections.setdefault(p["_id"], set()).add(place_id)

        existing_edges = {tuple(sorted([edge["from"], edge["to"]])) for edge in edges}
        for connected_entities in person_connections.values():
            ent_list = list(connected_entities)
            for i in range(len(ent_list)):
                for j in range(i + 1, len(ent_list)):
                    e1 = ent_list[i]
                    e2 = ent_list[j]
                    if node_types.get(e1) != person_group and node_types.get(e2) != person_group:
                        t = tuple(sorted([e1, e2]))
                        if t not in existing_edges:
                            edges.append({"from": e1, "to": e2, "dashes": True})
                            existing_edges.add(t)

        return NetworkData(nodes=nodes, edges=edges)

    def get_sources(self) -> List[dict]:
        return self.list_sources()

    def get_global_stats(self, source: str = None) -> Dict[str, int]:
        query = self._source_query(source)
        return {
            "persons": db.persons.count_documents(query),
            "works": db.works.count_documents(query),
            "places": db.places.count_documents({}),
            "subjects": db.subjects.count_documents({}),
            "languages": db.languages.count_documents({}),
            "sources": db.sources.count_documents({}),
        }

    def _place_coordinates(self, place_ids: Iterable[str]) -> Dict[str, tuple]:
        return {
            p["_id"]: (p["name"], p["location"]["coordinates"])
            for p in db.places.find({"_id": {"$in": list(set(place_ids))}, "location": {"$exists": True}}, {"name": 1, "location": 1})
        }

    def get_geo_json(self, source: str = None) -> Dict[str, Any]:
        persons = list(db.persons.find(self._source_query(source), {"name": 1, "places": 1, "times": 1, "sources": 1}))
        places = self._place_coordinates(rel["place"] for p in persons for rel in p["places"])
        source_names = self._names("sources", (s for p in persons for s in p["sources"]))

        features = []
        seen = set()
        for p in persons:
            buckets = time_buckets(p["times"]) or [None]
            sources = [source_names[s] for s in p["sources"] if s in source_names] or ["Unknown"]
            for rel in p["places"]:
                if rel["place"] not in places:
                    continue
                place_label, (long, lat) = places[rel["place"]]
                place_type = rel.get("type") or "Unknown"
                for bucket in buckets:
                    for source_label in sources:
                        key = (p["_id"], rel["place"], place_type, bucket, source_label)
                        if key in seen:
                            continue
                        seen.add(key)
                        features.append({
                            "type": "Feature",
                            "geometry": {"type": "Point", "coordinates": [long, lat]},
                            "properties": {
                                "person_id": p["_id"],
                                "person_label": p["name"],
                                "place_label": place_label,
                                "type": place_type,
                                "bucket": bucket,
                                "source": source_label,
                            },
                        })

        return {"type": "FeatureCollection", "features": features}

    def get_translation_flows(self) -> List[Dict[str, Any]]:
        pairs = self._translation_pairs()
        persons = {
            p["_id"]: p
            for p in db.persons.find({"_id": {"$in": _unique(i for pair in pairs for i in pair)}}, {"name": 1, "places": 1})
        }
        places = self._place_coordinates(rel["place"] for p in persons.values() for rel in p["places"])

        def person_coords(person: dict) -> List[tuple]:
            return _unique((lat, long) for _, (long, lat) in (places[rel["place"]] for rel in person["places"] if rel["place"] in places))

        flows = []
        for translator_id, author_id in pairs:
            translator = persons.get(translator_id)
            author = persons.get(author_id)
            if not translator or not author:
                continue
            for t_lat, t_long in person_coords(translator):
                for a_lat, a_long in person_coords(author):
                    flows.append({
                        "translator_id": translator_id,
                        "translator_label": translator["name"],
                        "author_id": author_id,
                        "author_label": author["name"],
                        "path": [[t_lat, t_long], [a_lat, a_long]],
                    })
        return flows

    def _schema_fields(self, schema: dict, prefix: str = ""):
        for name, prop in schema.get("properties", {}).items():
            path = f"{prefix}{name}"
            yield path, prop
            item = prop.get("items", prop)
            if "properties" in item:
                yield from self._schema_fields(item, f"{path}.")

    def _document_fields(self, value, prefix: str = ""):
        if isinstance(value, dict):
            for name, child in value.items():
                path = f"{prefix}{name}"
                yield path
                yield from self._document_fields(child, f"{path}.")
        elif isinstance(value, list):
            for child in value:
                yield from self._document_fields(child, prefix)

    def get_ontology_graph(self) -> Dict[str, Any]:
        nodes = [
            {"id": name, "label": schema["title"], "title": schema.get("description"), "group": "Class"}
            for name, schema in COLLECTIONS.items()
        ]
        edges = []
        for name, schema in COLLECTIONS.items():
            for path, prop in self._schema_fields(schema):
                pattern = prop.get("items", prop).get("pattern")
                if path == "_id" or not pattern:
                    continue
                for target in ref_targets(pattern):
                    edges.append({"from": name, "to": target, "label": path, "arrows": "to", "font": {"align": "middle"}})
        return {"nodes": nodes, "edges": edges}

    def get_ontology_audit(self) -> Dict[str, Any]:
        defined_classes = set(COLLECTIONS)
        defined_properties = {f"{name}.{path}" for name, schema in COLLECTIONS.items() for path, _ in self._schema_fields(schema)}

        actual_classes = set()
        actual_properties = set()
        for name in db.list_collection_names():
            for doc in db[name].find():
                actual_classes.add(name)
                actual_properties.update(f"{name}.{path}" for path in self._document_fields(doc))

        return {
            "classes": {
                "defined_count": len(defined_classes),
                "actual_count": len(actual_classes),
                "unused": sorted(defined_classes - actual_classes),
                "undefined": sorted(actual_classes - defined_classes),
            },
            "properties": {
                "defined_count": len(defined_properties),
                "actual_count": len(actual_properties),
                "unused": sorted(defined_properties - actual_properties),
                "undefined": sorted(actual_properties - defined_properties),
            },
        }


entity_service = EntityService()
