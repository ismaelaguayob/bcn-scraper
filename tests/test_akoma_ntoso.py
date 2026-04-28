from urllib.error import HTTPError

from bcn_scraper.akoma_ntoso import (
    AKN_ERROR_PREFIX,
    add_akoma_ntoso_content,
    akn_url_from_document_uri,
    debug_akoma_ntoso_errors,
    fetch_akoma_ntoso,
    is_retryable_akn_error,
)


class FakeResponse:
    def __init__(self, content):
        self.content = content

    def read(self):
        return self.content


def test_akn_url_from_document_uri():
    assert (
        akn_url_from_document_uri("http://datos.bcn.cl/recurso/cl/documento/707224")
        == "http://datos.bcn.cl/recurso/cl/documento/707224.xml"
    )
    assert (
        akn_url_from_document_uri("http://datos.bcn.cl/recurso/cl/documento/707224/")
        == "http://datos.bcn.cl/recurso/cl/documento/707224.xml"
    )
    assert akn_url_from_document_uri("") == ""


def test_fetch_akoma_ntoso_validates_xml(monkeypatch):
    def fake_urlopen(req, timeout):
        return FakeResponse(b'<?xml version="1.0"?><akomaNtoso><doc /></akomaNtoso>')

    monkeypatch.setattr("bcn_scraper.akoma_ntoso.urlopen", fake_urlopen)

    content = fetch_akoma_ntoso("http://datos.bcn.cl/recurso/cl/documento/1.xml")

    assert content.startswith('<?xml version="1.0"?>')
    assert "<akomaNtoso>" in content


def test_fetch_akoma_ntoso_returns_error_for_invalid_xml(monkeypatch):
    def fake_urlopen(req, timeout):
        return FakeResponse(b'{"status":"error"}')

    monkeypatch.setattr("bcn_scraper.akoma_ntoso.urlopen", fake_urlopen)

    content = fetch_akoma_ntoso(
        "http://datos.bcn.cl/recurso/cl/documento/706988.xml",
        max_attempts=1,
    )

    assert content.startswith(AKN_ERROR_PREFIX)
    assert "invalid XML" in content


def test_fetch_akoma_ntoso_returns_error_for_unexpected_xml_root(monkeypatch):
    def fake_urlopen(req, timeout):
        return FakeResponse(b'<?xml version="1.0"?><error />')

    monkeypatch.setattr("bcn_scraper.akoma_ntoso.urlopen", fake_urlopen)

    content = fetch_akoma_ntoso(
        "http://datos.bcn.cl/recurso/cl/documento/1.xml",
        max_attempts=1,
    )

    assert content.startswith(AKN_ERROR_PREFIX)
    assert "unexpected XML root" in content


def test_fetch_akoma_ntoso_does_not_retry_invalid_xml(monkeypatch):
    calls = {"count": 0}

    def fake_urlopen(req, timeout):
        calls["count"] += 1
        return FakeResponse(b'{"status":"error"}')

    monkeypatch.setattr("bcn_scraper.akoma_ntoso.urlopen", fake_urlopen)

    content = fetch_akoma_ntoso(
        "http://datos.bcn.cl/recurso/cl/documento/706988.xml",
        max_attempts=2,
    )

    assert calls["count"] == 1
    assert content.startswith(AKN_ERROR_PREFIX)
    assert "invalid XML" in content


def test_fetch_akoma_ntoso_does_not_retry_http_500(monkeypatch):
    calls = {"count": 0}

    def fake_urlopen(req, timeout):
        calls["count"] += 1
        raise HTTPError(req.full_url, 500, "server error", hdrs=None, fp=None)

    monkeypatch.setattr("bcn_scraper.akoma_ntoso.urlopen", fake_urlopen)

    content = fetch_akoma_ntoso(
        "http://datos.bcn.cl/recurso/cl/documento/704345.xml",
        max_attempts=2,
    )

    assert calls["count"] == 1
    assert content.startswith(f"{AKN_ERROR_PREFIX} HTTP 500")


def test_fetch_akoma_ntoso_retries_http_503(monkeypatch):
    calls = {"count": 0}

    def fake_urlopen(req, timeout):
        calls["count"] += 1
        if calls["count"] == 1:
            raise HTTPError(req.full_url, 503, "server unavailable", hdrs=None, fp=None)
        return FakeResponse(b'<akomaNtoso />')

    monkeypatch.setattr("bcn_scraper.akoma_ntoso.urlopen", fake_urlopen)
    monkeypatch.setattr("bcn_scraper.akoma_ntoso.sleep", lambda seconds: None)

    content = fetch_akoma_ntoso(
        "http://datos.bcn.cl/recurso/cl/documento/704345.xml",
        max_attempts=2,
    )

    assert calls["count"] == 2
    assert content == "<akomaNtoso />"


def test_fetch_akoma_ntoso_does_not_retry_http_404(monkeypatch):
    calls = {"count": 0}

    def fake_urlopen(req, timeout):
        calls["count"] += 1
        raise HTTPError(req.full_url, 404, "not found", hdrs=None, fp=None)

    monkeypatch.setattr("bcn_scraper.akoma_ntoso.urlopen", fake_urlopen)

    content = fetch_akoma_ntoso(
        "http://datos.bcn.cl/recurso/cl/documento/missing.xml",
        max_attempts=3,
    )

    assert calls["count"] == 1
    assert content.startswith(f"{AKN_ERROR_PREFIX} HTTP 404")


def test_add_akoma_ntoso_content_uses_akn_url():
    import pandas as pd

    df = pd.DataFrame({"akn_url": ["http://example.test/1.xml", ""]})

    enriched = add_akoma_ntoso_content(df, fetcher=lambda url: f"<xml>{url}</xml>")

    assert enriched.loc[0, "akn_content"] == "<xml>http://example.test/1.xml</xml>"
    assert enriched.loc[1, "akn_content"] == ""


def test_is_retryable_akn_error_detects_only_network_errors():
    assert is_retryable_akn_error(
        "ERROR: URL error for http://datos.bcn.cl/recurso/cl/documento/704058.xml: "
        "_ssl.c:1063: The handshake operation timed out; attempts=3"
    )
    assert is_retryable_akn_error("ERROR: network error for http://example.test: timed out")
    assert not is_retryable_akn_error("ERROR: HTTP 500 for http://example.test; attempts=1")
    assert not is_retryable_akn_error("ERROR: invalid XML for http://example.test")
    assert not is_retryable_akn_error("<akomaNtoso />")


def test_debug_akoma_ntoso_errors_retries_only_network_rows():
    import pandas as pd

    df = pd.DataFrame({
        "akn_url": [
            "http://datos.bcn.cl/recurso/cl/documento/704058.xml",
            "http://datos.bcn.cl/recurso/cl/documento/706777.xml",
            "http://datos.bcn.cl/recurso/cl/documento/706988.xml",
            "http://datos.bcn.cl/recurso/cl/documento/707224.xml",
        ],
        "akn_content": [
            "ERROR: URL error for http://datos.bcn.cl/recurso/cl/documento/704058.xml: "
            "The handshake operation timed out; attempts=1",
            "ERROR: HTTP 500 for http://datos.bcn.cl/recurso/cl/documento/706777.xml; attempts=1",
            "ERROR: invalid XML for http://datos.bcn.cl/recurso/cl/documento/706988.xml",
            "<akomaNtoso />",
        ],
    })
    calls = []

    def fake_fetcher(url):
        calls.append(url)
        return f"<akomaNtoso>{url}</akomaNtoso>"

    result = debug_akoma_ntoso_errors(df, fetcher=fake_fetcher)

    assert calls == ["http://datos.bcn.cl/recurso/cl/documento/704058.xml"]
    assert result.loc[0, "akn_content"].startswith("<akomaNtoso>")
    assert result.loc[1, "akn_content"].startswith("ERROR: HTTP 500")
    assert result.loc[2, "akn_content"].startswith("ERROR: invalid XML")
    assert result.loc[3, "akn_content"] == "<akomaNtoso />"
