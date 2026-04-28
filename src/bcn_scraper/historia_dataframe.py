"""Helpers to convert Historia de la Ley XML to pandas DataFrame."""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional

import xml.etree.ElementTree as ET
import re

from .akoma_ntoso import akn_url_from_document_uri


DATAFRAME_COLUMNS = [
    "title",
    "date",
    "excerpt",
    "xml_content",
    "txt_content",
    "akn_content",
    "xml_url",
    "akn_url",
    "law_title",
    "law_excerpt",
    "publication_date",
    "bcn_url",
]

DOCUMENT_URI_RE = re.compile(r'uriDocumento="([^"]+)"')
DATE_RE = re.compile(r'fecha="(\d{4}-\d{2}-\d{2})"')


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


def extract_document_uri(html: str) -> str:
    """Extract ``uriDocumento`` from embedded Historia de la Ley HTML."""
    m = DOCUMENT_URI_RE.search(html or "")
    return m.group(1) if m else ""


def historia_tramites_to_dataframe(
    xml_bytes: bytes,
    *,
    clean_text: bool = False,
    bcn_url: str = "",
    xml_url: str = "",
):
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
                    m = DATE_RE.search(contenido_html)
                    if m:
                        fecha_tramite = m.group(1)
            document_uri = extract_document_uri(contenido_html)
            rows.append({
                'title': titulo_tr,
                'date': fecha_tramite,
                'excerpt': bajada_tr,
                'xml_content': contenido_html,
                'txt_content': clean_tramite_html(contenido_html) if clean_text else '',
                'akn_content': '',
                'xml_url': xml_url,
                'akn_url': akn_url_from_document_uri(document_uri),
                'law_title': titulo,
                'law_excerpt': bajada,
                'publication_date': fecha_pub,
                'bcn_url': bcn_url,
            })
    df = pd.DataFrame(rows, columns=DATAFRAME_COLUMNS)
    return df


def historia_tramite_xmls_to_dataframe(
    xmls: Iterable[bytes],
    *,
    clean_text: bool = False,
    bcn_url: str = "",
    xml_urls: Optional[Iterable[str]] = None,
):
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError("pandas is required for historia_tramite_xmls_to_dataframe") from e

    xmls_list = list(xmls)
    xml_urls_list = list(xml_urls) if xml_urls is not None else [""] * len(xmls_list)
    if len(xml_urls_list) < len(xmls_list):
        xml_urls_list.extend([""] * (len(xmls_list) - len(xml_urls_list)))

    frames = [
        historia_tramites_to_dataframe(
            xml_bytes,
            clean_text=clean_text,
            bcn_url=bcn_url,
            xml_url=xml_urls_list[idx],
        )
        for idx, xml_bytes in enumerate(xmls_list)
    ]
    frames = [frame for frame in frames if not frame.empty]
    if not frames:
        return pd.DataFrame(columns=DATAFRAME_COLUMNS)
    return pd.concat(frames, ignore_index=True)[DATAFRAME_COLUMNS]
