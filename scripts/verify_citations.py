#!/usr/bin/env python3
"""Verify citations against arXiv, Crossref, and Semantic Scholar; write BibTeX.

Reads a candidates JSON list of {title, arxiv_id?, doi?, s2_paper_id?}
and keeps only records that a live API confirms, with a title-overlap check
so a wrong arXiv id cannot launder a different paper.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ARXIV = "http://export.arxiv.org/api/query"
S2 = "https://api.semanticscholar.org/graph/v1"
CROSSREF = "https://api.crossref.org/works"


def get(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "calibshift-verify/0.2 (mailto:bobshenruililin@gmail.com)"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def titles_match(a: str, b: str) -> bool:
    stop = {"the", "a", "an", "of", "and", "in", "on", "for", "to", "with", "from", "your"}

    def toks(s: str) -> set[str]:
        cleaned = "".join(ch.lower() if ch.isalnum() else " " for ch in s)
        return {t for t in cleaned.split() if t not in stop and len(t) > 2}

    A, B = toks(a), toks(b)
    if not A or not B:
        return False
    return (len(A & B) / len(A)) >= 0.5


def verify_arxiv(arxiv_id: str) -> dict | None:
    q = urllib.parse.urlencode({"id_list": arxiv_id})
    xml = get(f"{ARXIV}?{q}").decode("utf-8", errors="replace")
    if "<entry>" not in xml:
        return None
    title = ""
    if "<title>" in xml:
        start = xml.find("<title>", xml.find("<entry>")) + len("<title>")
        end = xml.find("</title>", start)
        title = " ".join(xml[start:end].split())
    return {"title": title, "arxiv_id": arxiv_id}


def verify_doi(doi: str) -> dict | None:
    raw = get(f"{CROSSREF}/{urllib.parse.quote(doi)}")
    data = json.loads(raw.decode())
    msg = data.get("message") or {}
    titles = msg.get("title") or []
    if not titles:
        return None
    year = None
    issued = (msg.get("issued") or {}).get("date-parts") or [[]]
    if issued and issued[0]:
        year = issued[0][0]
    authors = []
    for a in msg.get("author") or []:
        given = a.get("given") or ""
        family = a.get("family") or ""
        name = (given + " " + family).strip() or a.get("name")
        if name:
            authors.append(name)
    return {
        "title": titles[0],
        "year": year,
        "authors": authors,
        "doi": doi,
        "container": (msg.get("container-title") or [None])[0],
    }


def verify_s2(query: str) -> dict | None:
    q = urllib.parse.urlencode(
        {"query": query, "limit": 1, "fields": "title,year,externalIds,authors,venue"}
    )
    raw = get(f"{S2}/paper/search?{q}")
    data = json.loads(raw.decode())
    papers = data.get("data") or []
    if not papers:
        return None
    return papers[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", default="paper/candidates.json")
    parser.add_argument("--out-bib", default="paper/verified.bib")
    parser.add_argument("--out-json", default="paper/verified_papers.json")
    args = parser.parse_args()
    cands = json.loads(Path(args.candidates).read_text())
    verified = []
    rejected = []
    for i, c in enumerate(cands):
        rec = dict(c)
        ok = False
        evidence = []
        want = c.get("title") or ""
        if c.get("arxiv_id"):
            try:
                ar = verify_arxiv(c["arxiv_id"])
                time.sleep(0.2)
                if ar and ar["title"] and titles_match(want, ar["title"]):
                    rec["arxiv_verified_title"] = ar["title"]
                    evidence.append("arxiv_api")
                    ok = True
                elif ar and ar["title"]:
                    rec["arxiv_title_mismatch"] = ar["title"]
            except Exception as exc:  # noqa: BLE001
                rec["arxiv_error"] = str(exc)
        if not ok and c.get("doi"):
            try:
                cr = verify_doi(c["doi"])
                time.sleep(0.15)
                if cr and cr.get("title") and titles_match(want, cr["title"]):
                    rec["crossref_verified_title"] = cr["title"]
                    rec["crossref_year"] = cr.get("year")
                    evidence.append("crossref")
                    ok = True
            except Exception as exc:  # noqa: BLE001
                rec["crossref_error"] = str(exc)
        if not ok:
            try:
                s2 = verify_s2(want or c.get("arxiv_id") or "")
                time.sleep(0.6)
                if s2 and s2.get("title") and titles_match(want, s2["title"]):
                    rec["s2_verified_title"] = s2["title"]
                    rec["s2_year"] = s2.get("year")
                    evidence.append("semantic_scholar")
                    ok = True
            except Exception as exc:  # noqa: BLE001
                rec["s2_error"] = str(exc)
        rec["verified_via"] = evidence
        if ok:
            verified.append(rec)
        else:
            rejected.append(rec)
        print(f"[{i+1}/{len(cands)}] {'OK' if ok else 'REJECT'} {c.get('title', '')[:70]}")

    Path(args.out_json).write_text(
        json.dumps({"verified": verified, "rejected": rejected}, indent=2) + "\n"
    )
    lines = ["% Auto-generated by scripts/verify_citations.py. Do not add unverified entries.\n"]
    for rec in verified:
        key = rec.get("key") or rec.get("arxiv_id") or f"paper{len(lines)}"
        title = (
            rec.get("arxiv_verified_title")
            or rec.get("crossref_verified_title")
            or rec.get("s2_verified_title")
            or rec.get("title")
        )
        authors = rec.get("authors") or "Unknown"
        if isinstance(authors, list):
            authors = " and ".join(authors)
        year = rec.get("year") or rec.get("crossref_year") or rec.get("s2_year") or "n.d."
        lines.append(f"@misc{{{key},")
        lines.append(f"  title = {{{title}}},")
        lines.append(f"  author = {{{authors}}},")
        lines.append(f"  year = {{{year}}},")
        if rec.get("arxiv_id"):
            lines.append(f"  eprint = {{{rec['arxiv_id']}}},")
            lines.append("  archivePrefix = {arXiv},")
        if rec.get("doi"):
            lines.append(f"  doi = {{{rec['doi']}}},")
        lines.append("}\n")
    Path(args.out_bib).write_text("\n".join(lines))
    print(f"verified={len(verified)} rejected={len(rejected)} -> {args.out_bib}")


if __name__ == "__main__":
    main()
