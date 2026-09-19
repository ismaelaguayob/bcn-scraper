"""Small, synthetic person histories; no network requests in this module."""
from datetime import date, datetime

import pandas as pd
import pytest

from bcn_scraper.parliamentary_data import (
    BCNBIO_ORIGINAL_DATE, BCNBIO_HAS_END, BCNBIO_HAS_MILITANCY,
    build_parliamentarian_table, canonical_resource_url, debug_parliamentarian_data_errors,
    fetch_parliamentarian_data, missing_parliamentarian_data_mask,
)
from test_parliamentary_data import (
    PERSON, OLD_MILITANCY, CURRENT_MILITANCY, OLD_PARTY, CURRENT_PARTY,
    literal, rdf_fixture, fixture_fetcher,
)


def custom_fetcher(fixture):
    def fetch(resource):
        key = canonical_resource_url(resource)
        return {key: fixture.get(key, {})}
    return fetch


@pytest.mark.parametrize("selector", [None, "current", "latest"])
def test_current_mode_keeps_fast_legacy_behavior(selector):
    calls = []
    def fetch(resource):
        calls.append(resource)
        return fixture_fetcher(resource)
    person = fetch_parliamentarian_data(PERSON, fetcher=fetch, date=selector)
    assert person["current_party_href"] == CURRENT_PARTY
    assert person["party_at_date"] is None
    assert "militancies" not in person
    assert not any(url.endswith(("/inicio", "/fin")) for url in calls)


def test_all_includes_dated_history_without_extra_flags():
    person = fetch_parliamentarian_data(PERSON, fetcher=fixture_fetcher, date="all")
    assert person["militancy_selection"] == "all"
    assert person["current_party_href"] == CURRENT_PARTY
    assert [(m["start_date"], m["end_date"]) for m in person["militancies"]] == [
        ("1990-03-11", "2022-11-01"), ("2022-11-02", None)]


@pytest.mark.parametrize("selector,party", [
    ("1990-03-10", None), ("1990-03-11", OLD_PARTY), ("2022-01-03", OLD_PARTY),
    ("2022-11-01", OLD_PARTY), ("2022-11-02", CURRENT_PARTY),
    (date(2022, 1, 3), OLD_PARTY), (datetime(2025, 1, 29, 12), CURRENT_PARTY),
])
def test_date_selects_historical_party_with_inclusive_boundaries(selector, party):
    person = fetch_parliamentarian_data(PERSON, fetcher=fixture_fetcher, date=selector)
    assert person["party_at_date_href"] == party
    assert person["current_party_href"] == CURRENT_PARTY  # never relabel historical as current
    assert person["militancy_at_date_status"] == ("matched" if party else "not_found")


def test_overlap_is_ambiguous_and_does_not_select_first_party():
    fixture = rdf_fixture()
    fixture[f"{CURRENT_MILITANCY}/inicio"][BCNBIO_ORIGINAL_DATE] = [literal("2022-11-01")]
    person = fetch_parliamentarian_data(PERSON, fetcher=custom_fetcher(fixture), date="2022-11-01")
    assert person["militancy_at_date_status"] == "ambiguous"
    assert person["party_at_date"] is None
    assert len(person["militancy_at_date_candidates"]) == 2


@pytest.mark.parametrize("start,target,status", [
    ("2022", "2022-11-03", "uncertain_dates"),
    ("2022", "2023-01-01", "matched"),
    ("2022-11", "2022-11-20", "uncertain_dates"),
    ("2022-11", "2022-12-01", "matched"),
    ("unknown", "2023-01-01", "uncertain_dates"),
])
def test_partial_dates_do_not_impute_start_day(start,target,status):
    fixture = rdf_fixture()
    fixture[f"{CURRENT_MILITANCY}/inicio"][BCNBIO_ORIGINAL_DATE] = [literal(start)]
    person = fetch_parliamentarian_data(PERSON, fetcher=custom_fetcher(fixture), date=target)
    assert person["militancy_at_date_status"] == status
    if status != "matched":
        assert person["party_at_date"] is None


def test_missing_linked_end_is_not_treated_as_open_ended():
    fixture = rdf_fixture()
    fixture.pop(f"{OLD_MILITANCY}/fin")
    person = fetch_parliamentarian_data(PERSON, fetcher=custom_fetcher(fixture), date="2025-01-29")
    assert person["militancy_at_date_status"] == "uncertain_dates"
    assert person["party_at_date"] is None


def test_no_history_does_not_invent_independent_affiliation():
    fixture = rdf_fixture()
    fixture[PERSON][BCNBIO_HAS_MILITANCY] = []
    person = fetch_parliamentarian_data(PERSON, fetcher=custom_fetcher(fixture), date="2022-01-03")
    assert person["militancy_at_date_status"] == "not_found"
    assert person["party_at_date"] is None


@pytest.mark.parametrize("selector", ["2022-02-30", "2022", "2022-1-3", "typo", 2022, pd.NaT])
def test_invalid_selector_fails_before_network(selector):
    def forbid(_):
        raise AssertionError("network must not be reached")
    with pytest.raises((ValueError, TypeError)):
        fetch_parliamentarian_data(PERSON, fetcher=forbid, date=selector)


def test_builder_forwards_date_and_deduplicates_one_person():
    speech={"debate_body":{"items":[{"kind":"participation", "speaker_href":PERSON}]}}
    frame=pd.DataFrame({"speech_content":[speech,speech]})
    table=build_parliamentarian_table(frame,fetcher=fixture_fetcher,date="2022-01-03",show_progress=False)
    assert len(table)==1
    assert table.loc[0,"party_at_date_href"]==OLD_PARTY
    assert table.loc[0,"participation_count"]==2


def test_debug_refreshes_for_new_date_and_skips_already_resolved_rows():
    old=fetch_parliamentarian_data(PERSON,fetcher=fixture_fetcher,date="2022-01-03")
    frame=pd.DataFrame([old])
    repaired=debug_parliamentarian_data_errors(frame,fetcher=fixture_fetcher,date="2025-01-29",show_progress=False)
    assert repaired.loc[0,"party_at_date_href"]==CURRENT_PARTY
    assert frame.loc[0,"reference_date"]=="2022-01-03"
    def forbid(_):
        raise AssertionError("complete rows should not be fetched")
    debug_parliamentarian_data_errors(repaired,fetcher=forbid,date="2025-01-29",show_progress=False)


def test_debug_detects_missing_dates_in_old_history_and_force_works():
    person=fetch_parliamentarian_data(PERSON,fetcher=fixture_fetcher,date="all")
    person["militancies"][0]["end_date"]=None
    frame=pd.DataFrame([person])
    assert missing_parliamentarian_data_mask(frame,date="all").tolist()==[True]
    repaired=debug_parliamentarian_data_errors(frame,fetcher=fixture_fetcher,date="all",show_progress=False)
    assert repaired.loc[0,"militancies"][0]["end_date"]=="2022-11-01"
    calls=[]
    def fetch(resource):
        calls.append(resource)
        return fixture_fetcher(resource)
    debug_parliamentarian_data_errors(repaired,fetcher=fetch,date="all",force=True,show_progress=False)
    assert PERSON in calls


def test_cli_small_parquet_refresh_preserves_metadata_and_backup(tmp_path,monkeypatch):
    pytest.importorskip("pyarrow")
    import bcn_scraper.parliamentarians_cli as cli
    monkeypatch.setattr(cli,"CachedRDFJsonFetcher",lambda **kwargs: fixture_fetcher)
    source=tmp_path/"parliamentarians.parquet"
    original=pd.DataFrame({
        "person_href":[PERSON],"speaker_ids":[["per1"]],"note":["keep"],
        "current_militancy_start_date":[float("nan")],
        "current_militancy_end_date":[float("nan")],
        "reference_date":[float("nan")],"party_at_date":[float("nan")],
    })
    original.to_parquet(source,index=False)
    assert cli.main(["--input",str(source),"--date","all","--no-progress"])==0
    result=pd.read_parquet(source)
    assert len(result)==1 and result.loc[0,"note"]=="keep"
    assert len(result.loc[0,"militancies"])==2
    assert result.loc[0,"current_militancy_start_date"]=="2022-11-02"
    backups=list(tmp_path.glob("*.bak"))
    assert len(backups)==1 and pd.read_parquet(backups[0]).loc[0,"note"]=="keep"
    assert cli.main(["--input",str(source),"--date","2022-01-03","--limit","1",
                     "--output-dir",str(tmp_path/"sample"),"--no-progress"])==0
    sampled=pd.read_parquet(next((tmp_path/"sample").glob("*.parquet")))
    assert sampled.loc[0,"party_at_date_href"]==OLD_PARTY
    assert pd.read_parquet(source).loc[0,"militancy_selection"]=="all"


def test_cli_rejects_sample_overwrite_before_fetch(tmp_path,monkeypatch):
    import bcn_scraper.parliamentarians_cli as cli
    def forbid(**_):
        raise AssertionError("network must not be reached")
    monkeypatch.setattr(cli,"CachedRDFJsonFetcher",forbid)
    with pytest.raises(SystemExit):
        cli.main(["--input",str(tmp_path/"missing.parquet"),"--limit","2"])


def test_failed_history_resource_does_not_assign_current_party_to_past():
    def fetch(resource):
        if resource == OLD_MILITANCY:
            raise RuntimeError("simulated unavailable resource")
        return fixture_fetcher(resource)
    person = fetch_parliamentarian_data(PERSON, fetcher=fetch, date="2025-01-29")
    assert person["militancy_at_date_status"] == "uncertain_dates"
    assert person["party_at_date"] is None
    assert missing_parliamentarian_data_mask(pd.DataFrame([person]),date="2025-01-29").tolist() == [True]


def test_debug_clears_stale_historical_fields_when_switching_to_current():
    person = fetch_parliamentarian_data(PERSON,fetcher=fixture_fetcher,date="2022-01-03")
    frame = pd.DataFrame([person])
    repaired = debug_parliamentarian_data_errors(frame,date="current",fetcher=fixture_fetcher,show_progress=False)
    assert repaired.loc[0,"militancy_selection"] == "current"
    assert pd.isna(repaired.loc[0,"reference_date"])
    assert pd.isna(repaired.loc[0,"party_at_date"])


@pytest.mark.parametrize("selector", ["current", "all", "2022-01-03"])
def test_debug_fills_numeric_null_columns_from_legacy_parquet(tmp_path, selector):
    pytest.importorskip("pyarrow")
    person = fetch_parliamentarian_data(PERSON, fetcher=fixture_fetcher)
    # Legacy exports can represent unrequested or missing fields as float NaN.
    for key in ("birth_date", "current_militancy_start_date", "current_militancy_end_date",
                "has_current_militancy", "militancies", "militancy_at_date_candidates",
                "reference_date", "party_at_date", "error"):
        person[key] = float("nan")
    person.update(participation_count=7, note="preserve")
    source = tmp_path / "legacy.parquet"
    pd.DataFrame([person]).to_parquet(source, index=False)
    original = pd.read_parquet(source)
    assert original["current_militancy_start_date"].dtype == "float64"
    snapshot = original.copy(deep=True)

    repaired = debug_parliamentarian_data_errors(
        original, fetcher=fixture_fetcher, date=selector, show_progress=False, force=True,
    )

    pd.testing.assert_frame_equal(original, snapshot)
    pd.testing.assert_frame_equal(repaired[["participation_count", "note"]],
                                  original[["participation_count", "note"]])
    assert repaired.loc[0, "birth_date"] == "1968-07-05"
    assert bool(repaired.loc[0, "has_current_militancy"]) is True
    if selector != "current":
        assert repaired.loc[0, "current_militancy_start_date"] == "2022-11-02"
        assert len(repaired.loc[0, "militancies"]) == 2
    if selector == "2022-01-03":
        assert repaired.loc[0, "party_at_date_href"] == OLD_PARTY
    output = tmp_path / "refreshed.parquet"
    repaired.to_parquet(output, index=False)
    assert pd.read_parquet(output).loc[0, "birth_date"] == "1968-07-05"


def test_debug_records_fetch_error_in_numeric_null_column():
    original = pd.DataFrame({"person_href": [PERSON], "error": [float("nan")]})

    def unavailable(_):
        raise RuntimeError("simulated unavailable person")

    repaired = debug_parliamentarian_data_errors(
        original, fetcher=unavailable, date="all", show_progress=False,
    )
    assert repaired.loc[0, "data_status"] == "fetch_error"
    assert repaired.loc[0, "error"] == "simulated unavailable person"
    assert pd.isna(original.loc[0, "error"])
