import json

import pandas as pd

from bcn_scraper.speech_dataframe import (
    build_speech_analysis_dataframe,
    flatten_speech_content,
)


BCN_PERSON = "http://datos.bcn.cl/recurso/persona/2362"
WIKI_PERSON = "https://es.wikipedia.org/wiki/Jeannette_Jara"


def project_attrs():
    return {
        "bill_uri": {"raw": "#bill17489", "ref_id": "bill17489", "show_as": "17489-04"},
        "constitutional_stage": {"raw": "#stage2", "ref_id": "stage2", "show_as": "Segundo Trámite Constitucional"},
        "regulatory_stage": {"raw": "#reg1", "ref_id": "reg1", "show_as": "Discusión General"},
        "debate_result": {"raw": "#approved", "ref_id": "approved", "show_as": "Aprobado"},
    }


def normalized_speech_content():
    return {
        "debate_body": {
            "point_of_order": [{
                "id": "po1",
                "kind": "point_of_order",
                "section_name": "Tabla",
                "title": "ORDEN DEL DÍA",
                "projects": [{
                    "id": "proj1",
                    "section_name": "ProyectoDeLey",
                    "title": "REFORMA DE PENSIONES",
                    "attributes": project_attrs(),
                    "items": [
                        {
                            "kind": "participation",
                            "id": "p1",
                            "time_step": 1,
                            "speaker_id": "per1",
                            "speaker": "Ximena Rincón González",
                            "speaker_href": BCN_PERSON,
                            "type": "Intervención",
                            "role": "Senadora",
                            "is_labeled": True,
                            "content": ["Gracias, Presidente.", "Voy a fundamentar mi voto."],
                            "raw_content": [
                                "El señor PRESIDENTE.-",
                                "Tiene la palabra la senadora Rincón.",
                                "La señora RINCÓN.-",
                                "Gracias, Presidente.",
                                "Voy a fundamentar mi voto.",
                            ],
                            "speech_marker": "La señora RINCÓN.-",
                            "discarded_preamble": [
                                "El señor PRESIDENTE.-",
                                "Tiene la palabra la senadora Rincón.",
                            ],
                        },
                        {
                            "kind": "participation",
                            "id": "pre1",
                            "time_step": 2,
                            "source_kind": "preamble",
                            "type": "Preambulo procedimental",
                            "is_preamble": True,
                            "is_labeled": False,
                            "content": ["Tiene la palabra la ministra Jara."],
                        },
                        {
                            "kind": "participation",
                            "id": "p2",
                            "time_step": 3,
                            "source_kind": "unlabeled_text",
                            "speaker_id": "PersonaExt1",
                            "speaker": "Jeannette Jara",
                            "speaker_href": WIKI_PERSON,
                            "type": "Intervención no etiquetada",
                            "role": "Ministra del Trabajo y Previsión Social",
                            "is_labeled": False,
                            "speaker_resolution_status": "user_provided",
                            "speaker_source": "manual",
                            "content": ["Gracias por la invitación."],
                        },
                        {
                            "kind": "transcription_event",
                            "id": "ev1",
                            "time_step": 4,
                            "type": "Transcription event",
                            "content": ["(Aplausos en tribunas)."],
                        },
                        {
                            "kind": "section",
                            "id": "nested1",
                            "section_name": "Subdebate",
                            "title": "Subdebate",
                            "time_step": 5,
                            "items": [{
                                "kind": "participation",
                                "id": "p3",
                                "time_step": 1,
                                "source_kind": "interruption",
                                "speaker_id": None,
                                "speaker": "Presidencia",
                                "type": "Interrupcion",
                                "is_labeled": False,
                                "is_interruption": True,
                                "content": ["Ruego guardar silencio."],
                            }],
                        },
                        {
                            "kind": "unlabeled_text",
                            "id": "u1",
                            "time_step": 6,
                            "speaker_resolution_status": "unresolved",
                            "content": ["Bloque no atribuido."],
                        },
                    ],
                }],
            }],
            "other_debates": [{
                "id": "od1",
                "kind": "other_debate",
                "section_name": "TextoDebate",
                "title": "Otro debate",
                "items": [{
                    "kind": "participation",
                    "id": "p4",
                    "time_step": 1,
                    "speaker_id": "per99",
                    "speaker": "Otra persona",
                    "type": "Intervención",
                    "role": "Diputada",
                    "content": ["Intervención fuera de proyecto."],
                }],
            }],
        }
    }


def source_df(as_json=False):
    speech_content = normalized_speech_content()
    if as_json:
        speech_content = json.dumps(speech_content, ensure_ascii=False)
    return pd.DataFrame({
        "speech_content": [speech_content],
        "title": ["Discusión en Sala"],
        "date": ["2025-01-01"],
        "akn_url": ["https://example.test/akn.xml"],
        "xml_url": ["https://example.test/doc.xml"],
        "bcn_url": ["https://example.test/historia"],
        "document_uri": ["http://datos.bcn.cl/recurso/documento/1"],
    })


def parliamentarians_df():
    return pd.DataFrame({
        "person_href": [BCN_PERSON, BCN_PERSON],
        "person_id": ["2362", "2362-duplicate"],
        "name": ["Ximena Rincón González", "Duplicada"],
        "gender": ["mujer", "mujer"],
        "nationality": ["Chile", "Chile"],
        "birth_date": ["1968-07-05", "1968-07-05"],
        "birth_place": ["Concepción", "Concepción"],
        "image_url": ["https://www.bcn.cl/laborparlamentaria/imagen/2362.jpg", "duplicate"],
        "thumbnail_url": ["https://www.bcn.cl/laborparlamentaria/imagen/110x110/2362.jpg", "duplicate"],
        "current_party": ["Partido Demócratas Chile", "Duplicado"],
        "current_party_href": ["http://datos.bcn.cl/recurso/cl/organismo/partido-politico/partido-democratas-chile", "duplicate"],
        "current_militancy_href": [f"{BCN_PERSON}/militancia/11291", "duplicate"],
        "current_militancy_start_date": [None, None],
        "current_militancy_end_date": [None, None],
        "has_current_militancy": [True, True],
        "militancy_count": [2, 2],
        "data_status": ["ok", "ok"],
    })


def test_flatten_speech_content_defaults_to_discursive_rows_only():
    flat = flatten_speech_content(source_df())

    assert flat["participation_id"].tolist() == ["p1", "p2", "p3", "p4"]
    assert "pre1" not in flat["participation_id"].tolist()
    assert "ev1" not in flat["participation_id"].tolist()
    assert "u1" not in flat["participation_id"].tolist()

    first = flat[flat["participation_id"] == "p1"].iloc[0]
    assert first["source_row_index"] == 0
    assert first["title"] == "Discusión en Sala"
    assert first["section_kind"] == "project"
    assert first["point_of_order_id"] == "po1"
    assert first["project_id"] == "proj1"
    assert first["project_title"] == "REFORMA DE PENSIONES"
    assert first["bill_number"] == "17489-04"
    assert first["constitutional_stage"] == "Segundo Trámite Constitucional"
    assert first["regulatory_stage"] == "Discusión General"
    assert first["debate_result"] == "Aprobado"
    assert first["content"] == "Gracias, Presidente.\nVoy a fundamentar mi voto."
    assert first["content_paragraphs"] == ["Gracias, Presidente.", "Voy a fundamentar mi voto."]
    assert first["n_paragraphs"] == 2
    assert first["n_words"] == 7
    assert first["has_raw_content"] == True
    assert first["has_discarded_preamble"] == True
    assert first["content_status"] == "ok"
    assert first["speaker_id"] == "PersonaBCN2362"
    assert first["speaker_bcn_id"] == "2362"
    assert first["speaker_local_id"] == "per1"
    assert first["utterance_id"].startswith("utt_")

    interruption = flat[flat["participation_id"] == "p3"].iloc[0]
    assert interruption["section_name"] == "Subdebate"
    assert interruption["is_interruption"] == True
    assert interruption["speaker_href"] is None

    other_debate = flat[flat["participation_id"] == "p4"].iloc[0]
    assert other_debate["section_kind"] == "other_debate"
    assert pd.isna(other_debate["project_id"])


def test_flatten_speech_content_optional_debug_rows_and_json_input():
    flat = flatten_speech_content(
        source_df(as_json=True),
        include_preambles=True,
        include_transcription_events=True,
        include_unresolved=True,
    )

    assert flat["participation_id"].tolist() == ["p1", "pre1", "p2", "ev1", "p3", "u1", "p4"]

    preamble = flat[flat["participation_id"] == "pre1"].iloc[0]
    assert preamble["is_preamble"] == True
    assert preamble["content_status"] == "preamble"
    assert preamble["source_kind"] == "preamble"

    event = flat[flat["participation_id"] == "ev1"].iloc[0]
    assert event["kind"] == "transcription_event"
    assert event["content_status"] == "transcription_event"
    assert event["speaker_id"] is None
    assert event["speaker_href"] is None

    discursive = flatten_speech_content(source_df(as_json=True))
    shared = flat.loc[flat["participation_id"].eq("p1"), "utterance_id"].iloc[0]
    assert shared == discursive.loc[
        discursive["participation_id"].eq("p1"), "utterance_id"
    ].iloc[0]
    assert flat["utterance_id"].is_unique

    unresolved = flat[flat["participation_id"] == "u1"].iloc[0]
    assert unresolved["kind"] == "unlabeled_text"
    assert unresolved["content_status"] == "unresolved"
    assert unresolved["speaker_resolution_status"] == "unresolved"


def test_build_speech_analysis_dataframe_merges_parliamentarians_without_duplication():
    analysis = build_speech_analysis_dataframe(source_df(), parliamentarians=parliamentarians_df())

    assert len(analysis) == 4

    matched = analysis[analysis["participation_id"] == "p1"].iloc[0]
    assert matched["speaker_data_status"] == "ok"
    assert matched["person_id"] == "2362"
    assert matched["name"] == "Ximena Rincón González"
    assert matched["gender"] == "mujer"
    assert matched["current_party"] == "Partido Demócratas Chile"
    assert matched["speaker_id"] == "PersonaBCN2362"
    assert matched["speaker_local_id"] == "per1"

    external = analysis[analysis["participation_id"] == "p2"].iloc[0]
    assert external["speaker_href"] == WIKI_PERSON
    assert external["speaker_data_status"] == "not_bcn_person"
    assert pd.isna(external["person_id"])
    assert pd.isna(external["gender"])
    assert pd.isna(external["current_party"])

    missing_href = analysis[analysis["participation_id"] == "p3"].iloc[0]
    assert missing_href["speaker_data_status"] == "missing_href"
    assert missing_href["speaker_href"] is None
    assert pd.isna(missing_href["person_id"])


def test_build_speech_analysis_dataframe_keeps_document_qualified_local_id_history():
    identity_audit = pd.DataFrame([
        {
            "document_uri": "doc:previous-a",
            "local_speaker_id": "PersonaAut9",
            "speaker_href": BCN_PERSON,
        },
        {
            "document_uri": "doc:previous-b",
            "local_speaker_id": "per8",
            "speaker_href": BCN_PERSON,
        },
    ])

    analysis = build_speech_analysis_dataframe(
        source_df(),
        parliamentarians=parliamentarians_df(),
        identity_audit=identity_audit,
    )

    matched = analysis[analysis["participation_id"] == "p1"].iloc[0]
    assert matched["speaker_id"] == "PersonaBCN2362"
    assert matched["speaker_bcn_id"] == "2362"
    assert matched["speaker_local_id"] == "per1"
    assert matched["speaker_local_ids"] == ["PersonaAut9", "per1", "per8"]
    assert matched["speaker_local_refs"] == [
        "doc:previous-a#PersonaAut9",
        "doc:previous-b#per8",
        "http://datos.bcn.cl/recurso/documento/1#per1",
    ]

    external = analysis[analysis["participation_id"] == "p2"].iloc[0]
    assert external["speaker_id"] == "PersonaExt1"
    assert external["speaker_bcn_id"] is None
    assert external["speaker_local_ids"] == ["PersonaExt1"]


def test_build_speech_analysis_dataframe_marks_not_merged_without_parliamentarians():
    analysis = build_speech_analysis_dataframe(source_df())

    assert set(analysis["speaker_data_status"]) == {"not_merged"}
    assert "person_id" in analysis.columns
    assert analysis["person_id"].isna().all()


def test_build_speech_analysis_dataframe_marks_bcn_href_not_found_in_parliamentarians():
    parliamentarians = parliamentarians_df()
    parliamentarians["person_href"] = "http://datos.bcn.cl/recurso/persona/9999"

    analysis = build_speech_analysis_dataframe(source_df(), parliamentarians=parliamentarians)

    missing = analysis[analysis["participation_id"] == "p1"].iloc[0]
    assert missing["speaker_href"] == BCN_PERSON
    assert missing["speaker_data_status"] == "not_found"
    assert pd.isna(missing["person_id"])
    assert pd.isna(missing["gender"])
    assert pd.isna(missing["current_party"])


def test_build_speech_analysis_dataframe_includes_event_status_when_requested():
    analysis = build_speech_analysis_dataframe(
        source_df(),
        parliamentarians=parliamentarians_df(),
        include_transcription_events=True,
    )

    event = analysis[analysis["participation_id"] == "ev1"].iloc[0]
    assert event["speaker_data_status"] == "not_applicable"
    assert event["content_status"] == "transcription_event"
    assert pd.isna(event["person_id"])
