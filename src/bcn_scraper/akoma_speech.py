"""Extract structured speech data from BCN Akoma Ntoso XML."""

from __future__ import annotations

import copy
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from typing import Dict, Iterable, List, Optional

from .akoma_ntoso import AKN_ERROR_PREFIX


PROJECT_SECTION_NAMES = {"ProyectoDeLey", "ProyectoDeResolucion", "TextoDebate"}
IGNORED_DEBATE_SECTION_NAMES = {
    "Actas",
    "AnexoSesion",
    "DocumentoAnexo",
    "DocumentoCuenta",
    "DocumentosDeLaCuenta",
    "OtrosDocumentosDeLaCuenta",
    "PeticionesDeOficio",
}
IGNORED_DEBATE_BODY_TAGS = {"prayers", "petitions", "adjournment"}
TEXT_TAGS = {"p", "summary"}
SPEECH_MARKER_RE = re.compile(
    r"^(?P<prefix>(?:El|La)\s+"
    r"(?:señor|señora|señorita|ministro|ministra|subsecretario|subsecretaria|"
    r"senador|senadora|diputado|diputada))\s+"
    r"(?P<body>.+?)\s*\.\s*-$",
    re.IGNORECASE,
)
PROCEDURAL_PROMPT_RE = re.compile(
    r"\b("
    r"tiene la palabra|"
    r"ofrezco la palabra|"
    r"ofrecemos la palabra|"
    r"le ofrecemos la palabra|"
    r"puede hacer uso de la palabra|"
    r"hasta por"
    r")\b",
    re.IGNORECASE,
)
TRANSCRIPTION_EVENT_RE = re.compile(
    r"^\s*(?:[-–—]\s*)?(?:\([^)]*\))?\s*"
    r"(?:[-–—]\s*)?"
    r".*\b(aplausos?|risas?|manifestaciones|murmullos|protestas)\b.*"
    r"(?:\.\s*)?(?:\))?\s*$",
    re.IGNORECASE,
)
VOTE_TOTAL_KEYS = {
    "totalVotosAFavor": "in_favor",
    "totalVotosEnContra": "against",
    "totalVotosSeAbstiene": "abstention",
}


def local_name(name: str) -> str:
    """Return an XML local name without namespace."""
    return name.rsplit("}", 1)[-1] if "}" in name else name


def clean_text(text: str) -> str:
    """Normalize XML text to a compact single-line string."""
    return re.sub(r"\s+", " ", text or "").strip()


def normalize_text_key(text: str) -> str:
    """Normalize text for fuzzy dictionary keys."""
    decomposed = unicodedata.normalize("NFKD", text or "")
    ascii_text = "".join(char for char in decomposed if not unicodedata.combining(char))
    ascii_text = re.sub(r"[^A-Za-z0-9]+", " ", ascii_text).strip().upper()
    return re.sub(r"\s+", " ", ascii_text)


def text_content(elem: ET.Element) -> str:
    """Return normalized text for an element and all descendants."""
    return clean_text(" ".join(elem.itertext()))


def attr(elem: ET.Element, name: str) -> str:
    """Read an attribute by local name, ignoring namespace prefixes."""
    if name in elem.attrib:
        return elem.attrib[name]
    for key, value in elem.attrib.items():
        if local_name(key) == name:
            return value
    return ""


def strip_ref(value: str) -> str:
    """Normalize AKN reference attributes such as '#per12' to 'per12'."""
    return (value or "").strip().lstrip("#")


def is_procedural_prompt(text: str) -> bool:
    """Return True for procedural paragraphs that introduce a next speaker."""
    return bool(PROCEDURAL_PROMPT_RE.search(text or ""))


def is_transcription_event(text: str) -> bool:
    """Return True for standalone transcription events such as applause."""
    return bool(TRANSCRIPTION_EVENT_RE.match(clean_text(text)))


def direct_children(elem: ET.Element) -> List[ET.Element]:
    """Return direct child elements."""
    return list(elem)


def direct_texts(elem: ET.Element, tags: Iterable[str] = TEXT_TAGS) -> List[str]:
    """Return non-empty text from direct children whose tag is in tags."""
    tag_set = set(tags)
    texts = []
    for child in direct_children(elem):
        if local_name(child.tag) in tag_set:
            text = text_content(child)
            if text:
                texts.append(text)
    return texts


def first_direct_text(elem: ET.Element, tag: str) -> str:
    """Return text from the first direct child with the given tag."""
    for child in direct_children(elem):
        if local_name(child.tag) == tag:
            return text_content(child)
    return ""


def first_descendant(root: ET.Element, tag: str) -> Optional[ET.Element]:
    """Return the first descendant with a local tag name."""
    for elem in root.iter():
        if local_name(elem.tag) == tag:
            return elem
    return None


def descendants_by_tag(root: ET.Element, tag: str) -> List[ET.Element]:
    """Return descendants with a local tag name."""
    return [elem for elem in root.iter() if local_name(elem.tag) == tag]


def reference_entry(elem: ET.Element, kind: str) -> Dict[str, str]:
    """Build a metadata reference entry."""
    entry = {
        "kind": kind,
        "id": attr(elem, "id"),
        "show_as": clean_text(attr(elem, "showAs")),
        "href": attr(elem, "href"),
    }
    name = attr(elem, "name")
    if name:
        entry["name"] = clean_text(name)
    return entry


def parse_akn_references(root: ET.Element) -> Dict[str, Dict[str, Dict[str, str]]]:
    """Extract TLC references from AKN metadata."""
    metadata = {
        "persons": {},
        "roles": {},
        "organizations": {},
        "references": {},
        "all": {},
    }
    kind_by_tag = {
        "TLCPerson": "person",
        "TLCRole": "role",
        "TLCOrganization": "organization",
        "TLCReference": "reference",
    }
    collection_by_kind = {
        "person": "persons",
        "role": "roles",
        "organization": "organizations",
        "reference": "references",
    }

    references = first_descendant(root, "references")
    if references is None:
        return metadata

    for elem in direct_children(references):
        tag = local_name(elem.tag)
        if tag not in kind_by_tag:
            continue
        kind = kind_by_tag[tag]
        entry = reference_entry(elem, kind)
        entry_id = entry["id"]
        if not entry_id:
            continue
        metadata[collection_by_kind[kind]][entry_id] = entry
        metadata["all"][entry_id] = entry
    return metadata


def resolve_metadata(metadata: Dict[str, Dict[str, Dict[str, str]]], ref: str) -> Dict[str, str]:
    """Resolve '#id' or 'id' against metadata."""
    return metadata.get("all", {}).get(strip_ref(ref), {})


def resolved_show_as(metadata: Dict[str, Dict[str, Dict[str, str]]], ref: str) -> str:
    """Return show_as/name for a reference when available."""
    entry = resolve_metadata(metadata, ref)
    return entry.get("show_as") or entry.get("name") or ""


def parse_cover_page(root: ET.Element) -> Dict[str, object]:
    """Extract coverPage text."""
    cover_page = first_descendant(root, "coverPage")
    if cover_page is None:
        return {"raw_text": "", "paragraphs": []}
    paragraphs = direct_texts(cover_page, tags={"p"})
    return {"raw_text": "\n".join(paragraphs), "paragraphs": paragraphs}


def parse_attendance(root: ET.Element, metadata: Dict[str, Dict[str, Dict[str, str]]]) -> Dict[str, object]:
    """Extract rollCall text and referenced people."""
    roll_call = first_descendant(root, "rollCall")
    if roll_call is None:
        return {"raw_text": "", "paragraphs": [], "people": []}

    paragraphs = direct_texts(roll_call, tags={"p"})
    people = []
    seen = set()
    for person in descendants_by_tag(roll_call, "person"):
        person_id = strip_ref(attr(person, "refersTo"))
        if not person_id or person_id in seen:
            continue
        seen.add(person_id)
        person_meta = resolve_metadata(metadata, person_id)
        people.append({
            "person_id": person_id,
            "person": person_meta.get("show_as") or text_content(person),
            "href": person_meta.get("href", ""),
            "text": text_content(person),
        })

    return {"raw_text": "\n".join(paragraphs), "paragraphs": paragraphs, "people": people}


def project_attributes(elem: ET.Element, metadata: Dict[str, Dict[str, Dict[str, str]]]) -> Dict[str, object]:
    """Extract and resolve BCN project/debate attributes."""
    fields = {
        "uriProyectoLey": "bill_uri",
        "uriTramiteConstitucional": "constitutional_stage",
        "uriTramiteReglamentario": "regulatory_stage",
        "uriResultadoDebate": "debate_result",
    }
    result = {}
    for xml_attr, key in fields.items():
        value = attr(elem, xml_attr)
        if not value:
            continue
        ref_id = strip_ref(value)
        result[key] = {
            "ref_id": ref_id,
            "raw": value,
            "show_as": resolved_show_as(metadata, ref_id),
            "href": resolve_metadata(metadata, ref_id).get("href", ""),
        }
    return result


def participation_item(
    elem: ET.Element,
    metadata: Dict[str, Dict[str, Dict[str, str]]],
    time_step: int,
) -> Dict[str, object]:
    """Extract a Participacion debateSection as an item."""
    speaker_id = strip_ref(attr(elem, "refersTo"))
    speaker_meta = resolve_metadata(metadata, speaker_id)
    type_id = strip_ref(attr(elem, "uriTipoParticipacion"))
    role_id = strip_ref(attr(elem, "uriRol"))

    return {
        "kind": "participation",
        "id": attr(elem, "id"),
        "time_step": time_step,
        "speaker_id": speaker_id or None,
        "speaker": speaker_meta.get("show_as") or None,
        "speaker_href": speaker_meta.get("href") or None,
        "type_id": type_id or None,
        "type": resolved_show_as(metadata, type_id) or None,
        "role_id": role_id or None,
        "role": resolved_show_as(metadata, role_id) or None,
        "content": direct_texts(elem),
    }


def unlabeled_text_item(paragraphs: List[str], time_step: int, item_id: str = "") -> Dict[str, object]:
    """Build an unlabeled text item from consecutive paragraphs."""
    return {
        "kind": "unlabeled_text",
        "id": item_id or None,
        "time_step": time_step,
        "speaker_id": None,
        "speaker": None,
        "type": None,
        "content": paragraphs,
    }


def votation_item(
    elem: ET.Element,
    metadata: Dict[str, Dict[str, Dict[str, str]]],
    time_step: int,
) -> Dict[str, object]:
    """Extract a Votacion debateSection as an item."""
    totals = {}
    for quantity in descendants_by_tag(elem, "quantity"):
        quantity_id = strip_ref(attr(quantity, "refersTo"))
        key = VOTE_TOTAL_KEYS.get(quantity_id, quantity_id)
        value = attr(quantity, "normalized") or text_content(quantity)
        try:
            totals[key] = int(value)
        except ValueError:
            totals[key] = value

    votes = []
    for vote in descendants_by_tag(elem, "vote"):
        person_id = strip_ref(attr(vote, "by"))
        choice_id = strip_ref(attr(vote, "choice"))
        person_meta = resolve_metadata(metadata, person_id)
        votes.append({
            "person_id": person_id or None,
            "person": person_meta.get("show_as") or None,
            "person_href": person_meta.get("href") or None,
            "choice_id": choice_id or None,
            "choice": resolved_show_as(metadata, choice_id) or None,
            "text": text_content(vote),
        })

    outcomes = [
        {
            "ref_id": strip_ref(attr(outcome, "refersTo")) or None,
            "outcome": resolved_show_as(metadata, attr(outcome, "refersTo")) or text_content(outcome),
            "text": text_content(outcome),
        }
        for outcome in descendants_by_tag(elem, "outcome")
    ]

    return {
        "kind": "votation",
        "id": attr(elem, "id"),
        "time_step": time_step,
        "content": direct_texts(elem, tags={"p", "summary"}),
        "totals": totals,
        "votes": votes,
        "outcomes": outcomes,
    }


def parse_ordered_items(
    elem: ET.Element,
    metadata: Dict[str, Dict[str, Dict[str, str]]],
) -> List[Dict[str, object]]:
    """Parse direct debate children into ordered items."""
    items: List[Dict[str, object]] = []
    pending_paragraphs: List[str] = []
    pending_id = ""
    time_step = 1

    def flush_unlabeled() -> None:
        nonlocal pending_paragraphs, pending_id, time_step
        if pending_paragraphs:
            items.append(unlabeled_text_item(pending_paragraphs, time_step, pending_id))
            time_step += 1
            pending_paragraphs = []
            pending_id = ""

    for child in direct_children(elem):
        tag = local_name(child.tag)
        if tag in {"heading", "num"}:
            continue
        if tag in TEXT_TAGS:
            text = text_content(child)
            if text:
                if not pending_id:
                    pending_id = attr(child, "id")
                pending_paragraphs.append(text)
            continue
        if tag != "debateSection":
            continue

        section_name = attr(child, "name")
        if section_name == "Antecedente":
            continue
        flush_unlabeled()
        if section_name == "Participacion":
            items.append(participation_item(child, metadata, time_step))
            time_step += 1
        elif section_name == "Votacion":
            items.append(votation_item(child, metadata, time_step))
            time_step += 1
        elif section_name in IGNORED_DEBATE_SECTION_NAMES or section_name == "Cuenta":
            continue
        else:
            nested_items = parse_ordered_items(child, metadata)
            if nested_items:
                items.append({
                    "kind": "section",
                    "id": attr(child, "id"),
                    "section_name": section_name,
                    "title": first_direct_text(child, "heading"),
                    "time_step": time_step,
                    "items": nested_items,
                })
                time_step += 1

    flush_unlabeled()
    return items


def is_project_section(elem: ET.Element) -> bool:
    """Return True if a debateSection should be parsed as a project/topic."""
    if local_name(elem.tag) != "debateSection":
        return False
    section_name = attr(elem, "name")
    return section_name in PROJECT_SECTION_NAMES or bool(attr(elem, "uriProyectoLey"))


def parse_background(elem: ET.Element) -> Dict[str, object]:
    """Extract Antecedente children as project background."""
    paragraphs = []
    for child in direct_children(elem):
        if local_name(child.tag) == "debateSection" and attr(child, "name") == "Antecedente":
            paragraphs.extend(direct_texts(child))
    return {"raw_text": "\n".join(paragraphs), "paragraphs": paragraphs}


def parse_project(
    elem: ET.Element,
    metadata: Dict[str, Dict[str, Dict[str, str]]],
) -> Dict[str, object]:
    """Parse a project/topic section under Orden del Dia/Tabla."""
    background = parse_background(elem)
    return {
        "id": attr(elem, "id"),
        "section_name": attr(elem, "name"),
        "title": first_direct_text(elem, "heading"),
        "attributes": project_attributes(elem, metadata),
        "background": background["raw_text"],
        "background_paragraphs": background["paragraphs"],
        "items": parse_ordered_items(elem, metadata),
    }


def parse_generic_debate_section(
    elem: ET.Element,
    metadata: Dict[str, Dict[str, Dict[str, str]]],
    *,
    kind: str,
    parent_id: str = "",
) -> Dict[str, object]:
    """Parse non-project debate sections such as TextoDebate or Incidente."""
    return {
        "id": attr(elem, "id"),
        "kind": kind,
        "section_name": attr(elem, "name"),
        "parent_id": parent_id or None,
        "title": first_direct_text(elem, "heading"),
        "items": parse_ordered_items(elem, metadata),
    }


def parse_point_of_order(
    elem: ET.Element,
    metadata: Dict[str, Dict[str, Dict[str, str]]],
) -> Dict[str, object]:
    """Parse pointOfOrder or debateSection name='Tabla'."""
    point = {
        "id": attr(elem, "id"),
        "kind": "point_of_order",
        "section_name": attr(elem, "name") or local_name(elem.tag),
        "title": first_direct_text(elem, "heading"),
        "projects": [],
        "incidents": [],
        "other_sections": [],
    }
    for child in direct_children(elem):
        if local_name(child.tag) != "debateSection":
            continue
        section_name = attr(child, "name")
        if is_project_section(child):
            point["projects"].append(parse_project(child, metadata))
        elif section_name == "Incidente":
            point["incidents"].append(parse_generic_debate_section(
                child,
                metadata,
                kind="incident",
                parent_id=point["id"],
            ))
        elif section_name not in IGNORED_DEBATE_SECTION_NAMES and section_name != "Cuenta":
            point["other_sections"].append(parse_generic_debate_section(
                child,
                metadata,
                kind="section",
                parent_id=point["id"],
            ))
    return point


def parse_address(
    elem: ET.Element,
    metadata: Dict[str, Dict[str, Dict[str, str]]],
) -> Dict[str, object]:
    """Parse legacy/random address sections without imposing a fixed schema."""
    sections = []
    for child in direct_children(elem):
        if local_name(child.tag) == "debateSection":
            section_name = attr(child, "name")
            if section_name in IGNORED_DEBATE_SECTION_NAMES or section_name == "Cuenta":
                continue
            sections.append(parse_generic_debate_section(child, metadata, kind=section_name or "section"))

    return {
        "id": attr(elem, "id"),
        "kind": "address",
        "title": first_direct_text(elem, "heading"),
        "items": parse_ordered_items(elem, metadata),
        "sections": sections,
    }


def parse_debate_body(root: ET.Element, metadata: Dict[str, Dict[str, Dict[str, str]]]) -> Dict[str, object]:
    """Extract relevant debate body structures."""
    debate_body = first_descendant(root, "debateBody")
    output = {
        "point_of_order": [],
        "other_debates": [],
        "incidents": [],
        "addresses": [],
    }
    if debate_body is None:
        return output

    for child in direct_children(debate_body):
        tag = local_name(child.tag)
        if tag in IGNORED_DEBATE_BODY_TAGS or tag == "rollCall":
            continue
        if tag == "pointOfOrder":
            output["point_of_order"].append(parse_point_of_order(child, metadata))
        elif tag == "address":
            output["addresses"].append(parse_address(child, metadata))
        elif tag == "debateSection":
            section_name = attr(child, "name")
            if section_name == "Cuenta":
                for nested in child.iter():
                    if nested is not child and local_name(nested.tag) == "debateSection" and attr(nested, "name") == "Tabla":
                        output["point_of_order"].append(parse_point_of_order(nested, metadata))
                continue
            if section_name == "Tabla":
                output["point_of_order"].append(parse_point_of_order(child, metadata))
            elif section_name == "TextoDebate":
                output["other_debates"].append(parse_generic_debate_section(child, metadata, kind="other_debate"))
            elif section_name == "Incidente":
                output["incidents"].append(parse_generic_debate_section(child, metadata, kind="incident"))
            elif section_name in IGNORED_DEBATE_SECTION_NAMES:
                continue
            elif is_project_section(child):
                output["point_of_order"].append({
                    "id": None,
                    "kind": "point_of_order",
                    "section_name": "implicit",
                    "title": "",
                    "projects": [parse_project(child, metadata)],
                    "incidents": [],
                    "other_sections": [],
                })
            else:
                output["other_debates"].append(parse_generic_debate_section(child, metadata, kind="other_debate"))
    return output


def public_metadata(metadata: Dict[str, Dict[str, Dict[str, str]]]) -> Dict[str, Dict[str, Dict[str, str]]]:
    """Return metadata without internal lookup indexes."""
    return {key: value for key, value in metadata.items() if key != "all"}


def resolve_public_metadata(metadata: Dict[str, Dict[str, Dict[str, str]]], ref: str) -> Dict[str, str]:
    """Resolve an id against public speech_content metadata."""
    ref_id = strip_ref(ref)
    for collection in ("persons", "roles", "organizations", "references"):
        entry = metadata.get(collection, {}).get(ref_id)
        if entry:
            return entry
    return {}


def is_missing_akn_content(value) -> bool:
    """Return True for empty/NA values commonly produced by pandas."""
    if value is None:
        return True
    try:
        if value != value:
            return True
    except TypeError:
        pass
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (bytes, bytearray)):
        return not bytes(value).strip()
    return False


def normalize_akn_content(value) -> Optional[str]:
    """Normalize supported AKN content values to text."""
    if is_missing_akn_content(value):
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("utf-8", errors="replace")
    return None


def detect_speech_marker(paragraph: str) -> Optional[Dict[str, str]]:
    """Detect a paragraph that starts a speech turn."""
    text = clean_text(paragraph)
    match = SPEECH_MARKER_RE.match(text)
    if not match:
        return None

    body = clean_text(match.group("body"))
    parentheticals = [clean_text(value) for value in re.findall(r"\(([^)]*)\)", body) if clean_text(value)]
    name_text = clean_text(re.sub(r"\([^)]*\)", "", body))
    name_text = clean_text(name_text.split(",", 1)[0])
    speaker_key = normalize_text_key(name_text)
    if not speaker_key:
        return None

    return {
        "marker": text,
        "speaker_key": speaker_key,
        "speaker_display": name_text,
        "role_from_marker": "; ".join(parentheticals),
        "prefix": clean_text(match.group("prefix")),
    }


class ExternalSpeakerRegistry:
    """Resolve or create metadata for speakers detected by regex."""

    def __init__(self, external_speakers: Optional[Dict[str, Dict[str, str]]] = None) -> None:
        self._speakers: Dict[str, Dict[str, str]] = {}
        self._next_id = 1
        for key, value in (external_speakers or {}).items():
            normalized_key = normalize_text_key(key)
            if not normalized_key:
                continue
            entry = dict(value or {})
            entry.setdefault("speaker_key", normalized_key)
            self._speakers[normalized_key] = entry

    def _next_external_id(self) -> str:
        used_ids = {entry.get("speaker_id") for entry in self._speakers.values()}
        while f"PersonaExt{self._next_id}" in used_ids:
            self._next_id += 1
        speaker_id = f"PersonaExt{self._next_id}"
        self._next_id += 1
        return speaker_id

    def resolve(
        self,
        marker: Dict[str, str],
        metadata: Optional[Dict[str, Dict[str, Dict[str, str]]]] = None,
    ) -> Dict[str, object]:
        """Resolve a marker to user-provided or generated speaker metadata."""
        speaker_key = marker["speaker_key"]
        entry = dict(self._speakers.get(speaker_key, {}))
        user_provided = bool(entry)
        if not entry:
            entry = {"speaker_key": speaker_key}

        metadata_entry = {}
        if entry.get("speaker_id") and metadata:
            metadata_entry = resolve_public_metadata(metadata, entry["speaker_id"])

        if not entry.get("speaker_id"):
            entry["speaker_id"] = self._next_external_id()
        if not entry.get("speaker"):
            entry["speaker"] = metadata_entry.get("show_as") or marker.get("speaker_display") or speaker_key
        if not entry.get("role") and marker.get("role_from_marker"):
            entry["role"] = marker["role_from_marker"]
        if not entry.get("role") and entry.get("role_id") and metadata:
            entry["role"] = resolve_public_metadata(metadata, entry["role_id"]).get("show_as", "")
        if not entry.get("speaker_href") and entry.get("href"):
            entry["speaker_href"] = entry["href"]
        if not entry.get("speaker_href") and metadata_entry.get("href"):
            entry["speaker_href"] = metadata_entry["href"]

        entry.setdefault("speaker_key", speaker_key)
        entry["speaker_resolution_status"] = "user_provided" if user_provided else "regex"
        if metadata_entry:
            entry["speaker_source"] = "akn_metadata"
        elif user_provided:
            entry["speaker_source"] = "manual"
        else:
            entry["speaker_source"] = "regex"
        self._speakers[speaker_key] = entry
        return entry


def external_participation_item(
    *,
    marker: Dict[str, str],
    speaker: Dict[str, object],
    content: List[str],
    raw_content: List[str],
    discarded_preamble: List[str],
    source_id: Optional[str],
) -> Dict[str, object]:
    """Build a participation item from unlabeled text."""
    return {
        "kind": "participation",
        "source_kind": "unlabeled_text",
        "id": source_id,
        "time_step": None,
        "speaker_id": speaker.get("speaker_id"),
        "speaker": speaker.get("speaker"),
        "speaker_href": speaker.get("speaker_href"),
        "speaker_key": speaker.get("speaker_key") or marker.get("speaker_key"),
        "speaker_marker": marker.get("marker"),
        "speaker_display": marker.get("speaker_display"),
        "type_id": None,
        "type": speaker.get("type") or "Intervención no etiquetada",
        "role_id": speaker.get("role_id"),
        "role": speaker.get("role"),
        "speaker_resolution_status": speaker.get("speaker_resolution_status"),
        "is_labeled": False,
        "content": content,
        "raw_content": raw_content,
        "discarded_preamble": discarded_preamble,
    }


def preamble_participation_item(
    *,
    content: List[str],
    source_id: Optional[str],
    marker: Optional[Dict[str, str]] = None,
    speaker: Optional[Dict[str, object]] = None,
) -> Dict[str, object]:
    """Build a procedural preamble as a specially tagged participation."""
    return {
        "kind": "participation",
        "source_kind": "preamble",
        "id": source_id,
        "time_step": None,
        "speaker_id": speaker.get("speaker_id") if speaker else None,
        "speaker": speaker.get("speaker") if speaker else None,
        "speaker_href": speaker.get("speaker_href") if speaker else None,
        "speaker_key": (speaker.get("speaker_key") if speaker else None) or (marker.get("speaker_key") if marker else None),
        "speaker_marker": marker.get("marker") if marker else None,
        "speaker_display": marker.get("speaker_display") if marker else None,
        "type_id": None,
        "type": "Preambulo procedimental",
        "role_id": speaker.get("role_id") if speaker else None,
        "role": speaker.get("role") if speaker else (marker.get("role_from_marker") if marker else None),
        "speaker_resolution_status": speaker.get("speaker_resolution_status") if speaker else None,
        "speaker_source": speaker.get("speaker_source") if speaker else None,
        "is_labeled": False,
        "is_preamble": True,
        "content": content,
        "raw_content": content,
        "discarded_preamble": [],
    }


def transcription_event_item(content: str, source_id: Optional[str]) -> Dict[str, object]:
    """Build a standalone transcription event item."""
    return {
        "kind": "transcription_event",
        "source_kind": "unlabeled_text",
        "id": source_id,
        "time_step": None,
        "type": "Transcription event",
        "content": [content],
    }


def interruption_participation_item(
    *,
    marker: Dict[str, str],
    speaker: Dict[str, object],
    content: List[str],
    source_id: Optional[str],
) -> Dict[str, object]:
    """Build an interruption item inside a labeled participation."""
    return {
        "kind": "participation",
        "source_kind": "interruption",
        "id": source_id,
        "time_step": None,
        "speaker_id": speaker.get("speaker_id"),
        "speaker": speaker.get("speaker"),
        "speaker_href": speaker.get("speaker_href"),
        "speaker_key": speaker.get("speaker_key") or marker.get("speaker_key"),
        "speaker_marker": marker.get("marker"),
        "speaker_display": marker.get("speaker_display"),
        "type_id": None,
        "type": "Interrupcion",
        "role_id": speaker.get("role_id"),
        "role": speaker.get("role"),
        "speaker_resolution_status": speaker.get("speaker_resolution_status"),
        "speaker_source": speaker.get("speaker_source"),
        "is_labeled": False,
        "is_interruption": True,
        "content": content,
        "raw_content": content,
        "discarded_preamble": [],
    }


def split_unlabeled_item(
    item: Dict[str, object],
    registry: ExternalSpeakerRegistry,
    metadata: Dict[str, Dict[str, Dict[str, str]]],
    split_transcription_events: bool,
) -> List[Dict[str, object]]:
    """Split one unlabeled_text item into speaker-level participation items."""
    paragraphs = [clean_text(paragraph) for paragraph in item.get("content", []) if clean_text(paragraph)]
    if not paragraphs:
        return [item]

    result: List[Dict[str, object]] = []
    current_marker = None
    current_speaker = None
    current_content: List[str] = []
    current_raw: List[str] = []
    current_procedural: List[str] = []
    pre_marker_preamble: List[str] = []
    last_marker = None
    last_speaker = None

    def flush_current() -> None:
        nonlocal current_marker, current_speaker, current_content, current_raw, current_procedural
        if current_marker and current_speaker:
            if current_content:
                raw_content = ([current_marker["marker"]] if current_raw else []) + current_procedural + current_content
                result.append(external_participation_item(
                    marker=current_marker,
                    speaker=current_speaker,
                    content=current_content,
                    raw_content=raw_content,
                    discarded_preamble=[],
                    source_id=item.get("id"),
                ))
            elif current_raw or current_procedural:
                result.append(preamble_participation_item(
                    marker=current_marker,
                    speaker=current_speaker,
                    content=current_raw + current_procedural,
                    source_id=item.get("id"),
                ))
        current_marker = None
        current_speaker = None
        current_content = []
        current_raw = []
        current_procedural = []

    def flush_pre_marker_preamble() -> None:
        nonlocal pre_marker_preamble
        if pre_marker_preamble:
            result.append(preamble_participation_item(
                content=pre_marker_preamble,
                source_id=item.get("id"),
            ))
            pre_marker_preamble = []

    for paragraph in paragraphs:
        marker = detect_speech_marker(paragraph)
        if marker:
            flush_current()
            flush_pre_marker_preamble()
            current_marker = marker
            current_speaker = registry.resolve(marker, metadata)
            current_raw = [paragraph]
            current_content = []
            current_procedural = []
            last_marker = current_marker
            last_speaker = current_speaker
            continue

        if split_transcription_events and is_transcription_event(paragraph):
            flush_current()
            flush_pre_marker_preamble()
            result.append(transcription_event_item(paragraph, item.get("id")))
            if last_marker and last_speaker:
                current_marker = last_marker
                current_speaker = last_speaker
                current_raw = []
                current_content = []
                current_procedural = []
            continue

        if current_marker:
            if is_procedural_prompt(paragraph):
                if current_content:
                    flush_current()
                    pre_marker_preamble.append(paragraph)
                else:
                    current_procedural.append(paragraph)
                continue
            current_content.append(paragraph)
            current_raw.append(paragraph)
        else:
            pre_marker_preamble.append(paragraph)

    flush_current()
    if not result:
        unresolved = dict(item)
        unresolved["speaker_resolution_status"] = "unresolved"
        return [unresolved]
    flush_pre_marker_preamble()
    return result


def speaker_marker_matches(marker: Dict[str, str], item: Dict[str, object]) -> bool:
    """Return True when a detected marker appears to name the participation speaker."""
    speaker = normalize_text_key(str(item.get("speaker") or ""))
    marker_key = marker.get("speaker_key", "")
    if not speaker or not marker_key:
        return False
    return marker_key in speaker


def clean_labeled_participation_item(
    item: Dict[str, object],
    registry: ExternalSpeakerRegistry,
    metadata: Dict[str, Dict[str, Dict[str, str]]],
    split_transcription_events: bool,
) -> List[Dict[str, object]]:
    """Split procedural preambles/events/interruptions from labeled participations."""
    content = [clean_text(paragraph) for paragraph in item.get("content", []) if clean_text(paragraph)]
    if not content:
        return [item]

    output: List[Dict[str, object]] = []
    current_mode = "main"
    current_segment: List[str] = []
    current_marker = None
    current_speaker = None
    current_speech_marker = None

    def append_main_segment(segment: List[str], speech_marker: Optional[str]) -> None:
        if not segment:
            return
        cleaned = dict(item)
        cleaned["content"] = segment
        cleaned["raw_content"] = content
        if speech_marker:
            cleaned["speech_marker"] = speech_marker
        cleaned.setdefault("discarded_preamble", [])
        cleaned["is_labeled"] = True
        output.append(cleaned)

    def flush_segment() -> None:
        nonlocal current_segment, current_mode, current_marker, current_speaker, current_speech_marker
        if not current_segment:
            current_mode = "main"
            current_marker = None
            current_speaker = None
            current_speech_marker = None
            return
        if current_mode == "main":
            append_main_segment(current_segment, current_speech_marker)
        else:
            has_procedural_prompt = any(is_procedural_prompt(paragraph) for paragraph in current_segment)
            if has_procedural_prompt:
                output.append(preamble_participation_item(
                    content=current_segment,
                    source_id=item.get("id"),
                    marker=current_marker,
                    speaker=current_speaker,
                ))
            else:
                output.append(interruption_participation_item(
                    content=current_segment,
                    source_id=item.get("id"),
                    marker=current_marker,
                    speaker=current_speaker or {},
                ))
        current_mode = "main"
        current_segment = []
        current_marker = None
        current_speaker = None
        current_speech_marker = None

    for paragraph in content:
        marker = detect_speech_marker(paragraph)
        if split_transcription_events and is_transcription_event(paragraph):
            flush_segment()
            output.append(transcription_event_item(paragraph, item.get("id")))
            continue

        if marker and speaker_marker_matches(marker, item):
            flush_segment()
            current_mode = "main"
            current_speech_marker = marker["marker"]
            continue

        if marker:
            flush_segment()
            current_mode = "interruption"
            current_marker = marker
            current_speaker = registry.resolve(marker, metadata)
            current_segment = [paragraph]
            continue

        current_segment.append(paragraph)

    flush_segment()

    return output or [item]


def normalize_items(
    items: List[Dict[str, object]],
    registry: ExternalSpeakerRegistry,
    metadata: Dict[str, Dict[str, Dict[str, str]]],
    *,
    split_unlabeled: bool,
    clean_labeled: bool,
    split_transcription_events: bool,
) -> List[Dict[str, object]]:
    """Normalize item lists recursively."""
    normalized: List[Dict[str, object]] = []
    for item in items:
        current_item = dict(item)
        if "items" in current_item and isinstance(current_item["items"], list):
            current_item["items"] = normalize_items(
                current_item["items"],
                registry,
                metadata,
                split_unlabeled=split_unlabeled,
                clean_labeled=clean_labeled,
                split_transcription_events=split_transcription_events,
            )

        if split_unlabeled and current_item.get("kind") == "unlabeled_text":
            normalized.extend(split_unlabeled_item(
                current_item,
                registry,
                metadata,
                split_transcription_events,
            ))
        elif (
            clean_labeled
            and current_item.get("kind") == "participation"
            and current_item.get("source_kind") not in {"unlabeled_text", "preamble"}
        ):
            normalized.extend(clean_labeled_participation_item(
                current_item,
                registry,
                metadata,
                split_transcription_events,
            ))
        else:
            if current_item.get("kind") == "participation" and "is_labeled" not in current_item:
                current_item["is_labeled"] = True
            normalized.append(current_item)

    for idx, item in enumerate(normalized, start=1):
        item["time_step"] = idx
    return normalized


def normalize_speech_dict(
    speech_content: Dict[str, object],
    registry: ExternalSpeakerRegistry,
    *,
    split_unlabeled: bool,
    clean_labeled: bool,
    split_transcription_events: bool,
) -> Dict[str, object]:
    """Normalize one speech_content dictionary."""
    result = copy.deepcopy(speech_content)
    if "error" in result:
        return result
    metadata = result.get("metadata", {})

    def visit(value):
        if isinstance(value, dict):
            if isinstance(value.get("items"), list):
                value["items"] = normalize_items(
                    value["items"],
                    registry,
                    metadata,
                    split_unlabeled=split_unlabeled,
                    clean_labeled=clean_labeled,
                    split_transcription_events=split_transcription_events,
                )
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(result)
    return result


def parse_speech_content_value(value) -> Dict[str, object]:
    """Return a speech_content dict from dict/JSON/missing values."""
    if isinstance(value, dict):
        return value
    if is_missing_akn_content(value):
        return {"error": "missing_speech_content"}
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as e:
            return {"error": "invalid_speech_content_json", "message": str(e)}
        if isinstance(parsed, dict):
            return parsed
        return {"error": "invalid_speech_content_type", "type": type(parsed).__name__}
    return {"error": "invalid_speech_content_type", "type": type(value).__name__}


def normalize_speech_content(
    df,
    *,
    source_col: str = "speech_content",
    output_col: str = "speech_content",
    external_speakers: Optional[Dict[str, Dict[str, str]]] = None,
    split_unlabeled: bool = True,
    clean_labeled: bool = True,
    split_transcription_events: bool = True,
    as_json: bool = False,
):
    """Normalize speech_content for analysis, including unlabeled speaker splits."""
    result = df.copy()
    registry = ExternalSpeakerRegistry(external_speakers)

    if source_col not in result.columns:
        result[output_col] = "" if as_json else None
        return result

    def convert(value):
        parsed = parse_speech_content_value(value)
        normalized = normalize_speech_dict(
            parsed,
            registry,
            split_unlabeled=split_unlabeled,
            clean_labeled=clean_labeled,
            split_transcription_events=split_transcription_events,
        )
        if as_json:
            return json.dumps(normalized, ensure_ascii=False)
        return normalized

    result[output_col] = result[source_col].map(convert)
    return result


def collect_unlabeled_speaker_candidates(
    df,
    *,
    source_col: str = "speech_content",
    external_speakers: Optional[Dict[str, Dict[str, str]]] = None,
    as_dataframe: bool = True,
):
    """Collect regex-detected unlabeled speakers that need manual metadata."""
    manual = {
        normalize_text_key(key): dict(value or {})
        for key, value in (external_speakers or {}).items()
        if normalize_text_key(key)
    }
    candidates: Dict[str, Dict[str, object]] = {}

    def add_candidate(marker: Dict[str, str], example: str, context: Dict[str, object]) -> None:
        speaker_key = marker["speaker_key"]
        entry = candidates.setdefault(speaker_key, {
            "speaker_key": speaker_key,
            "speaker_display": marker.get("speaker_display", ""),
            "role_from_marker": marker.get("role_from_marker", ""),
            "n_occurrences": 0,
            "examples": [],
            "documents": [],
        })
        entry["n_occurrences"] += 1
        if example and len(entry["examples"]) < 3:
            entry["examples"].append(example)
        document = {
            "row_index": context.get("row_index"),
            "title": context.get("title", ""),
            "date": context.get("date", ""),
            "akn_url": context.get("akn_url", ""),
            "xml_url": context.get("xml_url", ""),
        }
        if document not in entry["documents"] and len(entry["documents"]) < 5:
            entry["documents"].append(document)

    def visit(value, context: Dict[str, object]) -> None:
        if isinstance(value, dict):
            if value.get("kind") == "unlabeled_text":
                for paragraph in value.get("content", []):
                    marker = detect_speech_marker(paragraph)
                    if marker:
                        add_candidate(marker, clean_text(paragraph), context)
            elif value.get("kind") == "participation" and value.get("source_kind") == "unlabeled_text":
                marker = {
                    "speaker_key": value.get("speaker_key") or normalize_text_key(value.get("speaker", "")),
                    "speaker_display": value.get("speaker_display") or value.get("speaker", ""),
                    "role_from_marker": value.get("role") or "",
                }
                if marker["speaker_key"]:
                    add_candidate(marker, value.get("speaker_marker") or "", context)
            for child in value.values():
                visit(child, context)
        elif isinstance(value, list):
            for child in value:
                visit(child, context)

    if source_col not in df.columns:
        rows: List[Dict[str, object]] = []
    else:
        for row_index, row in df.iterrows():
            context = {
                "row_index": row_index,
                "title": row.get("title", ""),
                "date": row.get("date", ""),
                "akn_url": row.get("akn_url", ""),
                "xml_url": row.get("xml_url", ""),
            }
            visit(parse_speech_content_value(row[source_col]), context)
        rows = []
        for speaker_key, entry in sorted(candidates.items()):
            manual_entry = manual.get(speaker_key, {})
            missing_fields = [
                field
                for field in ("speaker", "speaker_id", "speaker_href", "role")
                if not manual_entry.get(field)
            ]
            rows.append({
                **entry,
                "first_row_index": entry["documents"][0]["row_index"] if entry["documents"] else None,
                "first_title": entry["documents"][0]["title"] if entry["documents"] else "",
                "first_date": entry["documents"][0]["date"] if entry["documents"] else "",
                "first_akn_url": entry["documents"][0]["akn_url"] if entry["documents"] else "",
                "first_xml_url": entry["documents"][0]["xml_url"] if entry["documents"] else "",
                "has_manual_entry": bool(manual_entry),
                "manual_speaker": manual_entry.get("speaker", ""),
                "manual_speaker_id": manual_entry.get("speaker_id", ""),
                "manual_speaker_href": manual_entry.get("speaker_href") or manual_entry.get("href", ""),
                "manual_role": manual_entry.get("role", ""),
                "missing_fields": missing_fields,
                "metadata_status": "complete" if manual_entry and not missing_fields else "incomplete",
            })

    if not as_dataframe:
        return rows

    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError("pandas is required for collect_unlabeled_speaker_candidates") from e
    return pd.DataFrame(rows)


def extract_speech_from_akn(akn_content: str) -> Dict[str, object]:
    """Convert a BCN AKN session XML string into structured speech data."""
    normalized_content = normalize_akn_content(akn_content)
    if normalized_content is None:
        return {"error": "missing_akn_content"}
    if normalized_content.startswith(AKN_ERROR_PREFIX):
        return {"error": "invalid_akn_content", "message": normalized_content}

    try:
        root = ET.fromstring(normalized_content)
    except ET.ParseError as e:
        return {"error": "invalid_xml", "message": str(e)}

    if local_name(root.tag) != "akomaNtoso":
        return {"error": "unexpected_root", "root": local_name(root.tag)}

    metadata = parse_akn_references(root)
    return {
        "session_information": parse_cover_page(root),
        "attendance": parse_attendance(root, metadata),
        "debate_body": parse_debate_body(root, metadata),
        "metadata": public_metadata(metadata),
    }


def add_speech_content(
    df,
    *,
    source_col: str = "akn_content",
    output_col: str = "speech_content",
    as_json: bool = False,
):
    """Return a copy of df with structured speech data extracted from AKN."""
    result = df.copy()
    if source_col not in result.columns:
        result[output_col] = "" if as_json else None
        return result

    def convert(value):
        extracted = extract_speech_from_akn(value)
        if as_json:
            return json.dumps(extracted, ensure_ascii=False)
        return extracted

    result[output_col] = result[source_col].map(convert)
    return result
