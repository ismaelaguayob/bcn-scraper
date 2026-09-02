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


def test_extract_speech_handles_projects_directly_inside_cuenta():
    akn = """\
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
             xmlns:bcn="http://datos.bcn.cl">
  <debate>
    <meta>
      <references>
        <TLCReference id="pl1" showAs="15625-13"
                      href="http://datos.bcn.cl/recurso/cl/proyecto-de-ley/15625-13" />
        <TLCPerson id="per1" showAs="diputada de prueba"
                   href="http://datos.bcn.cl/recurso/persona/1" />
      </references>
    </meta>
    <debateBody>
      <debateSection name="Cuenta" id="cuenta1">
        <debateSection name="TextoDebate" id="texto-cuenta">
          <p>Texto general de la Cuenta que no corresponde a un proyecto.</p>
        </debateSection>
        <debateSection name="ProyectoDeLey" id="proyecto1"
                       bcn:uriProyectoLey="#pl1">
          <heading>MODIFICACIÓN DE LA LEY DE PENSIONES</heading>
          <debateSection name="Participacion" id="participacion1"
                         refersTo="#per1">
            <p>La señora DIPUTADA DE PRUEBA.-</p>
            <p>Intervención del proyecto previsional.</p>
          </debateSection>
        </debateSection>
      </debateSection>
    </debateBody>
  </debate>
</akomaNtoso>
"""

    data = extract_speech_from_akn(akn)

    assert len(data["debate_body"]["point_of_order"]) == 1
    point_of_order = data["debate_body"]["point_of_order"][0]
    assert point_of_order["section_name"] == "implicit_cuenta"
    assert len(point_of_order["projects"]) == 1
    project = point_of_order["projects"][0]
    assert project["title"] == "MODIFICACIÓN DE LA LEY DE PENSIONES"
    assert project["attributes"]["bill_uri"]["show_as"] == "15625-13"
    assert [item["kind"] for item in project["items"]] == ["participation"]
    assert project["items"][0]["content"][-1] == "Intervención del proyecto previsional."


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
    assert items[2]["content"] == ["Ruego a las tribunas guardar silencio."]
    assert items[2]["raw_content"] == [
        "El señor GARCÍA (Presidente).-",
        "Ruego a las tribunas guardar silencio.",
    ]
    assert items[3]["speaker"] == "rojo edwards silva"
    assert items[3]["content"] == ["Presidente, ¿me podría devolver el tiempo perdido?"]
    assert items[4]["source_kind"] == "interruption"
    assert items[4]["content"] == ["Por favor, senador Edwards, intervenga."]
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
    assert rows["JARA"]["identity_status"] == "resolved"
    assert rows["MARCEL"]["metadata_status"] == "incomplete"
    assert rows["MARCEL"]["identity_status"] == "unresolved"
    assert "speaker_id" in rows["MARCEL"]["missing_fields"]
    assert rows["MARCEL"]["first_title"] == "4. Discusión en Sala"
    assert rows["MARCEL"]["first_akn_url"] == "http://datos.bcn.cl/recurso/cl/documento/706982.xml"


def test_collect_unlabeled_speaker_candidates_uses_normalized_resolution_progress():
    speech_content = {
        "debate_body": {
            "point_of_order": [{
                "projects": [{
                    "items": [
                        {
                            "kind": "participation",
                            "source_kind": "unlabeled_text",
                            "speaker_key": "GARCIA",
                            "speaker_marker": "El señor GARCÍA (Presidente).-",
                            "speaker_id": "PersonaAut9",
                            "speaker": "jose garcia ruminot",
                            "speaker_href": "http://datos.bcn.cl/recurso/persona/1961",
                            "role": "Presidente",
                            "speaker_resolution_status": "user_provided",
                            "speaker_source": "akn_metadata",
                            "content": ["Tiene la palabra el senador."],
                        },
                        {
                            "kind": "participation",
                            "source_kind": "interruption",
                            "speaker_key": "LANDEROS",
                            "speaker_marker": "El señor LANDEROS (Secretario).-",
                            "speaker_id": "PersonaExt4",
                            "speaker": "LANDEROS",
                            "speaker_href": None,
                            "role": "Secretario",
                            "speaker_resolution_status": "regex",
                            "speaker_source": "regex",
                            "content": ["Señor Presidente."],
                        },
                    ]
                }]
            }]
        }
    }
    df = pd.DataFrame({"speech_content": [speech_content]})

    candidates = collect_unlabeled_speaker_candidates(
        df,
        external_speakers={"GARCIA": {"speaker_id": "PersonaAut9"}},
    )
    rows = {row["speaker_key"]: row for row in candidates.to_dict("records")}

    assert rows["GARCIA"]["identity_status"] == "resolved"
    assert rows["GARCIA"]["metadata_status"] == "complete"
    assert rows["GARCIA"]["resolved_speaker"] == "jose garcia ruminot"
    assert rows["GARCIA"]["resolved_speaker_href"] == "http://datos.bcn.cl/recurso/persona/1961"
    assert rows["GARCIA"]["speaker_sources"] == ["akn_metadata"]

    assert rows["LANDEROS"]["identity_status"] == "regex_only"
    assert rows["LANDEROS"]["metadata_status"] == "incomplete"
    assert "speaker_href" in rows["LANDEROS"]["missing_fields"]


def test_normalize_speech_content_splits_overlap_and_document_separators():
    speech_content = {
        "debate_body": {
            "point_of_order": [{
                "projects": [{
                    "items": [{
                        "kind": "unlabeled_text",
                        "id": "p1",
                        "content": [
                            "La señora JARA (Ministra del Trabajo).-",
                            "Inicio de la respuesta.",
                            "-Hablan varios diputados a la vez.",
                            "Continúo con la respuesta.",
                            "-o-",
                            "Cierro la respuesta.",
                        ],
                    }]
                }]
            }]
        }
    }
    df = pd.DataFrame({"speech_content": [speech_content]})

    normalized = normalize_speech_content(
        df,
        external_speakers={
            "JARA": {
                "speaker": "Jeannette Jara",
                "speaker_id": "PersonaExt1",
                "role": "Ministra del Trabajo",
            }
        },
    )
    items = normalized.loc[0, "speech_content"]["debate_body"]["point_of_order"][0]["projects"][0]["items"]

    assert [item["kind"] for item in items] == [
        "participation",
        "transcription_event",
        "participation",
        "transcription_event",
        "participation",
    ]
    assert items[1]["content"] == ["-Hablan varios diputados a la vez."]
    assert items[3]["content"] == ["-o-"]
    assert items[2]["content"] == ["Continúo con la respuesta."]
    assert items[2]["raw_content"] == ["Continúo con la respuesta."]
    assert items[4]["raw_content"] == ["Cierro la respuesta."]


def test_normalize_speech_content_uses_name_qualifier_for_unique_akn_person():
    speech_content = {
        "metadata": {
            "persons": {
                "per1": {
                    "kind": "person",
                    "id": "per1",
                    "show_as": "guillermo andres ramirez diez",
                    "href": "http://datos.bcn.cl/recurso/persona/4570",
                },
                "per2": {
                    "kind": "person",
                    "id": "per2",
                    "show_as": "matias ramirez pascal",
                    "href": "http://datos.bcn.cl/recurso/persona/5187",
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
                        "kind": "unlabeled_text",
                        "id": "p1",
                        "content": [
                            "El señor RAMÍREZ (don Guillermo).- .",
                            "Formulo una consulta a la Mesa.",
                        ],
                    }]
                }]
            }]
        },
    }
    df = pd.DataFrame({"speech_content": [speech_content]})

    normalized = normalize_speech_content(df)
    item = normalized.loc[0, "speech_content"]["debate_body"]["point_of_order"][0]["projects"][0]["items"][0]

    assert item["speaker_id"] == "per1"
    assert item["speaker"] == "guillermo andres ramirez diez"
    assert item["speaker_source"] == "akn_metadata"
    assert item["speaker_resolution_status"] == "akn_unique"
    assert item["role"] is None
    assert item["content"] == ["Formulo una consulta a la Mesa."]


def test_normalize_speech_content_uses_comma_name_qualifier_and_keeps_role():
    speech_content = {
        "metadata": {
            "persons": {
                "per1": {
                    "kind": "person",
                    "id": "per1",
                    "show_as": "raul humberto soto mardones",
                    "href": "http://datos.bcn.cl/recurso/persona/4629",
                },
                "per2": {
                    "kind": "person",
                    "id": "per2",
                    "show_as": "leonardo enrique soto ferrada",
                    "href": "http://datos.bcn.cl/recurso/persona/4523",
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
                        "kind": "unlabeled_text",
                        "content": [
                            "El señor SOTO, don Raúl (Presidente accidental).-",
                            "Tiene la palabra la diputada.",
                        ],
                    }]
                }]
            }]
        },
    }

    normalized = normalize_speech_content(pd.DataFrame({"speech_content": [speech_content]}))
    item = normalized.loc[0, "speech_content"]["debate_body"]["point_of_order"][0]["projects"][0]["items"][0]

    assert item["speaker_id"] == "per1"
    assert item["speaker_resolution_status"] == "akn_unique"
    assert item["role"] == "Presidente accidental"


def test_generated_regex_entry_remains_unresolved_after_repeated_occurrences():
    speech_content = {
        "debate_body": {
            "point_of_order": [{
                "projects": [{
                    "items": [{
                        "kind": "unlabeled_text",
                        "content": [
                            "El señor LANDEROS (Secretario).-",
                            "Primera aclaración.",
                            "El señor LANDEROS (Secretario).-",
                            "Segunda aclaración.",
                        ],
                    }]
                }]
            }]
        }
    }
    df = pd.DataFrame({"speech_content": [speech_content]})

    normalized = normalize_speech_content(df)
    candidates = collect_unlabeled_speaker_candidates(normalized)
    row = candidates.iloc[0]

    assert row["speaker_key"] == "LANDEROS"
    assert row["identity_status"] == "regex_only"
    assert row["resolution_statuses"] == ["regex"]
    assert row["speaker_sources"] == ["regex"]


def test_normalize_speech_content_applies_document_specific_speaker_ids():
    def speech_content(person_id):
        return {
            "metadata": {
                "persons": {
                    person_id: {
                        "kind": "person",
                        "id": person_id,
                        "show_as": "jose carlos meza pereira",
                        "href": "http://datos.bcn.cl/recurso/persona/5272",
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
                            "content": ["El señor MEZA.-", "Intervención."],
                        }]
                    }]
                }]
            },
        }

    df = pd.DataFrame({
        "document_uri": ["doc:a", "doc:b"],
        "speech_content": [speech_content("per72"), speech_content("per112")],
    })
    overrides = {
        "doc:a": {"MEZA": {"speaker_id": "per72"}},
        "doc:b": {"MEZA": {"speaker_id": "per112"}},
    }

    normalized = normalize_speech_content(
        df,
        document_speaker_overrides=overrides,
    )
    items = [
        row["debate_body"]["point_of_order"][0]["projects"][0]["items"][0]
        for row in normalized["speech_content"]
    ]

    assert [item["speaker_id"] for item in items] == ["per72", "per112"]
    assert {item["speaker"] for item in items} == {"jose carlos meza pereira"}
    assert {item["speaker_source"] for item in items} == {"akn_metadata"}

    candidate = collect_unlabeled_speaker_candidates(normalized).iloc[0]
    assert candidate["identity_status"] == "resolved"
    assert not candidate["has_resolution_conflict"]
    assert candidate["observed_speaker_ids"] == ["per112", "per72"]


def test_stable_href_resolves_the_document_local_id_in_each_akn():
    def speech_content(person_id, other_id):
        return {
            "metadata": {
                "persons": {
                    person_id: {
                        "kind": "person",
                        "id": person_id,
                        "show_as": "sergio bobadilla munoz",
                        "href": "http://datos.bcn.cl/recurso/persona/2861",
                    },
                    other_id: {
                        "kind": "person",
                        "id": other_id,
                        "show_as": "otra persona",
                        "href": "http://datos.bcn.cl/recurso/persona/9999",
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
                            "kind": "unlabeled_text",
                            "content": ["El señor BOBADILLA.-", "Intervención."],
                        }]
                    }]
                }]
            },
        }

    df = pd.DataFrame({
        "speech_content": [
            speech_content("per8", "per107"),
            speech_content("per107", "per8"),
        ]
    })
    normalized = normalize_speech_content(
        df,
        external_speakers={
            "BOBADILLA": {
                "speaker_href": "http://datos.bcn.cl/recurso/persona/2861",
            }
        },
    )
    items = [
        value["debate_body"]["point_of_order"][0]["projects"][0]["items"][0]
        for value in normalized["speech_content"]
    ]

    assert [item["speaker_id"] for item in items] == ["per8", "per107"]
    assert {item["speaker_href"] for item in items} == {
        "http://datos.bcn.cl/recurso/persona/2861"
    }
    assert {item["speaker_resolution_status"] for item in items} == {"stable_href"}


def test_bare_surname_does_not_match_an_unrelated_akn_reference():
    speech_content = {
        "metadata": {
            "persons": {
                "per1": {
                    "kind": "person",
                    "id": "per1",
                    "show_as": "jose oyarce jara",
                    "href": "http://datos.bcn.cl/recurso/persona/9999",
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
                        "content": ["La señora JARA.-", "Intervención ministerial."],
                    }]
                }]
            }]
        },
    }

    normalized = normalize_speech_content(pd.DataFrame({"speech_content": [speech_content]}))
    item = normalized.loc[0, "speech_content"]["debate_body"]["point_of_order"][0]["projects"][0]["items"][0]

    assert item["speaker"] == "JARA"
    assert item["speaker_resolution_status"] == "regex"
    assert item["speaker_href"] is None


def test_procedural_prompt_disambiguates_same_surname_in_corpus_registry():
    speech_content = {
        "metadata": {
            "persons": {
                "PersonaBCN339": {
                    "kind": "person",
                    "id": "PersonaBCN339",
                    "show_as": "pedro araya guerrero",
                    "href": "http://datos.bcn.cl/recurso/persona/339",
                    "registry_source": "corpus_akn",
                },
                "PersonaBCN5192": {
                    "kind": "person",
                    "id": "PersonaBCN5192",
                    "show_as": "jaime rafael ricardo araya guerrero",
                    "href": "http://datos.bcn.cl/recurso/persona/5192",
                    "registry_source": "corpus_akn",
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
                        "kind": "unlabeled_text",
                        "content": [
                            "Tiene la palabra el diputado Jaime Araya.",
                            "El señor ARAYA.-",
                            "Intervención de Jaime.",
                        ],
                    }]
                }]
            }]
        },
    }

    normalized = normalize_speech_content(pd.DataFrame({"speech_content": [speech_content]}))
    items = normalized.loc[0, "speech_content"]["debate_body"]["point_of_order"][0]["projects"][0]["items"]
    speech = next(item for item in items if item.get("kind") == "participation" and not item.get("is_preamble"))

    assert speech["speaker"] == "jaime rafael ricardo araya guerrero"
    assert speech["speaker_href"] == "http://datos.bcn.cl/recurso/persona/5192"
    assert speech["speaker_resolution_status"] == "akn_context"


def test_candidate_report_accepts_multiple_resolved_people_for_one_surname_key():
    speech_content = {
        "debate_body": {
            "point_of_order": [{
                "projects": [{
                    "items": [
                        {
                            "kind": "participation",
                            "source_kind": "unlabeled_text",
                            "speaker_key": "ARAYA",
                            "speaker": "pedro araya guerrero",
                            "speaker_id": "PersonaBCN339",
                            "speaker_href": "http://datos.bcn.cl/recurso/persona/339",
                            "speaker_resolution_status": "stable_href",
                            "speaker_source": "akn_metadata",
                            "content": ["Intervención en el Senado."],
                        },
                        {
                            "kind": "participation",
                            "source_kind": "unlabeled_text",
                            "speaker_key": "ARAYA",
                            "speaker": "jaime araya guerrero",
                            "speaker_id": "PersonaBCN5192",
                            "speaker_href": "http://datos.bcn.cl/recurso/persona/5192",
                            "speaker_resolution_status": "akn_context",
                            "speaker_source": "corpus_registry",
                            "content": ["Intervención en la Cámara."],
                        },
                    ]
                }]
            }]
        }
    }

    report = collect_unlabeled_speaker_candidates(
        pd.DataFrame({"speech_content": [speech_content]})
    ).iloc[0]

    assert report["identity_status"] == "resolved"
    assert report["has_multiple_resolved_identities"]
    assert not report["has_resolution_conflict"]
    assert report["metadata_status"] == "multiple_resolved"


def test_collect_unlabeled_speaker_candidates_flags_manual_identity_conflict():
    speech_content = {
        "debate_body": {
            "point_of_order": [{
                "projects": [{
                    "items": [{
                        "kind": "participation",
                        "source_kind": "unlabeled_text",
                        "speaker_key": "PEREZ",
                        "speaker_id": "per1",
                        "speaker": "ana perez",
                        "speaker_href": "http://datos.bcn.cl/recurso/persona/1",
                        "speaker_resolution_status": "akn_unique",
                        "speaker_source": "akn_metadata",
                        "content": ["Intervención."],
                    }]
                }]
            }]
        }
    }
    df = pd.DataFrame({"speech_content": [speech_content]})

    candidates = collect_unlabeled_speaker_candidates(
        df,
        external_speakers={
            "PEREZ": {
                "speaker": "beatriz perez",
                "speaker_id": "per2",
                "speaker_href": "http://datos.bcn.cl/recurso/persona/2",
            }
        },
    )

    assert candidates.loc[0, "identity_status"] == "conflict"
    assert candidates.loc[0, "has_resolution_conflict"]
