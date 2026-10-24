---
name: crossref-doi-verification
description: "Verify that reference DOIs really resolve, and fetch abstracts, using the Crossref + OpenAlex REST APIs. Use when the user asks to verify/check a DOI, asks to find related papers with 通过验证的DOI, builds or audits a reference list (bibliography, .bib, GB/T 7714 or IEEE entries, 附录 DOI 记录), needs an abstract for a paper, or must decide the correct citation year for a journal article. Not for web search ranking, full-text reading of local PDFs, or citation-style formatting itself."
---

# Crossref + OpenAlex DOI Verification

## Overview

Turn a paper title (or a claimed DOI) into a citable record whose DOI has actually
resolved against the registering agency, plus an abstract when one exists. Crossref
gives authoritative bibliography metadata but **no abstracts**; OpenAlex supplies the
abstract as an inverted index that must be rebuilt.

## Hard rules

1. **Never write a DOI from memory.** In the run that produced this skill, 4 of 5
   recalled IEEE DOIs returned HTTP 404 (`10.1109/TITS.2016.2524868`,
   `10.1109/TCST.2016.2617239`, `10.1109/TCYB.2015.2416828` ...). A DOI is only ever
   typed into a document after `resolve` printed `OK` for it.
2. **Search results are candidates, not facts.** Re-resolve the chosen DOI one-by-one;
   Crossref search can return a stale or lowercase variant.
3. **No abstract on record → say so.** Write `NO_ABSTRACT`, never a plausible paraphrase.
4. **DOIs printed in a PDF footer can be wrong.** One local extract had
   `10.1109/ITSC48978.2021.9564659`; Crossref's authoritative record is `...9564416`.
   Trust the API over the document.
5. **An arXiv preprint DOI is not the citation.** Resolve the journal version
   (e.g. `1603.03225` → `10.1109/TCST.2016.2594588`, IEEE TCST 2017, 25(3):899-910).

## Workflow

Run the bundled script (Python 3 stdlib only, no install):

```bash
cd "<this-skill-dir>/scripts"
```

### 1. Find candidate DOIs

```bash
python verify_doi.py search --title "Finite-time consensus for heterogeneous multi-agent systems with mixed-order agents" --author Sun --rows 4
```

Uses `query.title` + `query.author` (fielded queries; a whole-bibliography
`query.bibliographic` match is not reliable enough here). Each hit carries a
`title~0.xx` similarity and an `exact|similar|WEAK-check-manually` tag:

- Accept `exact` only if the surname in the returned author list matches the paper you read.
- A `similar` hit under a **wrong guessed author** is noise: querying `author=Swerdlow`
  for a platoon paper returned pain-clinic and rat-behaviour articles. Drop or fix
  `--author` before believing anything.
- `NO_HITS` → shorten to 5–8 salient title words (drop the subtitle), then retry.

### 2. Resolve each DOI one at a time (this is the verification)

```bash
python verify_doi.py resolve --doi 10.1080/00207721.2013.843732 --doi 10.1109/TAC.2010.2088710
python verify_doi.py resolve --file dois.txt --json     # batch; one DOI per line
```

Prints `OK`/`ERR` per line with container, volume, issue, pages, authors, and all
three date fields. Exit code 3 means some DOI failed — resolve those before writing.

### 3. Choose the citation year from `published-print`

Priority: `published-print` → `published-online` → `issued`. The volume/issue belongs
to the **print** year, and the year embedded in the DOI string is usually the
online-first year. Verified examples:

| DOI | print | online | issued | cite as |
|---|---|---|---|---|
| `10.1080/00207721.2013.843732` | 2015-08-18 | 2013-10-08 | 2013-10-08 | 2015, 46(11):1961-1970 |
| `10.1080/00207179.2014.950047` | 2015-02 | 2014-08-28 | 2014-08-28 | 2015, 88(2):285-294 |
| `10.1109/TAC.2010.2088710` | 2011 | — | 2011 | 2011, 56(1):200-206 |
| `10.1109/MITS.2018.2889654` | 2021 | — | 2021 | 2021, 13(2):127-141 |

OpenAlex's `publication_year` disagrees with Crossref on these (it reports 2013/2014/2019)
— prefer Crossref for the year, use OpenAlex only for the abstract.

### 4. Abstracts

```bash
python verify_doi.py abstract --doi 10.1080/00207721.2013.843732
```

Crossref `/works/{doi}` has no `abstract` field for T&F and most IEEE records.
OpenAlex stores `abstract_inverted_index` (`{word: [positions]}`); the script inverts
it back into sentence order. Expect real gaps — `10.1016/j.automatica.2011.01.081` and
`10.1016/j.neucom.2020.06.089` legitimately return none.

## Failure playbook

| Symptom | Cause | Do |
|---|---|---|
| `HTTP Error 404` | DOI not registered | Never cite. Re-run `search`; report the DOI as invalid |
| `HTTP Error 429 Too Many Requests` | Crossref rate limit | Script backs off 1→7 s; raise `--pause` (default 1.0 s) or lower `--attempts` |
| `UnicodeEncodeError: 'gbk' codec` | Windows GBK console meets `ö`/`−` in titles | `export PYTHONIOENCODING=utf-8`; script already sanitizes stdout so plain runs survive |
| `_ssl.c:1064 handshake timed out` / `read operation timed out` | Publisher-hosted API is dead | Do not keep retrying; switch to OpenAlex |
| WebFetch `403 Forbidden` on `tandfonline.com/doi/abs/...`, `ieeexplore.ieee.org` | Publishers block bots | Do not retry that URL; use the API routes above |
| Semantic Scholar API hangs / empty output | Confirmed unusable here | Skip it; OpenAlex is the working abstract source |
| Same paper, two DOIs (e.g. `...(20000430)10:5<...>3.0.co;2-x` vs `3.3.co;2-o`) | Taylor &amp; Francis DOI re-issue | Prefer the modern short DOI, or the one on the PDF |

Set `MAILTO=you@example.org` to enter Crossref's polite pool when batch-resolving
dozens of DOIs.

## Recording the result

Append a verification table to the deliverable so claims stay auditable, one line per
reference, and state the date and API:

```
[3] Sun F., Zhu W. Finite-time consensus for heterogeneous multi-agent systems with
    mixed-order agents. Int. J. Systems Science, 2015, 46(11): 1961-1970.
    DOI: 10.1080/00207721.2013.843732 (Crossref OK 2026-10-15)
```

If a DOI could not be verified, keep the entry but mark `DOI 未验证` rather than
silently dropping or guessing it.

## Resources

- `scripts/verify_doi.py` — the whole pipeline; `--help` for flags.
- `references/api-notes.md` — raw endpoint shapes, field names, date-field semantics,
  and full transcripts of the failed routes. Read it when a call behaves unexpectedly
  or you need to hand-roll a query.
