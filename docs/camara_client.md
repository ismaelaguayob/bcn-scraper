# CamaraClient

Ubicación: `src/bcn_scraper/camara_client.py`

## Descripción
Cliente mínimo para obtener y parsear la tramitación desde la Cámara de Diputados.

## Métodos
- `fetch_tramitacion(prm_id: str, prm_boletin: str) -> str`
  - Descarga el HTML de tramitación usando `prmID` y `prmBOLETIN`.
- `parse_tramitacion(html: str) -> List[Dict[str, str]]`
  - Busca la tabla con encabezados esperados y extrae filas.
  - Devuelve: fecha, sesión, etapa, subetapa, URL de documento.

## Notas
- Usa BeautifulSoup y requiere `beautifulsoup4`.
- Devuelve URLs absolutas cuando existen enlaces de documento.
