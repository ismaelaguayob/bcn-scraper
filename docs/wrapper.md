# Wrapper: Historia DataFrame

Ubicación: `src/bcn_scraper/wrapper.py`

## Descripción
Wrapper para resolver el ID de Historia de la Ley a partir de número de ley o
boletín y devolver un DataFrame con trámites reglamentarios.

## Clases
### HistoriaWrapperResult
- `query: str`
- `identificador: str`
- `result: HistoriaSearchResult`

## Funciones
- `historia_dataframe_from_ley_o_boletin(numero_ley: Optional[str], numero_boletin: Optional[str])`
  - Usa `HistoriaLookup.search` (advanced para ley/boletín con fallback simple).
  - Descarga XML con `HistoriaClient`.
  - Convierte a DataFrame con `historia_tramites_to_dataframe`.
  - Retorna `(HistoriaWrapperResult, DataFrame)`.

## Notas
- Requiere `pandas` instalado (`.[dataframe]`).
