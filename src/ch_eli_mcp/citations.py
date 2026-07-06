"""Citation contract for ch-eli-mcp.

Fedlex is genuinely ELI-native: every act has a URI of the form
``https://fedlex.data.admin.ch/eli/cc/{year}/{number}``. The Swiss citation
convention layered on top is the SR number (Systematische Sammmlung /
Classified Compilation number, e.g. "101" for the Federal Constitution) -
we surface both.
"""

from __future__ import annotations

from typing import Any

from .models import Act, Citation

_LANG_URIS = {
    "DEU": "de",
    "FRA": "fr",
    "ITA": "it",
    "ENG": "en",
}

_PUBLIC_BASE = "https://www.fedlex.admin.ch"
_DATA_BASE = "https://fedlex.data.admin.ch"


def lang_uri(lang: str) -> str:
    """Map a short language code (de/fr/it/en) to the EU authority-table URI Fedlex expects."""
    code = lang.upper()
    if code in ("DE", "FR", "IT", "EN"):
        code = {"DE": "DEU", "FR": "FRA", "IT": "ITA", "EN": "ENG"}[code]
    if code not in _LANG_URIS:
        raise ValueError(f"unsupported lang={lang!r}")
    return f"http://publications.europa.eu/resource/authority/language/{code}"


def parse_act(uri: str, lang: str, row: dict[str, Any]) -> Act:
    def _val(key: str) -> str | None:
        return row.get(key, {}).get("value")

    return Act(
        uri=uri,
        lang=lang,
        sr_number=_val("sr_number"),
        title=_val("title"),
        title_short=_val("title_short"),
    )


def build_citation(a: Act) -> Citation:
    short_lang = {"DEU": "de", "FRA": "fr", "ITA": "it", "ENG": "en"}.get(a.lang, "en")
    path = a.uri.replace(_DATA_BASE, "").lstrip("/")
    source_url = f"{_PUBLIC_BASE}/{path}/{short_lang}"
    label = a.title_short or a.title or a.uri
    human = f"{label} (SR {a.sr_number})" if a.sr_number else label
    return Citation(lex_uri=a.uri, human_readable_citation=human, source_url=source_url)
