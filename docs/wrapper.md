# Wrapper: Historia DataFrame

Ubicación: `src/bcn_scraper/wrapper.py`

## Descripción
Wrapper para resolver el ID de Historia de la Ley a partir de número de ley o
boletín y devolver un DataFrame con trámites reglamentarios.

## Funciones
- `historia_dataframe_from_ley_o_boletin(numero_ley: Optional[str], numero_boletin: Optional[str], clean_text: bool = False)`
  - Usa `HistoriaLookup.search` (advanced para ley/boletín; si falla, lanza error).
  - Descarga XML con `HistoriaClient`.
  - Convierte a DataFrame con `historia_tramites_to_dataframe`.
  - Retorna solo el DataFrame.

## Notas
- Requiere `pandas`.
- `clean_text=True` agrega `tramite_texto` con HTML limpiado.
