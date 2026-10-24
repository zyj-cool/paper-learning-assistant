# API Notes — Crossref + OpenAlex

Endpoints, field semantics, and dead-end routes observed during skill creation.
Read this when a call behaves unexpectedly or you need to hand-roll a query.

## Crossref REST API

Base: `https://api.crossref.org/works`

### Search (finding candidate DOIs)

```
GET /works?query.title=<title>&query.author=<surname>&rows=5&select=DOI,title,container-title,author,issued,published,volume,page,type
```

- Use fielded queries (`query.title` + `query.author`), NOT `query.bibliographic`.
  `query.bibliographic` has lower hit rate and can trigger GBK encoding errors on Windows.
- Response: `message.items[]`, each with `title~0.xx` similarity to be computed client-side.
- `select` trims the payload; omit it only if you need full metadata (e.g. funder, license).

### Resolve (authoritative metadata per DOI)

```
GET /works/{doi}
```

- Returns `message` object with all metadata fields.
- Key fields: `DOI`, `title[0]`, `container-title[0]`, `type`, `volume`, `issue`, `page`, `author[]`.
- Date fields (see "Date-field semantics" below): `published-print`, `published-online`, `issued`.
- HTTP 404 = DOI not registered. Never cite.
- HTTP 429 = rate limited. Back off 1-7 s; raise `--pause` or lower `--attempts`.
- **No `abstract` field** for T&F and most IEEE records. Use OpenAlex for abstracts.

### Polite pool

Set `MAILTO=you@example.org` environment variable. The script builds a `User-Agent`
header with the mailto; Crossref prioritizes polite requests.

## OpenAlex API

Base: `https://api.openalex.org/works`

### Abstract retrieval

```
GET /works/doi:{doi}
```

- Response: JSON with `abstract_inverted_index` field.
- `abstract_inverted_index` is `{word: [position, ...]}` — an inverted index.
- Rebuild by placing each word at its positions, then joining in position order.
- `publication_year` may disagree with Crossref's `published-print` year. Prefer Crossref
  for the citation year; use OpenAlex only for the abstract.
- Some records legitimately have no abstract (`abstract_inverted_index` is null or empty).
  Output `NO_ABSTRACT`, never paraphrase.

## Date-field semantics

Crossref returns up to three date fields. They mean different things:

| Field | Meaning | Example |
|---|---|---|
| `published-print` | Print/issue publication date | 2015-08-18 |
| `published-online` | Online-first publication date | 2013-10-08 |
| `issued` | Earliest publication date (usually = online) | 2013-10-08 |

**Citation year priority**: `published-print` > `published-online` > `issued`.

The volume/issue belongs to the **print** year. The year embedded in the DOI string
(e.g. `10.1080/00207721.2013.843732` has "2013") is usually the online-first year and
does NOT determine the citation year.

Verified examples:

| DOI | print | online | issued | cite as |
|---|---|---|---|---|
| `10.1080/00207721.2013.843732` | 2015-08-18 | 2013-10-08 | 2013-10-08 | 2015, 46(11):1961-1970 |
| `10.1080/00207179.2014.950047` | 2015-02 | 2014-08-28 | 2014-08-28 | 2015, 88(2):285-294 |
| `10.1109/TAC.2010.2088710` | 2011 | — | 2011 | 2011, 56(1):200-206 |
| `10.1109/MITS.2018.2889654` | 2021 | — | 2021 | 2021, 13(2):127-141 |

## Dead-end routes (confirmed unusable)

| Route | Symptom | Verdict |
|---|---|---|
| Semantic Scholar API | Hangs, empty output, background task exits 0 with nothing | Skip; OpenAlex is the working abstract source |
| WebFetch on `tandfonline.com/doi/abs/...` | HTTP 403 Forbidden | Publisher blocks bots; use Crossref API instead |
| WebFetch on `ieeexplore.ieee.org` | HTTP 403 Forbidden | Publisher blocks bots; use Crossref API instead |
| `query.bibliographic` in Crossref | Low hit rate, can trigger GBK `UnicodeEncodeError` | Use `query.title` + `query.author` |
| Guessing DOIs from memory | 4 of 5 recalled IEEE DOIs returned HTTP 404 | Always search first, then resolve |

## HTTP status codes

| Code | Meaning | Action |
|---|---|---|
| 200 | OK | Parse JSON |
| 404 | DOI not registered | Never cite; re-run search |
| 429 | Too Many Requests | Back off; raise `--pause` |
| 401/403 | Auth required or forbidden | Do not retry; switch API |
| 5xx | Server error | Retry with backoff |

## Windows-specific notes

- Default `sys.stdout.encoding` is `gbk` on Chinese Windows.
- Characters like `ö` (Allgöwer), `−` (U+2212 minus), `—` (U+2014 em-dash) cause
  `UnicodeEncodeError: 'gbk' codec can't encode character`.
- Fix: `export PYTHONIOENCODING=utf-8` before running the script.
- The script's `emit()` function also sanitizes output with `encode(replace)` fallback.
