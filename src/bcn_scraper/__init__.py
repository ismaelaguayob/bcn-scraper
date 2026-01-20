"""BCN scraper library."""
from .historia_client import HistoriaClient
from .historia_lookup import HistoriaLookup, HistoriaSearchResult
from .historia_advanced import HistoriaAdvancedSearch, AdvancedSearchResult
from .historia_dataframe import historia_tramites_to_dataframe, clean_tramite_html
from .historia_suggest import HistoriaSuggest, SuggestResult
from .wrapper import historia_dataframe_from_ley_o_boletin

__all__ = [
    "HistoriaClient",
    "HistoriaLookup",
    "HistoriaSearchResult",
    "HistoriaAdvancedSearch",
    "AdvancedSearchResult",
    "historia_tramites_to_dataframe",
    "clean_tramite_html",
    "HistoriaSuggest",
    "SuggestResult",
    "historia_dataframe_from_ley_o_boletin",
]
__version__ = "0.1.0"
