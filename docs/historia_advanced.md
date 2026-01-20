# HistoriaAdvancedSearch

Ubicación: `src/bcn_scraper/historia_advanced.py`

## Descripción
Cliente para búsqueda avanzada en Historia de la Ley usando el flujo XAJAX.
Se usa para resolver número de ley o boletín con mejor precisión.

## Clases
### AdvancedSearchResult
- `identificador: str`
- `url: str`
- `titulo: str`
- `numero_ley: str`

### HistoriaAdvancedSearch
#### Métodos
- `_call_ver_texto(query_json: str) -> str`
  - Ejecuta `xajax=verTextoCompleto` con JSON de criterios.
- `_extract_list_url(xajax_resp: str) -> Optional[str]`
  - Extrae la URL de resultados desde la respuesta XAJAX.
- `_fetch_list_page(list_url: str) -> str`
  - Descarga el HTML de la lista de resultados.
- `_xajax_list_uri(html: str) -> Optional[str]`
  - Lee `xajaxRequestUri` desde el HTML de resultados.
- `_fetch_list_results(xajax_list_url: str) -> str`
  - Ejecuta `xajax=mostrarResultadoBusqueda` para obtener resultados.
- `_parse_results(xajax_resp: str) -> List[AdvancedSearchResult]`
  - Parsea IDs y metadatos desde la respuesta.
- `search(...) -> List[AdvancedSearchResult]`
  - Construye el JSON de criterios y retorna resultados.

## Notas
- Para búsqueda exacta por número se usa `numero` con espacio inicial.
- Para boletín se usa el campo `boletin` (no `numero_boletines`).
- Otros criterios pueden retornar vacío según comportamiento del sitio.
