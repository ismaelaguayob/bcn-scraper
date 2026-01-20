from bcn_scraper.historia_dataframe import clean_tramite_html, historia_tramites_to_dataframe


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
          <div class="item" fecha="1999-12-31"><p>Hola <b>mundo</b></p></div>
        </xml>
      </tramite_reglamentario>
    </historia>'''
    df = historia_tramites_to_dataframe(xml, clean_text=True)
    assert list(df.columns).index('fecha_publicacion') < list(df.columns).index('tramite_fecha')
    assert df.loc[0, 'tramite_fecha'] == '1999-12-31'
    assert 'tramite_texto' in df.columns
    assert 'Hola' in df.loc[0, 'tramite_texto']
    assert 'mundo' in df.loc[0, 'tramite_texto']
