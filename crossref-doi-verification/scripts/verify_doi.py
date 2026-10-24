#!/usr/bin/env python3
"""Verify reference DOIs against Crossref, and fetch abstracts from OpenAlex.

Stdlib only. Subcommands: search | resolve | abstract.
"""

import argparse
import difflib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

CROSSREF = "https://api.crossref.org/works"
OPENALEX = "https://api.openalex.org/works"

UA = "crossref-doi-verification/1.0 (https://github.com/local/skill; mailto:%s)" % os.environ.get("MAILTO", "none@example.org")


def emit(line=""):
    """Print without ever raising UnicodeEncodeError on a GBK Windows console."""
    enc = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        data = line.encode(enc, "replace").decode(enc, "replace")
    except (LookupError, UnicodeError):
        data = line.encode("ascii", "replace").decode("ascii", "replace")
    sys.stdout.write(data + "\n")
    sys.stdout.flush()


def get_json(url, attempts=4, timeout=25):
    """GET with backoff for 429 / 5xx / network stalls. Returns (obj, error_str)."""
    delay = 1.0
    last = "no attempt"
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8", "replace")), None
        except urllib.error.HTTPError as e:
            last = "HTTP %d %s" % (e.code, e.reason)
            if e.code in (404, 401, 403):
                return None, last
            if e.code == 429 and i == attempts - 1:
                return None, last + " (rate limited; raise --pause or retry later)"
        except Exception as e:  # timeouts, TLS handshake stalls, DNS
            last = type(e).__name__ + ": " + str(e)[:120]
        if i < attempts - 1:
            time.sleep(min(delay, 7.0))
            delay *= 2
    return None, last


def date_parts(item, key):
    v = item.get(key) or {}
    dp = (v.get("date-parts") or [None])[0]
    if not dp:
        return None
    return "-".join("%04d" % p if i == 0 else "%02d" % p for i, p in enumerate(dp))


def authors(item, n=4):
    out = []
    for a in (item.get("author") or [])[:n]:
        fam = (a.get("family") or "").strip()
        giv = (a.get("given") or "").strip()
        if fam:
            out.append("%s %s" % (fam, " ".join(w[0] + "." for w in giv.split() if w)))
    rest = len(item.get("author") or []) - n
    if rest > 0:
        out.append("et al.")
    return ", ".join(out)


def norm(s):
    return " ".join((s or "").lower().replace("-", " ").replace(",", " ").split())


def title_sim(query, candidate):
    return difflib.SequenceMatcher(None, norm(query), norm(candidate)).ratio()


def cmd_search(args):
    q = {
        "query.title": args.title,
        "rows": str(args.rows),
        "select": "DOI,title,container-title,author,issued,published,volume,page,type",
    }
    if args.author:
        q["query.author"] = args.author
    if args.year:
        q["filter"] = "from-pub-date:%s-01-01,until-pub-date:%s-12-31" % (args.year, args.year)
    url = CROSSREF + "?" + urllib.parse.urlencode(q)
    data, err = get_json(url, attempts=args.attempts)
    if err:
        emit("QUERY ERROR %s" % err)
        return 1
    items = (data.get("message") or {}).get("items") or []
    emit('QUERY "%s"%s -> %d candidates (Crossref relevance order)' % (args.title, " author=" + args.author if args.author else "", len(items)))
    if not items:
        emit("  NO_HITS -- loosen the title (drop subtitle, use 5-8 salient words) or drop --author")
        return 1
    for it in items:
        cand = (it.get("title") or [""])[0]
        score = title_sim(args.title, cand)
        tag = "exact" if score >= 0.85 else ("similar" if score >= 0.5 else "WEAK-check-manually")
        ct = (it.get("container-title") or [""])
        ct = ct[0] if ct else ""
        emit("  %s | %s | %s | issued=%s | v%s p%s | %s | title~%.2f %s" % (
            it.get("DOI"), cand[:78], ct[:45], date_parts(it, "issued") or "-",
            it.get("volume") or "-", it.get("page") or "-", authors(it, 3), score, tag))
    emit("NOTE: candidates are unverified. Re-resolve the chosen DOI with `resolve` before citing.")
    return 0


def cmd_resolve(args):
    dois = list(args.doi)
    if args.file:
        with open(args.file, encoding="utf-8-sig") as fh:
            dois += [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]
    if not dois:
        emit("NO_DOIS")
        return 2
    rows = []
    for i, doi in enumerate(dois):
        if i:
            time.sleep(args.pause)
        url = CROSSREF + "/" + urllib.parse.quote(doi.strip(), safe="/:_-()")
        data, err = get_json(url, attempts=args.attempts)
        if err or not data:
            hint = " -- DOI NOT registered, never cite as-is; re-search it" if "404" in err else ""
            emit("ERR %s | %s%s" % (doi, err, hint))
            rows.append({"doi": doi, "error": err})
            continue
        it = data.get("message") or {}
        ct = it.get("container-title") or [""]
        rec = {
            "doi": it.get("DOI", doi),
            "title": (it.get("title") or [""])[0],
            "container": ct[0] if ct else "",
            "type": it.get("type", ""),
            "volume": it.get("volume"),
            "issue": it.get("issue"),
            "page": it.get("page"),
            "year_print": date_parts(it, "published-print"),
            "year_online": date_parts(it, "published-online"),
            "year_issued": date_parts(it, "issued"),
            "authors": authors(it, 8),
        }
        rows.append(rec)
        cite = rec["year_print"] or rec["year_online"] or rec["year_issued"] or "?"
        emit("OK  %s | %s | %s | CITE=%s (print=%s online=%s issued=%s) | v%s n%s p%s | %s" % (
            rec["doi"], rec["title"][:70], rec["container"][:42], cite,
            rec["year_print"] or "-", rec["year_online"] or "-", rec["year_issued"] or "-",
            rec["volume"] or "-", rec["issue"] or "-", rec["page"] or "-", rec["authors"][:60]))
    if args.json:
        emit(json.dumps(rows, ensure_ascii=False))
    n_ok = sum(1 for r in rows if "error" not in r)
    emit("SUMMARY %d/%d resolved" % (n_ok, len(rows)))
    return 0 if n_ok == len(rows) else 3


def rebuild_abstract(inv):
    if not inv:
        return ""
    pos = {}
    for word, idxs in inv.items():
        for p in idxs:
            pos[p] = word
    return " ".join(pos[i] for i in sorted(pos))


def cmd_abstract(args):
    for i, doi in enumerate(args.doi):
        if i:
            time.sleep(args.pause)
        url = OPENALEX + "/doi:" + urllib.parse.quote(doi.strip(), safe="/:_-()")
        data, err = get_json(url, attempts=args.attempts)
        if err:
            if "404" in err:
                emit("%s | OPENALEX_NOT_INDEXED (Crossref DOI may still be valid)" % doi)
            else:
                emit("%s | ERROR %s" % (doi, err))
            continue
        w = data or {}
        emit("=== %s | %s | openalex_year=%s" % (doi, (w.get("title") or "")[:75], w.get("publication_year")))
        text = rebuild_abstract(w.get("abstract_inverted_index"))
        if text:
            emit("ABSTRACT: %s" % text[:1600])
        else:
            emit("NO_ABSTRACT: OpenAlex holds none. Do not invent or paraphrase one.")
    return 0


def main():
    p = argparse.ArgumentParser(description="Crossref + OpenAlex DOI verification")
    p.add_argument("--attempts", type=int, default=4, help="HTTP retries with backoff")
    p.add_argument("--pause", type=float, default=1.0, help="seconds between requests (anti-429)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="find candidate DOIs by title + author")
    s.add_argument("--title", required=True)
    s.add_argument("--author", help="one surname, e.g. Baldi")
    s.add_argument("--year", help="restrict publication year")
    s.add_argument("--rows", type=int, default=5)

    r = sub.add_parser("resolve", help="authoritative metadata per DOI (accepts many)")
    r.add_argument("--doi", action="append", default=[])
    r.add_argument("--file", help="text file with one DOI per line")
    r.add_argument("--json", action="store_true")

    a = sub.add_parser("abstract", help="reconstruct abstracts from OpenAlex")
    a.add_argument("--doi", action="append", default=[])

    args = p.parse_args()
    try:
        return {"search": cmd_search, "resolve": cmd_resolve, "abstract": cmd_abstract}[args.cmd](args)
    except KeyboardInterrupt:
        emit("INTERRUPTED")
        return 130
    except Exception as e:
        emit("FATAL %s: %s" % (type(e).__name__, str(e)[:200]))
        return 1


if __name__ == "__main__":
    sys.exit(main())
