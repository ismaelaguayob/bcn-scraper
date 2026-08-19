"""Quality controls for manifest-driven parliamentary speech corpora."""

from __future__ import annotations

from typing import Iterable, Optional

import pandas as pd


REQUIRED_MANIFEST_COLUMNS = {
    "document_uri",
    "expected_title",
    "expected_date",
    "bill_number",
    "speech_source",
    "include_in_speech_pipeline",
}


def _has_value(value) -> bool:
    if value is None:
        return False
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    try:
        if pd.isna(value):
            return False
    except (TypeError, ValueError):
        pass
    return bool(str(value).strip())


def _missing_mask(series: pd.Series) -> pd.Series:
    return ~series.map(_has_value)


def _akn_status(value) -> str:
    if not _has_value(value):
        return "missing"
    text = str(value).lstrip()
    if text.upper().startswith("ERROR:"):
        return "error"
    if text.startswith("<"):
        return "valid_xml"
    return "invalid"


def _document_rows(df: Optional[pd.DataFrame], document_uri: str) -> pd.DataFrame:
    if df is None or "document_uri" not in df.columns:
        return pd.DataFrame()
    return df.loc[df["document_uri"].eq(document_uri)]


def _count_nonempty(df: pd.DataFrame, column: str) -> int:
    if df.empty or column not in df.columns:
        return 0
    return int(df[column].map(_has_value).sum())


def build_speech_quality_report(
    manifest: pd.DataFrame,
    source_df: pd.DataFrame,
    speech_df: pd.DataFrame,
    speech_df_full: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Build one quality-control row per document declared in ``manifest``.

    ``expected_pending`` is reserved for documents whose ``speech_source`` starts
    with ``pending_`` and intentionally have no flattened speech yet.
    """
    missing_columns = REQUIRED_MANIFEST_COLUMNS.difference(manifest.columns)
    if missing_columns:
        raise ValueError(f"Manifest columns missing: {sorted(missing_columns)}")
    if manifest["document_uri"].duplicated().any():
        raise ValueError("Manifest document_uri values must be unique")
    if "document_uri" not in source_df.columns:
        raise ValueError("source_df must contain document_uri")
    if source_df["document_uri"].dropna().duplicated().any():
        raise ValueError("source_df document_uri values must be unique")

    rows = []
    for expected in manifest.to_dict(orient="records"):
        document_uri = expected["document_uri"]
        source_rows = _document_rows(source_df, document_uri)
        speech_rows = _document_rows(speech_df, document_uri)
        full_rows = _document_rows(speech_df_full, document_uri)
        source = source_rows.iloc[0] if len(source_rows) == 1 else None

        source_present = source is not None
        title_matches = bool(
            source_present and str(source.get("title", "")) == str(expected["expected_title"])
        )
        date_matches = bool(
            source_present and str(source.get("date", "")) == str(expected["expected_date"])
        )
        source_xml_nonempty = bool(source_present and _has_value(source.get("xml_content")))
        source_text_nonempty = bool(source_present and _has_value(source.get("txt_content")))
        akn_status = _akn_status(source.get("akn_content")) if source_present else "missing"

        empty_content_rows = (
            int(_missing_mask(speech_rows["content"]).sum())
            if not speech_rows.empty and "content" in speech_rows.columns
            else 0
        )
        missing_date_rows = (
            int(_missing_mask(speech_rows["date"]).sum())
            if not speech_rows.empty and "date" in speech_rows.columns
            else 0
        )
        missing_uri_rows = (
            int(_missing_mask(speech_rows["document_uri"]).sum())
            if not speech_rows.empty
            else 0
        )
        unexpected_bill_rows = (
            int(speech_rows["bill_number"].ne(expected["bill_number"]).sum())
            if not speech_rows.empty and "bill_number" in speech_rows.columns
            else 0
        )
        duplicate_item_path_rows = (
            int(speech_rows.duplicated(["document_uri", "item_path"]).sum())
            if not speech_rows.empty and "item_path" in speech_rows.columns
            else 0
        )
        duplicate_row_index_rows = (
            int(speech_rows["row_index"].duplicated().sum())
            if not speech_rows.empty and "row_index" in speech_rows.columns
            else 0
        )
        duplicate_utterance_id_rows = (
            int(speech_rows["utterance_id"].duplicated().sum())
            if not speech_rows.empty and "utterance_id" in speech_rows.columns
            else 0
        )
        duplicate_utterance_order_rows = (
            int(speech_rows.duplicated(["document_uri", "utterance_order"]).sum())
            if (
                not speech_rows.empty
                and {"document_uri", "utterance_order"}.issubset(speech_rows.columns)
            )
            else 0
        )
        n_chars_mismatch_rows = (
            int(speech_rows["n_chars"].ne(speech_rows["content"].fillna("").str.len()).sum())
            if not speech_rows.empty and {"n_chars", "content"}.issubset(speech_rows.columns)
            else 0
        )

        unresolved_identity_rows = 0
        discussion_rows = 0
        analytical_voting_rows = 0
        voting_rows = 0
        identity_only_speaker_rows = 0
        missing_speaker_data_rows = 0
        participation_rows = 0
        analytical_transcription_event_rows = 0
        unstable_bcn_speaker_id_rows = 0
        local_primary_speaker_id_rows = 0
        if not speech_rows.empty:
            participation_mask = (
                speech_rows["kind"].eq("participation")
                if "kind" in speech_rows.columns
                else pd.Series(True, index=speech_rows.index)
            )
            participation_rows = int(participation_mask.sum())
            if "kind" in speech_rows.columns:
                analytical_transcription_event_rows = int(
                    speech_rows["kind"].eq("transcription_event").sum()
                )
            unresolved_identity = pd.Series(False, index=speech_rows.index)
            if "speaker" in speech_rows.columns:
                unresolved_identity |= _missing_mask(speech_rows["speaker"])
            if "speaker_id" in speech_rows.columns:
                unresolved_identity |= _missing_mask(speech_rows["speaker_id"])
            if "speaker_resolution_status" in speech_rows.columns:
                unresolved_identity |= speech_rows["speaker_resolution_status"].eq("regex")
            unresolved_identity_rows = int((unresolved_identity & participation_mask).sum())
            if "speaker_id" in speech_rows.columns:
                speaker_ids = speech_rows["speaker_id"].fillna("").astype(str)
                local_primary_speaker_id_rows = int(
                    (participation_mask & speaker_ids.str.match(r"^(?:per|PersonaAut)\d+$")).sum()
                )
            if {"speaker_href", "speaker_id"}.issubset(speech_rows.columns):
                href_ids = speech_rows["speaker_href"].fillna("").astype(str).str.extract(
                    r"/recurso/persona/(\d+)/?$",
                    expand=False,
                )
                bcn_mask = participation_mask & href_ids.notna()
                expected_ids = "PersonaBCN" + href_ids.fillna("")
                unstable_bcn_speaker_id_rows = int(
                    (bcn_mask & speech_rows["speaker_id"].ne(expected_ids)).sum()
                )
            if "section_name" in speech_rows.columns:
                discussion_rows = int(speech_rows["section_name"].eq("Discusion").sum())
                analytical_voting_rows = int(speech_rows["section_name"].eq("Votacion").sum())
            if "speaker_data_status" in speech_rows.columns:
                identity_only_speaker_rows = int(
                    speech_rows["speaker_data_status"].eq("identity_only").sum()
                )
                missing_speaker_data_rows = int(
                    speech_rows["speaker_data_status"].isin({"not_found", "missing_href"}).sum()
                )

        unresolved_content_rows = 0
        transcription_event_rows = 0
        overlap_event_rows = 0
        separator_event_rows = 0
        if not full_rows.empty:
            event_mask = pd.Series(False, index=full_rows.index)
            if "kind" in full_rows.columns:
                unresolved_content_rows = int(full_rows["kind"].eq("unlabeled_text").sum())
                event_mask = full_rows["kind"].eq("transcription_event")
                transcription_event_rows = int(event_mask.sum())
            if "section_name" in full_rows.columns:
                voting_rows = int(full_rows["section_name"].eq("Votacion").sum())
            event_text = full_rows.get("content", pd.Series("", index=full_rows.index)).fillna("")
            event_text = event_text.loc[event_mask]
            overlap_event_rows = int(
                event_text.str.contains(
                    r"hablan varios|interviene fuera de micr[oó]fono|se manifiestan",
                    case=False,
                    regex=True,
                ).sum()
            )
            separator_event_rows = int(
                event_text.str.fullmatch(r"\s*[-–—]\s*[o0]\s*[-–—]\s*\.?\s*", case=False).sum()
            )

        issues = []
        if not source_present:
            issues.append("source_missing")
        if source_present and not title_matches:
            issues.append("title_mismatch")
        if source_present and not date_matches:
            issues.append("date_mismatch")
        if source_present and not source_xml_nonempty:
            issues.append("xml_content_empty")
        if source_present and not source_text_nonempty:
            issues.append("txt_content_empty")

        include_speech = bool(expected["include_in_speech_pipeline"])
        expected_pending = str(expected["speech_source"]).startswith("pending_")
        if include_speech and not expected_pending:
            if str(expected["speech_source"]) == "akn" and akn_status != "valid_xml":
                issues.append(f"akn_{akn_status}")
            if speech_rows.empty:
                issues.append("speech_rows_empty")
            if speech_df_full is not None and len(full_rows) < len(speech_rows):
                issues.append("full_rows_below_speech_rows")
            if str(expected["speech_source"]) == "history_xml_fallback":
                if discussion_rows == 0:
                    issues.append("fallback_discussion_rows_empty")
                if voting_rows == 0:
                    issues.append("fallback_voting_rows_empty")
                if analytical_voting_rows:
                    issues.append(f"analytical_voting_rows={analytical_voting_rows}")
        elif include_speech and expected_pending and not speech_rows.empty:
            issues.append("pending_source_has_speech_rows")

        if empty_content_rows:
            issues.append(f"empty_content_rows={empty_content_rows}")
        if missing_date_rows:
            issues.append(f"missing_date_rows={missing_date_rows}")
        if missing_uri_rows:
            issues.append(f"missing_uri_rows={missing_uri_rows}")
        if unexpected_bill_rows:
            issues.append(f"unexpected_bill_rows={unexpected_bill_rows}")
        if duplicate_item_path_rows:
            issues.append(f"duplicate_item_path_rows={duplicate_item_path_rows}")
        if duplicate_row_index_rows:
            issues.append(f"duplicate_row_index_rows={duplicate_row_index_rows}")
        if duplicate_utterance_id_rows:
            issues.append(f"duplicate_utterance_id_rows={duplicate_utterance_id_rows}")
        if duplicate_utterance_order_rows:
            issues.append(f"duplicate_utterance_order_rows={duplicate_utterance_order_rows}")
        if n_chars_mismatch_rows:
            issues.append(f"n_chars_mismatch_rows={n_chars_mismatch_rows}")
        if unresolved_identity_rows:
            issues.append(f"unresolved_identity_rows={unresolved_identity_rows}")
        if unstable_bcn_speaker_id_rows:
            issues.append(f"unstable_bcn_speaker_id_rows={unstable_bcn_speaker_id_rows}")
        if local_primary_speaker_id_rows:
            issues.append(f"local_primary_speaker_id_rows={local_primary_speaker_id_rows}")

        warning_issues = []
        parse_warning_rows = _count_nonempty(full_rows, "parse_warning")
        if unresolved_content_rows:
            warning_issues.append(f"unresolved_content_rows={unresolved_content_rows}")
        if parse_warning_rows:
            warning_issues.append(f"parse_warning_rows={parse_warning_rows}")
        if missing_speaker_data_rows:
            warning_issues.append(f"missing_speaker_data_rows={missing_speaker_data_rows}")

        if issues:
            quality_status = "fail"
        elif include_speech and expected_pending:
            quality_status = "expected_pending"
        elif warning_issues:
            quality_status = "warning"
        else:
            quality_status = "pass"

        rows.append({
            "document_uri": document_uri,
            "expected_title": expected["expected_title"],
            "expected_date": expected["expected_date"],
            "bill_number": expected["bill_number"],
            "speech_source": expected["speech_source"],
            "quality_status": quality_status,
            "source_present": source_present,
            "title_matches": title_matches,
            "date_matches": date_matches,
            "source_xml_nonempty": source_xml_nonempty,
            "source_text_nonempty": source_text_nonempty,
            "akn_status": akn_status,
            "speech_rows": len(speech_rows),
            "participation_rows": participation_rows,
            "analytical_transcription_event_rows": analytical_transcription_event_rows,
            "full_rows": len(full_rows),
            "transcription_event_rows": transcription_event_rows,
            "overlap_event_rows": overlap_event_rows,
            "separator_event_rows": separator_event_rows,
            "empty_content_rows": empty_content_rows,
            "missing_date_rows": missing_date_rows,
            "missing_uri_rows": missing_uri_rows,
            "unexpected_bill_rows": unexpected_bill_rows,
            "duplicate_item_path_rows": duplicate_item_path_rows,
            "duplicate_row_index_rows": duplicate_row_index_rows,
            "duplicate_utterance_id_rows": duplicate_utterance_id_rows,
            "duplicate_utterance_order_rows": duplicate_utterance_order_rows,
            "n_chars_mismatch_rows": n_chars_mismatch_rows,
            "unresolved_identity_rows": unresolved_identity_rows,
            "unstable_bcn_speaker_id_rows": unstable_bcn_speaker_id_rows,
            "local_primary_speaker_id_rows": local_primary_speaker_id_rows,
            "unresolved_content_rows": unresolved_content_rows,
            "parse_warning_rows": parse_warning_rows,
            "discussion_rows": discussion_rows,
            "voting_rows": voting_rows,
            "analytical_voting_rows": analytical_voting_rows,
            "identity_only_speaker_rows": identity_only_speaker_rows,
            "missing_speaker_data_rows": missing_speaker_data_rows,
            "issues": issues,
            "warnings": warning_issues,
        })

    return pd.DataFrame(rows)


def validate_speech_quality_report(
    report: pd.DataFrame,
    speech_df: pd.DataFrame,
    *,
    allowed_statuses: Iterable[str] = ("pass", "warning", "expected_pending"),
) -> None:
    """Raise ``ValueError`` when a report or flattened output violates invariants."""
    allowed_statuses = set(allowed_statuses)
    invalid = report.loc[~report["quality_status"].isin(allowed_statuses)]
    if not invalid.empty:
        details = invalid[["document_uri", "quality_status", "issues"]].to_dict(orient="records")
        raise ValueError(f"Speech quality checks failed: {details}")

    if "document_uri" not in speech_df.columns:
        raise ValueError("speech_df must contain document_uri")
    if _missing_mask(speech_df["document_uri"]).any():
        raise ValueError("speech_df contains rows without document_uri")

    unexpected_documents = sorted(
        set(speech_df["document_uri"].dropna()).difference(report["document_uri"])
    )
    if unexpected_documents:
        raise ValueError(f"speech_df contains unexpected documents: {unexpected_documents}")

    if "content" in speech_df.columns and _missing_mask(speech_df["content"]).any():
        raise ValueError("speech_df contains empty content")
