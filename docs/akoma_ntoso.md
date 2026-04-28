# Akoma Ntoso

Ubicación: `src/bcn_scraper/akoma_ntoso.py`

## Descripción
Utilidades para construir y descargar XML Akoma Ntoso desde URIs de documentos
BCN (`uriDocumento`).

## Funciones
- `akn_url_from_document_uri(document_uri: str) -> str`
  - Convierte `http://datos.bcn.cl/recurso/cl/documento/707224` en
    `http://datos.bcn.cl/recurso/cl/documento/707224.xml`.
- `fetch_akoma_ntoso(akn_url: str, timeout: int = 30, max_attempts: int = 1, backoff_seconds: float = 0.0) -> str`
  - Descarga el XML Akoma Ntoso, valida que sea XML bien formado y que la raíz
    sea `akomaNtoso`.
  - Por defecto no reintenta, para evitar esperas largas en extracciones
    completas.
  - Si hay error HTTP, error de red o XML inválido, retorna un string que
    comienza con `ERROR:`.
- `add_akoma_ntoso_content(df, fetcher=fetch_akoma_ntoso)`
  - Retorna una copia del DataFrame con `akn_content` poblado a partir de
    `akn_url`.
- `is_retryable_akn_error(value: str) -> bool`
  - Identifica errores de timeout, handshake o red que conviene reintentar en
    una segunda pasada.
  - No marca como reintentables los HTTP 500 ni los errores de XML inválido.
- `debug_akoma_ntoso_errors(df, timeout: int = 90, max_attempts: int = 3, backoff_seconds: float = 2.0)`
  - Recibe un DataFrame creado por el wrapper y reintenta solo filas cuyo
    `akn_content` contiene errores de timeout/handshake/red.
  - Omite errores HTTP 500 y errores de parseo porque BCN puede devolver
    payloads no XML (`{"status":"error"}`) para documentos sin AKN usable.

## Manejo de Errores
BCN puede responder contenido no XML para algunos documentos. Por ejemplo,
`https://datos.bcn.cl/recurso/cl/documento/706988.xml` puede responder
`{"status":"error"}`. En esos casos se preserva la fila y `akn_content` queda
con un mensaje `ERROR: invalid XML ...`.

La descarga Akoma Ntoso es opcional porque puede tomar varios segundos por
documento y no todas las leyes o trámites tienen AKN publicado. Es útil cuando
se necesitan IDs de actores u otra metadata que no está disponible en el XML de
Historia de la Ley.
