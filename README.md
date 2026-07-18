# ch-eli-mcp

<!-- mcp-name: io.github.matematicsolutions/ch-eli-mcp -->

MCP server for Swiss federal legislation via Fedlex, the Federal
Chancellery's official publication platform. Fedlex is genuinely
ELI-native (European Legislation Identifier) even though Switzerland is
not an EU member. Multilingual: German, French, Italian, English.

## What this is not

This connector returns metadata (title, SR number) via SPARQL - not the
operative text of the law. `source_url` points to the public Fedlex page
where the full text lives.

## Tools

| Tool | Purpose |
|---|---|
| `ch_search_acts` | Full-text search over act titles, in one of four languages |
| `ch_get_act` | Full detail for one act by its Fedlex ELI URI |

Every response carries `lex_uri` (the native ELI URI - not invented, taken
directly from Fedlex), `source_url` (the public HTML page), and
`human_readable_citation` (e.g. `"Bundesverfassung der Schweizerischen
Eidgenossenschaft (SR 101)"` - the SR number is Switzerland's own
Systematische Sammlung / Classified Compilation citation convention).

## Install

```bash
pip install ch-eli-mcp
```


### Windows 11 ze Smart App Control

Smart App Control blokuje niepodpisane pliki wykonywalne, a `uvx.exe`, `pip.exe`
i generowany przy instalacji `ch-eli-mcp.exe` podpisane nie sa. `python.exe`
z python.org jest podpisany przez Python Software Foundation, wiec uruchomienie
przez modul omija blokade:

```bash
python -m pip install ch-eli-mcp
python -m ch_eli_mcp
```

```json
{ "mcpServers": { "ch-eli-mcp": { "command": "python", "args": ["-m", "ch_eli_mcp"] } } }
```

Nie wylaczaj Smart App Control, zeby to obejsc - wylaczenia nie da sie cofnac
bez ponownej instalacji systemu.

## Configuration

| Env var | Default |
|---|---|
| `CH_ELI_CACHE_DIR` | `~/.matematic/cache/ch-eli` |
| `CH_ELI_AUDIT_DIR` | `~/.matematic/audit` |
| `CH_ELI_BASE_URL` | `https://fedlex.data.admin.ch/sparqlendpoint` |

## License

Apache-2.0 (code). Fedlex content is official Swiss federal publication
material (see [SOURCES.md](SOURCES.md)).
