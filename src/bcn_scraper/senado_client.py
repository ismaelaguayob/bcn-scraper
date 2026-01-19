"""Client for Senado tramitacion pages and document downloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class SenadoDocumento:
    tipo: str
    url: str


class SenadoClient:
    """Minimal client to scrape Senado tramitacion endpoints."""

    base = "https://tramitacion.senado.cl"

    def fetch_boletin(self, boletin: str) -> str:
        url = f"{self.base}/appsenado/index.php?mo=tramitacion&ac=boletin_x_fecha&boletin={boletin}&etc=0"
        req = Request(url, headers={"User-Agent": "bcn-scraper/0.1"})
        return urlopen(req, timeout=30).read().decode("utf-8", errors="ignore")

    def fetch_datos_proy(self, boletin: str) -> str:
        url = f"{self.base}/appsenado/index.php?mo=tramitacion&ac=datos_proy&nboletin={boletin}&etc=0"
        req = Request(url, headers={"User-Agent": "bcn-scraper/0.1"})
        return urlopen(req, timeout=30).read().decode("utf-8", errors="ignore")

    def extract_proyid(self, datos_html: str) -> Optional[str]:
        # proyid=16006;
        import re
        m = re.search(r"proyid\s*=\s*(\d+)", datos_html)
        if not m:
            return None
        return m.group(1)

    def fetch_tramites(self, proyid: str) -> str:
        url = f"{self.base}/appsenado/index.php?mo=tramitacion&ac=tramites&proyid={proyid}&etc=0"
        req = Request(url, headers={"User-Agent": "bcn-scraper/0.1"})
        return urlopen(req, timeout=30).read().decode("utf-8", errors="ignore")

    def parse_tramites(self, tramites_html: str) -> List[Dict[str, str]]:
        soup = BeautifulSoup(tramites_html, "html.parser")
        rows: List[Dict[str, str]] = []
        for tr in soup.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) >= 7:
                # skip header-like rows
                if tds[0].get_text(' ', strip=True).lower().startswith('sesión'):
                    continue
                doc_td = tds[4]
                link = doc_td.find('a')
                rows.append({
                    'sesion_leg': tds[0].get_text(' ', strip=True),
                    'fecha': tds[1].get_text(' ', strip=True),
                    'subetapa': tds[2].get_text(' ', strip=True),
                    'etapa': tds[3].get_text(' ', strip=True),
                    'documento_texto': doc_td.get_text(' ', strip=True),
                    'documento_url': link.get('href') if link else '',
                    'fecha_sort': tds[5].get_text(' ', strip=True),
                    'strcompa': tds[6].get_text(' ', strip=True),
                })
        return rows
