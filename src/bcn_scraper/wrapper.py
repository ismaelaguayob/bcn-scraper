"""Wrapper utilities for Historia de la Ley data extraction."""

from __future__ import annotations

from typing import Callable, Mapping, Optional

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
    fetch_akn: bool = False,
    akn_filter: Optional[Callable[[Mapping[str, str]], bool]] = None,
    akn_fetcher: Callable[[str], str] = fetch_akoma_ntoso,
):
    """Resolve Historia de la Ley ID and return a DataFrame of all tramites.

    When ``fetch_akn=True``, ``akn_filter`` optionally selects which tramites
    receive AKN. It takes a dictionary with the row's metadata (for example,
    ``title`` or ``document_uri``) and returns a boolean. Without a filter all
    AKN is fetched; with ``fetch_akn=False`` the filter is ignored.
    """
    lookup = HistoriaLookup()
    results = lookup.search(numero_ley=numero_ley, numero_boletin=numero_boletin)
    if not results:
        query = numero_ley or numero_boletin or ""
        raise ValueError(f"No results for query: {query}")

    selected = results[0]
    bcn_url = getattr(selected, "url", f"https://www.bcn.cl/historiadelaley/nc/historia-de-la-ley/{selected.identificador}/")
    client = HistoriaClient()
    if prefer_individual_tramites:
        tramite_downloads = client.fetch_tramite_xml_downloads(selected.identificador)
        if tramite_downloads:
            df = historia_tramite_xmls_to_dataframe(
                [download.content for download in tramite_downloads],
                clean_text=clean_text,
                bcn_url=bcn_url,
                xml_urls=[download.xml_url for download in tramite_downloads],
            )
            return add_akoma_ntoso_content(
                df, fetcher=akn_fetcher, akn_filter=akn_filter
            ) if fetch_akn else df

    download = client.fetch_historia_xml_download(selected.identificador)
    df = historia_tramites_to_dataframe(
        download.content,
        clean_text=clean_text,
        bcn_url=bcn_url,
        xml_url=download.xml_url,
    )
    return add_akoma_ntoso_content(
        df, fetcher=akn_fetcher, akn_filter=akn_filter
    ) if fetch_akn else df
