# Parliamentary Data

Este módulo extrae datos personales y partidarios desde `datos.bcn.cl` para
parlamentarios que aparecen como speakers en `speech_content`.

La fuente elegida es `datos.json` (`application/rdf+json`). Es menos legible que
RDF/XML a ojo, pero para el paquete es más estable: se parsea con `json` de la
librería estándar, no exige una dependencia RDF nueva y permite seguir recursos
enlazados (`nacimiento`, `militancia`, partido político) con la misma estructura.

## Funciones públicas

```python
from bcn_scraper import (
    build_parliamentarian_table,
    collect_bcn_speaker_references,
    fetch_parliamentarian_data,
)
```

### `fetch_parliamentarian_data`

Descarga y parsea una persona BCN:

```python
person = fetch_parliamentarian_data("http://datos.bcn.cl/recurso/persona/1778")
```

Campos principales:

- `person_href`: URL del recurso BCN.
- `person_id`: identificador numérico BCN.
- `name`: `foaf:name`, con formato BCN.
- `gender`: `foaf:gender`.
- `nationality`: nacionalidad derivada de `bcnbio:nationality`.
- `nationality_href`: URL RDF de nacionalidad.
- `birth_href`: URL RDF de nacimiento.
- `birth_date`: fecha de nacimiento, si el recurso enlazado responde.
- `birth_place`: lugar de nacimiento, si está disponible.
- `image_url`: URL `foaf:img` o `foaf:depiction`.
- `thumbnail_url`: miniatura BCN, si existe.
- `current_militancy_href`: militancia actual elegida.
- `current_party`: partido actual.
- `current_party_href`: URL RDF del partido.
- `current_militancy_start_date`: fecha de inicio solo si `fetch_militancy_dates=True`.
- `current_militancy_end_date`: normalmente `None` para militancia actual.
- `has_current_militancy`: `True` si se detectó militancia sin `hasEnd`.
- `militancy_count`: número de militancias enlazadas.
- `data_status`: `ok`, `not_bcn_person`, `not_found` o `fetch_error`.

La regla de militancia actual es estricta: se revisan las militancias enlazadas
por `bcnbio:hasMilitancy` y se toma como actual la que no tiene
`bcnbio:hasEnd`. Si ninguna cumple, se usa la primera como fallback y
`has_current_militancy=False`.

Por velocidad, el default no descarga fechas de militancia ni incluye el
historial completo:

```python
person = fetch_parliamentarian_data(
    "http://datos.bcn.cl/recurso/persona/2362",
    include_all_militancies=True,
    fetch_militancy_dates=True,
)
```

### `collect_bcn_speaker_references`

Recolecta referencias BCN desde participaciones efectivas, no desde toda la
metadata AKN:

```python
refs = collect_bcn_speaker_references(data_normalized)
```

Esto evita mezclar asistentes o personas declaradas en metadata con quienes
realmente hablan. Si una participación tiene `speaker_id` pero no
`speaker_href`, se resuelve contra `speech_content["metadata"]["persons"]`.
Speakers externos, por ejemplo Wikipedia, se ignoran en esta primera versión.

Columnas:

- `person_href`
- `person_id`
- `speaker_ids`
- `speaker_names_seen`
- `roles_seen`
- `participation_count`
- `document_count`
- `first_row_index`
- `first_title`
- `first_date`

### `build_parliamentarian_table`

Construye una tabla enriquecida, una fila por persona BCN que aparece como
speaker:

```python
table = build_parliamentarian_table(data_normalized)
```

Ejemplo completo:

```python
import pandas as pd
from bcn_scraper import (
    add_speech_content,
    build_parliamentarian_table,
    normalize_speech_content,
)

data = pd.read_csv("data/datos_bcn_akn.csv", sep=";")
data_analysis = data[
    data["title"].str.contains("Discusión en Sala|Mensaje|Informe", case=False, na=False)
]

data_speech = add_speech_content(data_analysis)
data_normalized = normalize_speech_content(
    data_speech,
    split_transcription_events=True,
    clean_labeled=True,
    external_speakers={
        "JARA": {
            "speaker": "Jeannette Jara",
            "speaker_id": "PersonaExt1",
            "speaker_href": "https://es.wikipedia.org/wiki/Jeannette_Jara",
            "role": "Ministra del Trabajo y Previsión Social",
        },
        "MARCEL": {
            "speaker": "Mario Marcel",
            "speaker_id": "PersonaExt2",
            "speaker_href": "https://es.wikipedia.org/wiki/Mario_Marcel",
            "role": "Ministro de Hacienda",
        },
        "CIFUENTES": {"speaker_id": "per0"},
        "GARCIA": {"speaker_id": "PersonaAut9"},
    },
)

parliamentarians = build_parliamentarian_table(data_normalized)
```

Para una tabla más completa, pero más lenta:

```python
parliamentarians = build_parliamentarian_table(
    data_normalized,
    include_all_militancies=True,
    fetch_militancy_dates=True,
    timeout=60,
    max_attempts=3,
    backoff_seconds=2,
)
```

## Rendimiento y red

BCN puede responder lento en recursos enlazados. El fetcher usa cache por URL,
`timeout`, `max_attempts` y `backoff_seconds`. El flujo recomendado para muchas
personas es partir con el default y activar fechas/historial completo solo si
esas variables serán usadas en el análisis.

Los tests unitarios usan fixtures RDF/JSON sintéticos y no dependen de red.
