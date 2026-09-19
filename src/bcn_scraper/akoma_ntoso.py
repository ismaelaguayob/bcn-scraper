"""Utilities for BCN Akoma Ntoso document XML."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from time import sleep
from typing import Callable, Mapping, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


AKN_ERROR_PREFIX = "ERROR:"
RETRYABLE_HTTP_CODES = {502, 503, 504}
RETRYABLE_ERROR_MARKERS = (
    "handshake operation timed out",
    "timed out",
    "timeout",
    "url error",
    "network error",
    "connection reset",
    "temporary failure",
    "remote end closed connection",
)


def akn_url_from_document_uri(document_uri: str) -> str:
    """Build the BCN Akoma Ntoso XML URL from a datos.bcn document URI."""
    document_uri = (document_uri or "").strip()
    if not document_uri:
        return ""
    return document_uri.rstrip("/") + ".xml"


def fetch_akoma_ntoso(
    akn_url: str,
    *,
    timeout: int = 30,
    max_attempts: int = 1,
    backoff_seconds: float = 0.0,
) -> str:
    """Download and validate Akoma Ntoso XML.

    Returns the XML as text when BCN returns well-formed XML. On HTTP, network,
    decoding, or XML parse errors, returns an ``ERROR: ...`` string so callers
    can keep row-level provenance without failing the whole extraction.

    The default is intentionally modest because AKN is slow and not always
    available in BCN. Use ``debug_akoma_ntoso_errors`` to retry handshake or
    timeout failures with more aggressive parameters after a first extraction.
    """
    akn_url = (akn_url or "").strip()
    if not akn_url:
        return ""

    attempts = max(1, max_attempts)
    last_error = ""
    for attempt in range(1, attempts + 1):
        try:
            req = Request(akn_url, headers={"User-Agent": "bcn-scraper/0.1"})
            content = urlopen(req, timeout=timeout).read().decode("utf-8", errors="replace")
        except HTTPError as e:
            last_error = f"{AKN_ERROR_PREFIX} HTTP {e.code} for {akn_url}"
            if e.code not in RETRYABLE_HTTP_CODES:
                return f"{last_error}; attempts={attempt}"
        except URLError as e:
            last_error = f"{AKN_ERROR_PREFIX} URL error for {akn_url}: {e.reason}"
        except OSError as e:
            last_error = f"{AKN_ERROR_PREFIX} network error for {akn_url}: {e}"
        else:
            try:
                root = ET.fromstring(content)
            except ET.ParseError as e:
                preview = content[:200].replace("\n", " ").strip()
                return f"{AKN_ERROR_PREFIX} invalid XML for {akn_url}: {e}; preview={preview}; attempts={attempt}"
            else:
                if root.tag.split("}", 1)[-1] == "akomaNtoso":
                    return content
                return f"{AKN_ERROR_PREFIX} unexpected XML root for {akn_url}: {root.tag}; attempts={attempt}"

        if attempt < attempts:
            sleep(backoff_seconds * attempt)

    return f"{last_error}; attempts={attempts}"


def is_retryable_akn_error(value: str) -> bool:
    """Return True when an AKN error looks like a network/timeout failure."""
    text = (value or "").strip()
    if not text.startswith(AKN_ERROR_PREFIX):
        return False
    lower = text.lower()
    if "http 500" in lower or "invalid xml" in lower or "unexpected xml root" in lower:
        return False
    return any(marker in lower for marker in RETRYABLE_ERROR_MARKERS)


def add_akoma_ntoso_content(
    df,
    *,
    fetcher: Callable[[str], str] = fetch_akoma_ntoso,
    akn_filter: Optional[Callable[[Mapping[str, str]], bool]] = None,
):
    """Fetch AKN for selected tramites, preserving every row and its metadata.

    ``akn_filter`` receives each tramite as a dictionary and returns whether to
    fetch its AKN. With no filter, all rows are selected. Unselected rows retain
    their existing ``akn_content`` (or an empty string if the column is new).
    """
    result = df.copy()
    if "akn_content" not in result.columns:
        result["akn_content"] = ""
    if "akn_url" not in result.columns or result.empty:
        return result

    selected = (
        [akn_filter(row) for row in result.to_dict(orient="records")]
        if akn_filter is not None
        else slice(None)
    )
    result.loc[selected, "akn_content"] = (
        result.loc[selected, "akn_url"].fillna("").map(
            lambda url: fetcher(url) if url else ""
        )
    )
    return result


def debug_akoma_ntoso_errors(
    df,
    *,
    timeout: int = 90,
    max_attempts: int = 3,
    backoff_seconds: float = 2.0,
    fetcher: Optional[Callable[[str], str]] = None,
):
    """Retry only rows whose ``akn_content`` failed due to timeout/network errors.

    This helper is meant for second-pass debugging. It deliberately skips HTTP
    500 and XML parse errors because BCN can return non-XML payloads for
    documents that do not have usable Akoma Ntoso content.
    """
    result = df.copy()
    if "akn_content" not in result.columns or "akn_url" not in result.columns:
        return result

    def refetch(url: str) -> str:
        if fetcher is not None:
            return fetcher(url)
        return fetch_akoma_ntoso(
            url,
            timeout=timeout,
            max_attempts=max_attempts,
            backoff_seconds=backoff_seconds,
        )

    for idx, row in result.iterrows():
        url = row.get("akn_url", "")
        content = row.get("akn_content", "")
        if url and is_retryable_akn_error(content):
            result.at[idx, "akn_content"] = refetch(url)
    return result
