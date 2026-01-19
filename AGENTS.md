# AGENTS.md

## Alcance del proyecto
Este repositorio implementa clientes HTTP para extraer datos legislativos de:
- Historia de la Ley (flujo XAJAX).
- Cámara de Diputados y Senado (tramitación y documentos).

El objetivo inmediato es ordenar el paquete, mantener fixtures locales para pruebas
sin red y documentar claramente el flujo de cada cliente.

## Estado actual (enero 2026)
- Historia de la Ley: extracción de payloads, descarga de XML y parseo de trámites.
- Cámara y Senado: scraping de tramitación con parseo de tablas HTML (features por desarrollar).
- Pruebas unitarias basadas en fixtures locales en `data/`.

## Dependencias y entorno (uv)
Se utiliza `uv` para gestionar entorno y dependencias.

Comandos típicos:
```bash
uv venv
uv pip install -e ".[test]"
uv run pytest
```

## Estructura sugerida
- `src/bcn_scraper/`: librería principal.
- `tests/`: pruebas basadas en fixtures locales.
- `data/`: fixtures HTML/XML/CSV usados en pruebas o ejemplos.
- `docs/`: documentación por módulo/clase.

## Convenciones
- Evitar dependencias de red en tests.
- Agregar fixtures nuevos en `data/externo` y referenciarlos en pruebas.
- Mantener clientes separados por fuente (Historia, Cámara, Senado).
