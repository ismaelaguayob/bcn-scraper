from bcn_scraper.wrapper import historia_dataframe_from_ley_o_boletin
from bcn_scraper.historia_lookup import HistoriaLookup
from bcn_scraper.historia_client import HistoriaClient, HistoriaXmlDownload


def test_wrapper_returns_dataframe(monkeypatch):
    def fake_search(self, query=None, *, numero_ley=None, numero_boletin=None):
        return [type('R', (), {
            'identificador': '1',
            'url': 'https://www.bcn.cl/historiadelaley/nc/historia-de-la-ley/1/',
        })()]

    def fake_fetch(self, identificador):
        return HistoriaXmlDownload(content=b'''<?xml version="1.0" encoding="utf-8"?>
        <historia>
          <titulo>Norma</titulo>
          <bajada>Resumen</bajada>
          <fecha_publicacion>01-01-2000</fecha_publicacion>
          <tramite_reglamentario>
            <titulo>Tramite 1</titulo>
            <bajada>Detalle</bajada>
            <xml>
              <div class="item" fecha="1999-12-31" uriDocumento="http://datos.bcn.cl/recurso/cl/documento/1"><p>Hola</p></div>
            </xml>
          </tramite_reglamentario>
        </historia>''', xml_url="https://www.bcn.cl/historiadelaley/obtienearchivo?id=1")

    def fake_fetch_tramite_xml_downloads(self, identificador):
        return []

    monkeypatch.setattr(HistoriaLookup, "search", fake_search)
    monkeypatch.setattr(HistoriaClient, "fetch_tramite_xml_downloads", fake_fetch_tramite_xml_downloads)
    monkeypatch.setattr(HistoriaClient, "fetch_historia_xml_download", fake_fetch)

    df = historia_dataframe_from_ley_o_boletin(numero_ley="123", clean_text=True)
    assert "txt_content" in df.columns
    assert "date" in df.columns
    assert df.loc[0, "xml_url"] == "https://www.bcn.cl/historiadelaley/obtienearchivo?id=1"
    assert df.loc[0, "akn_url"] == "http://datos.bcn.cl/recurso/cl/documento/1.xml"
    assert df.loc[0, "akn_content"] == ""


def test_wrapper_prefers_individual_tramite_xmls(monkeypatch):
    def fake_search(self, query=None, *, numero_ley=None, numero_boletin=None):
        return [type('R', (), {
            'identificador': '8372',
            'url': 'https://www.bcn.cl/historiadelaley/nc/historia-de-la-ley/8372/',
        })()]

    def fake_fetch_tramite_xml_downloads(self, identificador):
        return [
            HistoriaXmlDownload(content=b'''<?xml version="1.0" encoding="utf-8"?>
            <historia>
              <titulo>Norma</titulo>
              <bajada>Resumen</bajada>
              <fecha_publicacion>01-01-2000</fecha_publicacion>
              <tramite_reglamentario>
                <titulo>4.4. Oficio del Tribunal Constitucional</titulo>
                <bajada>Sentencia de Requerimiento. Fecha 03 de marzo, 2025.</bajada>
                <xml>
                  <div class="item" fecha="2025-03-03" uriDocumento="http://datos.bcn.cl/recurso/cl/documento/707224"><h2>4.4. Oficio del Tribunal Constitucional</h2></div>
                </xml>
              </tramite_reglamentario>
            </historia>''', xml_url="https://www.bcn.cl/historiadelaley/obtienearchivo?id=707224"),
            HistoriaXmlDownload(content=b'''<?xml version="1.0" encoding="utf-8"?>
            <historia>
              <titulo>Norma</titulo>
              <bajada>Resumen</bajada>
              <fecha_publicacion>01-01-2000</fecha_publicacion>
              <tramite_reglamentario>
                <titulo>4.5. Oficio del Tribunal Constitucional</titulo>
                <bajada>Sentencia del Tribunal Constitucional. Fecha 07 de marzo, 2025.</bajada>
                <xml>
                  <div class="item" fecha="2025-03-07" uriDocumento="http://datos.bcn.cl/recurso/cl/documento/706990"><h2>4.5. Oficio del Tribunal Constitucional</h2></div>
                </xml>
              </tramite_reglamentario>
            </historia>''', xml_url="https://www.bcn.cl/historiadelaley/obtienearchivo?id=706990"),
        ]

    def fail_fetch(self, identificador):
        raise AssertionError("aggregate XML should not be fetched")

    monkeypatch.setattr(HistoriaLookup, "search", fake_search)
    monkeypatch.setattr(HistoriaClient, "fetch_tramite_xml_downloads", fake_fetch_tramite_xml_downloads)
    monkeypatch.setattr(HistoriaClient, "fetch_historia_xml_download", fail_fetch)

    df = historia_dataframe_from_ley_o_boletin(numero_ley="21735", fetch_akn=False)

    assert list(df["title"]) == [
        "4.4. Oficio del Tribunal Constitucional",
        "4.5. Oficio del Tribunal Constitucional",
    ]
    assert list(df["date"]) == ["2025-03-03", "2025-03-07"]
    assert "707224" in df.loc[0, "xml_content"]
    assert "706990" in df.loc[1, "xml_content"]
    assert df.loc[0, "xml_url"] == "https://www.bcn.cl/historiadelaley/obtienearchivo?id=707224"
    assert df.loc[1, "akn_url"] == "http://datos.bcn.cl/recurso/cl/documento/706990.xml"


def test_wrapper_fetches_akoma_ntoso_content(monkeypatch):
    def fake_search(self, query=None, *, numero_ley=None, numero_boletin=None):
        return [type('R', (), {
            'identificador': '1',
            'url': 'https://www.bcn.cl/historiadelaley/nc/historia-de-la-ley/1/',
        })()]

    def fake_fetch_tramite_xml_downloads(self, identificador):
        return [
            HistoriaXmlDownload(content=b'''<?xml version="1.0" encoding="utf-8"?>
            <historia>
              <titulo>Norma</titulo>
              <bajada>Resumen</bajada>
              <fecha_publicacion>01-01-2000</fecha_publicacion>
              <tramite_reglamentario>
                <titulo>Tramite 1</titulo>
                <bajada>Detalle</bajada>
                <xml>
                  <div class="item" fecha="1999-12-31" uriDocumento="http://datos.bcn.cl/recurso/cl/documento/1"><p>Hola</p></div>
                </xml>
              </tramite_reglamentario>
            </historia>''', xml_url="https://www.bcn.cl/historiadelaley/obtienearchivo?id=1"),
        ]

    monkeypatch.setattr(HistoriaLookup, "search", fake_search)
    monkeypatch.setattr(HistoriaClient, "fetch_tramite_xml_downloads", fake_fetch_tramite_xml_downloads)

    df = historia_dataframe_from_ley_o_boletin(
        numero_ley="1",
        clean_text=True,
        fetch_akn=True,
        akn_fetcher=lambda url: f"<akomaNtoso>{url}</akomaNtoso>",
    )

    assert df.loc[0, "akn_content"] == "<akomaNtoso>http://datos.bcn.cl/recurso/cl/documento/1.xml</akomaNtoso>"
