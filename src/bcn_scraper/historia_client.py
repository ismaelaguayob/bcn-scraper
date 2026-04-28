"""Client for Historia de la Ley (BCN) using the XAJAX flow."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html import unescape
from typing import Dict, List, Optional
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class HistoriaPayload:
    """Payload used by herrDescargarXML/ DOC / PDF handlers."""

    raw: Dict[str, object]

    @property
    def identificador(self) -> Optional[str]:
        return str(self.raw.get("identificador")) if self.raw.get("identificador") else None


@dataclass(frozen=True)
class HistoriaXmlDownload:
    """Downloaded Historia XML plus the exact BCN URL used to retrieve it."""

    content: bytes
    xml_url: str


class HistoriaClient:
    """Client for Historia de la Ley that mirrors the XAJAX flow.

    Flow:
      1) Fetch historia page HTML.
      2) Extract payload JSON from onclick="herrDescargarXML(...)".
      3) POST to XAJAX endpoint (xajax= herrDescargarXML) with payload.
      4) Parse XAJAX response to extract obtienearchivo URL.
      5) Download XML.
    """

    def __init__(self, base: str = "https://www.bcn.cl/historiadelaley/") -> None:
        self.base = base.rstrip("/") + "/"

    def fetch_historia_html(self, identificador: str) -> str:
        url = urljoin(self.base, f"nc/historia-de-la-ley/{identificador}/")
        req = Request(url, headers={"User-Agent": "bcn-scraper/0.1"})
        return urlopen(req, timeout=30).read().decode("utf-8", errors="ignore")

    def extract_payloads(self, html: str) -> List[HistoriaPayload]:
        """Extract JSON payloads embedded in herrDescargarXML onclick attributes."""
        payloads: List[HistoriaPayload] = []
        # Handle multiple quoting styles (&quot; and literal quotes).
        patterns = [
            re.compile(r"herrDescargarXML\(&quot;(\{.*?\})&quot;\)", re.DOTALL),
            re.compile(r"herrDescargarXML\(\\\"(\{.*?\})\\\"\)", re.DOTALL),
            re.compile(r"herrDescargarXML\(\"(\{.*?\})\"\)", re.DOTALL),
        ]
        raw_payloads: List[str] = []
        for pattern in patterns:
            raw_payloads.extend(pattern.findall(html))

        for raw in raw_payloads:
            # unescape HTML entities then decode unicode escapes
            s = unescape(raw)
            s = s.encode("utf-8").decode("unicode_escape")
            try:
                data = json.loads(s)
            except json.JSONDecodeError:
                data = json.loads(s.replace("\\\"", '"'))
            payloads.append(HistoriaPayload(raw=data))
        return payloads

    def extract_tramite_payloads(self, html: str) -> List[HistoriaPayload]:
        """Extract payloads for individual tramite_reglamentario XML downloads."""
        payloads = []
        for payload in self.extract_payloads(html):
            pos = payload.raw.get("pos")
            if isinstance(pos, str) and re.match(r"^\d+-\d+$", pos):
                payloads.append(payload)
        return payloads

    def xajax_endpoint_from_html(self, html: str) -> Optional[str]:
        m = re.search(r"xajaxRequestUri=\"([^\"]+)\"", html)
        return m.group(1) if m else None

    def request_xml_url(self, xajax_url: str, payload: HistoriaPayload) -> str:
        """Call XAJAX endpoint and return the XML download URL."""
        data = {
            "xajax": "herrDescargarXML",
            "xajaxargs[]": json.dumps(payload.raw),
        }
        req = Request(xajax_url, data=urlencode(data).encode("utf-8"), headers={"User-Agent": "bcn-scraper/0.1"})
        resp = urlopen(req, timeout=30).read().decode("utf-8", errors="ignore")
        # Response is XML with JS: window.open('...')
        m = re.search(r"open\('([^']+)'", resp)
        if not m:
            raise RuntimeError("No download URL found in XAJAX response")
        return urljoin(self.base, m.group(1))

    def fetch_historia_xml_download(self, identificador: str) -> HistoriaXmlDownload:
        """Download the aggregate XML for a Historia de la Ley with its URL."""
        html = self.fetch_historia_html(identificador)
        payloads = self.extract_payloads(html)
        if not payloads:
            raise RuntimeError("No payloads found in Historia HTML")
        xajax_url = self.xajax_endpoint_from_html(html)
        if not xajax_url:
            raise RuntimeError("No xajaxRequestUri found")
        xml_url = self.request_xml_url(xajax_url, payloads[0])
        req = Request(xml_url, headers={"User-Agent": "bcn-scraper/0.1"})
        return HistoriaXmlDownload(content=urlopen(req, timeout=60).read(), xml_url=xml_url)

    def fetch_historia_xml(self, identificador: str) -> bytes:
        """Download the aggregate XML for a Historia de la Ley."""
        return self.fetch_historia_xml_download(identificador).content

    def fetch_tramite_xml_downloads(self, identificador: str) -> List[HistoriaXmlDownload]:
        """Download individual tramite_reglamentario XML files with their URLs."""
        html = self.fetch_historia_html(identificador)
        payloads = self.extract_tramite_payloads(html)
        if not payloads:
            return []
        xajax_url = self.xajax_endpoint_from_html(html)
        if not xajax_url:
            raise RuntimeError("No xajaxRequestUri found")

        xmls: List[HistoriaXmlDownload] = []
        for payload in payloads:
            xml_url = self.request_xml_url(xajax_url, payload)
            req = Request(xml_url, headers={"User-Agent": "bcn-scraper/0.1"})
            xmls.append(HistoriaXmlDownload(content=urlopen(req, timeout=60).read(), xml_url=xml_url))
        return xmls

    def fetch_tramite_xmls(self, identificador: str) -> List[bytes]:
        """Download XML files for each individual tramite_reglamentario."""
        return [download.content for download in self.fetch_tramite_xml_downloads(identificador)]

    @staticmethod
    def parse_tramites(xml_bytes: bytes) -> List[Dict[str, str]]:
        """Parse tramite_reglamentario nodes into dicts.

        Returns list of dicts with titulo, bajada, contenido_html, fecha_tramite.
        """
        import xml.etree.ElementTree as ET

        rows: List[Dict[str, str]] = []
        root = ET.fromstring(xml_bytes)
        # iterate through tramite_reglamentario
        for elem in root.iter():
            tag = elem.tag.split('}', 1)[-1]
            if tag == 'tramite_reglamentario':
                titulo = ''
                bajada = ''
                contenido_html = ''
                fecha_tramite = ''
                for child in elem:
                    ctag = child.tag.split('}', 1)[-1]
                    if ctag == 'titulo':
                        titulo = (child.text or '').strip()
                    elif ctag == 'bajada':
                        bajada = (child.text or '').strip()
                    elif ctag == 'xml':
                        contenido_html = ''.join(ET.tostring(e, encoding='unicode') for e in list(child))
                        m = re.search(r'fecha="(\d{4}-\d{2}-\d{2})"', contenido_html)
                        if m:
                            fecha_tramite = m.group(1)
                rows.append({
                    'titulo': titulo,
                    'bajada': bajada,
                    'contenido_html': contenido_html,
                    'fecha_tramite': fecha_tramite,
                })
        return rows
