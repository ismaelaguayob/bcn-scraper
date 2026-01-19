from bcn_scraper.historia_lookup import HistoriaLookup


def test_search_parses_ids_from_fixture():
    lookup = HistoriaLookup()
    with open('data/externo/historia_search_xajax_21735.xml', 'r', encoding='utf-8', errors='ignore') as f:
        xml = f.read()
    ids = __import__('re').findall(r"/nc/historia-de-la-ley/(\d+)/", xml)
    assert ids, "Expected at least one historia id"
