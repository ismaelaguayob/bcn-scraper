"""Utilities for BCN Akoma Ntoso document XML."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from time import sleep
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


AKN_ERROR_PREFIX = "ERROR:"
RETRYABLE_HTTP_CODES = {500, 502, 503, 504}


def akn_url_from_document_uri(document_uri: str) -> str:
    """Build the BCN Akoma Ntoso XML URL from a datos.bcn document URI."""
    document_uri = (document_uri or "").strip()
    if not document_uri:
        return ""
    return document_uri.rstrip("/") + ".xml"


def fetch_akoma_ntoso(
    akn_url: str,
    *,
    timeout: int = 60,
    max_attempts: int = 3,
    backoff_seconds: float = 2.0,
) -> str:
    """Download and validate Akoma Ntoso XML.

    Returns the XML as text when BCN returns well-formed XML. On HTTP, network,
    decoding, or XML parse errors, returns an ``ERROR: ...`` string so callers
    can keep row-level provenance without failing the whole extraction.
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
                return last_error
        except URLError as e:
            last_error = f"{AKN_ERROR_PREFIX} URL error for {akn_url}: {e.reason}"
        except OSError as e:
            last_error = f"{AKN_ERROR_PREFIX} network error for {akn_url}: {e}"
        else:
            try:
                root = ET.fromstring(content)
            except ET.ParseError as e:
                preview = content[:200].replace("\n", " ").strip()
                last_error = f"{AKN_ERROR_PREFIX} invalid XML for {akn_url}: {e}; preview={preview}"
            else:
                if root.tag.split("}", 1)[-1] == "akomaNtoso":
                    return content
                last_error = f"{AKN_ERROR_PREFIX} unexpected XML root for {akn_url}: {root.tag}"

        if attempt < attempts:
            sleep(backoff_seconds * attempt)

    return f"{last_error}; attempts={attempts}"


def add_akoma_ntoso_content(
    df,
    *,
    fetcher: Callable[[str], str] = fetch_akoma_ntoso,
):
    """Return a copy of ``df`` with ``akn_content`` filled from ``akn_url``."""
    result = df.copy()
    if "akn_content" not in result.columns:
        result["akn_content"] = ""
    if "akn_url" not in result.columns:
        return result

    result["akn_content"] = result["akn_url"].map(lambda url: fetcher(url) if url else "")
    return result
