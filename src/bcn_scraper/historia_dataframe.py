"""Helpers to convert Historia de la Ley XML to pandas DataFrame."""

from __future__ import annotations

from typing import Dict, List
from html import unescape

import xml.etree.ElementTree as ET


def historia_tramites_to_dataframe(xml_bytes: bytes):
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError("pandas is required for historia_tramites_to_dataframe") from e

    rows: List[Dict[str, str]] = []
    root = ET.fromstring(xml_bytes)

    # basic metadata
    titulo = (root.findtext('titulo') or '').strip()
    bajada = (root.findtext('bajada') or '').strip()
    fecha_pub = (root.findtext('fecha_publicacion') or '').strip()

    for elem in root.iter():
        tag = elem.tag.split('}', 1)[-1]
        if tag == 'tramite_reglamentario':
            titulo_tr = ''
            bajada_tr = ''
            contenido_html = ''
            for child in elem:
                ctag = child.tag.split('}', 1)[-1]
                if ctag == 'titulo':
                    titulo_tr = (child.text or '').strip()
                elif ctag == 'bajada':
                    bajada_tr = (child.text or '').strip()
                elif ctag == 'xml':
                    contenido_html = ''.join(ET.tostring(e, encoding='unicode') for e in list(child))
            rows.append({
                'titulo_norma': titulo,
                'bajada_norma': bajada,
                'fecha_publicacion': fecha_pub,
                'tramite_titulo': titulo_tr,
                'tramite_bajada': bajada_tr,
                'tramite_contenido_html': contenido_html,
            })

    return pd.DataFrame(rows)
