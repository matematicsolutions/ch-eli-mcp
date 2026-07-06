"""Plain dataclasses mirroring the Fedlex jolux ontology (SPARQL query results)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Act:
    uri: str
    lang: str
    sr_number: str | None
    title: str | None
    title_short: str | None


@dataclass(frozen=True)
class Citation:
    lex_uri: str
    human_readable_citation: str
    source_url: str
