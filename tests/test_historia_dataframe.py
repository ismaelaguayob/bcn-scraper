from bcn_scraper.historia_dataframe import (
    DATAFRAME_COLUMNS,
    clean_tramite_html,
    extract_document_uri,
    historia_tramites_to_dataframe,
)


def test_clean_tramite_html_basic():
    html = '<div><h2>Titulo</h2><p>Linea 1</p><p>Linea 2</p><script>ignore()</script></div>'
    text = clean_tramite_html(html)
    assert 'Titulo' in text
    assert 'Linea 1' in text
    assert 'Linea 2' in text
    assert 'ignore' not in text


def test_historia_tramites_to_dataframe_order_and_clean():
    xml = b'''<?xml version="1.0" encoding="utf-8"?>
    <historia>
      <titulo>Norma</titulo>
        <bajada>Resumen</bajada>
      <fecha_publicacion>01-01-2000</fecha_publicacion>
      <tramite_reglamentario>
        <titulo>Tramite 1</titulo>
        <bajada>Detalle</bajada>
        <xml>
          <div class="item" fecha="1999-12-31" uriDocumento="http://datos.bcn.cl/recurso/cl/documento/1"><p>Hola <b>mundo</b></p></div>
        </xml>
      </tramite_reglamentario>
    </historia>'''
    df = historia_tramites_to_dataframe(
        xml,
        clean_text=True,
        bcn_url="https://www.bcn.cl/historiadelaley/nc/historia-de-la-ley/1/",
        xml_url="https://www.bcn.cl/historiadelaley/obtienearchivo?id=1",
    )
    assert list(df.columns) == DATAFRAME_COLUMNS
    assert df.loc[0, 'date'] == '1999-12-31'
    assert df.loc[0, 'title'] == 'Tramite 1'
    assert df.loc[0, 'excerpt'] == 'Detalle'
    assert df.loc[0, 'xml_url'] == 'https://www.bcn.cl/historiadelaley/obtienearchivo?id=1'
    assert df.loc[0, 'document_uri'] == 'http://datos.bcn.cl/recurso/cl/documento/1'
    assert df.loc[0, 'akn_url'] == 'http://datos.bcn.cl/recurso/cl/documento/1.xml'
    assert df.loc[0, 'law_title'] == 'Norma'
    assert df.loc[0, 'law_excerpt'] == 'Resumen'
    assert df.loc[0, 'publication_date'] == '01-01-2000'
    assert df.loc[0, 'bcn_url'] == 'https://www.bcn.cl/historiadelaley/nc/historia-de-la-ley/1/'
    assert 'Hola' in df.loc[0, 'txt_content']
    assert 'mundo' in df.loc[0, 'txt_content']


def test_extract_document_uri():
    html = '<div uriDocumento="http://datos.bcn.cl/recurso/cl/documento/704142"></div>'
    assert extract_document_uri(html) == "http://datos.bcn.cl/recurso/cl/documento/704142"
    assert extract_document_uri("<div></div>") == ""
