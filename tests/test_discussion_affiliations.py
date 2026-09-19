"""Tiny saved histories and discussion tables; all requests use local fixtures."""
from collections import Counter
import hashlib

import pandas as pd
import pytest

from bcn_scraper.discussion_affiliations import (
    DiscussionAffiliationResolver, PersistentRDFJsonFetcher, discussion_references,
)
from bcn_scraper.parliamentary_data import fetch_parliamentarian_data
from test_parliamentary_data import PERSON, CURRENT_MILITANCY, OLD_PARTY, CURRENT_PARTY, fixture_fetcher


def forbid(*args, **kwargs):
    raise AssertionError('No network request expected')


def speeches():
    return pd.DataFrame([
        {'person_href': PERSON, 'date': day, 'document_uri': document,
         'kind': 'participation', 'analysis_included': True}
        for day, document in [('2022-01-03', 'doc1'), ('2025-01-29', 'doc2'), ('2022-01-03', 'doc1')]
    ])


def history():
    return fetch_parliamentarian_data(PERSON, fetcher=fixture_fetcher, date='all')


def test_uses_each_actual_discussion_and_complete_history_from_another_law():
    saved = history()
    saved['first_date'] = '2030-01-01'
    saved['birth_date'] = None  # Unrelated biography gaps do not trigger requests.
    resolver = DiscussionAffiliationResolver([
        pd.DataFrame([{'person_href': PERSON, 'data_status': 'fetch_error'}]), pd.DataFrame([saved])
    ], forbid)
    result = resolver.table(discussion_references(speeches()))
    assert len(result) == 2
    assert result.party_at_date_href.tolist() == [OLD_PARTY, CURRENT_PARTY]
    assert result.reference_date.tolist() == ['2022-01-03', '2025-01-29']
    assert 'militancies' not in result and 'current_party' not in result
    assert result.affiliation_data_status.tolist() == ['ok', 'ok']


@pytest.mark.parametrize('failed_resource', [CURRENT_MILITANCY, CURRENT_MILITANCY + '/inicio'])
def test_rerun_retries_failed_resource_and_reuses_successful_downloads(tmp_path, failed_resource):
    first_calls = Counter()
    def first_fetch(resource):
        first_calls[resource] += 1
        if resource == failed_resource:
            raise RuntimeError('handshake timeout')
        return fixture_fetcher(resource)
    saved = [pd.DataFrame([{'person_href': PERSON, 'data_status': 'fetch_error'}])]
    first = DiscussionAffiliationResolver(saved, PersistentRDFJsonFetcher(tmp_path, first_fetch))
    assert first.resolve(PERSON, '2025-01-29')['affiliation_data_status'] == 'incomplete'
    failed_path = tmp_path / (hashlib.sha256(failed_resource.encode()).hexdigest() + '.json')
    assert not failed_path.exists()

    second_calls = Counter()
    def second_fetch(resource):
        second_calls[resource] += 1
        return fixture_fetcher(resource)
    second = DiscussionAffiliationResolver(saved, PersistentRDFJsonFetcher(tmp_path, second_fetch))
    result = second.table(discussion_references(speeches()))
    assert result.party_at_date_href.tolist() == [OLD_PARTY, CURRENT_PARTY]
    assert set(first_calls) & set(second_calls) == {failed_resource}
    assert all(n == 1 for n in second_calls.values())
    third = DiscussionAffiliationResolver(saved, PersistentRDFJsonFetcher(tmp_path, forbid))
    assert third.resolve(PERSON, '2025-01-29')['party_at_date_href'] == CURRENT_PARTY


def test_offline_missing_history_is_unavailable_not_independent():
    resolver = DiscussionAffiliationResolver([], forbid, offline=True)
    result = resolver.resolve(PERSON, '2022-01-03')
    assert result['militancy_at_date_status'] == 'unavailable'
    assert result['party_at_date'] is None
    assert result['affiliation_data_status'] == 'incomplete'


@pytest.mark.parametrize('value', [None, 'all', '2022-02-30'])
def test_rejects_missing_or_invalid_discussion_dates(value):
    frame = speeches()
    frame.loc[0, 'date'] = value
    with pytest.raises((TypeError, ValueError)):
        discussion_references(frame)


def test_empty_and_non_bcn_speakers():
    frame = speeches()
    frame['person_href'] = 'https://example.org/external'
    refs = discussion_references(frame)
    result = DiscussionAffiliationResolver([], forbid).table(refs)
    assert result.empty and 'party_at_date' in result


def test_cli_exports_only_dated_affiliations_preserving_sources(tmp_path, monkeypatch):
    pytest.importorskip('pyarrow')
    import bcn_scraper.discussion_affiliations as module
    from bcn_scraper.parliamentarians_cli import main
    monkeypatch.setattr(module, 'PersistentRDFJsonFetcher', lambda *args, **kwargs: forbid)
    folder = tmp_path / 'ley_1'
    folder.mkdir()
    source = folder / 'parliamentarians.parquet'
    pd.DataFrame([history()]).to_parquet(source, index=False)
    speech_path = folder / 'speech_df.parquet'
    speeches().to_parquet(speech_path, index=False)
    before = {p: p.read_bytes() for p in [source, speech_path]}
    args = ['--input', str(source), '--date', 'discussions', '--no-progress']
    assert main(args) == 0
    output = folder / 'parliamentarian_affiliations.parquet'
    result = pd.read_parquet(output)
    assert result.party_at_date_href.tolist() == [OLD_PARTY, CURRENT_PARTY]
    assert main(args) == 0
    assert len(list(folder.glob('parliamentarian_affiliations.parquet.*.bak'))) == 1
    for path, content in before.items():
        assert path.read_bytes() == content
    assert main(args + ['--limit', '1', '--output-dir', str(tmp_path / 'sample')]) == 0
    sample = pd.read_parquet(next((tmp_path / 'sample').glob('*.parquet')))
    assert len(sample) == 1
    assert len(pd.read_parquet(output)) == 2


def test_cli_validates_all_laws_before_any_download(tmp_path, monkeypatch):
    pytest.importorskip('pyarrow')
    import bcn_scraper.discussion_affiliations as module
    from bcn_scraper.parliamentarians_cli import main
    monkeypatch.setattr(module, 'PersistentRDFJsonFetcher', forbid)
    source = tmp_path / 'parliamentarians.parquet'
    pd.DataFrame([{'person_href': PERSON}]).to_parquet(source)
    speeches().to_parquet(tmp_path / 'speech_df.parquet')
    with pytest.raises(SystemExit):
        main(['--input', str(source), str(tmp_path / 'missing.parquet'), '--date', 'discussions'])
