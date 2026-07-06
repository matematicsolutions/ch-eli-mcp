"""Async httpx client for the Fedlex SPARQL endpoint (fedlex.data.admin.ch).

Keyless, live Virtuoso SPARQL endpoint over Swiss federal legislation,
modelled with the JOLux ontology (same family used by Luxembourg's Legilux).
Fedlex is genuinely ELI-native - the resource URI itself is the ELI.

Note: Virtuoso's ``bif:contains`` full-text extension is disabled on this
public endpoint ("Illegal requests in query"), unlike the Chilean BCN
endpoint - full-text search here uses a standard SPARQL ``CONTAINS`` filter,
which is slower but portable.
"""

from __future__ import annotations

import anyio
import httpx

from .cache import HttpCache
from .citations import lang_uri

DEFAULT_BASE_URL = "https://fedlex.data.admin.ch/sparqlendpoint"
DEFAULT_TIMEOUT = httpx.Timeout(40.0, connect=10.0)
USER_AGENT = "ch-eli-mcp/0.1.0 (+https://github.com/matematicsolutions/ch-eli-mcp)"

_RETRY_STATUS = frozenset({429, 500, 502, 503, 504})
_MAX_ATTEMPTS = 3

_PREFIXES = """\
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
"""

_SEARCH_QUERY = _PREFIXES + """\
SELECT DISTINCT ?s ?title ?title_short ?sr_number WHERE {
  ?s a jolux:ConsolidationAbstract ; jolux:isRealizedBy ?expr .
  ?expr jolux:language <%s> ; jolux:title ?title .
  OPTIONAL { ?expr jolux:titleShort ?title_short }
  OPTIONAL { ?s jolux:classifiedByTaxonomyEntry ?tax . ?tax skos:notation ?sr_number }
  FILTER(CONTAINS(LCASE(?title), "%s"))
} LIMIT %d
"""

_GET_QUERY = _PREFIXES + """\
SELECT ?title ?title_short ?sr_number WHERE {
  <%s> jolux:isRealizedBy ?expr .
  ?expr jolux:language <%s> ; jolux:title ?title .
  OPTIONAL { ?expr jolux:titleShort ?title_short }
  OPTIONAL { <%s> jolux:classifiedByTaxonomyEntry ?tax . ?tax skos:notation ?sr_number }
}
"""


class FedlexClient:
    """Async client. Use as ``async with FedlexClient() as c: ...``."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        cache: HttpCache | None = None,
        timeout: httpx.Timeout = DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = base_url
        self._cache = cache or HttpCache()
        self._http = httpx.AsyncClient(
            timeout=timeout,
            headers={"User-Agent": USER_AGENT, "Accept": "application/sparql-results+json"},
        )

    async def __aenter__(self) -> FedlexClient:
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._http.aclose()
        self._cache.close()

    async def _query(self, sparql: str, *, category: str) -> list[dict]:
        cache_key = self.base_url + "?q=" + sparql
        cached = self._cache.get(cache_key)
        if cached is not None and isinstance(cached, list):
            return cached
        last_exc: Exception | None = None
        for attempt in range(_MAX_ATTEMPTS):
            try:
                resp = await self._http.get(self.base_url, params={"query": sparql})
                resp.raise_for_status()
                bindings = resp.json()["results"]["bindings"]
                self._cache.set(cache_key, bindings, ttl=HttpCache.ttl_for(category))
                return bindings
            except httpx.HTTPStatusError as exc:
                last_exc = exc
                if exc.response.status_code not in _RETRY_STATUS or attempt == _MAX_ATTEMPTS - 1:
                    raise
            except (httpx.TransportError, httpx.TimeoutException) as exc:
                last_exc = exc
                if attempt == _MAX_ATTEMPTS - 1:
                    raise
            await anyio.sleep(0.5 * (2**attempt))
        assert last_exc is not None
        raise last_exc

    async def search(self, query: str, lang: str = "DEU", limit: int = 20) -> list[dict]:
        needle = query.lower().replace('"', '\\"')
        sparql = _SEARCH_QUERY % (lang_uri(lang), needle, limit)
        return await self._query(sparql, category="search")

    async def get_act(self, uri: str, lang: str = "DEU") -> list[dict]:
        sparql = _GET_QUERY % (uri, lang_uri(lang), uri)
        return await self._query(sparql, category="act")
