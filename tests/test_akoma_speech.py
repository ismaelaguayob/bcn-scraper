import json
from pathlib import Path

import pandas as pd

from bcn_scraper.akoma_speech import (
    add_speech_content,
    collect_unlabeled_speaker_candidates,
    extract_speech_from_akn,
    normalize_speech_content,
)


FIXTURES = Path("new_features_&_reports/speech_data_from_akn/test_data")


def load_akn(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


def walk_items(items):
    for item in items:
        yield item
        if "items" in item:
            yield from walk_items(item["items"])


def test_extract_speech_from_senate_akn_resolves_metadata_and_projects():
    data = extract_speech_from_akn(load_akn("709595.xml"))

    assert data["metadata"]["persons"]["PersonaAut3"]["show_as"] == "gustavo adolfo sanhueza duenas"
    assert data["session_information"]["paragraphs"]
    assert len(data["debate_body"]["point_of_order"]) == 1

    first_project = data["debate_body"]["point_of_order"][0]["projects"][0]
    assert first_project["attributes"]["bill_uri"]["show_as"] == "17489-04"
    assert first_project["attributes"]["constitutional_stage"]["show_as"] == "Segundo Trámite Constitucional"
    assert "TITULARIDAD EN EL CARGO" in first_project["title"]

    first_participation = next(item for item in first_project["items"] if item["kind"] == "participation")
    assert first_participation["speaker_id"] == "PersonaAut3"
    assert first_participation["speaker"] == "gustavo adolfo sanhueza duenas"
    assert first_participation["type"] == "Intervención"
    assert first_participation["role"] == "Senador"
    assert first_participation["content"][:2] == ["El señor SANHUEZA.-", "Gracias, Presidente."]


def test_extract_speech_groups_consecutive_unlabeled_paragraphs():
    data = extract_speech_from_akn(load_akn("709595.xml"))
    first_project = data["debate_body"]["point_of_order"][0]["projects"][0]

    first_item = first_project["items"][0]

    assert first_item["kind"] == "unlabeled_text"
    assert first_item["time_step"] == 1
    assert first_item["content"] == [
        "El señor OSSANDÓN (Presidente).-",
        "Tiene la palabra el senador Sanhueza.",
    ]


def test_extract_speech_handles_tabla_inside_cuenta_as_point_of_order():
    data = extract_speech_from_akn(load_akn("686161.xml"))

    point_of_order = data["debate_body"]["point_of_order"][0]

    assert point_of_order["section_name"] == "Tabla"
    assert point_of_order["title"] == "TABLA"
    assert len(point_of_order["projects"]) == 1
    assert point_of_order["projects"][0]["section_name"] == "TextoDebate"
    assert len([item for item in point_of_order["projects"][0]["items"] if item["kind"] == "participation"]) >= 20


def test_extract_speech_extracts_address_votation_totals_and_votes():
    data = extract_speech_from_akn(load_akn("665620.xml"))

    address_items = []
    for address in data["debate_body"]["addresses"]:
        address_items.extend(walk_items(address["items"]))

    votation = next(item for item in address_items if item["kind"] == "votation" and item["votes"])

    assert votation["totals"] == {"in_favor": 105, "against": 0, "abstention": 1}
    assert len(votation["votes"]) == 107
    assert votation["votes"][0]["choice"] == "A Favor"
    assert votation["votes"][0]["person_id"] == "per65"
    assert votation["votes"][0]["person"] == "sergio aguilo melo"


def test_add_speech_content_serializes_json_from_wrapper_dataframe_fixture():
    df = pd.read_csv(FIXTURES / "datos_bcn_akn.csv", sep=";", nrows=8)

    enriched = add_speech_content(df, as_json=True)
    parsed = enriched["speech_content"].map(json.loads)

    assert "speech_content" in enriched.columns
    assert parsed.iloc[0]["metadata"]["references"]
    assert parsed.iloc[6]["error"] == "invalid_akn_content"


def test_add_speech_content_returns_dicts_by_default():
    df = pd.DataFrame({"akn_content": [b"<akomaNtoso><debate /></akomaNtoso>"]})

    enriched = add_speech_content(df)

    assert isinstance(enriched.loc[0, "speech_content"], dict)
    assert "metadata" in enriched.loc[0, "speech_content"]


def test_add_speech_content_handles_missing_and_bytes_values():
    df = pd.DataFrame({
        "akn_content": [
            float("nan"),
            None,
            "",
            b"<akomaNtoso><debate /></akomaNtoso>",
        ]
    })

    enriched = add_speech_content(df, as_json=False)

    assert enriched.loc[0, "speech_content"]["error"] == "missing_akn_content"
    assert enriched.loc[1, "speech_content"]["error"] == "missing_akn_content"
    assert enriched.loc[2, "speech_content"]["error"] == "missing_akn_content"
    assert "metadata" in enriched.loc[3, "speech_content"]


def test_normalize_speech_content_splits_unlabeled_speakers_with_manual_metadata():
    speech_content = {
        "debate_body": {
            "point_of_order": [{
                "projects": [{
                    "items": [{
                        "kind": "unlabeled_text",
                        "id": "u1",
                        "time_step": 1,
                        "content": [
                            "Ministra Jeannette Jara, le ofrecemos la palabra.",
                            "La señora JARA (ministra del Trabajo y Previsión Social).-",
                            "Gracias, Presidente.",
                            "Lo saludo a usted y a todos los senadores.",
                            "(Aplausos en tribunas).",
                            "Continúo con el punto central del proyecto.",
                            "Ofrezco la palabra al señor ministro de Hacienda, don Mario Marcel.",
                            "El señor MARCEL (ministro de Hacienda).-",
                            "Muchas gracias, Presidente.",
                        ],
                    }]
                }]
            }]
        }
    }
    df = pd.DataFrame({"speech_content": [speech_content]})

    enriched = normalize_speech_content(
        df,
        external_speakers={
            "JARA": {
                "speaker": "Jeannette Jara",
                "speaker_id": "PersonaExt10",
                "speaker_href": "https://example.test/jara",
                "role": "Ministra del Trabajo y Previsión Social",
            }
        },
    )
    items = enriched.loc[0, "speech_content"]["debate_body"]["point_of_order"][0]["projects"][0]["items"]

    assert [item["source_kind"] for item in items if item["kind"] == "participation"] == [
        "preamble",
        "unlabeled_text",
        "unlabeled_text",
        "preamble",
        "unlabeled_text",
    ]
    assert items[0]["is_preamble"]
    assert items[0]["content"] == ["Ministra Jeannette Jara, le ofrecemos la palabra."]
    assert items[1]["speaker"] == "Jeannette Jara"
    assert items[1]["speaker_id"] == "PersonaExt10"
    assert items[1]["speaker_href"] == "https://example.test/jara"
    assert items[1]["speaker_resolution_status"] == "user_provided"
    assert items[1]["content"] == [
        "Gracias, Presidente.",
        "Lo saludo a usted y a todos los senadores.",
    ]
    assert items[2]["kind"] == "transcription_event"
    assert items[2]["content"] == ["(Aplausos en tribunas)."]
    assert items[3]["speaker"] == "Jeannette Jara"
    assert items[3]["content"] == ["Continúo con el punto central del proyecto."]
    assert items[4]["is_preamble"]
    assert items[4]["content"] == ["Ofrezco la palabra al señor ministro de Hacienda, don Mario Marcel."]
    assert items[5]["speaker"] == "MARCEL"
    assert items[5]["speaker_id"] == "PersonaExt1"
    assert items[5]["speaker_resolution_status"] == "regex"
    assert items[5]["role"] == "ministro de Hacienda"
    assert items[5]["content"] == ["Muchas gracias, Presidente."]


def test_normalize_speech_content_keeps_unresolved_unlabeled_text():
    speech_content = {
        "debate_body": {
            "point_of_order": [{
                "projects": [{
                    "items": [{
                        "kind": "unlabeled_text",
                        "id": "u1",
                        "time_step": 1,
                        "content": ["Este bloque no tiene marcador de habla."],
                    }]
                }]
            }]
        }
    }
    df = pd.DataFrame({"speech_content": [json.dumps(speech_content)]})

    enriched = normalize_speech_content(df)
    item = enriched.loc[0, "speech_content"]["debate_body"]["point_of_order"][0]["projects"][0]["items"][0]

    assert item["kind"] == "unlabeled_text"
    assert item["speaker_resolution_status"] == "unresolved"


def test_normalize_speech_content_can_return_json():
    speech_content = {
        "debate_body": {
            "point_of_order": [{
                "projects": [{
                    "items": [{
                        "kind": "unlabeled_text",
                        "content": ["El señor MARCEL (ministro de Hacienda).-", "Muchas gracias."],
                    }]
                }]
            }]
        }
    }
    df = pd.DataFrame({"speech_content": [speech_content]})

    enriched = normalize_speech_content(df, as_json=True)
    parsed = json.loads(enriched.loc[0, "speech_content"])
    item = parsed["debate_body"]["point_of_order"][0]["projects"][0]["items"][0]

    assert item["speaker_id"] == "PersonaExt1"
    assert item["speaker"] == "MARCEL"


def test_normalize_speech_content_resolves_unlabeled_speaker_from_akn_metadata():
    speech_content = {
        "metadata": {
            "persons": {
                "PersonaAut9": {
                    "kind": "person",
                    "id": "PersonaAut9",
                    "show_as": "jose garcia ruminot",
                    "href": "http://datos.bcn.cl/recurso/persona/1961",
                }
            },
            "roles": {},
            "organizations": {},
            "references": {},
        },
        "debate_body": {
            "point_of_order": [{
                "projects": [{
                    "items": [{
                        "kind": "unlabeled_text",
                        "content": ["El señor GARCÍA (Presidente).-", "Tiene la palabra el senador."],
                    }]
                }]
            }]
        },
    }
    df = pd.DataFrame({"speech_content": [speech_content]})

    enriched = normalize_speech_content(
        df,
        external_speakers={"GARCIA": {"speaker_id": "PersonaAut9"}},
    )
    item = enriched.loc[0, "speech_content"]["debate_body"]["point_of_order"][0]["projects"][0]["items"][0]

    assert item["source_kind"] == "preamble"
    assert item["speaker_id"] == "PersonaAut9"
    assert item["speaker"] == "jose garcia ruminot"
    assert item["speaker_href"] == "http://datos.bcn.cl/recurso/persona/1961"
    assert item["speaker_source"] == "akn_metadata"


def test_normalize_speech_content_cleans_labeled_participation_preamble():
    speech_content = {
        "debate_body": {
            "point_of_order": [{
                "projects": [{
                    "items": [{
                        "kind": "participation",
                        "id": "p1",
                        "speaker_id": "per1",
                        "speaker": "johannes kaiser barents-von hohenhagen",
                        "content": [
                            "La señorita YEOMANS, doña Gael (Vicepresidenta).-",
                            "Tiene la palabra el diputado Johannes Kaiser.",
                            "El señor KAISER.-",
                            "Señorita Presidenta, muchas gracias.",
                        ],
                    }]
                }]
            }]
        }
    }
    df = pd.DataFrame({"speech_content": [speech_content]})

    enriched = normalize_speech_content(df)
    items = enriched.loc[0, "speech_content"]["debate_body"]["point_of_order"][0]["projects"][0]["items"]

    assert len(items) == 2
    assert items[0]["source_kind"] == "preamble"
    assert items[0]["is_preamble"]
    assert items[0]["content"] == [
        "La señorita YEOMANS, doña Gael (Vicepresidenta).-",
        "Tiene la palabra el diputado Johannes Kaiser.",
    ]
    assert items[1]["speaker"] == "johannes kaiser barents-von hohenhagen"
    assert items[1]["speech_marker"] == "El señor KAISER.-"
    assert items[1]["content"] == ["Señorita Presidenta, muchas gracias."]


def test_normalize_speech_content_splits_events_inside_labeled_participation():
    speech_content = {
        "debate_body": {
            "point_of_order": [{
                "projects": [{
                    "items": [{
                        "kind": "participation",
                        "id": "p1",
                        "speaker_id": "per1",
                        "speaker": "senador ejemplo",
                        "content": [
                            "Señor Presidente, voy a votar favorablemente.",
                            "(Aplausos)",
                            "Continúo con mi argumento.",
                            "He dicho.",
                            "-Aplausos.",
                        ],
                    }]
                }]
            }]
        }
    }
    df = pd.DataFrame({"speech_content": [speech_content]})

    enriched = normalize_speech_content(df)
    items = enriched.loc[0, "speech_content"]["debate_body"]["point_of_order"][0]["projects"][0]["items"]

    assert [item["kind"] for item in items] == [
        "participation",
        "transcription_event",
        "participation",
        "transcription_event",
    ]
    assert items[0]["content"] == ["Señor Presidente, voy a votar favorablemente."]
    assert items[1]["content"] == ["(Aplausos)"]
    assert items[2]["content"] == ["Continúo con mi argumento.", "He dicho."]
    assert items[3]["content"] == ["-Aplausos."]


def test_normalize_speech_content_splits_interruptions_inside_labeled_participation():
    speech_content = {
        "metadata": {
            "persons": {
                "PersonaAut9": {
                    "kind": "person",
                    "id": "PersonaAut9",
                    "show_as": "jose garcia ruminot",
                    "href": "http://datos.bcn.cl/recurso/persona/1961",
                },
                "PersonaAut4": {
                    "kind": "person",
                    "id": "PersonaAut4",
                    "show_as": "rojo edwards silva",
                    "href": "http://datos.bcn.cl/recurso/persona/187",
                },
            },
            "roles": {},
            "organizations": {},
            "references": {},
        },
        "debate_body": {
            "point_of_order": [{
                "projects": [{
                    "items": [{
                        "kind": "participation",
                        "id": "p1",
                        "speaker_id": "PersonaAut4",
                        "speaker": "rojo edwards silva",
                        "content": [
                            "Gracias, Presidente.",
                            "Ahora, quiero salir de la...",
                            "(Manifestaciones de rechazo en tribunas).",
                            "El señor GARCÍA (Presidente).-",
                            "Ruego a las tribunas guardar silencio.",
                            "El señor EDWARDS.-",
                            "Presidente, ¿me podría devolver el tiempo perdido?",
                            "El señor GARCÍA (Presidente).-",
                            "Por favor, senador Edwards, intervenga.",
                            "El señor EDWARDS.-",
                            "Presidente, quiero salir de la caricatura.",
                        ],
                    }]
                }]
            }]
        },
    }
    df = pd.DataFrame({"speech_content": [speech_content]})

    enriched = normalize_speech_content(
        df,
        external_speakers={
            "GARCIA": {"speaker_id": "PersonaAut9"},
            "EDWARDS": {"speaker_id": "PersonaAut4"},
        },
    )
    items = enriched.loc[0, "speech_content"]["debate_body"]["point_of_order"][0]["projects"][0]["items"]

    assert [item["kind"] for item in items] == [
        "participation",
        "transcription_event",
        "participation",
        "participation",
        "participation",
        "participation",
    ]
    assert items[0]["speaker"] == "rojo edwards silva"
    assert items[0]["content"] == ["Gracias, Presidente.", "Ahora, quiero salir de la..."]
    assert items[2]["source_kind"] == "interruption"
    assert items[2]["speaker"] == "jose garcia ruminot"
    assert items[3]["speaker"] == "rojo edwards silva"
    assert items[3]["content"] == ["Presidente, ¿me podría devolver el tiempo perdido?"]
    assert items[4]["source_kind"] == "interruption"
    assert items[5]["speaker"] == "rojo edwards silva"
    assert items[5]["content"] == ["Presidente, quiero salir de la caricatura."]


def test_collect_unlabeled_speaker_candidates_reports_missing_manual_metadata():
    speech_content = {
        "debate_body": {
            "point_of_order": [{
                "projects": [{
                    "items": [{
                        "kind": "unlabeled_text",
                        "content": [
                            "La señora JARA (ministra del Trabajo y Previsión Social).-",
                            "Gracias.",
                            "El señor MARCEL (ministro de Hacienda).-",
                            "Gracias.",
                        ],
                    }]
                }]
            }]
        }
    }
    df = pd.DataFrame({
        "title": ["4. Discusión en Sala"],
        "date": ["2025-01-27"],
        "akn_url": ["http://datos.bcn.cl/recurso/cl/documento/706982.xml"],
        "xml_url": ["https://www.bcn.cl/historiadelaley/obtienearchivo?id=706982"],
        "speech_content": [speech_content],
    })

    candidates = collect_unlabeled_speaker_candidates(
        df,
        external_speakers={
            "JARA": {
                "speaker": "Jeannette Jara",
                "speaker_id": "PersonaExt1",
                "speaker_href": "https://example.test/jara",
                "role": "Ministra del Trabajo y Previsión Social",
            }
        },
    )

    rows = {row["speaker_key"]: row for row in candidates.to_dict("records")}
    assert rows["JARA"]["metadata_status"] == "complete"
    assert rows["MARCEL"]["metadata_status"] == "incomplete"
    assert "speaker_id" in rows["MARCEL"]["missing_fields"]
    assert rows["MARCEL"]["first_title"] == "4. Discusión en Sala"
    assert rows["MARCEL"]["first_akn_url"] == "http://datos.bcn.cl/recurso/cl/documento/706982.xml"
