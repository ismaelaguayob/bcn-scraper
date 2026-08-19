"""Flatten normalized AKN speech content into analysis DataFrames."""
from __future__ import annotations

import hashlib
import re
from typing import Dict, Iterable, List, Optional, Set

import pandas as pd

from .akoma_speech import parse_speech_content_value
from .parliamentary_data import bcn_person_id, is_bcn_person_url


DOCUMENT_COLUMNS = [
    "title",
    "date",
    "akn_url",
    "xml_url",
    "bcn_url",
    "document_uri",
]

PARLIAMENTARIAN_COLUMNS = [
    "person_id",
    "person_href",
    "name",
    "gender",
    "nationality",
    "birth_date",
    "birth_place",
    "image_url",
    "thumbnail_url",
    "current_party",
    "current_party_href",
    "current_militancy_href",
    "current_militancy_start_date",
    "current_militancy_end_date",
    "has_current_militancy",
    "militancy_count",
]


def _empty(value: object) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    if isinstance(value, str):
        return not value.strip()
    return False


def _as_paragraphs(value: object) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _join_paragraphs(paragraphs: List[str]) -> str:
    return "\n".join(paragraphs)


def _word_count(text: str) -> int:
    return len(re.findall(r"\S+", text or ""))


def _utterance_id(context: Dict[str, object], item_path: str) -> str:
    """Return a deterministic identifier for one source item.

    ``item_path`` is structural within the normalized document. Combining it
    with ``document_uri`` keeps the identifier equal across filtered views of
    the same corpus (for example, the analytical and audit outputs).
    """
    document_uri = context.get("document_uri")
    if _empty(document_uri):
        document_uri = f"source-row:{context.get('source_row_index')}"
    payload = f"{document_uri}\x1f{item_path}".encode("utf-8")
    return f"utt_{hashlib.sha256(payload).hexdigest()[:20]}"


def _speaker_identifiers(item: Dict[str, object]) -> Dict[str, Optional[str]]:
    """Separate the stable speaker identifier from the document-local one."""
    local_id = item.get("speaker_id")
    local_id = None if _empty(local_id) else str(local_id)
    person_id = bcn_person_id(item.get("speaker_href"))
    stable_id = f"PersonaBCN{person_id}" if person_id else local_id

    # The history fallback already receives a canonical PersonaBCN id from the
    # corpus registry. It is not an AKN-local id and must not be presented as one.
    if person_id and local_id == stable_id:
        local_id = None

    return {
        "speaker_id": stable_id,
        "speaker_bcn_id": person_id,
        "speaker_local_id": local_id,
    }


def _project_attr(project: Dict[str, object], key: str, field: str = "show_as") -> Optional[object]:
    attrs = project.get("attributes", {})
    if not isinstance(attrs, dict):
        return None
    value = attrs.get(key, {})
    if isinstance(value, dict):
        return value.get(field)
    return None


def _document_context(row_index: object, row: pd.Series) -> Dict[str, object]:
    context = {
        "source_row_index": row_index,
    }
    for column in DOCUMENT_COLUMNS:
        context[column] = row.get(column) if column in row.index else None
    return context


def _point_context(point: Dict[str, object]) -> Dict[str, object]:
    return {
        "point_of_order_id": point.get("id"),
        "point_of_order_title": point.get("title"),
    }


def _project_context(project: Dict[str, object]) -> Dict[str, object]:
    return {
        "section_kind": "project",
        "section_name": project.get("section_name"),
        "section_id": project.get("id"),
        "project_id": project.get("id"),
        "project_title": project.get("title"),
        "bill_ref": _project_attr(project, "bill_uri", "raw"),
        "bill_number": _project_attr(project, "bill_uri", "show_as"),
        "constitutional_stage": _project_attr(project, "constitutional_stage", "show_as"),
        "regulatory_stage": _project_attr(project, "regulatory_stage", "show_as"),
        "debate_result": _project_attr(project, "debate_result", "show_as"),
    }


def _section_context(section: Dict[str, object], *, fallback_kind: str = "section") -> Dict[str, object]:
    return {
        "section_kind": section.get("kind") or fallback_kind,
        "section_name": section.get("section_name"),
        "section_id": section.get("id"),
    }


def _content_status(item: Dict[str, object]) -> str:
    kind = item.get("kind")
    if kind == "unlabeled_text":
        return "unresolved"
    if kind == "transcription_event":
        return "transcription_event"
    if item.get("is_preamble"):
        return "preamble"
    if not _as_paragraphs(item.get("content")):
        return "empty"
    return "ok"


def _should_include_item(
    item: Dict[str, object],
    *,
    include_unresolved: bool,
    include_preambles: bool,
    include_transcription_events: bool,
) -> bool:
    kind = item.get("kind")
    if kind == "participation":
        if item.get("is_preamble") and not include_preambles:
            return False
        return True
    if kind == "unlabeled_text":
        return include_unresolved
    if kind == "transcription_event":
        return include_transcription_events
    return False


def _flatten_item(item: Dict[str, object], context: Dict[str, object], item_path: str, item_depth: int) -> Dict[str, object]:
    content_paragraphs = _as_paragraphs(item.get("content"))
    content = _join_paragraphs(content_paragraphs)
    raw_content_paragraphs = _as_paragraphs(item.get("raw_content"))
    discarded_preamble_paragraphs = _as_paragraphs(item.get("discarded_preamble"))
    raw_content = _join_paragraphs(raw_content_paragraphs) if raw_content_paragraphs else None
    discarded_preamble = (
        _join_paragraphs(discarded_preamble_paragraphs)
        if discarded_preamble_paragraphs
        else None
    )

    kind = item.get("kind")
    is_labeled = item.get("is_labeled")
    if kind == "participation" and is_labeled is None:
        is_labeled = True
    speaker_identifiers = _speaker_identifiers(item)

    return {
        **context,
        "participation_id": item.get("id"),
        "time_step": item.get("time_step"),
        "utterance_id": _utterance_id(context, item_path),
        "item_path": item_path,
        "item_depth": item_depth,
        "kind": kind,
        **speaker_identifiers,
        "speaker": item.get("speaker"),
        "speaker_href": item.get("speaker_href"),
        "role": item.get("role"),
        "participation_type": item.get("type"),
        "source_kind": item.get("source_kind") or ("labeled" if kind == "participation" else kind),
        "is_labeled": is_labeled,
        "is_interruption": bool(item.get("is_interruption")),
        "is_preamble": bool(item.get("is_preamble")),
        "speaker_resolution_status": item.get("speaker_resolution_status"),
        "speaker_source": item.get("speaker_source"),
        "content": content,
        "content_paragraphs": content_paragraphs,
        "n_paragraphs": len(content_paragraphs),
        "n_chars": len(content),
        "n_words": _word_count(content),
        "raw_content": raw_content,
        "raw_content_paragraphs": raw_content_paragraphs if raw_content_paragraphs else None,
        "speech_marker": item.get("speech_marker") or item.get("speaker_marker"),
        "discarded_preamble": discarded_preamble,
        "discarded_preamble_paragraphs": (
            discarded_preamble_paragraphs if discarded_preamble_paragraphs else None
        ),
        "parse_warning": item.get("parse_warning") or item.get("warning"),
        "has_raw_content": bool(raw_content_paragraphs),
        "has_discarded_preamble": bool(discarded_preamble_paragraphs),
        "content_status": _content_status(item),
    }


def _iter_items(
    items: Iterable[Dict[str, object]],
    context: Dict[str, object],
    path_prefix: str,
    *,
    include_unresolved: bool,
    include_preambles: bool,
    include_transcription_events: bool,
    item_depth: int = 0,
) -> Iterable[Dict[str, object]]:
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        item_path = f"{path_prefix}.items[{index}]"
        if item.get("kind") == "section":
            section_context = {**context, **_section_context(item)}
            yield from _iter_items(
                item.get("items", []),
                section_context,
                item_path,
                include_unresolved=include_unresolved,
                include_preambles=include_preambles,
                include_transcription_events=include_transcription_events,
                item_depth=item_depth + 1,
            )
            continue
        if _should_include_item(
            item,
            include_unresolved=include_unresolved,
            include_preambles=include_preambles,
            include_transcription_events=include_transcription_events,
        ):
            yield _flatten_item(item, context, item_path, item_depth)


def _iter_project_rows(
    project: Dict[str, object],
    context: Dict[str, object],
    path_prefix: str,
    *,
    include_unresolved: bool,
    include_preambles: bool,
    include_transcription_events: bool,
) -> Iterable[Dict[str, object]]:
    project_context = {**context, **_project_context(project)}
    yield from _iter_items(
        project.get("items", []),
        project_context,
        path_prefix,
        include_unresolved=include_unresolved,
        include_preambles=include_preambles,
        include_transcription_events=include_transcription_events,
    )


def _iter_section_rows(
    section: Dict[str, object],
    context: Dict[str, object],
    path_prefix: str,
    *,
    fallback_kind: str,
    include_unresolved: bool,
    include_preambles: bool,
    include_transcription_events: bool,
) -> Iterable[Dict[str, object]]:
    section_context = {**context, **_section_context(section, fallback_kind=fallback_kind)}
    yield from _iter_items(
        section.get("items", []),
        section_context,
        path_prefix,
        include_unresolved=include_unresolved,
        include_preambles=include_preambles,
        include_transcription_events=include_transcription_events,
    )
    for section_index, nested in enumerate(section.get("sections", [])):
        if isinstance(nested, dict):
            yield from _iter_section_rows(
                nested,
                section_context,
                f"{path_prefix}.sections[{section_index}]",
                fallback_kind=str(nested.get("kind") or "section"),
                include_unresolved=include_unresolved,
                include_preambles=include_preambles,
                include_transcription_events=include_transcription_events,
            )


def _iter_speech_content_rows(
    speech_content: Dict[str, object],
    context: Dict[str, object],
    *,
    include_unresolved: bool,
    include_preambles: bool,
    include_transcription_events: bool,
) -> Iterable[Dict[str, object]]:
    if not isinstance(speech_content, dict) or "error" in speech_content:
        return
    debate_body = speech_content.get("debate_body", {})
    if not isinstance(debate_body, dict):
        return

    for point_index, point in enumerate(debate_body.get("point_of_order", [])):
        if not isinstance(point, dict):
            continue
        point_context = {
            **context,
            **_point_context(point),
            "section_kind": point.get("kind") or "point_of_order",
            "section_name": point.get("section_name"),
            "section_id": point.get("id"),
        }
        point_path = f"debate_body.point_of_order[{point_index}]"
        for project_index, project in enumerate(point.get("projects", [])):
            if isinstance(project, dict):
                yield from _iter_project_rows(
                    project,
                    point_context,
                    f"{point_path}.projects[{project_index}]",
                    include_unresolved=include_unresolved,
                    include_preambles=include_preambles,
                    include_transcription_events=include_transcription_events,
                )
        for incident_index, incident in enumerate(point.get("incidents", [])):
            if isinstance(incident, dict):
                yield from _iter_section_rows(
                    incident,
                    point_context,
                    f"{point_path}.incidents[{incident_index}]",
                    fallback_kind="incident",
                    include_unresolved=include_unresolved,
                    include_preambles=include_preambles,
                    include_transcription_events=include_transcription_events,
                )
        for section_index, section in enumerate(point.get("other_sections", [])):
            if isinstance(section, dict):
                yield from _iter_section_rows(
                    section,
                    point_context,
                    f"{point_path}.other_sections[{section_index}]",
                    fallback_kind="section",
                    include_unresolved=include_unresolved,
                    include_preambles=include_preambles,
                    include_transcription_events=include_transcription_events,
                )

    for section_name in ("other_debates", "incidents"):
        for section_index, section in enumerate(debate_body.get(section_name, [])):
            if isinstance(section, dict):
                yield from _iter_section_rows(
                    section,
                    context,
                    f"debate_body.{section_name}[{section_index}]",
                    fallback_kind="incident" if section_name == "incidents" else "other_debate",
                    include_unresolved=include_unresolved,
                    include_preambles=include_preambles,
                    include_transcription_events=include_transcription_events,
                )

    for address_index, address in enumerate(debate_body.get("addresses", [])):
        if not isinstance(address, dict):
            continue
        address_context = {
            **context,
            "section_kind": "address",
            "section_name": address.get("section_name"),
            "section_id": address.get("id"),
        }
        address_path = f"debate_body.addresses[{address_index}]"
        yield from _iter_items(
            address.get("items", []),
            address_context,
            address_path,
            include_unresolved=include_unresolved,
            include_preambles=include_preambles,
            include_transcription_events=include_transcription_events,
        )
        for section_index, section in enumerate(address.get("sections", [])):
            if isinstance(section, dict):
                yield from _iter_section_rows(
                    section,
                    address_context,
                    f"{address_path}.sections[{section_index}]",
                    fallback_kind=str(section.get("kind") or "section"),
                    include_unresolved=include_unresolved,
                    include_preambles=include_preambles,
                    include_transcription_events=include_transcription_events,
                )


def flatten_speech_content(
    df: pd.DataFrame,
    *,
    source_col: str = "speech_content",
    include_unresolved: bool = False,
    include_preambles: bool = False,
    include_transcription_events: bool = False,
) -> pd.DataFrame:
    """Flatten normalized speech_content into one row per relevant item."""
    if source_col not in df.columns:
        return pd.DataFrame()

    rows: List[Dict[str, object]] = []
    for source_row_index, row in df.iterrows():
        speech_content = parse_speech_content_value(row[source_col])
        context = _document_context(source_row_index, row)
        rows.extend(_iter_speech_content_rows(
            speech_content,
            context,
            include_unresolved=include_unresolved,
            include_preambles=include_preambles,
            include_transcription_events=include_transcription_events,
        ))

    result = pd.DataFrame(rows)
    if result.empty:
        return result
    result.insert(0, "row_index", range(len(result)))
    return result


def _prepare_parliamentarians(parliamentarians: pd.DataFrame) -> pd.DataFrame:
    if parliamentarians is None or parliamentarians.empty or "person_href" not in parliamentarians.columns:
        return pd.DataFrame(columns=["person_href", *PARLIAMENTARIAN_COLUMNS, "speaker_data_status"])
    columns = [column for column in PARLIAMENTARIAN_COLUMNS if column in parliamentarians.columns]
    prepared = parliamentarians[columns + (["data_status"] if "data_status" in parliamentarians.columns else [])].copy()
    prepared = prepared.drop_duplicates(subset=["person_href"], keep="first")
    if "data_status" in prepared.columns:
        prepared = prepared.rename(columns={"data_status": "speaker_data_status"})
    else:
        prepared["speaker_data_status"] = "ok"
    return prepared


def _fill_speaker_data_status(df: pd.DataFrame, *, has_parliamentarians: bool) -> pd.Series:
    statuses = []
    for _, row in df.iterrows():
        kind = row.get("kind")
        href = row.get("speaker_href")
        current_status = row.get("speaker_data_status")
        if kind == "transcription_event":
            statuses.append("not_applicable")
        elif not has_parliamentarians:
            statuses.append("not_merged")
        elif _empty(href):
            statuses.append("missing_href")
        elif not is_bcn_person_url(href):
            statuses.append("not_bcn_person")
        elif _empty(current_status):
            statuses.append("not_found")
        else:
            statuses.append(current_status)
    return pd.Series(statuses, index=df.index)


def _add_speaker_local_history(
    df: pd.DataFrame,
    identity_audit: Optional[pd.DataFrame],
) -> pd.DataFrame:
    """Attach every known local id, retaining its document-qualified form.

    Local AKN identifiers are only unique inside one document. The plain array
    is convenient for inspection, while ``speaker_local_refs`` is the
    unambiguous representation used for provenance.
    """
    result = df.copy()
    ids_by_speaker: Dict[str, Set[str]] = {}
    refs_by_speaker: Dict[str, Set[str]] = {}

    def add(stable_id: object, local_id: object, document_uri: object) -> None:
        if _empty(stable_id) or _empty(local_id):
            return
        stable_text = str(stable_id)
        local_text = str(local_id)
        ids_by_speaker.setdefault(stable_text, set()).add(local_text)
        if not _empty(document_uri):
            refs_by_speaker.setdefault(stable_text, set()).add(
                f"{document_uri}#{local_text}"
            )

    required_audit_columns = {"document_uri", "local_speaker_id", "speaker_href"}
    if identity_audit is not None and required_audit_columns.issubset(identity_audit.columns):
        for audit_row in identity_audit.to_dict(orient="records"):
            person_id = bcn_person_id(audit_row.get("speaker_href"))
            if person_id:
                add(
                    f"PersonaBCN{person_id}",
                    audit_row.get("local_speaker_id"),
                    audit_row.get("document_uri"),
                )

    for observed in result.to_dict(orient="records"):
        add(
            observed.get("speaker_id"),
            observed.get("speaker_local_id"),
            observed.get("document_uri"),
        )

    result["speaker_local_ids"] = result["speaker_id"].map(
        lambda stable_id: sorted(ids_by_speaker.get(str(stable_id), set()))
        if not _empty(stable_id)
        else []
    )
    result["speaker_local_refs"] = result["speaker_id"].map(
        lambda stable_id: sorted(refs_by_speaker.get(str(stable_id), set()))
        if not _empty(stable_id)
        else []
    )
    return result


def build_speech_analysis_dataframe(
    df: pd.DataFrame,
    *,
    parliamentarians: Optional[pd.DataFrame] = None,
    identity_audit: Optional[pd.DataFrame] = None,
    source_col: str = "speech_content",
    include_unresolved: bool = False,
    include_preambles: bool = False,
    include_transcription_events: bool = False,
) -> pd.DataFrame:
    """Flatten speech content and optionally merge BCN identity data.

    ``speaker_id`` is stable across documents: BCN people use
    ``PersonaBCN<person_id>`` and actors external to BCN retain their project
    registry id. ``speaker_local_id`` preserves the id from the current source,
    while ``speaker_local_ids`` and ``speaker_local_refs`` record its corpus
    history when ``identity_audit`` is supplied.
    """
    flat = flatten_speech_content(
        df,
        source_col=source_col,
        include_unresolved=include_unresolved,
        include_preambles=include_preambles,
        include_transcription_events=include_transcription_events,
    )
    if flat.empty:
        return flat

    has_parliamentarians = parliamentarians is not None and not parliamentarians.empty
    if has_parliamentarians:
        prepared = _prepare_parliamentarians(parliamentarians)
        result = flat.merge(
            prepared,
            how="left",
            left_on="speaker_href",
            right_on="person_href",
            suffixes=("", "_parliamentarian"),
        )
    else:
        result = flat.copy()
        for column in PARLIAMENTARIAN_COLUMNS:
            if column not in result.columns:
                result[column] = None
        result["speaker_data_status"] = None

    result["speaker_data_status"] = _fill_speaker_data_status(
        result,
        has_parliamentarians=has_parliamentarians,
    )
    for column in PARLIAMENTARIAN_COLUMNS:
        if column not in result.columns:
            result[column] = None
    return _add_speaker_local_history(result, identity_audit)
