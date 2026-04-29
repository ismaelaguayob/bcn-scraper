# Akoma Speech

Ubicacion: `src/bcn_scraper/akoma_speech.py`

## Descripcion
Extrae discurso y metadata estructurada desde XML Akoma Ntoso de BCN. El modulo
esta pensado para filas del DataFrame del wrapper que tienen `akn_content`
correspondiente a diarios de sesion o tramites con estructura de debate.

La implementacion usa `xml.etree.ElementTree` de la libreria estandar. No se
agrego una dependencia XML extra porque los AKN de prueba son XML valido y el
problema principal es preservar orden, resolver referencias y manejar variantes
del esquema BCN.

## Funciones
- `extract_speech_from_akn(akn_content: str) -> dict`
  - Convierte un XML AKN en un diccionario anidado.
  - No falla si el contenido esta vacio, empieza con `ERROR:` o no es XML valido;
    en esos casos retorna un objeto con `error`.
- `add_speech_content(df, source_col: str = "akn_content", output_col: str = "speech_content", as_json: bool = False)`
  - Retorna una copia del DataFrame con una columna nueva `speech_content`.
  - Por defecto deja diccionarios Python en la columna para facilitar el
    procesamiento posterior. Con `as_json=True` serializa como JSON string para
    guardar en CSV/Parquet.
- `normalize_speech_content(df, source_col: str = "speech_content", output_col: str = "speech_content", external_speakers=None, split_unlabeled: bool = True, clean_labeled: bool = False, as_json: bool = False)`
  - Segunda capa analitica sobre `speech_content`.
  - Divide bloques `unlabeled_text` cuando detecta marcadores de habla con regex.
  - Crea pseudo-participaciones con `source_kind = "unlabeled_text"` e
    `is_labeled = False`.
  - Permite pasar metadata manual para speakers externos o no etiquetados.
  - `clean_labeled` queda reservado para la siguiente etapa: limpiar preambulos
    procedimentales dentro de participaciones etiquetadas.

Ejemplo con speakers externos:

```python
from bcn_scraper import add_speech_content, normalize_speech_content

df = add_speech_content(df)

df = normalize_speech_content(
    df,
    external_speakers={
        "JARA": {
            "speaker": "Jeannette Jara",
            "speaker_id": "PersonaExt1",
            "speaker_href": "https://example.test/jara",
            "role": "Ministra del Trabajo y Previsión Social",
        },
        "MARCEL": {
            "speaker": "Mario Marcel",
            "speaker_id": "PersonaExt2",
            "role": "Ministro de Hacienda",
        },
    },
)
```

## Esquema MVP
El JSON usa listas ordenadas en vez de claves `project_n` o `participation_n`.
Esto conserva el orden documental y facilita recorrer, filtrar o transformar los
datos a tablas.

```json
{
  "session_information": {
    "raw_text": "...",
    "paragraphs": []
  },
  "attendance": {
    "raw_text": "...",
    "paragraphs": [],
    "people": []
  },
  "debate_body": {
    "point_of_order": [],
    "other_debates": [],
    "incidents": [],
    "addresses": []
  },
  "metadata": {
    "persons": {},
    "roles": {},
    "organizations": {},
    "references": {}
  }
}
```

## Debate Body
Cada proyecto o seccion relevante contiene `items`, una lista ordenada de
unidades de contenido. `time_step` se reinicia dentro de cada seccion/proyecto.

Tipos de item del MVP:
- `participation`: viene de `debateSection name="Participacion"`.
- `unlabeled_text`: agrupa parrafos directos consecutivos no etiquetados.
- `votation`: viene de `debateSection name="Votacion"`.
- `section`: contenedor generico para secciones anidadas no normalizadas aun.

Las participaciones resuelven, cuando existe metadata:
- `speaker_id`, `speaker`, `speaker_href`
- `type_id`, `type`
- `role_id`, `role`

Luego de `normalize_speech_content`, los bloques `unlabeled_text` con marcador
de habla se transforman en `participation` con:
- `speaker_id`: proviene del diccionario manual o se genera como `PersonaExtN`.
- `speaker`: proviene del diccionario manual o del marcador detectado.
- `speaker_href`: opcional, proviene del diccionario manual.
- `speaker_resolution_status`: `user_provided` o `regex`.
- `speaker_marker`: parrafo marcador, por ejemplo `La señora JARA (...).-`.
- `discarded_preamble`: parrafos procedimentales previos al marcador.
- `raw_content`: contenido original, incluyendo el marcador.
- `content`: discurso atribuido al speaker, sin el marcador.

Las votaciones extraen:
- `content`: parrafos/summary de la votacion.
- `totals`: cantidades etiquetadas con `quantity`, por ejemplo `in_favor`,
  `against`, `abstention`.
- `votes`: votos individuales etiquetados con `vote`, resolviendo persona y
  opcion cuando existe metadata.
- `outcomes`: resultados etiquetados con `outcome`.

## Variantes Cubiertas
- `pointOfOrder` normal como Orden del Dia.
- `debateSection name="Tabla"` tratado como equivalente a `pointOfOrder`.
- `Tabla` dentro de `Cuenta`, caso observado en `686161.xml`.
- `TextoDebate` como `other_debates`.
- `Incidente` como `incidents`.
- `address` como contenedor flexible para sesiones antiguas o estructuras menos
  regulares.

## Contenido Ignorado
Se descartan secciones administrativas documentadas como no relevantes para esta
feature, por ejemplo `Actas`, `DocumentosDeLaCuenta`, `DocumentoCuenta`,
`AnexoSesion`, `OtrosDocumentosDeLaCuenta`, `PeticionesDeOficio`, `prayers`,
`petitions` y `adjournment`.

La excepcion importante es `Cuenta`: su contenido ordinario se ignora, pero si
contiene una `Tabla`, esa tabla se extrae como `point_of_order`.

## Tests
Los tests usan fixtures locales en:

`new_features_&_reports/speech_data_from_akn/test_data/`

Casos cubiertos:
- `709595.xml`: metadata, proyectos, participaciones y votaciones del Senado.
- `686161.xml`: `Tabla` anidada dentro de `Cuenta`.
- `665620.xml`: votaciones antiguas con `quantity` y `vote` dentro de `address`.
- `datos_bcn_akn.csv`: DataFrame separado por `;`, incluyendo filas con AKN
  valido y filas con `ERROR:`.

Comando:

```bash
uv run pytest tests/test_akoma_speech.py
```
