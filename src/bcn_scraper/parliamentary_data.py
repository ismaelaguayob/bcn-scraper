"""Utilities to fetch and tabulate BCN parliamentary person data."""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from typing import Callable, Dict, Iterable, List, Optional, Tuple, Union

import pandas as pd


BCN_PERSON_RE = re.compile(r"https?://datos\.bcn\.cl/recurso/persona/(?P<id>\d+)(?:/)?$")
RDF_JSON_SUFFIX_RE = re.compile(r"/datos\.(?:json|rdf|n3|ntriples|html)$")

RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"
SKOS_PREF_LABEL = "http://www.w3.org/2004/02/skos/core#prefLabel"
DC_IDENTIFIER = "http://purl.org/dc/elements/1.1/identifier"
DC_DATE = "http://purl.org/dc/elements/1.1/date"
FOAF_NAME = "http://xmlns.com/foaf/0.1/name"
FOAF_GENDER = "http://xmlns.com/foaf/0.1/gender"
FOAF_IMG = "http://xmlns.com/foaf/0.1/img"
FOAF_DEPICTION = "http://xmlns.com/foaf/0.1/depiction"
FOAF_THUMBNAIL = "http://xmlns.com/foaf/0.1/thumbnail"
BIO_PLACE = "http://purl.org/vocab/bio/0.1/place"
BCNBIO_HAS_BORN = "http://datos.bcn.cl/ontologies/bcn-biographies#hasBorn"
BCNBIO_HAS_MILITANCY = "http://datos.bcn.cl/ontologies/bcn-biographies#hasMilitancy"
BCNBIO_HAS_POLITICAL_PARTY = "http://datos.bcn.cl/ontologies/bcn-biographies#hasPoliticalParty"
BCNBIO_HAS_BEGINNING = "http://datos.bcn.cl/ontologies/bcn-biographies#hasBeginning"
BCNBIO_HAS_END = "http://datos.bcn.cl/ontologies/bcn-biographies#hasEnd"
BCNBIO_NATIONALITY = "http://datos.bcn.cl/ontologies/bcn-biographies#nationality"
BCNBIO_ORIGINAL_DATE = "http://datos.bcn.cl/ontologies/bcn-biographies#originalDate"


RDFJson = Dict[str, Dict[str, List[Dict[str, object]]]]
RDFJsonFetcher = Callable[[str], RDFJson]


def canonical_resource_url(resource_url: str) -> str:
    """Return a BCN resource URL without datos.* suffixes or trailing slashes."""
    url = str(resource_url or "").strip()
    url = RDF_JSON_SUFFIX_RE.sub("", url)
    return url.rstrip("/")


def rdf_json_url(resource_url: str) -> str:
    """Build the datos.json URL for a BCN RDF resource."""
    return f"{canonical_resource_url(resource_url)}/datos.json"


def is_bcn_person_url(resource_url: object) -> bool:
    """Return True when value points to a BCN person resource."""
    if not isinstance(resource_url, str):
        return False
    return bool(BCN_PERSON_RE.match(canonical_resource_url(resource_url)))


def bcn_person_id(person_href: str) -> Optional[str]:
    """Extract the BCN numeric person id from a person URL."""
    match = BCN_PERSON_RE.match(canonical_resource_url(person_href))
    if not match:
        return None
    return match.group("id")


def fetch_rdf_json(
    resource_url: str,
    *,
    timeout: int = 60,
    max_attempts: int = 3,
    backoff_seconds: float = 2.0,
    user_agent: str = "bcn-scraper/0.1",
) -> RDFJson:
    """Fetch a BCN RDF/JSON resource with small retry/backoff logic."""
    url = rdf_json_url(resource_url)
    last_error: Optional[Exception] = None
    for attempt in range(1, max_attempts + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": user_agent})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = response.read().decode("utf-8")
            return json.loads(payload)
        except (TimeoutError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt == max_attempts:
                break
            time.sleep(backoff_seconds * attempt)
    raise RuntimeError(f"Could not fetch BCN RDF/JSON resource {url}: {last_error}")


class CachedRDFJsonFetcher:
    """Small cache wrapper so shared party/date resources are downloaded once."""

    def __init__(self, fetcher: Optional[RDFJsonFetcher] = None, **fetch_kwargs):
        self.fetcher = fetcher
        self.fetch_kwargs = fetch_kwargs
        self.cache: Dict[str, RDFJson] = {}

    def __call__(self, resource_url: str) -> RDFJson:
        key = canonical_resource_url(resource_url)
        if key not in self.cache:
            if self.fetcher:
                self.cache[key] = self.fetcher(key)
            else:
                self.cache[key] = fetch_rdf_json(key, **self.fetch_kwargs)
        return self.cache[key]


def _subject_variants(resource_url: str) -> Tuple[str, str]:
    url = canonical_resource_url(resource_url)
    if url.startswith("https://"):
        return url, "http://" + url[len("https://"):]
    if url.startswith("http://"):
        return url, "https://" + url[len("http://"):]
    return url, url


def rdf_subject(data: RDFJson, resource_url: Optional[str] = None) -> Dict[str, List[Dict[str, object]]]:
    """Return the subject property map for a resource, tolerating http/https variants."""
    if not data:
        return {}
    if resource_url:
        for subject in _subject_variants(resource_url):
            if subject in data:
                return data[subject]
    first_subject = next(iter(data.values()))
    return first_subject if isinstance(first_subject, dict) else {}


def rdf_values(props: Dict[str, List[Dict[str, object]]], predicate: str) -> List[Dict[str, object]]:
    """Return raw RDF/JSON values for a predicate."""
    values = props.get(predicate, [])
    return values if isinstance(values, list) else []


def first_rdf_value(props: Dict[str, List[Dict[str, object]]], *predicates: str) -> Optional[object]:
    """Return the first RDF/JSON value for any predicate."""
    for predicate in predicates:
        for value in rdf_values(props, predicate):
            if isinstance(value, dict) and "value" in value:
                return value["value"]
    return None


def rdf_uri_values(props: Dict[str, List[Dict[str, object]]], predicate: str) -> List[str]:
    """Return URI values for a predicate."""
    return [
        str(value["value"])
        for value in rdf_values(props, predicate)
        if isinstance(value, dict) and value.get("type") == "uri" and value.get("value")
    ]


def first_rdf_uri(props: Dict[str, List[Dict[str, object]]], *predicates: str) -> Optional[str]:
    """Return the first URI value for any predicate."""
    for predicate in predicates:
        values = rdf_uri_values(props, predicate)
        if values:
            return values[0]
    return None


def label_from_uri(uri: Optional[str]) -> Optional[str]:
    """Build a readable fallback label from a resource URI tail."""
    if not uri:
        return None
    tail = canonical_resource_url(uri).rsplit("/", 1)[-1]
    if not tail:
        return None
    return tail.replace("-", " ").replace("_", " ").strip().title()


def extract_date_resource(resource_url: Optional[str], fetcher: CachedRDFJsonFetcher) -> Optional[str]:
    """Fetch a linked date resource and return its original/date value."""
    if not resource_url:
        return None
    try:
        data = fetcher(resource_url)
    except RuntimeError:
        return None
    props = rdf_subject(data, resource_url)
    value = first_rdf_value(props, BCNBIO_ORIGINAL_DATE, DC_DATE)
    return str(value) if value is not None else None


def extract_party_name(party_href: Optional[str], fetcher: CachedRDFJsonFetcher) -> Optional[str]:
    """Fetch a political party label, falling back to the URI tail when absent."""
    if not party_href:
        return None
    try:
        data = fetcher(party_href)
    except RuntimeError:
        return label_from_uri(party_href)
    props = rdf_subject(data, party_href)
    value = first_rdf_value(props, FOAF_NAME, SKOS_PREF_LABEL, RDFS_LABEL)
    return str(value) if value is not None else label_from_uri(party_href)


def extract_birth_data(birth_href: Optional[str], fetcher: CachedRDFJsonFetcher) -> Dict[str, Optional[str]]:
    """Fetch and parse linked birth data."""
    output = {"birth_href": birth_href, "birth_date": None, "birth_place": None}
    if not birth_href:
        return output
    try:
        data = fetcher(birth_href)
    except RuntimeError:
        return output
    props = rdf_subject(data, birth_href)
    date_value = first_rdf_value(props, DC_DATE)
    place_value = first_rdf_value(props, BIO_PLACE)
    output["birth_date"] = str(date_value) if date_value is not None else None
    output["birth_place"] = str(place_value) if place_value is not None else None
    return output


def enrich_militancy_details(
    militancy: Dict[str, object],
    fetcher: CachedRDFJsonFetcher,
    *,
    fetch_dates: bool = False,
) -> Dict[str, object]:
    """Add party label and linked dates to a parsed militancy record."""
    output = dict(militancy)
    party_href = output.get("party_href")
    start_href = output.get("start_href")
    end_href = output.get("end_href")
    output["party"] = extract_party_name(str(party_href), fetcher) if party_href else None
    if fetch_dates:
        output["start_date"] = extract_date_resource(str(start_href), fetcher) if start_href else None
        output["end_date"] = extract_date_resource(str(end_href), fetcher) if end_href else None
    return output


def extract_militancy_data(
    militancy_href: str,
    fetcher: CachedRDFJsonFetcher,
    *,
    enrich: bool = False,
) -> Dict[str, object]:
    """Fetch and parse one BCN militancy resource."""
    output: Dict[str, object] = {
        "militancy_href": militancy_href,
        "party_href": None,
        "party": None,
        "start_href": None,
        "start_date": None,
        "end_href": None,
        "end_date": None,
        "is_current": None,
    }
    try:
        data = fetcher(militancy_href)
    except RuntimeError as exc:
        output["error"] = str(exc)
        return output

    props = rdf_subject(data, militancy_href)
    party_href = first_rdf_uri(props, BCNBIO_HAS_POLITICAL_PARTY)
    start_href = first_rdf_uri(props, BCNBIO_HAS_BEGINNING)
    end_href = first_rdf_uri(props, BCNBIO_HAS_END)

    output["party_href"] = party_href
    output["start_href"] = start_href
    output["end_href"] = end_href
    output["is_current"] = end_href is None
    if enrich:
        output = enrich_militancy_details(output, fetcher)
    return output


def parse_parliamentarian_data(
    person_href: str,
    person_data: RDFJson,
    fetcher: CachedRDFJsonFetcher,
    *,
    include_all_militancies: bool = False,
    fetch_militancy_dates: bool = False,
) -> Dict[str, object]:
    """Parse one person RDF/JSON graph and follow selected linked resources."""
    person_href = canonical_resource_url(person_href)
    props = rdf_subject(person_data, person_href)
    if not props:
        return {
            "person_href": person_href,
            "person_id": bcn_person_id(person_href),
            "data_status": "not_found",
        }

    nationality_href = first_rdf_uri(props, BCNBIO_NATIONALITY)
    birth_href = first_rdf_uri(props, BCNBIO_HAS_BORN)
    birth_data = extract_birth_data(birth_href, fetcher)
    militancy_hrefs = rdf_uri_values(props, BCNBIO_HAS_MILITANCY)
    militancies = [extract_militancy_data(href, fetcher) for href in militancy_hrefs]
    current_militancies = [item for item in militancies if item.get("is_current") is True]
    current = current_militancies[0] if current_militancies else (militancies[0] if militancies else {})
    if current:
        current = enrich_militancy_details(current, fetcher, fetch_dates=fetch_militancy_dates)
    if include_all_militancies:
        militancies = [
            current
            if item.get("militancy_href") == current.get("militancy_href")
            else enrich_militancy_details(item, fetcher, fetch_dates=fetch_militancy_dates)
            for item in militancies
        ]

    output: Dict[str, object] = {
        "person_href": person_href,
        "person_id": str(first_rdf_value(props, DC_IDENTIFIER) or bcn_person_id(person_href) or ""),
        "name": first_rdf_value(props, FOAF_NAME, SKOS_PREF_LABEL, RDFS_LABEL),
        "gender": first_rdf_value(props, FOAF_GENDER),
        "nationality": label_from_uri(nationality_href),
        "nationality_href": nationality_href,
        "birth_href": birth_data["birth_href"],
        "birth_date": birth_data["birth_date"],
        "birth_place": birth_data["birth_place"],
        "image_url": first_rdf_uri(props, FOAF_IMG, FOAF_DEPICTION),
        "thumbnail_url": first_rdf_uri(props, FOAF_THUMBNAIL),
        "current_militancy_href": current.get("militancy_href"),
        "current_party": current.get("party"),
        "current_party_href": current.get("party_href"),
        "current_militancy_start_date": current.get("start_date"),
        "current_militancy_end_date": current.get("end_date"),
        "has_current_militancy": bool(current_militancies),
        "militancy_count": len(militancies),
        "data_status": "ok",
    }
    if include_all_militancies:
        output["militancies"] = militancies
    return output


def fetch_parliamentarian_data(
    person_href: str,
    *,
    fetcher: Optional[RDFJsonFetcher] = None,
    include_all_militancies: bool = False,
    fetch_militancy_dates: bool = False,
    timeout: int = 60,
    max_attempts: int = 3,
    backoff_seconds: float = 2.0,
) -> Dict[str, object]:
    """Fetch BCN data for one parliamentarian/person resource."""
    if not is_bcn_person_url(person_href):
        return {
            "person_href": person_href,
            "person_id": None,
            "data_status": "not_bcn_person",
        }

    loader = CachedRDFJsonFetcher(
        fetcher,
        timeout=timeout,
        max_attempts=max_attempts,
        backoff_seconds=backoff_seconds,
    )
    person_url = canonical_resource_url(person_href)
    try:
        person_data = loader(person_url)
    except RuntimeError as exc:
        return {
            "person_href": person_url,
            "person_id": bcn_person_id(person_url),
            "data_status": "fetch_error",
            "error": str(exc),
        }
    return parse_parliamentarian_data(
        person_url,
        person_data,
        loader,
        include_all_militancies=include_all_militancies,
        fetch_militancy_dates=fetch_militancy_dates,
    )


def _parse_speech_value(value: object) -> Dict[str, object]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _iter_nested_dicts(value: object) -> Iterable[Dict[str, object]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _iter_nested_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_nested_dicts(child)


def _metadata_persons(speech_content: Dict[str, object]) -> Dict[str, Dict[str, object]]:
    metadata = speech_content.get("metadata", {})
    if not isinstance(metadata, dict):
        return {}
    persons = metadata.get("persons", {})
    if isinstance(persons, dict):
        return {str(key): value for key, value in persons.items() if isinstance(value, dict)}
    if isinstance(persons, list):
        return {
            str(value.get("id")): value
            for value in persons
            if isinstance(value, dict) and value.get("id")
        }
    return {}


def collect_bcn_speaker_references(
    df: pd.DataFrame,
    *,
    source_col: str = "speech_content",
    as_dataframe: bool = True,
) -> Union[pd.DataFrame, List[Dict[str, object]]]:
    """Collect unique BCN person references from participation items."""
    records: Dict[str, Dict[str, object]] = {}

    for row_index, value in df[source_col].items():
        speech_content = _parse_speech_value(value)
        if not speech_content or "error" in speech_content:
            continue
        persons = _metadata_persons(speech_content)
        document_title = df.at[row_index, "title"] if "title" in df.columns else None
        document_date = df.at[row_index, "date"] if "date" in df.columns else None

        for item in _iter_nested_dicts(speech_content.get("debate_body", {})):
            if item.get("kind") != "participation":
                continue
            speaker_id = item.get("speaker_id")
            metadata_entry = persons.get(str(speaker_id), {}) if speaker_id else {}
            speaker_href = item.get("speaker_href") or metadata_entry.get("href")
            if not is_bcn_person_url(speaker_href):
                continue

            speaker_href = canonical_resource_url(str(speaker_href))
            record = records.setdefault(
                speaker_href,
                {
                    "person_href": speaker_href,
                    "person_id": bcn_person_id(speaker_href),
                    "speaker_ids": set(),
                    "speaker_names_seen": set(),
                    "roles_seen": set(),
                    "participation_count": 0,
                    "document_count": 0,
                    "_documents": set(),
                    "first_row_index": row_index,
                    "first_title": document_title,
                    "first_date": document_date,
                },
            )
            if speaker_id:
                record["speaker_ids"].add(str(speaker_id))
            speaker_name = item.get("speaker") or metadata_entry.get("show_as")
            if speaker_name:
                record["speaker_names_seen"].add(str(speaker_name))
            role = item.get("role")
            if role:
                record["roles_seen"].add(str(role))
            record["participation_count"] += 1
            record["_documents"].add(row_index)
            record["document_count"] = len(record["_documents"])

    output: List[Dict[str, object]] = []
    for record in records.values():
        normalized = dict(record)
        normalized.pop("_documents", None)
        for key in ("speaker_ids", "speaker_names_seen", "roles_seen"):
            normalized[key] = sorted(normalized[key])
        output.append(normalized)

    output.sort(key=lambda item: (item.get("person_id") or "", item.get("person_href") or ""))
    if as_dataframe:
        return pd.DataFrame(output)
    return output


def build_parliamentarian_table(
    df: pd.DataFrame,
    *,
    source_col: str = "speech_content",
    fetcher: Optional[RDFJsonFetcher] = None,
    include_all_militancies: bool = False,
    fetch_militancy_dates: bool = False,
    timeout: int = 60,
    max_attempts: int = 3,
    backoff_seconds: float = 2.0,
) -> pd.DataFrame:
    """Build one row per BCN person who appears as a speech participant."""
    refs = collect_bcn_speaker_references(df, source_col=source_col, as_dataframe=False)
    loader = CachedRDFJsonFetcher(
        fetcher,
        timeout=timeout,
        max_attempts=max_attempts,
        backoff_seconds=backoff_seconds,
    )
    rows = []
    for ref in refs:
        person_href = ref["person_href"]
        try:
            person_data = loader(person_href)
            details = parse_parliamentarian_data(
                person_href,
                person_data,
                loader,
                include_all_militancies=include_all_militancies,
                fetch_militancy_dates=fetch_militancy_dates,
            )
        except RuntimeError as exc:
            details = {
                "person_href": person_href,
                "person_id": bcn_person_id(person_href),
                "data_status": "fetch_error",
                "error": str(exc),
            }
        rows.append({**ref, **details})
    return pd.DataFrame(rows)
