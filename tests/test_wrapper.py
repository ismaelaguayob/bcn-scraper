from bcn_scraper.wrapper import historia_dataframe_from_ley_o_boletin
from bcn_scraper.historia_dataframe import historia_tramites_to_dataframe
from bcn_scraper.historia_lookup import HistoriaLookup
from bcn_scraper.historia_client import HistoriaClient


def test_wrapper_returns_dataframe(monkeypatch):
    def fake_search(self, query=None, *, numero_ley=None, numero_boletin=None):
        return [type('R', (), {'identificador': '1'})()]

    def fake_fetch(self, identificador):
        return b'''<?xml version="1.0" encoding="utf-8"?>
        <historia>
          <titulo>Norma</titulo>
          <bajada>Resumen</bajada>
          <fecha_publicacion>01-01-2000</fecha_publicacion>
          <tramite_reglamentario>
            <titulo>Tramite 1</titulo>
            <bajada>Detalle</bajada>
            <xml>
              <div class="item" fecha="1999-12-31"><p>Hola</p></div>
            </xml>
          </tramite_reglamentario>
        </historia>'''

    monkeypatch.setattr(HistoriaLookup, "search", fake_search)
    monkeypatch.setattr(HistoriaClient, "fetch_historia_xml", fake_fetch)

    df = historia_dataframe_from_ley_o_boletin(numero_ley="123", clean_text=True)
    assert "tramite_texto" in df.columns
    assert "tramite_fecha" in df.columns
