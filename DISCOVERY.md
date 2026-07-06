# Discovery notes - Switzerland

Date: 2026-07-06.

## Why Switzerland, and why it stands out in this fleet

The user asked to also check Switzerland and Monaco after the Americas ROI
sweep. Live probing found Fedlex is the strongest non-EU legal API found so
far in this whole project: genuinely ELI-native (the resource URI itself is
the ELI, no adaptation needed, unlike NL/SE/FR/BR/US/CO/CA in this fleet,
which all had to explain why they do NOT have native ELI). Confirmed via
the JOLux ontology, the same one Luxembourg's Legilux uses - meaning
Switzerland and Luxembourg share a data model family despite Switzerland
being outside the EU.

## What was tried and what worked

- `https://fedlex.data.admin.ch/sparqlendpoint` - keyless SPARQL, confirmed
  live 2026-07-06.
- An existing third-party connector, `loicvuilliomenet-boop/fedlex-mcp`
  (found via web search, listed on mcpservers.org), confirmed Fedlex is a
  known target - but its GitHub license field reports `NOASSERTION`
  (all-rights-reserved by default), it has 1 star, and its last push was
  2026-03-30 (over 3 months stale at time of writing). Not forked or
  depended on; used only as a signal that the target is viable. This
  connector's code is written from scratch against the official endpoint.
- Virtuoso's `bif:contains` full-text extension is disabled on this public
  endpoint (`"Illegal requests in query"` error) - switched to a standard
  `FILTER(CONTAINS(LCASE(?title), "..."))`, confirmed working (e.g.
  searching "Datenschutz" correctly returns the Federal Data Protection Act
  and related instruments).
- The official tutorial repo `swiss/fedlex-sparql` (a JupyterLite notebook)
  provided the working query patterns for JOLux navigation (Work ->
  Expression -> title/titleShort, `classifiedByTaxonomyEntry` -> SR
  number).

## Monaco and Cyprus - checked and skipped in the same pass

- **Monaco** (`legimonaco.mc`) - plain HTML government site, no API surface
  found. Population ~39,000; even a clean API would carry limited ROI at
  this market size. SKIP.
- **Cyprus** (`cylaw.org`) - a bare Apache directory index of HTML files
  under `/nomoi/indexes/`, no JSON/XML API. This is the same
  "legal-information-institute" pattern (like SAFLII/KenyaLaw, already
  SKIP'd elsewhere in this fleet's discovery notes) - scraping-only, off
  the zero-cloud principle this fleet follows. SKIP.

## Not resolved / revisit later

- No confirmed bulk/offline mode - would need to resolve
  `jolux:isExemplifiedBy` manifestation links for full text, not attempted
  in this pass.
- Cantonal legislation and Federal Supreme Court case law not surveyed.
