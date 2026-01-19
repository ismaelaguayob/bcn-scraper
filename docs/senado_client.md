# SenadoClient

Ubicación: `src/bcn_scraper/senado_client.py`

## Descripción
Cliente para tramitación del Senado. Permite descargar HTML de boletín, datos del
proyecto y tramitación, y parsear filas con enlaces a documentos.

## Clases
### SenadoDocumento
- `tipo: str`
- `url: str`

### SenadoClient
#### Métodos
- `fetch_boletin(boletin: str) -> str`
  - Descarga HTML del boletín.
- `fetch_datos_proy(boletin: str) -> str`
  - Descarga HTML con datos del proyecto.
- `extract_proyid(datos_html: str) -> Optional[str]`
  - Extrae el `proyid` desde el HTML.
- `fetch_tramites(proyid: str) -> str`
  - Descarga HTML de trámites.
- `parse_tramites(tramites_html: str) -> List[Dict[str, str]]`
  - Extrae filas de trámites con metadatos y URL de documentos.

## Notas
- Usa BeautifulSoup y requiere `beautifulsoup4`.
- Las URLs de documentos pueden ser relativas a los endpoints del Senado.
