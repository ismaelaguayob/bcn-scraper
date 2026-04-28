"""Extract structured speech data from BCN Akoma Ntoso XML."""

from __future__ import annotations

import json
import re
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
    as_json: bool = True,
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
