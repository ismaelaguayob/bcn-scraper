"""BCN scraper library."""
from .akoma_ntoso import (
    AKN_ERROR_PREFIX,
    add_akoma_ntoso_content,
    akn_url_from_document_uri,
    fetch_akoma_ntoso,
)
from .historia_client import HistoriaClient
from .historia_lookup import HistoriaLookup, HistoriaSearchResult
from .historia_advanced import HistoriaAdvancedSearch, AdvancedSearchResult
from .historia_dataframe import (
    DATAFRAME_COLUMNS,
    clean_tramite_html,
    extract_document_uri,
    historia_tramite_xmls_to_dataframe,
    historia_tramites_to_dataframe,
)
from .historia_suggest import HistoriaSuggest, SuggestResult
from .wrapper import historia_dataframe_from_ley_o_boletin

__all__ = [
    "HistoriaClient",
    "AKN_ERROR_PREFIX",
    "add_akoma_ntoso_content",
    "akn_url_from_document_uri",
    "fetch_akoma_ntoso",
    "HistoriaLookup",
    "HistoriaSearchResult",
    "HistoriaAdvancedSearch",
    "AdvancedSearchResult",
    "DATAFRAME_COLUMNS",
    "historia_tramites_to_dataframe",
    "historia_tramite_xmls_to_dataframe",
    "extract_document_uri",
    "clean_tramite_html",
    "HistoriaSuggest",
    "SuggestResult",
    "historia_dataframe_from_ley_o_boletin",
]
__version__ = "0.1.0"
