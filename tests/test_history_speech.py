import pandas as pd

from bcn_scraper import (
    build_corpus_person_registry,
    collect_akn_person_identities,
    extract_speech_from_history_xml,
    flatten_speech_content,
    normalize_speech_content,
)


HISTORY_FRAGMENT = """
<div class="item" fecha="2025-01-29"
     partedocumento="http://datos.bcn.cl/recurso/cl/documento/706988/seccion/akn706988-ds9-ds10"
     tramitacion="http://datos.bcn.cl/recurso/cl/proyecto-de-ley/15480-13/tramitacion/33"
     uridocumento="http://datos.bcn.cl/recurso/cl/documento/706988">
  <h2>3.1. Discusión en Sala</h2>
  <p class="sub-headding">Fecha 29 de enero, 2025. Discusión única. Se aprueban modificaciones.</p>
  <span>
    <p>CREACIÓN DE UN NUEVO SISTEMA (TERCER TRÁMITE CONSTITUCIONAL. BOLETÍN N° 15480-13)</p>
    <p>El señor AEDO (Vicepresidente).-</p>
    <p>Se abre la discusión.</p>
    <p>Antecedentes:</p>
    <p>-Modificaciones del Senado.</p>
    <p>Tiene la palabra el diputado Jaime Araya.</p>
    <p>El señor ARAYA.-</p>
    <p>Esta es la intervención sustantiva.</p>
    <p>El señor AEDO (Vicepresidente).-</p>
    <p>Cerrado el debate.</p>
    <p>Corresponde votar las enmiendas.</p>
    <p>En votación.</p>
  </span>
</div>
"""


def corpus_registry():
    return {
        "PersonaBCN5253": {
            "kind": "person",
            "id": "PersonaBCN5253",
            "show_as": "eric aedo jeldres",
            "href": "http://datos.bcn.cl/recurso/persona/5253",
            "registry_source": "corpus_akn",
        },
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
    }


def test_history_fallback_separates_discussion_voting_and_background():
    parsed = extract_speech_from_history_xml(
        HISTORY_FRAGMENT,
        person_registry=corpus_registry(),
    )
    point = parsed["debate_body"]["point_of_order"][0]
    project = point["projects"][0]

    assert point["title"] == "ORDEN DEL DÍA"
    assert project["attributes"]["bill_uri"]["show_as"] == "15480-13"
    assert project["attributes"]["constitutional_stage"]["show_as"] == "Tercer Trámite Constitucional"
    assert project["background_paragraphs"] == ["Antecedentes:", "-Modificaciones del Senado."]
    assert [section["section_name"] for section in project["items"]] == ["Discusion", "Votacion"]
    assert project["items"][0]["items"][0]["content"][-1] == "Cerrado el debate."
    assert project["items"][1]["items"][0]["content"] == [
        "Corresponde votar las enmiendas.",
        "En votación.",
    ]


def test_history_fallback_normalizes_speakers_in_the_existing_flat_schema():
    parsed = extract_speech_from_history_xml(
        HISTORY_FRAGMENT,
        person_registry=corpus_registry(),
    )
    df = pd.DataFrame({
        "title": ["3.1. Discusión en Sala"],
        "date": ["2025-01-29"],
        "document_uri": ["http://datos.bcn.cl/recurso/cl/documento/706988"],
        "speech_content": [parsed],
    })
    normalized = normalize_speech_content(
        df,
        external_speakers={
            "AEDO": {"speaker_href": "http://datos.bcn.cl/recurso/persona/5253"},
        },
    )
    flat = flatten_speech_content(
        normalized,
        include_preambles=True,
        include_unresolved=True,
    )

    araya = flat.loc[flat["speaker_href"].eq("http://datos.bcn.cl/recurso/persona/5192")].iloc[0]
    assert araya["speaker"] == "jaime rafael ricardo araya guerrero"
    assert araya["speaker_resolution_status"] == "akn_context"
    assert araya["section_name"] == "Discusion"
    assert flat["bill_number"].eq("15480-13").all()
    assert set(flat["section_name"]) == {"Discusion", "Votacion"}


def test_identity_audit_keeps_local_ids_scoped_to_their_documents():
    def speech_content(document_person_id, href, name):
        return {
            "metadata": {
                "persons": {
                    document_person_id: {
                        "id": document_person_id,
                        "kind": "person",
                        "show_as": name,
                        "href": href,
                    }
                }
            }
        }

    df = pd.DataFrame({
        "document_uri": ["doc:a", "doc:b", "doc:c"],
        "title": ["A", "B", "C"],
        "date": ["2024-01-01"] * 3,
        "speech_content": [
            speech_content("per8", "http://datos.bcn.cl/recurso/persona/2861", "sergio bobadilla munoz"),
            speech_content("per107", "http://datos.bcn.cl/recurso/persona/2861", "sergio bobadilla munoz"),
            speech_content("per8", "http://datos.bcn.cl/recurso/persona/9999", "otra persona"),
        ],
    })

    audit = collect_akn_person_identities(df)
    registry = build_corpus_person_registry(df)

    assert audit.loc[audit["local_speaker_id"].eq("per8"), "local_id_reused_across_people"].all()
    assert audit.loc[
        audit["speaker_href"].eq("http://datos.bcn.cl/recurso/persona/2861"),
        "stable_person_uses_multiple_local_ids",
    ].all()
    assert registry["PersonaBCN2861"]["href"] == "http://datos.bcn.cl/recurso/persona/2861"
    assert registry["PersonaBCN2861"]["registry_source"] == "corpus_akn"
