import pandas as pd

from bcn_scraper.parliamentary_data import (
    BCNBIO_HAS_BEGINNING,
    BCNBIO_HAS_BORN,
    BCNBIO_HAS_END,
    BCNBIO_HAS_MILITANCY,
    BCNBIO_HAS_POLITICAL_PARTY,
    BCNBIO_NATIONALITY,
    BCNBIO_ORIGINAL_DATE,
    BIO_PLACE,
    DC_DATE,
    FOAF_GENDER,
    FOAF_IMG,
    FOAF_NAME,
    RDFS_LABEL,
    build_parliamentarian_table,
    canonical_resource_url,
    collect_bcn_speaker_references,
    fetch_parliamentarian_data,
    is_bcn_person_url,
    rdf_json_url,
)


def uri(value):
    return {"type": "uri", "value": value}


def literal(value):
    return {"type": "literal", "value": value}


PERSON = "http://datos.bcn.cl/recurso/persona/2362"
BIRTH = f"{PERSON}/nacimiento"
OLD_MILITANCY = f"{PERSON}/militancia/9844"
CURRENT_MILITANCY = f"{PERSON}/militancia/11291"
OLD_PARTY = "http://datos.bcn.cl/recurso/cl/organismo/partido-politico/partido-democrata-cristiano"
CURRENT_PARTY = "http://datos.bcn.cl/recurso/cl/organismo/partido-politico/partido-democratas-chile"


def rdf_fixture():
    return {
        PERSON: {
            FOAF_NAME: [literal("Ximena Rincón González")],
            FOAF_GENDER: [literal("mujer")],
            BCNBIO_NATIONALITY: [uri("http://datos.bcn.cl/recurso/pais/chile")],
            BCNBIO_HAS_BORN: [uri(BIRTH)],
            FOAF_IMG: [uri("https://www.bcn.cl/laborparlamentaria/imagen/2362.jpg")],
            BCNBIO_HAS_MILITANCY: [uri(OLD_MILITANCY), uri(CURRENT_MILITANCY)],
        },
        BIRTH: {
            DC_DATE: [literal("1968-07-05")],
            BIO_PLACE: [literal("Concepción")],
        },
        OLD_MILITANCY: {
            BCNBIO_HAS_POLITICAL_PARTY: [uri(OLD_PARTY)],
            BCNBIO_HAS_BEGINNING: [uri(f"{OLD_MILITANCY}/inicio")],
            BCNBIO_HAS_END: [uri(f"{OLD_MILITANCY}/fin")],
        },
        CURRENT_MILITANCY: {
            BCNBIO_HAS_POLITICAL_PARTY: [uri(CURRENT_PARTY)],
            BCNBIO_HAS_BEGINNING: [uri(f"{CURRENT_MILITANCY}/inicio")],
        },
        f"{OLD_MILITANCY}/inicio": {
            BCNBIO_ORIGINAL_DATE: [literal("1990-03-11")],
        },
        f"{OLD_MILITANCY}/fin": {
            BCNBIO_ORIGINAL_DATE: [literal("2022-11-01")],
        },
        f"{CURRENT_MILITANCY}/inicio": {
            BCNBIO_ORIGINAL_DATE: [literal("2022-11-02")],
        },
        OLD_PARTY: {
            RDFS_LABEL: [literal("Partido Demócrata Cristiano")],
        },
        CURRENT_PARTY: {
            RDFS_LABEL: [literal("Partido Demócratas Chile")],
        },
    }


def fixture_fetcher(resource_url):
    resource_url = canonical_resource_url(resource_url)
    fixture = rdf_fixture()
    return {resource_url: fixture.get(resource_url, {})}


def test_bcn_person_url_helpers_build_expected_json_url():
    assert is_bcn_person_url("https://datos.bcn.cl/recurso/persona/1778")
    assert not is_bcn_person_url("https://es.wikipedia.org/wiki/Jeannette_Jara")
    assert (
        rdf_json_url("https://datos.bcn.cl/recurso/persona/1778/datos.rdf")
        == "https://datos.bcn.cl/recurso/persona/1778/datos.json"
    )


def test_fetch_parliamentarian_data_extracts_current_militancy_without_end():
    data = fetch_parliamentarian_data(
        PERSON,
        fetcher=fixture_fetcher,
        include_all_militancies=True,
        fetch_militancy_dates=True,
    )

    assert data["data_status"] == "ok"
    assert data["person_id"] == "2362"
    assert data["name"] == "Ximena Rincón González"
    assert data["gender"] == "mujer"
    assert data["nationality"] == "Chile"
    assert data["birth_date"] == "1968-07-05"
    assert data["birth_place"] == "Concepción"
    assert data["image_url"] == "https://www.bcn.cl/laborparlamentaria/imagen/2362.jpg"
    assert data["current_militancy_href"] == CURRENT_MILITANCY
    assert data["current_party"] == "Partido Demócratas Chile"
    assert data["current_militancy_start_date"] == "2022-11-02"
    assert data["current_militancy_end_date"] is None
    assert data["has_current_militancy"] is True
    assert data["militancy_count"] == 2
    assert len(data["militancies"]) == 2
    assert data["militancies"][0]["is_current"] is False
    assert data["militancies"][1]["is_current"] is True


def test_collect_bcn_speaker_references_reads_participations_and_metadata():
    speech_content = {
        "metadata": {
            "persons": {
                "per1": {
                    "id": "per1",
                    "show_as": "ximena rincon gonzalez",
                    "href": PERSON,
                }
            }
        },
        "debate_body": {
            "point_of_order": [{
                "projects": [{
                    "items": [
                        {"kind": "participation", "speaker_id": "per1", "speaker": "Ximena Rincón", "role": "Senadora"},
                        {"kind": "unlabeled_text", "content": ["Texto procedimental."]},
                        {
                            "kind": "participation",
                            "speaker_id": "PersonaExt1",
                            "speaker_href": "https://es.wikipedia.org/wiki/Jeannette_Jara",
                            "speaker": "Jeannette Jara",
                        },
                        {
                            "kind": "participation",
                            "speaker_id": "per2",
                            "speaker_href": PERSON,
                            "speaker": "Ximena Rincón González",
                            "role": "Senadora",
                        },
                    ]
                }]
            }]
        },
    }
    df = pd.DataFrame({"speech_content": [speech_content], "title": ["Discusión en Sala"], "date": ["2025-01-01"]})

    refs = collect_bcn_speaker_references(df)

    assert len(refs) == 1
    row = refs.iloc[0]
    assert row["person_href"] == PERSON
    assert row["person_id"] == "2362"
    assert row["speaker_ids"] == ["per1", "per2"]
    assert row["roles_seen"] == ["Senadora"]
    assert row["participation_count"] == 2
    assert row["document_count"] == 1
    assert row["first_title"] == "Discusión en Sala"


def test_build_parliamentarian_table_merges_speaker_refs_and_bcn_data():
    speech_content = {
        "metadata": {"persons": {"per1": {"id": "per1", "href": PERSON, "show_as": "ximena rincon gonzalez"}}},
        "debate_body": {"items": [{"kind": "participation", "speaker_id": "per1", "role": "Senadora"}]},
    }
    df = pd.DataFrame({"speech_content": [speech_content]})

    table = build_parliamentarian_table(df, fetcher=fixture_fetcher, include_all_militancies=False)

    assert len(table) == 1
    assert table.loc[0, "person_href"] == PERSON
    assert table.loc[0, "name"] == "Ximena Rincón González"
    assert table.loc[0, "current_party"] == "Partido Demócratas Chile"
    assert "militancies" not in table.columns
