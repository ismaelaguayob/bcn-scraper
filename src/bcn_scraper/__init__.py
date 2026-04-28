"""BCN scraper library."""
from .akoma_ntoso import (
    AKN_ERROR_PREFIX,
    add_akoma_ntoso_content,
    akn_url_from_document_uri,
    debug_akoma_ntoso_errors,
    fetch_akoma_ntoso,
    is_retryable_akn_error,
)
from .akoma_speech import add_speech_content, extract_speech_from_akn
from .historia_client import HistoriaClient, HistoriaXmlDownload
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
    "debug_akoma_ntoso_errors",
    "fetch_akoma_ntoso",
    "is_retryable_akn_error",
    "add_speech_content",
    "extract_speech_from_akn",
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
    "HistoriaXmlDownload",
]
__version__ = "0.1.0"
