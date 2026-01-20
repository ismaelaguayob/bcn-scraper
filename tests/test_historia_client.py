from bcn_scraper.historia_client import HistoriaClient


def test_extract_payloads_from_local_html():
    client = HistoriaClient()
    with open('data/externo/historia_search_xajax_21735.xml', 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()
    payloads = client.extract_payloads(html)
    assert payloads, "Expected payloads from local Historia HTML"
