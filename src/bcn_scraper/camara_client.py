"""Client for Camara de Diputados tramitacion pages and document links."""

from __future__ import annotations

from typing import Dict, List
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup


class CamaraClient:
    """Minimal client to scrape Camara tramitacion page."""

    base = "https://www.camara.cl"

    def fetch_tramitacion(self, prm_id: str, prm_boletin: str) -> str:
        url = f"{self.base}/legislacion/proyectosdeley/tramitacion.aspx?prmID={prm_id}&prmBOLETIN={prm_boletin}"
        req = Request(url, headers={"User-Agent": "bcn-scraper/0.1"})
        return urlopen(req, timeout=30).read().decode("utf-8", errors="ignore")

    def parse_tramitacion(self, html: str) -> List[Dict[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        rows: List[Dict[str, str]] = []
        for table in soup.find_all('table'):
            headers = [th.get_text(' ', strip=True) for th in table.find_all('th')]
            if headers[:5] == ['Fecha', 'Sesión', 'Etapa', 'Sub-etapa', 'Documento']:
                for tr in table.find_all('tr'):
                    tds = tr.find_all('td')
                    if tds and len(tds) >= 5:
                        link = tds[4].find('a')
                        href = link.get('href') if link else ''
                        rows.append({
                            'fecha': tds[0].get_text(' ', strip=True),
                            'sesion': tds[1].get_text(' ', strip=True),
                            'etapa': tds[2].get_text(' ', strip=True),
                            'subetapa': tds[3].get_text(' ', strip=True),
                            'documento_url': urljoin(self.base, href) if href else '',
                        })
                break
        return rows
