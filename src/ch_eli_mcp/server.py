"""FastMCP entry point - Swiss federal legislation (Fedlex) tools.

Run:

    python -m ch_eli_mcp.server

Configuration via env:

- ``CH_ELI_CACHE_DIR`` (default ``~/.matematic/cache/ch-eli``)
- ``CH_ELI_AUDIT_DIR`` (default ``~/.matematic/audit``)
- ``CH_ELI_BASE_URL`` (default ``https://fedlex.data.admin.ch/sparqlendpoint``)
"""

from __future__ import annotations

import dataclasses
import os

import httpx
from fastmcp import FastMCP
from mcp.types import ToolAnnotations

from . import runtime
from .audit import AuditLogger, hash_input, timer
from .citations import build_citation, parse_act
from .client import DEFAULT_BASE_URL, FedlexClient

INSTRUCTIONS = """\
This MCP server exposes Fedlex, the Swiss Federal Chancellery's official publication platform for federal legislation. Fedlex is genuinely ELI-native - the resource URI itself is the ELI (European Legislation Identifier), even though Switzerland is not an EU member. Multilingual: German, French, Italian, English.

## Call order

1. `ch_search_acts` - full-text search over act titles in a given `lang` (`"DEU"`, `"FRA"`, `"ITA"`, or `"ENG"`).
2. `ch_get_act` - full detail for one act by its `uri` (from the search results), including its SR number (Systematische Sammlung / Classified Compilation number - the citation convention used in Swiss legal practice).

## Hard constraints

- **The ELI is the URI itself** - `lex_uri` is never invented, it comes directly from the SPARQL query result.
- **Every response has `human_readable_citation` + `source_url`** - cite both to the user (e.g. "Bundesverfassung der Schweizerischen Eidgenossenschaft (SR 101)").
- **No full-text law content** - this connector returns metadata (title, SR number), not the operative articles. Follow `source_url` for that.
- **Audit log JSONL** - every tool call appends to `~/.matematic/audit/ch-eli-mcp.jsonl`.

## Error iteration

Tools return a structured error with a `[code]` prefix:
- `invalid_arg` - a parameter is missing, out of range, or an unsupported `lang`.
- `not_found` - no act exists at that URI.
- `upstream_error` - a Fedlex SPARQL endpoint error (HTTP, timeout, malformed query). Retry once before surfacing.

## Response style

- Cite acts as `human_readable_citation`: "Bundesverfassung der Schweizerischen Eidgenossenschaft (SR 101)".
- NEVER invent a URI, SR number, or title - take each from the tool output.
"""


class ToolError(Exception):
    """Structured error for ch-eli MCP tools - visible to the LLM with a [code] prefix."""

    VALID_CODES = frozenset({"invalid_arg", "not_found", "upstream_error"})

    def __init__(self, code: str, message: str):
        if code not in self.VALID_CODES:
            raise ValueError(f"Unknown ToolError code: {code}. Valid: {sorted(self.VALID_CODES)}")
        self.code = code
        super().__init__(f"[{code}] {message}")


READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    idempotentHint=True,
    destructiveHint=False,
    openWorldHint=True,
)

mcp: FastMCP = FastMCP(name="ch-eli-mcp", instructions=INSTRUCTIONS)

_VALID_LANGS = frozenset({"DEU", "FRA", "ITA", "ENG"})


def _base_url() -> str:
    return os.environ.get("CH_ELI_BASE_URL", runtime.base_url("eli", DEFAULT_BASE_URL))


def _audit() -> AuditLogger:
    return AuditLogger()


def _check_lang(lang: str) -> str:
    code = lang.upper()
    if code not in _VALID_LANGS:
        raise ToolError("invalid_arg", f"lang={lang!r} must be one of {sorted(_VALID_LANGS)}.")
    return code


def _map_upstream(exc: Exception) -> Exception:
    if isinstance(exc, (httpx.HTTPStatusError, httpx.TransportError, httpx.TimeoutException)):
        return ToolError("upstream_error", f"Fedlex SPARQL endpoint error: {type(exc).__name__}: {exc}")
    return exc


def _to_dict(a) -> dict:
    citation = build_citation(a)
    return {**dataclasses.asdict(a), **dataclasses.asdict(citation)}


# ---------------------------------------------------------------------------
# ch_search_acts
# ---------------------------------------------------------------------------


@mcp.tool(annotations=READ_ONLY)
async def ch_search_acts(query: str, lang: str = "DEU", limit: int = 20) -> dict:
    """Full-text search over Swiss federal act titles.

    Args:
        query: free text, e.g. ``"Datenschutz"``.
        lang: one of ``"DEU"``, ``"FRA"``, ``"ITA"``, ``"ENG"`` (default ``"DEU"``).
        limit: max results (default 20).

    Returns:
        ``{"total": int, "items": [...]}`` - each item carries the citation contract.
    """
    audit = _audit()
    if not query or not query.strip():
        raise ToolError("invalid_arg", "query must be a non-empty string.")
    lang = _check_lang(lang)
    input_hash = hash_input({"query": query, "lang": lang, "limit": limit})

    with timer() as t:
        try:
            async with FedlexClient(base_url=_base_url()) as client:
                rows = await client.search(query, lang, limit)
        except Exception as exc:
            audit.log(tool="ch_search_acts", input_hash=input_hash, output_count_or_size=0,
                      duration_ms=t.duration_ms if t.duration_ms else 0, status="error",
                      error=f"{type(exc).__name__}: {exc}")
            raise _map_upstream(exc) from exc

    items = [
        _to_dict(parse_act(r["s"]["value"], lang, r)) for r in rows
    ]
    audit.log(tool="ch_search_acts", input_hash=input_hash, output_count_or_size=len(items),
              duration_ms=t.duration_ms, status="ok")
    return {"total": len(items), "items": items}


# ---------------------------------------------------------------------------
# ch_get_act
# ---------------------------------------------------------------------------


@mcp.tool(annotations=READ_ONLY)
async def ch_get_act(uri: str, lang: str = "DEU") -> dict:
    """Fetch full detail for one Swiss federal act by its Fedlex ELI URI.

    Args:
        uri: e.g. ``"https://fedlex.data.admin.ch/eli/cc/1999/404"``.
        lang: one of ``"DEU"``, ``"FRA"``, ``"ITA"``, ``"ENG"`` (default ``"DEU"``).

    Returns:
        A dict with ``sr_number``, ``title``, ``title_short``, ``lex_uri``,
        ``human_readable_citation``, ``source_url``.
    """
    audit = _audit()
    if not uri or not uri.startswith("https://fedlex.data.admin.ch/eli/"):
        raise ToolError("invalid_arg", "uri must be a https://fedlex.data.admin.ch/eli/... URI.")
    lang = _check_lang(lang)
    input_hash = hash_input({"uri": uri, "lang": lang})

    with timer() as t:
        try:
            async with FedlexClient(base_url=_base_url()) as client:
                rows = await client.get_act(uri, lang)
        except Exception as exc:
            audit.log(tool="ch_get_act", input_hash=input_hash, output_count_or_size=0,
                      duration_ms=t.duration_ms if t.duration_ms else 0, status="error",
                      error=f"{type(exc).__name__}: {exc}")
            raise _map_upstream(exc) from exc

    if not rows:
        raise ToolError("not_found", f"No act found at uri={uri!r} for lang={lang!r}.")
    result = _to_dict(parse_act(uri, lang, rows[0]))
    audit.log(tool="ch_get_act", input_hash=input_hash, output_count_or_size=1,
              duration_ms=t.duration_ms, status="ok")
    return result


def main() -> None:
    """Run the MCP server over stdio (default for Claude Code)."""
    mcp.run()


if __name__ == "__main__":
    main()
