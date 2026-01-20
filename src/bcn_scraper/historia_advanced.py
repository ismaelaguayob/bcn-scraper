"""Advanced search for Historia de la Ley (BCN) using XAJAX flow.

Note: The backend supports exact number search via key `numero`.
Other criteria may yield empty results depending on site behavior.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html import unescape
from typing import Dict, List, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class AdvancedSearchResult:
    identificador: str
    url: str
    titulo: str
    numero_ley: str


class HistoriaAdvancedSearch:
    """Advanced search supporting multiple criteria.

    Supported fields:
      - numero (ley o decreto) via numero_ley/numero_decreto
      - boletin
      - frase_publicacion
      - frase_tramitacion
      - fecha_publicacion (range)
      - fecha_inicio_tramite (range)
      - autor
    """

    base = "https://www.bcn.cl/historiadelaley/"
    xajax_url = "https://www.bcn.cl/historiadelaley/nc/busqueda-avanzada"

    def _call_ver_texto(self, query_json: str) -> str:
        payload = {
            "xajax": "verTextoCompleto",
            "xajaxargs[0]": query_json,
        }
        req = Request(self.xajax_url, data=urlencode(payload).encode("utf-8"), headers={"User-Agent": "bcn-scraper/0.1"})
        return urlopen(req, timeout=30).read().decode("utf-8", errors="ignore")

    def _extract_list_url(self, xajax_resp: str) -> Optional[str]:
        m = re.search(r"cargarUrlAjax\('([^']+)'", xajax_resp)
        if not m:
            return None
        return self.base + m.group(1)

    def _fetch_list_page(self, list_url: str) -> str:
        req = Request(list_url, headers={"User-Agent": "bcn-scraper/0.1"})
        return urlopen(req, timeout=30).read().decode("utf-8", errors="ignore")

    def _xajax_list_uri(self, html: str) -> Optional[str]:
        m = re.search(r"xajaxRequestUri=\"([^\"]+)\"", html)
        return m.group(1) if m else None

    def _fetch_list_results(self, xajax_list_url: str) -> str:
        payload = {"xajax": "mostrarResultadoBusqueda", "xajaxargs[]": ""}
        req = Request(xajax_list_url, data=urlencode(payload).encode("utf-8"), headers={"User-Agent": "bcn-scraper/0.1"})
        return urlopen(req, timeout=30).read().decode("utf-8", errors="ignore")

    def _parse_results(self, xajax_resp: str) -> List[AdvancedSearchResult]:
        ids = re.findall(r"/nc/historia-de-la-ley/(\d+)/", xajax_resp)
        payloads = re.findall(r"herrDescargarXML\(\"(\{.*?\})\"\)", xajax_resp, re.DOTALL)

        results: List[AdvancedSearchResult] = []
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
                m_title = re.search(r'"titulo":"([^"]+)"', raw)
                m_num = re.search(r'"numero_ley":"([^"]+)"', raw)
                if not m_num:
                    m_num = re.search(r'"numero":"([^"]+)"', raw)
                if m_title:
                    titulo = m_title.group(1)
                if m_num:
                    numero_ley = m_num.group(1)
            url = f"{self.base}nc/historia-de-la-ley/{hid}/"
            results.append(AdvancedSearchResult(identificador=hid, url=url, titulo=titulo, numero_ley=numero_ley))

        unique: Dict[str, AdvancedSearchResult] = {}
        for r in results:
            if r.identificador not in unique:
                unique[r.identificador] = r
            else:
                if (unique[r.identificador].titulo == "" and r.titulo) or (
                    unique[r.identificador].numero_ley == "" and r.numero_ley
                ):
                    unique[r.identificador] = r
        return list(unique.values())

    def search(self, *,
               numero_ley: Optional[str] = None,
               numero_boletin: Optional[str] = None,
               numero_decreto: Optional[str] = None,
               frase_publicacion: Optional[str] = None,
               frase_tramitacion: Optional[str] = None,
               fecha_publicacion_desde: Optional[str] = None,
               fecha_publicacion_hasta: Optional[str] = None,
               fecha_tramitacion_desde: Optional[str] = None,
               fecha_tramitacion_hasta: Optional[str] = None,
               autor: Optional[str] = None,
               operacion: str = "and") -> List[AdvancedSearchResult]:
        incluye: Dict[str, object] = {}

        # Exact number search uses key "numero" and expects leading space
        if numero_ley:
            incluye["numero"] = [{"valor": f" {numero_ley}", "excluye": False}]
        if numero_decreto:
            incluye["numero"] = [{"valor": f" {numero_decreto}", "excluye": False}]
        if numero_boletin:
            incluye["boletin"] = [{"valor": numero_boletin, "excluye": False}]
        if frase_publicacion:
            incluye["frase_publicacion"] = [{"valor": frase_publicacion, "excluye": False}]
        if frase_tramitacion:
            incluye["frase_tramitacion"] = [{"valor": frase_tramitacion, "excluye": False}]
        if autor:
            incluye["autor"] = [{"valor": autor, "excluye": False}]

        if fecha_publicacion_desde or fecha_publicacion_hasta:
            incluye["fecha_publicacion"] = [{
                "desde": fecha_publicacion_desde or "",
                "hasta": fecha_publicacion_hasta or "",
            }]
        if fecha_tramitacion_desde or fecha_tramitacion_hasta:
            incluye["fecha_inicio_tramite"] = [{
                "desde": fecha_tramitacion_desde or "",
                "hasta": fecha_tramitacion_hasta or "",
            }]

        query = {**incluye, "operacion": operacion}
        query_json = json.dumps(query, ensure_ascii=False)

        xajax_resp = self._call_ver_texto(query_json)
        list_url = self._extract_list_url(xajax_resp)
        if not list_url:
            return []
        list_html = self._fetch_list_page(list_url)
        xajax_list_url = self._xajax_list_uri(list_html)
        if not xajax_list_url:
            return []
        list_resp = self._fetch_list_results(xajax_list_url)
        return self._parse_results(list_resp)
