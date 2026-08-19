import pandas as pd
import pytest

from bcn_scraper.speech_quality import (
    build_speech_quality_report,
    validate_speech_quality_report,
)


def manifest_df():
    return pd.DataFrame([
        {
            "document_uri": "doc:message",
            "expected_title": "1.1. Mensaje",
            "expected_date": "2022-11-07",
            "bill_number": "15480-13",
            "speech_source": "history_xml",
            "include_in_speech_pipeline": False,
        },
        {
            "document_uri": "doc:sala",
            "expected_title": "1.2. Discusión en Sala",
            "expected_date": "2024-01-23",
            "bill_number": "15480-13",
            "speech_source": "akn",
            "include_in_speech_pipeline": True,
        },
        {
            "document_uri": "doc:pending",
            "expected_title": "3.1. Discusión en Sala",
            "expected_date": "2025-01-29",
            "bill_number": "15480-13",
            "speech_source": "pending_history_xml_fallback",
            "include_in_speech_pipeline": True,
        },
    ])


def source_df():
    return pd.DataFrame([
        {
            "document_uri": "doc:message",
            "title": "1.1. Mensaje",
            "date": "2022-11-07",
            "xml_content": "<div>Mensaje</div>",
            "txt_content": "Mensaje",
            "akn_content": "",
        },
        {
            "document_uri": "doc:sala",
            "title": "1.2. Discusión en Sala",
            "date": "2024-01-23",
            "xml_content": "<div>Sesión</div>",
            "txt_content": "Sesión",
            "akn_content": "<akomaNtoso/>",
        },
        {
            "document_uri": "doc:pending",
            "title": "3.1. Discusión en Sala",
            "date": "2025-01-29",
            "xml_content": "<div>Sesión</div>",
            "txt_content": "Sesión",
            "akn_content": "ERROR: HTTP 500",
        },
    ])


def speech_df():
    return pd.DataFrame([{
        "document_uri": "doc:sala",
        "date": "2024-01-23",
        "bill_number": "15480-13",
        "kind": "participation",
        "speaker": "Ana Pérez",
        "speaker_id": "PersonaBCN1",
        "speaker_resolution_status": "akn_unique",
        "content": "Intervención.",
    }])


def test_build_speech_quality_report_tracks_pass_and_expected_pending():
    speech = speech_df()
    full = pd.concat([
        speech,
        pd.DataFrame([{
            "document_uri": "doc:sala",
            "date": "2024-01-23",
            "bill_number": "15480-13",
            "kind": "transcription_event",
            "content": "(Hablan varios diputados a la vez)",
        }]),
    ], ignore_index=True)

    report = build_speech_quality_report(manifest_df(), source_df(), speech, full)
    rows = report.set_index("document_uri")

    assert rows.loc["doc:message", "quality_status"] == "pass"
    assert rows.loc["doc:sala", "quality_status"] == "pass"
    assert rows.loc["doc:sala", "speech_rows"] == 1
    assert rows.loc["doc:sala", "full_rows"] == 2
    assert rows.loc["doc:sala", "overlap_event_rows"] == 1
    assert rows.loc["doc:pending", "quality_status"] == "expected_pending"
    assert rows.loc["doc:pending", "akn_status"] == "error"

    validate_speech_quality_report(report, speech)


def test_build_speech_quality_report_fails_unexpected_bill_and_regex_identity():
    speech = speech_df()
    speech.loc[0, "bill_number"] = "otro"
    speech.loc[0, "speaker_resolution_status"] = "regex"

    report = build_speech_quality_report(manifest_df(), source_df(), speech, speech)
    row = report.loc[report["document_uri"].eq("doc:sala")].iloc[0]

    assert row["quality_status"] == "fail"
    assert "unexpected_bill_rows=1" in row["issues"]
    assert "unresolved_identity_rows=1" in row["issues"]
    with pytest.raises(ValueError, match="Speech quality checks failed"):
        validate_speech_quality_report(report, speech)


def test_transcription_events_do_not_require_speaker_identity():
    speech = pd.concat([
        speech_df(),
        pd.DataFrame([{
            "document_uri": "doc:sala",
            "date": "2024-01-23",
            "bill_number": "15480-13",
            "kind": "transcription_event",
            "speaker": None,
            "speaker_id": None,
            "content": "(Aplausos en las tribunas).",
        }]),
    ], ignore_index=True)

    report = build_speech_quality_report(manifest_df(), source_df(), speech, speech)
    row = report.loc[report["document_uri"].eq("doc:sala")].iloc[0]

    assert row["quality_status"] == "pass"
    assert row["participation_rows"] == 1
    assert row["analytical_transcription_event_rows"] == 1
    assert row["unresolved_identity_rows"] == 0


def test_validate_speech_quality_report_rejects_undeclared_document():
    speech = speech_df()
    report = build_speech_quality_report(manifest_df(), source_df(), speech, speech)
    unexpected = pd.concat([
        speech,
        speech.assign(document_uri="doc:other"),
    ], ignore_index=True)

    with pytest.raises(ValueError, match="unexpected documents"):
        validate_speech_quality_report(report, unexpected)


def test_build_speech_quality_report_flags_duplicate_paths_and_length_mismatch():
    speech = pd.concat([speech_df(), speech_df()], ignore_index=True)
    speech["item_path"] = "debate.items[0]"
    speech["row_index"] = 0
    speech["n_chars"] = [999, len("Intervención.")]

    report = build_speech_quality_report(manifest_df(), source_df(), speech, speech)
    row = report.loc[report["document_uri"].eq("doc:sala")].iloc[0]

    assert row["quality_status"] == "fail"
    assert "duplicate_item_path_rows=1" in row["issues"]
    assert "duplicate_row_index_rows=1" in row["issues"]
    assert "n_chars_mismatch_rows=1" in row["issues"]


def test_history_fallback_requires_discussion_and_keeps_voting_out_of_analysis():
    manifest = manifest_df()
    manifest.loc[manifest["document_uri"].eq("doc:pending"), "speech_source"] = "history_xml_fallback"
    discussion = pd.DataFrame([{
        "document_uri": "doc:pending",
        "date": "2025-01-29",
        "bill_number": "15480-13",
        "section_name": "Discusion",
        "kind": "participation",
        "speaker": "Ana Pérez",
        "speaker_id": "PersonaBCN1",
        "speaker_resolution_status": "corpus_registry",
        "speaker_data_status": "ok",
        "content": "Intervención.",
    }])
    speech = pd.concat([speech_df(), discussion], ignore_index=True)
    voting = discussion.assign(
        section_name="Votacion",
        content="En votación.",
    )
    full = pd.concat([speech, voting], ignore_index=True)

    report = build_speech_quality_report(manifest, source_df(), speech, full)
    fallback = report.loc[report["document_uri"].eq("doc:pending")].iloc[0]

    assert fallback["quality_status"] == "pass"
    assert fallback["discussion_rows"] == 1
    assert fallback["voting_rows"] == 1
    assert fallback["analytical_voting_rows"] == 0


def test_history_fallback_fails_if_voting_leaks_into_analysis():
    manifest = manifest_df()
    manifest.loc[manifest["document_uri"].eq("doc:pending"), "speech_source"] = "history_xml_fallback"
    fallback_rows = pd.DataFrame([
        {
            "document_uri": "doc:pending",
            "date": "2025-01-29",
            "bill_number": "15480-13",
            "section_name": section_name,
            "kind": "participation",
            "speaker": "Ana Pérez",
            "speaker_id": "PersonaBCN1",
            "speaker_resolution_status": "corpus_registry",
            "content": "Intervención.",
        }
        for section_name in ("Discusion", "Votacion")
    ])
    speech = pd.concat([speech_df(), fallback_rows], ignore_index=True)

    report = build_speech_quality_report(manifest, source_df(), speech, speech)
    fallback = report.loc[report["document_uri"].eq("doc:pending")].iloc[0]

    assert fallback["quality_status"] == "fail"
    assert "analytical_voting_rows=1" in fallback["issues"]
