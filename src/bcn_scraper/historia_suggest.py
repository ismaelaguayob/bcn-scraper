"""Suggestion endpoints for Historia de la Ley."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class SuggestResult:
    value: str


class HistoriaSuggest:
    """Query suggestion endpoints (eID=sugerenciaBusqueda).

    Topics observed:
      - numero_boletines
      - numeroley
      - palabras_frases
      - autores
    """

    base = "https://www.bcn.cl/historiadelaley/index.php"

    def suggest(self, topic: str, word: str) -> List[SuggestResult]:
        word = word.strip()
        params = {
            "eID": "sugerenciaBusqueda",
            "topico": topic,
            "palabra": word,
        }
        url = f"{self.base}?{urlencode(params)}"
        req = Request(url, headers={"User-Agent": "bcn-scraper/0.1"})
        data = urlopen(req, timeout=30).read().decode("utf-8", errors="ignore")
        try:
            items = json.loads(data)
        except json.JSONDecodeError:
            return []
        return [SuggestResult(value=str(i).strip()) for i in items]
