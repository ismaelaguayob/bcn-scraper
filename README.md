# bcn-scraper

Clientes HTTP para extraer datos legislativos desde:
- Historia de la Ley (flujo XAJAX).
- Cámara de Diputados y Senado (tramitación y documentos, en desarrollo).

## Instalación (uv)
```bash
uv venv
uv pip install -e ".[test]"
```

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

## Notas
- Los tests evitan red y usan archivos locales en `data/`.
- `pandas` es requerido para helpers de DataFrame.
- `clean_text=True` agrega la columna `tramite_texto`.
