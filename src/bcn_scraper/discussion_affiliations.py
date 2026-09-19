"""Resolve affiliations for actual speaker/discussion dates, reusing BCN data."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile

import pandas as pd

from .parliamentary_data import (
    CachedRDFJsonFetcher, _is_missing_value, _militancy_at_date, _militancy_options,
    canonical_resource_url, fetch_parliamentarian_data, is_bcn_person_url,
)


class PersistentRDFJsonFetcher(CachedRDFJsonFetcher):
    """Cache successful RDF responses across runs; never cache failed requests."""

    def __init__(self, cache_dir, fetcher=None, **kwargs):
        super().__init__(fetcher, **kwargs)
        self.cache_dir = Path(cache_dir)

    def __call__(self, resource_url):
        key = canonical_resource_url(resource_url)
        if key in self.cache:
            return self.cache[key]
        path = self.cache_dir / (hashlib.sha256(key.encode()).hexdigest() + '.json')
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding='utf-8'))
                if isinstance(data, dict):
                    self.cache[key] = data
                    return data
            except (ValueError, OSError):
                pass
        data = super().__call__(key)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(dir=self.cache_dir, suffix='.json')
        try:
            with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
                json.dump(data, stream, ensure_ascii=False)
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return data


def _history(record):
    value = record.get('militancies')
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return None
    if hasattr(value, 'tolist'):
        value = value.tolist()
    if not isinstance(value, (list, tuple)) or not all(isinstance(m, dict) for m in value):
        return None
    return list(value)


def _complete_history(record):
    history = _history(record)
    if record.get('data_status') != 'ok' or history is None:
        return False
    try:
        selection, day, _, _ = _militancy_options(record.get('militancy_selection'), False, False)
    except (ValueError, TypeError):
        return False
    if selection != 'all' and day is None:
        return False
    for item in history:
        if not _is_missing_value(item.get('error')):
            return False
        for href, field in (('start_href', 'start_date'), ('end_href', 'end_date')):
            if not _is_missing_value(item.get(href)) and _is_missing_value(item.get(field)):
                return False
    return True


def discussion_references(speeches):
    """One BCN person per discussion, using the discussion date, never first_date."""
    required = {'person_href', 'document_uri', 'date', 'kind'}
    if not required.issubset(speeches.columns):
        raise ValueError(f'Missing speech columns: {sorted(required - set(speeches.columns))}')
    mask = speeches['kind'].eq('participation') & speeches['person_href'].map(is_bcn_person_url)
    if 'analysis_included' in speeches:
        mask &= speeches['analysis_included'].fillna(False).astype(bool)
    refs = speeches.loc[mask, ['document_uri', 'date', 'person_href']].copy()
    refs['person_href'] = refs['person_href'].map(canonical_resource_url)
    days = []
    for value in refs['date']:
        selection, day, _, _ = _militancy_options(value, False, False)
        if day is None:
            raise ValueError('Every discussion requires a concrete date')
        days.append(selection)
    refs['date'] = days
    if refs['document_uri'].map(_is_missing_value).any():
        raise ValueError('Every discussion requires document_uri')
    if refs.groupby('document_uri')['date'].nunique().gt(1).any():
        raise ValueError('A discussion has conflicting dates')
    return refs.drop_duplicates().reset_index(drop=True)


class DiscussionAffiliationResolver:
    """Share complete saved histories and one fetch per person across laws/dates."""

    def __init__(self, tables, fetcher, *, offline=False):
        self.fetcher = fetcher
        self.offline = offline
        self.saved = {}
        self.resolved = {}
        for table in tables:
            for record in table.to_dict('records'):
                person = record.get('person_href')
                if not is_bcn_person_url(person):
                    continue
                person = canonical_resource_url(person)
                if person not in self.saved or _complete_history(record):
                    self.saved[person] = record

    def resolve(self, person, date):
        person = canonical_resource_url(person)
        _, day, _, _ = _militancy_options(date, False, False)
        if day is None:
            raise ValueError('A concrete discussion date is required')
        if person not in self.resolved:
            record = self.saved.get(person, {})
            if not _complete_history(record) and not self.offline:
                # BCN exposes intervals. Read them to establish membership at
                # the requested dates; only the selected affiliation is exported.
                record = fetch_parliamentarian_data(person, fetcher=self.fetcher, date='all')
            self.resolved[person] = record
        record = self.resolved[person]
        history = _history(record)
        selection = _militancy_at_date(history or [], day)
        if history is None:
            selection['militancy_at_date_status'] = 'unavailable'
        return {
            **selection,
            'affiliation_data_status': 'ok' if _complete_history(record) else 'incomplete',
            'affiliation_error': None if _is_missing_value(record.get('error')) else record['error'],
        }

    def table(self, references):
        rows = [dict(ref, **self.resolve(ref['person_href'], ref['date']))
                for ref in references.to_dict('records')]
        if rows:
            return pd.DataFrame(rows)
        sample = self.resolve_empty()
        return pd.DataFrame(columns=[*references.columns, *sample])

    @staticmethod
    def resolve_empty():
        _, day, _, _ = _militancy_options('2000-01-01', False, False)
        return {**_militancy_at_date([], day), 'affiliation_data_status': None, 'affiliation_error': None}


def run_discussions(args, parser, write_parquet):
    """CLI mode: validate inputs, then resolve only observed speaker/date pairs."""
    sources = list(dict.fromkeys(path.resolve() for path in args.input))
    work = []
    destinations = set()
    for source in sources:
        speech_path = source.with_name('speech_df.parquet')
        if not source.is_file() or not speech_path.is_file():
            parser.error(f'Requires {source} and {speech_path}')
        table = pd.read_parquet(source)
        if 'person_href' not in table:
            parser.error(f'Missing person_href: {source}')
        try:
            refs = discussion_references(pd.read_parquet(speech_path))
        except (TypeError, ValueError) as exc:
            parser.error(f'{speech_path}: {exc}')
        destination = (args.output_dir / f'{source.parent.name}_parliamentarian_affiliations.parquet'
                       if args.output_dir is not None
                       else source.with_name('parliamentarian_affiliations.parquet'))
        destination = destination.resolve()
        if destination in destinations or destination in sources or destination == speech_path:
            parser.error(f'Output collision: {destination}')
        destinations.add(destination)
        work.append((table, refs, destination))
    loader = PersistentRDFJsonFetcher(args.cache_dir, timeout=args.timeout,
                                      max_attempts=args.max_attempts,
                                      backoff_seconds=args.backoff_seconds)
    resolver = DiscussionAffiliationResolver([item[0] for item in work], loader, offline=args.offline)
    remaining = args.limit
    for _, refs, destination in work:
        if remaining is not None:
            if remaining == 0:
                break
            refs = refs.head(remaining)
            remaining -= len(refs)
        if not args.no_progress:
            print(f'{destination.parent.name}: resolving {len(refs)} person/discussion pairs', flush=True)
        result = resolver.table(refs)
        write_parquet(result, destination)
        print(f'{destination}: {len(result)} rows; '
              f'{result["militancy_at_date_status"].value_counts().to_dict()}', flush=True)
        pending = int(result['affiliation_data_status'].ne('ok').sum())
        if pending:
            print(f'Incomplete person/discussion pairs: {pending}; rerun to retry, or inspect source dates')
    return 0
