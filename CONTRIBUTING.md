# CONTRIBUTING

Gracias por contribuir a este proyecto. Esta guía explica cómo configurar el entorno,
ejecutar pruebas y mantener el repositorio ordenado.

## Requisitos
- Python >= 3.9
- `uv` instalado

## Configuración local
```bash
uv venv
uv pip install -e ".[test]"
```

## Ejecutar pruebas
Las pruebas usan fixtures locales en `data/` y no requieren red.
```bash
uv run pytest
```

## Estructura del repositorio
- `src/bcn_scraper/`: código fuente.
- `tests/`: pruebas unitarias.
- `data/`: fixtures y archivos de ejemplo.
- `docs/`: documentación técnica por clase/módulo.

## Guía de contribución
- Prefiere funciones puras y parseo basado en fixtures locales.
- Mantén separados los clientes por fuente (Historia, Cámara, Senado).
- Si agregas scraping, incluye un fixture local y una prueba.
- Documenta nuevas clases en `docs/`.

## Estilo de commits (opcional)
- Mensajes claros y concisos.
- Indica si agregas fixtures o modificas endpoints.
