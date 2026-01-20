"""Helpers to convert Historia de la Ley XML to pandas DataFrame."""

from __future__ import annotations

from typing import Dict, List
from html import unescape

import xml.etree.ElementTree as ET
import re


def clean_tramite_html(html: str) -> str:
    try:
        from bs4 import BeautifulSoup
    except ImportError as e:
        raise ImportError("beautifulsoup4 is required for clean_tramite_html") from e

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = []
    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def historia_tramites_to_dataframe(xml_bytes: bytes, *, clean_text: bool = False):
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
            fecha_tramite = ''
            for child in elem:
                ctag = child.tag.split('}', 1)[-1]
                if ctag == 'titulo':
                    titulo_tr = (child.text or '').strip()
                elif ctag == 'bajada':
                    bajada_tr = (child.text or '').strip()
                elif ctag == 'xml':
                    contenido_html = ''.join(ET.tostring(e, encoding='unicode') for e in list(child))
                    m = re.search(r'fecha="(\d{4}-\d{2}-\d{2})"', contenido_html)
                    if m:
                        fecha_tramite = m.group(1)
            rows.append({
                'titulo_norma': titulo,
                'bajada_norma': bajada,
                'fecha_publicacion': fecha_pub,
                'tramite_fecha': fecha_tramite,
                'tramite_titulo': titulo_tr,
                'tramite_bajada': bajada_tr,
                'tramite_contenido_html': contenido_html,
            })
    df = pd.DataFrame(rows)
    if clean_text and not df.empty:
        df['tramite_texto'] = df['tramite_contenido_html'].map(clean_tramite_html)
    return df
