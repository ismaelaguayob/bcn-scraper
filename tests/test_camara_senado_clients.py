from bcn_scraper.camara_client import CamaraClient
from bcn_scraper.senado_client import SenadoClient


def test_camara_parse_local_html():
    client = CamaraClient()
    with open('data/externo/camara_tramitacion.html', 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()
    rows = client.parse_tramitacion(html)
    assert rows, "Expected rows from Camara tramitacion HTML"


def test_senado_parse_local_html():
    client = SenadoClient()
    with open('data/externo/senado_tramites_16006.html', 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()
    rows = client.parse_tramites(html)
    assert rows, "Expected rows from Senado tramites HTML"
