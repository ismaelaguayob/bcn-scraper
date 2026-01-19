# HistoriaSuggest

Ubicación: `src/bcn_scraper/historia_suggest.py`

## Descripción
Cliente de sugerencias para Historia de la Ley. Consulta el endpoint
`eID=sugerenciaBusqueda` para obtener listas de términos.

## Clases
### SuggestResult
- `value: str`

### HistoriaSuggest
#### Métodos
- `suggest(topic: str, word: str) -> List[SuggestResult]`
  - Envía la consulta con `topico` y `palabra` y parsea la lista JSON.

## Notas
- Topics observados: `numero_boletines`, `numeroley`, `palabras_frases`, `autores`.
