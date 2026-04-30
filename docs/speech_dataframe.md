# Speech DataFrame

Este modulo convierte `speech_content` normalizado en tablas analiticas para la
tesis.

## Funciones publicas

```python
from bcn_scraper import (
    build_speech_analysis_dataframe,
    flatten_speech_content,
)
```

### `flatten_speech_content`

Aplana `speech_content` sin red ni metadata externa:

```python
speech_df = flatten_speech_content(data_normalized)
```

Por defecto entrega una fila por participacion discursiva relevante:
- incluye `kind = "participation"`;
- excluye preambulos procedimentales;
- excluye eventos de transcripcion;
- excluye bloques `unlabeled_text` no resueltos.

Flags de auditoria:

```python
speech_df = flatten_speech_content(
    data_normalized,
    include_unresolved=True,
    include_preambles=True,
    include_transcription_events=True,
)
```

`include_transcription_events=True` conserva eventos como aplausos,
manifestaciones, murmullos, risas o protestas con
`content_status = "transcription_event"`. No se fuerzan como participaciones
discursivas.

### `build_speech_analysis_dataframe`

Aplana y fusiona datos parlamentarios ya descargados:

```python
parliamentarians = build_parliamentarian_table(data_normalized)

speech_df = build_speech_analysis_dataframe(
    data_normalized,
    parliamentarians=parliamentarians,
)
```

El merge se hace solo por `speaker_href == person_href`. No se fusiona por
nombre, porque los nombres pueden variar entre documentos y fuentes.

La funcion no descarga datos de BCN. Ese paso queda separado en
`build_parliamentarian_table` y `debug_parliamentarian_data_errors`, para poder
controlar tiempos, reintentos y progreso.

## Columnas principales

Documento:
- `row_index`: indice de la tabla plana.
- `source_row_index`: indice de la fila original del DataFrame fuente.
- `title`, `date`, `akn_url`, `xml_url`, `bcn_url`, `document_uri`.

Contexto legislativo:
- `section_kind`, `section_name`, `section_id`.
- `point_of_order_id`, `point_of_order_title`.
- `project_id`, `project_title`.
- `bill_ref`, `bill_number`.
- `constitutional_stage`, `regulatory_stage`, `debate_result`.

Orden y auditoria:
- `participation_id`.
- `time_step`.
- `item_path`: ruta del item dentro del JSON anidado.
- `item_depth`: profundidad relativa dentro de secciones anidadas.

Speaker:
- `speaker_id`, `speaker`, `speaker_href`, `role`.
- `participation_type`.
- `source_kind`.
- `is_labeled`, `is_interruption`, `is_preamble`.
- `speaker_resolution_status`, `speaker_source`.

Contenido:
- `content`: texto unido por saltos de linea.
- `content_paragraphs`: lista original de parrafos.
- `n_paragraphs`, `n_chars`, `n_words`.
- `raw_content`, `raw_content_paragraphs`.
- `speech_marker`.
- `discarded_preamble`, `discarded_preamble_paragraphs`.

Calidad:
- `parse_warning`.
- `has_raw_content`.
- `has_discarded_preamble`.
- `content_status`: `ok`, `preamble`, `transcription_event`,
  `unresolved` o `empty`.

Datos BCN, si se entrega `parliamentarians`:
- `person_id`, `person_href`, `name`.
- `gender`, `nationality`, `birth_date`, `birth_place`.
- `image_url`, `thumbnail_url`.
- `current_party`, `current_party_href`.
- `current_militancy_href`.
- `current_militancy_start_date`, `current_militancy_end_date`.
- `has_current_militancy`, `militancy_count`.
- `speaker_data_status`.

## `speaker_data_status`

Esta columna explicita por que las columnas BCN estan llenas o vacias:

- `ok`: hubo match con la tabla parlamentaria.
- `not_merged`: no se entrego `parliamentarians`.
- `missing_href`: la participacion no tiene `speaker_href`.
- `not_bcn_person`: el `speaker_href` existe, pero no es `datos.bcn.cl`.
- `not_found`: el `speaker_href` es BCN, pero no esta en `parliamentarians`.
- `not_applicable`: fila que no representa a un speaker, por ejemplo evento de
  transcripcion.

Esta distincion permite testear consistencia: si `speaker_data_status = "ok"`,
las columnas BCN relevantes deberian venir llenas; si es `not_bcn_person`,
`missing_href` o `not_found`, deben quedar vacias.
