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

## Notas
- Los tests evitan red y usan archivos locales en `data/`.
- `pandas` es requerido para helpers de DataFrame.
- `clean_text=True` rellena la columna `txt_content`.
- El wrapper descarga XMLs individuales por trámite por defecto para evitar inconsistencias observadas en XMLs agregados de BCN.
- El wrapper descarga Akoma Ntoso por defecto en `akn_content`; usa `fetch_akn=False` para omitir esa descarga.
- La descarga Akoma Ntoso usa reintentos y timeout de 60 segundos por intento,
  porque algunos documentos de `datos.bcn.cl` pueden tardar varios segundos.
