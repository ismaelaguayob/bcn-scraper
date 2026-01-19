# HistoriaClient

Ubicación: `src/bcn_scraper/historia_client.py`

## Descripción
Cliente para Historia de la Ley que replica el flujo XAJAX:
HTML -> payloads -> llamada XAJAX -> URL `obtienearchivo` -> descarga de XML.

## Clases
### HistoriaPayload
Representa el payload JSON usado por `herrDescargarXML`.
- `raw: Dict[str, object]`
- `identificador` (property): retorna el identificador si existe.

### HistoriaClient
#### Métodos
- `__init__(base: str = "https://www.bcn.cl/historiadelaley/")`
  - Configura la base de URLs.
- `fetch_historia_html(identificador: str) -> str`
  - Descarga el HTML de una Historia de la Ley.
- `extract_payloads(html: str) -> List[HistoriaPayload]`
  - Extrae payloads JSON de handlers `herrDescargarXML`.
- `xajax_endpoint_from_html(html: str) -> Optional[str]`
  - Lee `xajaxRequestUri` desde el HTML.
- `request_xml_url(xajax_url: str, payload: HistoriaPayload) -> str`
  - Ejecuta `xajax=herrDescargarXML` y parsea la respuesta para obtener el XML.
- `fetch_historia_xml(identificador: str) -> bytes`
  - Implementa el flujo completo de descarga XML.
- `parse_tramites(xml_bytes: bytes) -> List[Dict[str, str]]`
  - Extrae trámites reglamentarios con `titulo`, `bajada`, `contenido_html`.

## Notas
- El flujo depende de HTML y XAJAX; cambios en el sitio pueden romperlo.
- `parse_tramites` devuelve HTML embebido en `contenido_html`.
