"""BCN scraper library."""
from .akoma_ntoso import (
    AKN_ERROR_PREFIX,
    add_akoma_ntoso_content,
    akn_url_from_document_uri,
    debug_akoma_ntoso_errors,
    fetch_akoma_ntoso,
    is_retryable_akn_error,
)
from .akoma_speech import (
    add_speech_content,
    collect_unlabeled_speaker_candidates,
    extract_speech_from_akn,
    normalize_speech_content,
)
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
from .parliamentary_data import (
    build_parliamentarian_table,
    collect_bcn_speaker_references,
    debug_parliamentarian_data_errors,
    fetch_parliamentarian_data,
    fetch_rdf_json,
    is_bcn_person_url,
    missing_parliamentarian_data_mask,
    parliamentarian_relevant_columns,
    rdf_json_url,
)
from .speech_dataframe import (
    build_speech_analysis_dataframe,
    flatten_speech_content,
)
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
    "collect_unlabeled_speaker_candidates",
    "extract_speech_from_akn",
    "normalize_speech_content",
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
    "build_parliamentarian_table",
    "collect_bcn_speaker_references",
    "debug_parliamentarian_data_errors",
    "fetch_parliamentarian_data",
    "fetch_rdf_json",
    "is_bcn_person_url",
    "missing_parliamentarian_data_mask",
    "parliamentarian_relevant_columns",
    "rdf_json_url",
    "build_speech_analysis_dataframe",
    "flatten_speech_content",
    "historia_dataframe_from_ley_o_boletin",
    "HistoriaXmlDownload",
]
__version__ = "0.1.0"
