"""Selective AKN fetching must never request omitted tramites."""

import socket
from types import SimpleNamespace

import pandas as pd
import pytest

from bcn_scraper.akoma_ntoso import add_akoma_ntoso_content, debug_akoma_ntoso_errors
from bcn_scraper.historia_client import HistoriaClient, HistoriaXmlDownload
from bcn_scraper.historia_lookup import HistoriaLookup
from bcn_scraper.wrapper import historia_dataframe_from_ley_o_boletin


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def fail(*args, **kwargs):
        pytest.fail("Tests must not access the network")

    monkeypatch.setattr(socket.socket, "connect", fail)
    monkeypatch.setattr(socket, "create_connection", fail)


@pytest.fixture(params=["individual", "aggregate", "fallback"])
def history_mode(request, monkeypatch):
    tramites = [
        ("1.1. Mensaje", "1"),
        ("1.2. Discusión en Sala", "2"),
        ("2.1. Informe de Comisión", "3"),
        ("2.2. Discusión en Sala", "4"),
    ]
    fragments = [
        f'<tramite_reglamentario><titulo>{title}</titulo><xml>'
        f'<div fecha="2025-01-01" uriDocumento="http://example.test/{number}">'
        f'<p>{title}</p></div></xml></tramite_reglamentario>'
        for title, number in tramites
    ]

    def download(content):
        return HistoriaXmlDownload(
            content=f"<historia>{content}</historia>".encode(),
            xml_url="http://example.test/historia.xml",
        )

    def individual(self, identifier):
        if request.param == "aggregate":
            pytest.fail("Individual XML should not be requested")
        return [download(fragment) for fragment in fragments] if request.param == "individual" else []

    def aggregate(self, identifier):
        if request.param == "individual":
            pytest.fail("Aggregate XML should not be requested")
        return download("".join(fragments))

    monkeypatch.setattr(HistoriaLookup, "search", lambda *args, **kwargs: [
        SimpleNamespace(identificador="1", url="http://example.test/historia/")
    ])
    monkeypatch.setattr(HistoriaClient, "fetch_tramite_xml_downloads", individual)
    monkeypatch.setattr(HistoriaClient, "fetch_historia_xml_download", aggregate)
    return request.param


@pytest.mark.parametrize("selection, expected", [
    (None, ["1", "2", "3", "4"]),
    (lambda tramite: "Discusión en Sala" in tramite["title"], ["2", "4"]),
    (lambda tramite: tramite["document_uri"] == "http://example.test/4", ["4"]),
    (lambda tramite: False, []),
])
def test_wrapper_selects_akn_without_removing_history(history_mode, selection, expected):
    calls = []

    def fetcher(url):
        calls.append(url)
        return "<akomaNtoso />"

    result = historia_dataframe_from_ley_o_boletin(
        numero_ley="21735",
        clean_text=True,
        prefer_individual_tramites=history_mode != "aggregate",
        fetch_akn=True,
        akn_filter=selection,
        akn_fetcher=fetcher,
    )

    assert calls == [f"http://example.test/{number}.xml" for number in expected]
    assert list(result["document_uri"]) == [f"http://example.test/{n}" for n in range(1, 5)]
    assert result["xml_content"].str.contains("<p>").all()
    assert result["txt_content"].str.len().gt(0).all()
    assert list(result["akn_content"]) == [
        "<akomaNtoso />" if str(n) in expected else "" for n in range(1, 5)
    ]

    # Omitted AKN stays blank and must not trigger a second-pass download.
    def unexpected_retry(url):
        pytest.fail(f"Unexpected retry for {url}")

    pd.testing.assert_frame_equal(
        debug_akoma_ntoso_errors(result, fetcher=unexpected_retry), result
    )


def test_fetch_akn_false_ignores_filter_and_fetcher(history_mode):
    def fail(value):
        pytest.fail("fetch_akn=False must skip both filter and fetcher")

    result = historia_dataframe_from_ley_o_boletin(
        numero_ley="21735",
        prefer_individual_tramites=history_mode != "aggregate",
        fetch_akn=False,
        akn_filter=fail,
        akn_fetcher=fail,
    )
    assert len(result) == 4
    assert result["akn_content"].eq("").all()


def test_add_akn_preserves_unselected_cached_content_and_input():
    source = pd.DataFrame({
        "title": ["Informe", "Discusión en Sala", "Discusión en Sala", "Discusión en Sala"],
        "akn_url": ["http://example.test/1", "http://example.test/2", "", None],
        "akn_content": ["cached", "old", "", ""],
    }, index=[4, 9, 12, 20])
    before = source.copy(deep=True)
    calls = []

    def fetcher(url):
        calls.append(url)
        return "new"

    result = add_akoma_ntoso_content(
        source, fetcher=fetcher,
        akn_filter=lambda tramite: tramite["title"] == "Discusión en Sala",
    )

    assert calls == ["http://example.test/2"]
    assert list(result["akn_content"]) == ["cached", "new", "", ""]
    assert list(result.index) == [4, 9, 12, 20]
    pd.testing.assert_frame_equal(source, before)


@pytest.mark.parametrize("source", [
    pd.DataFrame(columns=["title", "akn_url"]),
    pd.DataFrame({"title": ["Informe"]}),
])
def test_add_akn_handles_empty_history_or_missing_url(source):
    def fail(value):
        pytest.fail("No filter or fetch is needed without AKN URLs")

    result = add_akoma_ntoso_content(source, fetcher=fail, akn_filter=fail)
    assert list(result["title"]) == list(source["title"])
    assert "akn_content" in result
    assert result["akn_content"].eq("").all()
