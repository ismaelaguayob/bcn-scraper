from bcn_scraper.historia_client import HistoriaClient


def test_extract_payloads_from_local_html():
    client = HistoriaClient()
    with open('data/externo/historia_search_xajax_21735.xml', 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()
    payloads = client.extract_payloads(html)
    assert payloads, "Expected payloads from local Historia HTML"


def test_extract_tramite_payloads_from_historia_page_fixture():
    client = HistoriaClient()
    with open('data/historia_8372.html', 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()

    payloads = client.extract_tramite_payloads(html)
    by_pos = {payload.raw["pos"]: payload.raw for payload in payloads}

    assert "4-4" in by_pos
    assert "4-5" in by_pos
    assert '"707224"' in by_pos["4-4"]["hdncheck"]
    assert '"706990"' in by_pos["4-5"]["hdncheck"]
