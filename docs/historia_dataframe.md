# historia_dataframe

Ubicación: `src/bcn_scraper/historia_dataframe.py`

## Descripción
Funciones auxiliares para convertir XML de Historia de la Ley en DataFrame.

## Funciones
- `historia_tramites_to_dataframe(xml_bytes: bytes)`
  - Convierte el XML en un DataFrame de trámites reglamentarios.
  - Agrega metadatos de la norma (título, bajada, fecha de publicación).

## Dependencias
- Requiere `pandas` (opcional, no instalado por defecto).

## Notas
- Lanza `ImportError` si pandas no está disponible.
- El contenido HTML queda en la columna `tramite_contenido_html`.
