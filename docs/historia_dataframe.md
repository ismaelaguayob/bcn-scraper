# historia_dataframe

Ubicación: `src/bcn_scraper/historia_dataframe.py`

## Descripción
Funciones auxiliares para convertir XML de Historia de la Ley en DataFrame.

## Funciones
- `clean_tramite_html(html: str) -> str`
  - Limpia tags y devuelve texto legible por líneas.
- `extract_document_uri(html: str) -> str`
  - Extrae `uriDocumento` desde el HTML embebido de cada trámite.
- `historia_tramites_to_dataframe(xml_bytes: bytes, clean_text: bool = False, bcn_url: str = "")`
  - Convierte el XML en un DataFrame de trámites reglamentarios.
  - Extrae `date` desde el atributo `fecha` del HTML embebido.
  - Extrae `xml_url` desde `uriDocumento` y construye `akn_url`.
  - Si `clean_text=True`, rellena `txt_content`; si no, deja la columna vacía.
- `historia_tramite_xmls_to_dataframe(xmls: Iterable[bytes], clean_text: bool = False, bcn_url: str = "")`
  - Convierte una lista de XMLs individuales en un único DataFrame.
  - Mantiene el orden de los XMLs recibidos.

## Columnas
El DataFrame usa nombres en inglés y este orden:

1. `title`: título del trámite.
2. `date`: fecha del trámite en formato `YYYY-MM-DD`, si está disponible.
3. `excerpt`: bajada/resumen del trámite.
4. `xml_content`: HTML/XML embebido del trámite.
5. `txt_content`: texto limpio del trámite.
6. `akn_content`: XML Akoma Ntoso descargado por el wrapper, o `ERROR: ...`.
7. `xml_url`: URI BCN del documento (`uriDocumento`).
8. `akn_url`: URL Akoma Ntoso (`xml_url + ".xml"`).
9. `law_title`: título de la Historia de la Ley.
10. `law_excerpt`: bajada/resumen de la Historia de la Ley.
11. `publication_date`: fecha de publicación de la norma.
12. `bcn_url`: URL de la página Historia de la Ley usada como fuente.

## Dependencias
- Requiere `pandas`.
- Requiere `beautifulsoup4` para limpieza de HTML.

## Notas
- `historia_tramites_to_dataframe` no descarga Akoma Ntoso; solo construye
  `akn_url`. La descarga se hace en el wrapper o con `add_akoma_ntoso_content`.
