"""Fallback speech extraction from BCN Historia de la Ley HTML fragments."""

from __future__ import annotations

import json
import re
from typing import Dict, Iterable, Optional

from bs4 import BeautifulSoup

from .akoma_speech import clean_text, is_missing_akn_content, unlabeled_text_item


DISCUSSION_CLOSE_RE = re.compile(r"^cerrado el debate\.?$", re.IGNORECASE)
BILL_NUMBER_RE = re.compile(r"\b(?:bolet[ií]n\s*(?:n[°ºo]\s*)?)?(\d{4,6}-\d{2})\b", re.IGNORECASE)
STAGE_RE = re.compile(r"\(([^()]*(?:tr[aá]mite constitucional)[^()]*)\.", re.IGNORECASE)


def _attribute(value: str, *, show_as: str = "", href: str = "") -> Dict[str, str]:
    return {
        "ref_id": value,
        "raw": value,
        "show_as": show_as,
        "href": href,
    }


def _title_case_stage(value: str) -> str:
    normalized = clean_text(value).lower()
    return " ".join(word.capitalize() for word in normalized.split())


def _history_paragraphs(container) -> list[str]:
    return [
        clean_text(paragraph.get_text(" ", strip=True))
        for paragraph in container.find_all("p")
        if clean_text(paragraph.get_text(" ", strip=True))
    ]


def _split_background(paragraphs: list[str]) -> tuple[list[str], list[str]]:
    """Remove the short ``Antecedentes`` block from discursive paragraphs."""
    output = []
    background = []
    in_background = False
    for paragraph in paragraphs:
        if paragraph.rstrip(":").casefold() == "antecedentes":
            in_background = True
            background.append(paragraph)
            continue
        if in_background:
            if paragraph.startswith(("-", "–", "—")):
                background.append(paragraph)
                continue
            in_background = False
        output.append(paragraph)
    return output, background


def _phase_section(
    *,
    phase_name: str,
    title: str,
    section_id: str,
    paragraphs: Iterable[str],
) -> Optional[Dict[str, object]]:
    content = [clean_text(value) for value in paragraphs if clean_text(value)]
    if not content:
        return None
    return {
        "kind": "section",
        "id": section_id,
        "section_name": phase_name,
        "title": title,
        "source_kind": "history_xml_fallback",
        "items": [unlabeled_text_item(content, 1, f"{section_id}-text")],
    }


def extract_speech_from_history_xml(
    xml_content: str,
    *,
    person_registry: Optional[Dict[str, Dict[str, str]]] = None,
) -> Dict[str, object]:
    """Convert one Historia de la Ley HTML/XML item to the AKN speech schema.

    Historia fragments do not preserve AKN participation tags.  This fallback
    recovers the project and splits its ordered paragraphs into ``Discusion`` and
    ``Votacion`` at the explicit ``Cerrado el debate`` marker.  Speaker-level
    normalization is intentionally delegated to ``normalize_speech_content``.
    """
    if is_missing_akn_content(xml_content):
        return {"error": "missing_history_xml_content"}

    soup = BeautifulSoup(str(xml_content), "html.parser")
    item = soup.find("div", class_="item") or soup.find("div")
    if item is None:
        return {"error": "missing_history_item"}

    heading = item.find("h2")
    expected_title = clean_text(heading.get_text(" ", strip=True)) if heading else ""
    subheading_node = item.find("p", class_="sub-headding")
    subheading = clean_text(subheading_node.get_text(" ", strip=True)) if subheading_node else ""
    content_container = next(
        (
            child
            for child in item.find_all("span", recursive=False)
            if "person" not in (child.get("class") or [])
        ),
        item,
    )
    paragraphs = _history_paragraphs(content_container)
    if not paragraphs:
        return {"error": "history_item_without_paragraphs"}

    project_title = paragraphs.pop(0)
    discussion_close = next(
        (index for index, paragraph in enumerate(paragraphs) if DISCUSSION_CLOSE_RE.match(paragraph)),
        None,
    )
    if discussion_close is None:
        discussion_paragraphs = paragraphs
        voting_paragraphs: list[str] = []
        parse_warnings = ["discussion_close_not_found"]
    else:
        discussion_paragraphs = paragraphs[: discussion_close + 1]
        voting_paragraphs = paragraphs[discussion_close + 1 :]
        parse_warnings = []

    discussion_paragraphs, background_paragraphs = _split_background(discussion_paragraphs)

    document_uri = clean_text(item.get("uridocumento") or "")
    part_uri = clean_text(item.get("partedocumento") or "")
    section_id = part_uri.rstrip("/").rsplit("/", 1)[-1] if part_uri else "history-project"
    tramitacion_uri = clean_text(item.get("tramitacion") or "")
    bill_match = BILL_NUMBER_RE.search(project_title) or BILL_NUMBER_RE.search(tramitacion_uri)
    bill_number = bill_match.group(1) if bill_match else ""
    stage_match = STAGE_RE.search(project_title)
    constitutional_stage = _title_case_stage(stage_match.group(1)) if stage_match else ""

    regulatory_stage = "Discusión Única" if "discusión única" in subheading.casefold() else ""
    debate_result = "Se aprueban modificaciones" if "se aprueban modificaciones" in subheading.casefold() else ""

    phase_sections = [
        _phase_section(
            phase_name="Discusion",
            title="Discusión",
            section_id=f"{section_id}-discusion",
            paragraphs=discussion_paragraphs,
        ),
        _phase_section(
            phase_name="Votacion",
            title="Votación",
            section_id=f"{section_id}-votacion",
            paragraphs=voting_paragraphs,
        ),
    ]

    project = {
        "id": section_id,
        "section_name": "ProyectoDeLey",
        "title": project_title,
        "attributes": {
            "bill_uri": _attribute(
                tramitacion_uri or bill_number,
                show_as=bill_number,
                href=tramitacion_uri,
            ),
            "constitutional_stage": _attribute(
                constitutional_stage,
                show_as=constitutional_stage,
            ),
            "regulatory_stage": _attribute(
                regulatory_stage,
                show_as=regulatory_stage,
            ),
            "debate_result": _attribute(
                debate_result,
                show_as=debate_result,
            ),
        },
        "background": "\n".join(background_paragraphs),
        "background_paragraphs": background_paragraphs,
        "items": [section for section in phase_sections if section],
        "source_kind": "history_xml_fallback",
        "source_part_uri": part_uri,
        "parse_warnings": parse_warnings,
    }

    return {
        "session_information": {
            "raw_text": subheading,
            "paragraphs": [subheading] if subheading else [],
        },
        "attendance": {"raw_text": "", "paragraphs": [], "people": []},
        "debate_body": {
            "point_of_order": [{
                "id": f"{section_id}-orden-del-dia",
                "kind": "point_of_order",
                "section_name": "OrdenDelDia",
                "title": "ORDEN DEL DÍA",
                "projects": [project],
                "incidents": [],
                "other_sections": [],
                "source_kind": "history_xml_fallback",
            }],
            "other_debates": [],
            "incidents": [],
            "addresses": [],
        },
        "metadata": {
            "persons": dict(person_registry or {}),
            "roles": {},
            "organizations": {},
            "references": {},
        },
        "source_information": {
            "source_kind": "history_xml_fallback",
            "document_uri": document_uri,
            "part_uri": part_uri,
            "expected_title": expected_title,
            "parse_warnings": parse_warnings,
        },
    }


def add_history_speech_content(
    df,
    *,
    source_col: str = "xml_content",
    output_col: str = "speech_content",
    person_registry: Optional[Dict[str, Dict[str, str]]] = None,
    as_json: bool = False,
):
    """Return a copy with Historia XML fallback content parsed as speech."""
    result = df.copy()
    if source_col not in result.columns:
        result[output_col] = "" if as_json else None
        return result

    def convert(value):
        extracted = extract_speech_from_history_xml(value, person_registry=person_registry)
        return json.dumps(extracted, ensure_ascii=False) if as_json else extracted

    result[output_col] = result[source_col].map(convert)
    return result
