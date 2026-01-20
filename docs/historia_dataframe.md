# historia_dataframe

Ubicación: `src/bcn_scraper/historia_dataframe.py`

## Descripción
Funciones auxiliares para convertir XML de Historia de la Ley en DataFrame.

## Funciones
- `clean_tramite_html(html: str) -> str`
  - Limpia tags y devuelve texto legible por líneas.
- `historia_tramites_to_dataframe(xml_bytes: bytes, clean_text: bool = False)`
  - Convierte el XML en un DataFrame de trámites reglamentarios.
  - Agrega metadatos de la norma (título, bajada, fecha de publicación).
  - Extrae `tramite_fecha` desde el atributo `fecha` del HTML embebido.
  - Si `clean_text=True`, agrega `tramite_texto`.

## Dependencias
- Requiere `pandas`.
- Requiere `beautifulsoup4` para limpieza de HTML.

## Notas
- El contenido HTML queda en la columna `tramite_contenido_html`.
