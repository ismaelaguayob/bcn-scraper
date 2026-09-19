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
historial completo. Los parámetros de red también son conservadores por
defecto: `timeout=20`, `max_attempts=1`.

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
            "speaker": "Mario Marcel Cullell",
            "speaker_href": "http://datos.bcn.cl/recurso/persona/4216",
            "role": "Ministro de Hacienda",
        },
        "CIFUENTES": {
            "speaker_href": "http://datos.bcn.cl/recurso/persona/5200"
        },
    },
    document_speaker_overrides={
        "http://datos.bcn.cl/recurso/cl/documento/706982": {
            "GARCIA": {
                "speaker_href": "http://datos.bcn.cl/recurso/persona/279"
            }
        }
    },
)

parliamentarians = build_parliamentarian_table(data_normalized)
```

No se deben reutilizar `perN`/`PersonaAutN` entre documentos. El cruce estable
para consultar y unir información parlamentaria es `speaker_href` (y su
`person_id` numérico); el ID local solo conserva trazabilidad dentro de su AKN.

La función muestra una barra de progreso textual por defecto. Si estás en un
contexto donde no quieres salida progresiva, usa `show_progress=False`.

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

### `debug_parliamentarian_data_errors`

Reintenta solo filas incompletas de una tabla parlamentaria ya construida:

```python
from bcn_scraper import debug_parliamentarian_data_errors

parliamentarians = debug_parliamentarian_data_errors(
    parliamentarians,
    timeout=60,
    max_attempts=3,
    backoff_seconds=2,
)
```

Por defecto considera relevantes estas columnas:

```text
name, gender, nationality, birth_date, birth_place, image_url, current_party
```

Si quieres depurar una tabla más profunda, debes repetir las mismas opciones:

```python
parliamentarians = debug_parliamentarian_data_errors(
    parliamentarians,
    include_all_militancies=True,
    fetch_militancy_dates=True,
    timeout=90,
    max_attempts=3,
    backoff_seconds=2,
)
```

En ese caso también se revisan `militancies` y
`current_militancy_start_date`. Esto importa: una fila completa en modo rápido
puede ser incompleta para el modo profundo.

## Rendimiento y red

BCN puede responder lento en recursos enlazados. El fetcher usa cache por URL,
`timeout`, `max_attempts` y `backoff_seconds`. El flujo recomendado para muchas
personas es partir con el default y activar fechas/historial completo solo si
esas variables serán usadas en el análisis. Para datasets grandes, conviene:

1. Construir la tabla rápida con `build_parliamentarian_table(...)`.
2. Revisar cuántos datos faltan.
3. Ejecutar `debug_parliamentarian_data_errors(...)` solo sobre filas
   incompletas.

Los tests unitarios usan fixtures RDF/JSON sintéticos y no dependen de red.

## Militancia en una fecha, historial y modo actual

`fetch_parliamentarian_data`, `build_parliamentarian_table` y
`debug_parliamentarian_data_errors` aceptan el parámetro opcional `date`:

| Valor | Resultado |
| --- | --- |
| `None`, `"current"` o `"latest"` | Conserva el comportamiento rápido anterior: campos `current_*`, con la regla de militancia sin `hasEnd` y el fallback descrito arriba. |
| `"all"` | Recupera todas las militancias con sus partidos y fechas de inicio y término en `militancies`. |
| `"YYYY-MM-DD"`, `datetime.date` o `datetime.datetime` | Recupera el historial fechado y determina la militancia para ese día. En un `datetime` se usa su fecha calendario. |

```python
# Última militancia según la regla actual del extractor.
current = fetch_parliamentarian_data(person_href, date="current")

# Historial completo, incluidas sus fechas; no exige otros flags.
history = fetch_parliamentarian_data(person_href, date="all")

# Militancia en la fecha de un debate, sin alterar current_party.
at_date = fetch_parliamentarian_data(person_href, date="2022-01-03")
print(at_date["party_at_date"], at_date["militancy_at_date_status"])

# La misma selección se aplica a todos los participantes de una tabla de discurso.
parliamentarians = build_parliamentarian_table(data_normalized, date="2022-01-03")
```

Los flags anteriores `include_all_militancies` y `fetch_militancy_dates` siguen
funcionando. Una fecha concreta o `"all"` activa ambos. `current_party` conserva
su significado original incluso al consultar una fecha histórica. Los resultados
incluyen `militancy_selection` para identificar la consulta aplicada.

Una consulta histórica añade:

- `reference_date`: día consultado, en formato ISO;
- `party_at_date` y `party_at_date_href`: afiliación establecida para ese día;
- `militancy_at_date_href`, `militancy_at_date_start_date` y
  `militancy_at_date_end_date`: procedencia e intervalo de la afiliación;
- `militancy_at_date_status`: estado de la resolución;
- `militancy_at_date_candidates`: referencias a los periodos potencialmente compatibles.

Los extremos del intervalo son inclusivos. Si BCN informa solo un año o un mes,
se conserva esa precisión: la afiliación se asigna únicamente cuando la fecha
consultada queda inequívocamente dentro del periodo. Un término enlazado cuya
fecha falta no se interpreta como una militancia abierta.

| Estado | Interpretación |
| --- | --- |
| `matched` | Un único periodo confirma la afiliación en esa fecha. |
| `not_found` | Ningún periodo disponible cubre la fecha; no equivale a afirmar independencia política. |
| `ambiguous` | Más de un periodo confirma la fecha; no se elige el primero arbitrariamente. |
| `uncertain_dates` | Las fechas o datos disponibles impiden descartar candidatos o confirmar un intervalo. |

Salvo en `matched`, los campos de partido histórico quedan vacíos. Los campos
históricos quedan vacíos también en los modos `current` y `all`, que no consultan
un día concreto. Las cadenas de fecha inválidas se rechazan antes de acceder a red.

La depuración detecta cambios de fecha y fechas enlazadas faltantes en el
historial, además de las columnas biográficas incompletas. `force=True` permite
refrescar todas las personas BCN de una tabla existente, conservando sus demás
columnas:

```python
updated = debug_parliamentarian_data_errors(
    parliamentarians, date="all", force=True, timeout=30, max_attempts=2,
)
```

### Actualización de tablas existentes desde la terminal

El módulo `bcn_scraper.parliamentarians_cli` lee tablas Parquet con `person_href`.
Requiere un motor Parquet, como `pyarrow` (ya instalado en el proyecto de tesis).
Conserva las columnas de procedencia y comparte una caché de recursos entre todos
los archivos, para evitar descargar repetidamente las mismas personas y partidos.

Desde el directorio de la tesis, el siguiente comando actualiza los historiales
completos de las tres leyes:

```bash
uv run python -m bcn_scraper.parliamentarians_cli \
  --input data/proc_data/ley_*/parliamentarians.parquet \
  --date all
```

Antes de sustituir un archivo existente, guarda una copia con fecha UTC y sufijo
`.bak`. La escritura del nuevo Parquet es atómica. El comando informa los estados
de extracción y, para consultas históricas, los estados de resolución. Los errores
de descarga quedan registrados para revisión; no convierten una fecha incierta en
una afiliación confirmada.

Para una ley y una fecha concreta:

```bash
uv run python -m bcn_scraper.parliamentarians_cli \
  --input data/proc_data/ley_21419/parliamentarians.parquet \
  --date 2022-01-03
```

Sustituye `--date` por `current` para el enfoque anterior. Una fecha se aplica a
la tabla completa: si una ley tiene varias sesiones y quieres asignar la militancia
por sesión, consulta cada fecha por separado o conserva el historial con `all`.
Este comando actualiza las tablas de parlamentarios; las tablas de intervenciones
y fragmentos existentes deben regenerarse después mediante su procesamiento habitual.

Una prueba limitada exige una carpeta de salida distinta, para evitar reemplazar
el corpus completo por una muestra:

```bash
uv run python -m bcn_scraper.parliamentarians_cli \
  --input data/proc_data/ley_21419/parliamentarians.parquet \
  --date all --limit 2 --output-dir /tmp/bcn-parliamentarians-sample
```

`--limit` limita el número total de filas entre los archivos indicados. Las salidas
se nombran `<carpeta-origen>_<archivo>.parquet`. `--only-incomplete` reintenta solo
las filas incompletas o calculadas con otro selector. Los parámetros `--timeout`,
`--max-attempts`, `--backoff-seconds` y `--no-progress` controlan la consulta y su
presentación.

### Afiliación en cada discusión: `--date discussions`

Para el análisis de debates, una sola fecha por ley o `first_date` no representan
las fechas de todas sus discusiones. Este modo lee `speech_df.parquet` junto a cada
`parliamentarians.parquet`, selecciona las participaciones incluidas en el análisis
y utiliza la columna `date` de cada `document_uri`.

```bash
uv run python -m bcn_scraper.parliamentarians_cli \
  --input data/proc_data/ley_*/parliamentarians.parquet \
  --date discussions --timeout 60 --max-attempts 3
```

Genera `parliamentarian_affiliations.parquet` en la carpeta de cada ley, con una fila
por persona BCN y discusión. Exporta `party_at_date`, su URI, las fechas del período
seleccionado y `militancy_at_date_status`; no incluye el historial ni `current_party`.
Los estados `ambiguous`, `uncertain_dates` y `unavailable` conservan la afiliación
sin asignar cuando no puede establecerse. `not_found` significa que no se encontró
un intervalo compatible, no que la persona fuese independiente. Los hablantes sin
identificador BCN no se consultan. Para incorporar esta tabla al corpus, el cruce
es por `document_uri`, `date` y `person_href`, con validación `many_to_one`.

El modo reutiliza los historiales completos que ya existen en cualquiera de las
leyes, aunque falten otros datos biográficos. Consulta únicamente personas con
historial ausente o incompleto. BCN ofrece períodos de militancia: cuando faltan,
se consultan sus intervalos para resolver las fechas, pero el resultado analítico
contiene exclusivamente las afiliaciones seleccionadas.

Las nuevas respuestas RDF exitosas se conservan entre ejecuciones en
`.cache/bcn-scraper/rdf` (configurable con `--cache-dir`). Los errores de red no se
almacenan. Al repetir el comando se reutilizan esas respuestas y se reintentan los
recursos pendientes; si una fecha está ausente en una respuesta válida de BCN,
puede seguir sin resolverse incluso después del reintento. La caché es una
instantánea local, sin caducidad automática.

En este modo la reutilización es automática; no hace falta `--only-incomplete`.
En los modos anteriores (`all`, `current` o una fecha fija), la ejecución predeterminada
sí actualiza todas las filas y la caché de red solo dura esa ejecución;
`--only-incomplete` limita esas consultas a las filas incompletas.

Las tablas de biografías y discursos originales se conservan. Una salida existente
se respalda antes de reemplazarla. Este comando no modifica `proc.qmd` ni incorpora
automáticamente los nuevos campos a `speech_df` o a los chunks.

Para una prueba pequeña sin descargas:

```bash
uv run python -m bcn_scraper.parliamentarians_cli \
  --input data/proc_data/ley_21419/parliamentarians.parquet \
  --date discussions --offline --limit 3 --output-dir /tmp/bcn-affiliations-sample
```

`--limit` limita el total de pares persona/discusión y exige `--output-dir` para
preservar la salida completa. `--offline` resuelve solo con los historiales de las
tablas existentes; no intenta completar datos mediante peticiones RDF.
