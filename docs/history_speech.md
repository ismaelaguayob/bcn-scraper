# Fallback discursivo de Historia de la Ley

Ubicación: `src/bcn_scraper/history_speech.py`

`extract_speech_from_history_xml(xml_content, person_registry=...)` procesa un
fragmento HTML/XML de Historia de la Ley cuando el AKN del diario de sesión no
está disponible. Devuelve el mismo contenedor `speech_content` usado por el
parser AKN, para que luego pase por `normalize_speech_content` y
`build_speech_analysis_dataframe`.

El fallback:

- conserva el `document_uri`, `partedocumento` y trámite del proyecto;
- extrae boletín, etapa constitucional, resultado y título;
- representa el fragmento como proyecto dentro de `ORDEN DEL DÍA`;
- separa `Discusion` y `Votacion` usando el marcador explícito «Cerrado el
  debate»;
- retira el bloque breve de `Antecedentes` del contenido discursivo;
- acepta un registro de personas estable construido con
  `build_corpus_person_registry` desde otros AKN.

Ejemplo:

```python
from bcn_scraper import (
    add_speech_content,
    build_corpus_person_registry,
    extract_speech_from_history_xml,
    normalize_speech_content,
)

parsed = add_speech_content(df)
registry = build_corpus_person_registry(parsed)

parsed.at[row_index, "speech_content"] = extract_speech_from_history_xml(
    parsed.at[row_index, "xml_content"],
    person_registry=registry,
)
normalized = normalize_speech_content(parsed)
```

El registro usa IDs canónicos `PersonaBCN<person_id>` y `speaker_href`. No
reutiliza los `perN` de un documento anterior.
