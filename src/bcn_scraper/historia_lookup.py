"""Lookup Historia de la Ley IDs using simple and advanced search."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from html import unescape

from .historia_advanced import HistoriaAdvancedSearch, AdvancedSearchResult


@dataclass(frozen=True)
class HistoriaSearchResult:
    identificador: str
    url: str
    titulo: str
    numero_ley: str


class HistoriaLookup:
    """Search Historia de la Ley using simple or advanced flows.

    - Simple search: keyword queries (returns multiple results).
    - Advanced search: ley or boletin number (prefer exact ID).
    """

    base = "https://www.bcn.cl/historiadelaley/"

    def search_simple(self, query: str) -> List[HistoriaSearchResult]:
        xajax_url = f"{self.base}nc/lista-de-resultado-de-busqueda/{query}/"
        payload = {
            "xajax": "mostrarResultadoBusqueda",
            "xajaxargs[]": "",
        }
        req = Request(xajax_url, data=urlencode(payload).encode("utf-8"), headers={"User-Agent": "bcn-scraper/0.1"})
        resp = urlopen(req, timeout=30).read().decode("utf-8", errors="ignore")

        # Extract historia IDs and titles from the embedded HTML in XAJAX response
        ids = re.findall(r"/nc/historia-de-la-ley/(\d+)/", resp)
        # extract JSON-like payload in herrDescargarXML for titles/numero_ley
        payloads = re.findall(r"herrDescargarXML\(\"(\{.*?\})\"\)", resp, re.DOTALL)

        results: List[HistoriaSearchResult] = []
        for i, hid in enumerate(ids):
            titulo = ""
            numero_ley = ""
            if i < len(payloads):
                raw = unescape(payloads[i])
                raw = raw.encode("utf-8").decode("unicode_escape")
                raw = raw.replace("\\\"", '"')
                try:
                    raw = raw.encode("utf-8").decode("unicode_escape")
                except UnicodeDecodeError:
                    pass
                # lightweight extraction
                m_title = re.search(r'"titulo":"([^"]+)"', raw)
                m_num = re.search(r'"numero_ley":"([^"]+)"', raw)
                if not m_num:
                    m_num = re.search(r'"numero":"([^"]+)"', raw)
                if m_title:
                    titulo = m_title.group(1)
                if m_num:
                    numero_ley = m_num.group(1)
            url = f"{self.base}nc/historia-de-la-ley/{hid}/"
            results.append(HistoriaSearchResult(identificador=hid, url=url, titulo=titulo, numero_ley=numero_ley))

        # deduplicate by identificador
        unique = {}
        for r in results:
            if r.identificador not in unique:
                unique[r.identificador] = r
            else:
                # Keep the entry with more metadata
                if (unique[r.identificador].titulo == "" and r.titulo) or (
                    unique[r.identificador].numero_ley == "" and r.numero_ley
                ):
                    unique[r.identificador] = r
        return list(unique.values())

    def search_by_ley_or_boletin(
        self,
        *,
        numero_ley: Optional[str] = None,
        numero_boletin: Optional[str] = None,
    ) -> List[HistoriaSearchResult]:
        if not numero_ley and not numero_boletin:
            raise ValueError("Provide numero_ley or numero_boletin")
        advanced = HistoriaAdvancedSearch()
        results = advanced.search(numero_ley=numero_ley, numero_boletin=numero_boletin)
        mapped = [
            HistoriaSearchResult(
                identificador=r.identificador,
                url=r.url,
                titulo=r.titulo,
                numero_ley=r.numero_ley,
            )
            for r in results
        ]
        if mapped:
            return mapped
        fallback_query = numero_ley or numero_boletin or ""
        return self.search_simple(fallback_query)

    def search(
        self,
        query: Optional[str] = None,
        *,
        numero_ley: Optional[str] = None,
        numero_boletin: Optional[str] = None,
    ) -> List[HistoriaSearchResult]:
        if numero_ley or numero_boletin:
            return self.search_by_ley_or_boletin(numero_ley=numero_ley, numero_boletin=numero_boletin)
        if not query:
            raise ValueError("Provide query or numero_ley/numero_boletin")
        return self.search_simple(query)
