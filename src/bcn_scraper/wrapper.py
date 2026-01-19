"""Wrapper utilities for Historia de la Ley data extraction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .historia_client import HistoriaClient
from .historia_dataframe import historia_tramites_to_dataframe
from .historia_lookup import HistoriaLookup, HistoriaSearchResult


@dataclass(frozen=True)
class HistoriaWrapperResult:
    query: str
    identificador: str
    result: HistoriaSearchResult


def historia_dataframe_from_ley_o_boletin(
    *,
    numero_ley: Optional[str] = None,
    numero_boletin: Optional[str] = None,
):
    """Resolve Historia de la Ley ID and return a DataFrame of tramites."""
    lookup = HistoriaLookup()
    results = lookup.search(numero_ley=numero_ley, numero_boletin=numero_boletin)
    if not results:
        query = numero_ley or numero_boletin or ""
        raise ValueError(f"No results for query: {query}")

    selected = results[0]
    client = HistoriaClient()
    xml_bytes = client.fetch_historia_xml(selected.identificador)
    df = historia_tramites_to_dataframe(xml_bytes)
    return HistoriaWrapperResult(query=numero_ley or numero_boletin or "", identificador=selected.identificador, result=selected), df
