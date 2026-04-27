"""Wrapper utilities for Historia de la Ley data extraction."""

from __future__ import annotations

from typing import Callable, Optional

from .akoma_ntoso import add_akoma_ntoso_content, fetch_akoma_ntoso
from .historia_client import HistoriaClient
from .historia_dataframe import historia_tramite_xmls_to_dataframe, historia_tramites_to_dataframe
from .historia_lookup import HistoriaLookup


def historia_dataframe_from_ley_o_boletin(
    *,
    numero_ley: Optional[str] = None,
    numero_boletin: Optional[str] = None,
    clean_text: bool = False,
    prefer_individual_tramites: bool = True,
    fetch_akn: bool = True,
    akn_fetcher: Callable[[str], str] = fetch_akoma_ntoso,
):
    """Resolve Historia de la Ley ID and return a DataFrame of tramites."""
    lookup = HistoriaLookup()
    results = lookup.search(numero_ley=numero_ley, numero_boletin=numero_boletin)
    if not results:
        query = numero_ley or numero_boletin or ""
        raise ValueError(f"No results for query: {query}")

    selected = results[0]
    bcn_url = getattr(selected, "url", f"https://www.bcn.cl/historiadelaley/nc/historia-de-la-ley/{selected.identificador}/")
    client = HistoriaClient()
    if prefer_individual_tramites:
        tramite_xmls = client.fetch_tramite_xmls(selected.identificador)
        if tramite_xmls:
            df = historia_tramite_xmls_to_dataframe(tramite_xmls, clean_text=clean_text, bcn_url=bcn_url)
            return add_akoma_ntoso_content(df, fetcher=akn_fetcher) if fetch_akn else df

    xml_bytes = client.fetch_historia_xml(selected.identificador)
    df = historia_tramites_to_dataframe(xml_bytes, clean_text=clean_text, bcn_url=bcn_url)
    return add_akoma_ntoso_content(df, fetcher=akn_fetcher) if fetch_akn else df
