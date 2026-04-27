# Akoma Ntoso

Ubicación: `src/bcn_scraper/akoma_ntoso.py`

## Descripción
Utilidades para construir y descargar XML Akoma Ntoso desde URIs de documentos
BCN (`uriDocumento`).

## Funciones
- `akn_url_from_document_uri(document_uri: str) -> str`
  - Convierte `http://datos.bcn.cl/recurso/cl/documento/707224` en
    `http://datos.bcn.cl/recurso/cl/documento/707224.xml`.
- `fetch_akoma_ntoso(akn_url: str, timeout: int = 60, max_attempts: int = 3, backoff_seconds: float = 2.0) -> str`
  - Descarga el XML Akoma Ntoso, valida que sea XML bien formado y que la raíz
    sea `akomaNtoso`.
  - Reintenta errores transitorios: timeout/errores de red, HTTP 500/502/503/504
    y respuestas no XML temporales.
  - Si hay error HTTP, error de red o XML inválido, retorna un string que
    comienza con `ERROR:`.
- `add_akoma_ntoso_content(df, fetcher=fetch_akoma_ntoso)`
  - Retorna una copia del DataFrame con `akn_content` poblado a partir de
    `akn_url`.

## Manejo de Errores
BCN puede responder contenido no XML para algunos documentos. Por ejemplo,
`https://datos.bcn.cl/recurso/cl/documento/706988.xml` puede responder
`{"status":"error"}`. En esos casos se preserva la fila y `akn_content` queda
con un mensaje `ERROR: invalid XML ...` solo si se agotan los reintentos.
