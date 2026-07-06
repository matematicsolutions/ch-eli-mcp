"""Live smoke test against the real Fedlex SPARQL endpoint. Network required."""

from __future__ import annotations

import pytest

from ch_eli_mcp.citations import build_citation, parse_act
from ch_eli_mcp.client import FedlexClient


@pytest.mark.asyncio
async def test_search_and_get_act() -> None:
    async with FedlexClient() as client:
        rows = await client.search("Datenschutz", "DEU", limit=3)
        assert len(rows) == 3

        first = parse_act(rows[0]["s"]["value"], "DEU", rows[0])
        citation = build_citation(first)
        assert citation.lex_uri.startswith("https://fedlex.data.admin.ch/eli/")
        assert citation.source_url.startswith("https://www.fedlex.admin.ch/eli/")

        constitution_uri = "https://fedlex.data.admin.ch/eli/cc/1999/404"
        detail_rows = await client.get_act(constitution_uri, "DEU")
        assert detail_rows
        detail = parse_act(constitution_uri, "DEU", detail_rows[0])
        detail_citation = build_citation(detail)
        assert detail.sr_number == "101"
        assert detail_citation.human_readable_citation == "BV (SR 101)"
