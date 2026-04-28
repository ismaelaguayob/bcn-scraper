# Wrapper: Historia DataFrame

Ubicación: `src/bcn_scraper/wrapper.py`

## Descripción
Wrapper para resolver el ID de Historia de la Ley a partir de número de ley o
boletín y devolver un DataFrame con trámites reglamentarios.

## Funciones
- `historia_dataframe_from_ley_o_boletin(numero_ley: Optional[str], numero_boletin: Optional[str], clean_text: bool = False, prefer_individual_tramites: bool = True, fetch_akn: bool = False, akn_fetcher=fetch_akoma_ntoso)`
  - Usa `HistoriaLookup.search` (advanced para ley/boletín; si falla, lanza error).
  - Por defecto descarga los XML individuales de cada trámite reglamentario con `HistoriaClient.fetch_tramite_xml_downloads`.
  - Si no hay payloads individuales, usa el XML agregado de `HistoriaClient.fetch_historia_xml_download`.
  - Convierte a DataFrame con `historia_tramite_xmls_to_dataframe` o `historia_tramites_to_dataframe`.
  - Guarda en `xml_url` la URL real de descarga del XML de Historia de la Ley.
  - Construye `akn_url` desde `uriDocumento` agregando `.xml`.
  - Si `fetch_akn=True`, descarga Akoma Ntoso y rellena `akn_content`.
  - Retorna el DataFrame con columnas estandarizadas en inglés.

## Notas
- Requiere `pandas`.
- `clean_text=True` rellena `txt_content` con HTML limpiado.
- `prefer_individual_tramites=True` evita inconsistencias detectadas en algunos XML agregados de BCN.
- `fetch_akn=False` es el valor por defecto. Activa `fetch_akn=True` solo si
  necesitas IDs de actores u otra metadata disponible en Akoma Ntoso.
- Si Akoma Ntoso falla o no es XML válido, `akn_content` queda con un mensaje
  que comienza con `ERROR:`.
- La descarga AKN usa por defecto `timeout=30` y `max_attempts=1`. Para casos
  extremos, usa `debug_akoma_ntoso_errors`, que reintenta solo timeouts,
  handshakes o errores de red con parámetros más agresivos.
- BCN no tiene AKN usable para todos los documentos; algunos endpoints devuelven
  HTTP 500 o contenido no XML como `{"status":"error"}`.
