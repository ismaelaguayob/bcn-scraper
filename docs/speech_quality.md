# Speech quality

Ubicación: `src/bcn_scraper/speech_quality.py`

## Funciones

- `build_speech_quality_report(manifest, source_df, speech_df, speech_df_full=None)`
  - Genera una fila por documento declarado en el manifiesto.
  - Comprueba presencia de fuente, título, fecha, XML/texto, estado AKN,
    contenido vacío, URI/fecha faltante, boletines inesperados, rutas/índices
    duplicados, consistencia de `n_chars` e identidades resueltas solo por regex.
  - Cuenta filas discursivas, eventos de transcripción, solapamientos,
    separadores, contenido todavía no atribuido y estados de enriquecimiento de
    hablantes.
  - Para `speech_source=history_xml_fallback`, exige una fase `Discusion`, una
    fase `Votacion` en la salida completa y cero filas de votación en el corpus
    analítico.
  - Usa los estados `pass`, `warning`, `expected_pending` y `fail`.
  - Un `speech_source` que comienza por `pending_` puede tener cero filas sin
    ocultar la ausencia ni hacer fallar el resto del procesamiento.

- `validate_speech_quality_report(report, speech_df, allowed_statuses=...)`
  - Falla ante documentos con estado no permitido, documentos no declarados,
    contenido vacío o filas sin `document_uri`.
  - Por defecto permite `warning` y `expected_pending`, que siguen visibles en
    el reporte persistido.

El formato canónico recomendado es Parquet. Puede exportarse además a CSV para
inspección humana.
