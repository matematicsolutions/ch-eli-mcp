# Sources

## Fedlex SPARQL endpoint (`fedlex.data.admin.ch/sparqlendpoint`)

- **Origin**: Swiss Federal Chancellery.
- **License**: official federal publication platform; no separate reuse
  license found during discovery beyond it being the public consolidation
  meant for public use - same caution class as other government legal
  text sources in this fleet (flagged, not blocking a keyless-fetch
  connector).
- **Access**: keyless SPARQL 1.1 (Virtuoso), JSON results.
- **Ontology**: JOLux (`http://data.legilux.public.lu/resource/ontology/jolux#`)
  - the same ontology namespace used by Luxembourg's Legilux, confirmed by
  cross-referencing `lu-eli-mcp`'s discovery notes. Models Work
  (`ConsolidationAbstract`) / Expression (`isRealizedBy`, per-language
  title) / Manifestation (`isEmbodiedBy`, file format + download link).
- **Identifier**: the resource URI itself, e.g.
  `https://fedlex.data.admin.ch/eli/cc/1999/404` for the Federal
  Constitution - genuinely ELI, not an adapted local scheme (unlike most
  non-EU connectors in this fleet).
- **Citation convention**: SR number (Systematische Sammlung des
  Bundesrechts / Classified Compilation), e.g. "SR 101" - queried via
  `jolux:classifiedByTaxonomyEntry` -> `skos:notation`.
- **Full-text search caveat**: Virtuoso's `bif:contains` extension returns
  `"Illegal requests in query"` on this public endpoint (unlike Chile's BCN
  endpoint, where it works) - this connector uses a standard SPARQL
  `FILTER(CONTAINS(...))` instead, which is portable but slower on large
  result sets.

## Not covered (out of scope for this connector)

- **Full operative text** - the SPARQL endpoint exposes metadata and
  manifestation links (e.g. PDF download URLs via `jolux:isExemplifiedBy`),
  not inline article text. A future version could resolve those links.
- **Cantonal legislation** - each canton publishes separately; not
  surveyed in this pass.
- **Case law** (Federal Supreme Court decisions) - not surveyed in this
  pass; a natural v0.2 feature if Fedlex or a sibling platform exposes it
  via the same SPARQL endpoint.
