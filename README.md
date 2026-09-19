# bcn-scraper

Clientes HTTP para extraer datos legislativos desde:
- Historia de la Ley (flujo XAJAX).
- Cámara de Diputados y Senado (tramitación y documentos, en desarrollo).

## Instalación (uv)
```bash
uv venv
uv pip install -e ".[test]"
```

Si ya existe `.venv`, también puedes sincronizar dependencias y luego instalar el
paquete en modo editable:

```bash
uv sync
uv pip install -e ".[test]"
```

## Uso en Positron
En Positron selecciona el intérprete del entorno del proyecto:

```text
./.venv/bin/python
```

Para verificar que el kernel correcto está activo:

```python
import sys
import bcn_scraper

print(sys.executable)
print(bcn_scraper.__file__)
```

La salida debería apuntar a este repositorio, por ejemplo:

```text
/home/.../bcn-scraper/.venv/bin/python
/home/.../bcn-scraper/src/bcn_scraper/__init__.py
```

Si instalaste con `uv pip install -e ".[test]"`, no necesitas modificar
`sys.path` manualmente.

## Ejecutar pruebas
```bash
uv run pytest
```

## Estructura
- `src/bcn_scraper/`: librería principal.
- `tests/`: pruebas unitarias con fixtures locales.
- `data/`: fixtures HTML/XML/CSV de ejemplo.
- `docs/`: documentación técnica por clase/módulo.

## Documentación técnica
Revisa `docs/README.md` para el índice de clases y módulos documentados.

## Wrapper rápido (DataFrame)
```python
from bcn_scraper import historia_dataframe_from_ley_o_boletin

df = historia_dataframe_from_ley_o_boletin(numero_ley="21735", clean_text=True)
```

El DataFrame usa columnas estandarizadas en inglés:

```text
title, date, excerpt, xml_content, txt_content, akn_content,
xml_url, akn_url, law_title, law_excerpt, publication_date, bcn_url
```

Ejemplo por boletín:

```python
from bcn_scraper import historia_dataframe_from_ley_o_boletin

df = historia_dataframe_from_ley_o_boletin(numero_boletin="15480-13", clean_text=True)
print(df[["date", "title", "akn_url"]].head())
```

## Discurso desde Akoma Ntoso
```python
from bcn_scraper import (
    add_speech_content,
    historia_dataframe_from_ley_o_boletin,
    normalize_speech_content,
)

df = historia_dataframe_from_ley_o_boletin(
    numero_ley="21735",
    clean_text=True,
    fetch_akn=True,
    akn_filter=lambda tramite: "discusión en sala" in tramite["title"].casefold(),
)

df = add_speech_content(df)
df = normalize_speech_content(df)
```

`add_speech_content` agrega una columna `speech_content` con JSON anidado para
sesiones AKN: metadata de referencias, portada, asistencia, orden del día,
participaciones, texto no etiquetado agrupado y votaciones etiquetadas.
`normalize_speech_content` divide bloques no etiquetados cuando detecta
marcadores de habla, separa eventos como aplausos, limpia preámbulos
procedimentales y permite agregar metadata manual de speakers externos.

## Datos parlamentarios BCN
```python
from bcn_scraper import build_parliamentarian_table

parliamentarians = build_parliamentarian_table(df)
```

`build_parliamentarian_table` toma un DataFrame con `speech_content`
normalizado, detecta speakers con `speaker_href` de `datos.bcn.cl` y agrega
nombre BCN, género, nacionalidad, nacimiento, imagen y partido actual. Por
defecto evita descargar fechas de militancia para mantener el proceso ágil; se
pueden activar con `fetch_militancy_dates=True`. Las funciones largas muestran
barra de progreso por defecto.

Para una segunda pasada más paciente sobre filas incompletas:

```python
from bcn_scraper import debug_parliamentarian_data_errors

parliamentarians = debug_parliamentarian_data_errors(
    parliamentarians,
    timeout=60,
    max_attempts=3,
    backoff_seconds=2,
)
```

## DataFrame de discurso
```python
from bcn_scraper import build_speech_analysis_dataframe

speech_df = build_speech_analysis_dataframe(
    df,
    parliamentarians=parliamentarians,
)
```

`build_speech_analysis_dataframe` aplana `speech_content` normalizado a una fila
por participación discursiva y fusiona datos BCN por
`speaker_href == person_href`. Por defecto excluye preámbulos, eventos de
transcripción y bloques no resueltos; se pueden conservar para auditoría con
`include_preambles=True`, `include_transcription_events=True` e
`include_unresolved=True`.

## Notas
- Los tests evitan red y usan archivos locales en `data/`.
- `pandas` es requerido para helpers de DataFrame.
- `clean_text=True` rellena la columna `txt_content`.
- El wrapper descarga XMLs individuales por trámite por defecto para evitar inconsistencias observadas en XMLs agregados de BCN.
- La descarga Akoma Ntoso está desactivada por defecto; usa `fetch_akn=True`
  solo si necesitas IDs de actores u otra metadata AKN.
- La descarga AKN usa `timeout=30` y sin reintentos por defecto. Para reintentar
  fallas de handshake/timeout en una segunda pasada, usa
  `debug_akoma_ntoso_errors`.
- Algunos documentos de `datos.bcn.cl` no tienen AKN usable y pueden devolver
  HTTP 500 o contenido no XML.
