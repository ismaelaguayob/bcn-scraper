# HistoriaLookup

Ubicación: `src/bcn_scraper/historia_lookup.py`

## Descripción
Buscador para Historia de la Ley con dos flujos:
- búsqueda simple para keywords (varios resultados).
- búsqueda avanzada para número de ley o boletín (preferencia por ID exacto).

## Clases
### HistoriaSearchResult
- `identificador: str`
- `url: str`
- `titulo: str`
- `numero_ley: str`

### HistoriaLookup
#### Métodos
- `search_simple(query: str) -> List[HistoriaSearchResult]`
  - Ejecuta la búsqueda simple XAJAX y parsea IDs/metadatos básicos.
- `search_by_ley_or_boletin(numero_ley: Optional[str], numero_boletin: Optional[str]) -> List[HistoriaSearchResult]`
  - Usa búsqueda avanzada para ley/boletín. Si no hay resultados, lanza error e indica usar keywords.
- `search(query: Optional[str], numero_ley: Optional[str], numero_boletin: Optional[str]) -> List[HistoriaSearchResult]`
  - Enruta a simple o avanzada según el tipo de búsqueda.

## Notas
- Para keywords se recomienda la búsqueda simple por su cobertura.
- Para ley/boletín se usa búsqueda avanzada; si falla, se debe intentar con keywords.
