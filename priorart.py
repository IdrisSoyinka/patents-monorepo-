#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, html, json, os, pathlib, re, textwrap, time
from dataclasses import dataclass
from typing import List, Optional, Iterable

import requests
import arxiv
from rich.console import Console

console = Console()

# ===================== Schema =====================
@dataclass
class PriorArtHit:
    source: str                 # "arxiv", "pubmed", "uspto", ...
    id: str
    title: str
    url: str
    snippet: str                # “exact point of issue” window
    location: Optional[str]     # "Abstract", "Claims", etc.
    year: Optional[int] = None
    score: float = 0.0

# ===================== Query Expansion =====================
BIOMED_SYNONYMS = {
    "sirna": ["short interfering rna", "rna interference", "rnai"],
    "nanoparticle": ["nanocarrier", "nanosphere", "nano-particle"],
    "glioblastoma": ["gbm", "glioblastoma multiforme"],
    "egfrviii": ["egfr variant iii", "egfrv3", "egfr viii"],
    "antibody": ["mab", "monoclonal antibody"],
    "crispr": ["cas9", "genome editing"],
}

def normalize_token(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", t.lower())

def pluralize_variants(term: str) -> List[str]:
    out = {term}
    if term.endswith("y"): out.add(term[:-1]+"ies")
    if not term.endswith("s"): out.add(term+"s")
    if term.endswith("s"): out.add(term.rstrip("s"))
    return list(out)

def expand_query_terms(query: str, max_terms: int = 20) -> List[str]:
    """
    1) extract content terms
    2) add bigrams/trigrams
    3) add plural/singular variants
    4) add small domain synonyms
    """
    base = re.findall(r"[A-Za-z0-9\-]+", query)
    base = [t.lower() for t in base if len(t) > 2]
    grams = set(base)
    for i in range(len(base)-1):
        grams.add(base[i] + " " + base[i+1])
    for i in range(len(base)-2):
        grams.add(base[i] + " " + base[i+1] + " " + base[i+2])

    out = set()
    for g in grams:
        out.update(pluralize_variants(g))
        norm = normalize_token(g)
        if norm in BIOMED_SYNONYMS:
            for s in BIOMED_SYNONYMS[norm]:
                out.add(s)
                out.update(pluralize_variants(s))

    uniq = list(sorted(out, key=lambda x: (-len(x), x)))
    for t in base:
        if t not in uniq:
            uniq.insert(0, t)
    return uniq[:max_terms]

def build_boolean_query(core: str, expanded_terms: List[str]) -> str:
    expanded_terms = [t for t in expanded_terms if t.lower() not in core.lower()]
    if not expanded_terms:
        return core
    ors = " OR ".join(f"\"{t}\"" if " " in t else t for t in expanded_terms[:8])
    return f"({core}) AND ({ors})"

# ===================== Helpers =====================
def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()

def dedupe_hits(hits: Iterable[PriorArtHit]) -> List[PriorArtHit]:
    seen, out = set(), []
    for h in hits:
        key = (h.source, _norm(h.id) or _norm(h.title), h.url)
        if key not in seen:
            seen.add(key)
            out.append(h)
    return out

def rank_hits(hits: List[PriorArtHit]) -> List[PriorArtHit]:
    def weight(h: PriorArtHit) -> float:
        base = 1.0
        if h.source in {"uspto", "epo", "patentscope"}: base += 1.0
        if h.year:
            base += min(0.5, (2025 - h.year) * 0.01)  # mild recency bias
        base += min(0.5, len(h.snippet)/500.0)       # richer snippet
        return base + h.score
    return sorted(hits, key=weight, reverse=True)

def _best_window(text: str, query: str, window_chars: int = 420) -> str:
    text = text or ""
    if not text.strip():
        return ""
    terms = [t for t in re.split(r"[,\s;/]+", query) if len(t) > 3]
    idx = -1
    for t in terms:
        m = re.search(re.escape(t), text, flags=re.I)
        if m:
            idx = m.start()
            break
    if idx == -1:
        return text[:window_chars].strip()
    start = max(0, idx - window_chars // 2)
    end = min(len(text), idx + window_chars // 2)
    return text[start:end].strip()

# ===================== Adapters =====================
def search_arxiv(query: str, limit: int = 10) -> List[PriorArtHit]:
    hits: List[PriorArtHit] = []
    client = arxiv.Client()
    search = arxiv.Search(query=query, max_results=limit)
    for r in client.results(search):
        url = r.entry_id
        year = r.published.year if r.published else None
        snippet = _best_window(r.summary or "", query)
        hits.append(PriorArtHit(
            source="arxiv",
            id=r.get_short_id(),
            title=r.title,
            url=url,
            snippet=snippet,
            location="Abstract",
            year=year,
            score=0.2
        ))
    return hits

def search_pubmed(query: str, limit: int = 12) -> List[PriorArtHit]:
    """ESearch → IDs, then EFetch → abstracts for ‘exact point’ windows."""
    hits: List[PriorArtHit] = []
    try:
        es = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={"db":"pubmed","term":query,"retmax":limit,"retmode":"json"},
            timeout=30
        ).json()
        ids = es.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return hits

        ef = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            params={"db":"pubmed","id":",".join(ids),"rettype":"abstract","retmode":"xml"},
            timeout=30
        ).text

        articles = re.findall(r"<PubmedArticle>(.*?)</PubmedArticle>", ef, re.S|re.I)
        for block in articles:
            pmid_m = re.search(r"<PMID[^>]*>(\d+)</PMID>", block)
            pmid = pmid_m.group(1) if pmid_m else ""
            title_m = re.search(r"<ArticleTitle>(.*?)</ArticleTitle>", block, re.S|re.I)
            title = html.unescape(re.sub(r"<[^>]+>", "", (title_m.group(1) if title_m else "")).strip()) or f"PMID {pmid}"
            abs_parts = re.findall(r"<AbstractText[^>]*>(.*?)</AbstractText>", block, re.S|re.I)
            abstract = html.unescape(re.sub(r"<[^>]+>", "", " ".join(abs_parts))).strip()
            year_m = re.search(r"<PubDate>.*?<Year>(\d{4})</Year>", block, re.S|re.I)
            year = int(year_m.group(1)) if year_m else None
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            snippet = _best_window((abstract or title), query)
            hits.append(PriorArtHit(
                source="pubmed",
                id=pmid or title,
                title=title,
                url=url,
                snippet=snippet,
                location="Abstract" if abstract else "Title",
                year=year,
                score=0.15
            ))
    except Exception as e:
        console.print(f"[yellow]PubMed error:[/yellow] {e}")
    return hits

def search_uspto_patentsview(query: str, limit: int = 10) -> List[PriorArtHit]:
    """
    Uses the NEW PatentsView PatentSearch API (requires API key).
    We fetch grant metadata (title, abstract, year) and build an exact-point snippet from abstracts.
    """
    # Load API key from environment or .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass
    api_key = os.environ.get("PATENTSVIEW_API_KEY")
    if not api_key:
        console.print("[yellow]Missing PATENTSVIEW_API_KEY in environment/.env[/yellow]")
        return []

    url = "https://search.patentsview.org/api/v1/patent/"
    payload = {
        "q": {"_text_any": {"patent_title": query, "patent_abstract": query}},
        "f": ["patent_id", "patent_title", "patent_abstract", "patent_year"],
        "o": {"per_page": limit}
    }

    try:
        r = requests.post(
            url,
            headers={"X-Api-Key": api_key, "Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        r.raise_for_status()
        data = r.json().get("patents", [])
    except Exception as e:
        console.print(f"[yellow]USPTO PatentSearch error:[/yellow] {e}")
        return []

    hits: List[PriorArtHit] = []
    for p in data:
        num = (p.get("patent_id") or "").strip()
        title = (p.get("patent_title") or "").strip() or (f"US {num}" if num else "US patent")
        abstract = (p.get("patent_abstract") or "").strip()
        year = p.get("patent_year", None)
        url_view = f"https://patents.google.com/patent/US{num}" if num else "https://patents.google.com/"
        snippet = _best_window(abstract or title, query)
        hits.append(PriorArtHit(
            source="uspto",
            id=num or title,
            title=title,
            url=url_view,
            snippet=snippet,
            location="Abstract",
            year=year,
            score=0.3
        ))
    return hits

# ===================== Orchestrator =====================
def run_pipeline(user_query: str, limit_per_source: int = 10) -> List[PriorArtHit]:
    expanded = expand_query_terms(user_query)
    boolean_q = build_boolean_query(user_query, expanded)

    hits: List[PriorArtHit] = []
    hits += search_arxiv(boolean_q, limit_per_source)
    hits += search_pubmed(boolean_q, limit_per_source)
    hits += search_uspto_patentsview(boolean_q, limit_per_source)

    hits = dedupe_hits(hits)
    hits = rank_hits(hits)
    return hits

def save_report(query: str, expanded: List[str], hits: List[PriorArtHit]) -> str:
    ts = time.strftime("%Y%m%d-%H%M%S")
    pathlib.Path("reports").mkdir(exist_ok=True)
    md_path = f"reports/prior_art_{ts}.md"
    csv_path = f"reports/prior_art_{ts}.csv"

    # Markdown
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Prior Art Report\n\n")
        f.write(f"**Query:** {query}\n\n")
        if expanded:
            f.write("**Expanded key terms:** " + ", ".join(expanded) + "\n\n")
        f.write(f"**Total Results:** {len(hits)}\n\n")
        for i, h in enumerate(hits, 1):
            f.write(textwrap.dedent(f"""
            ## {i}. {h.title}
            - **Source:** {h.source}
            - **ID:** {h.id}
            - **URL:** {h.url}
            - **Year:** {h.year or '—'}
            - **Location:** {h.location or '—'}
            - **Relevance note (exact point):** {h.snippet.strip()}
            ---
            """))

    # CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["source","id","title","url","year","location","snippet"])
        for h in hits:
            w.writerow([h.source, h.id, h.title, h.url, h.year or "", h.location or "", h.snippet])

    return md_path

def main():
    ap = argparse.ArgumentParser(description="Unified prior-art search (arXiv + PubMed + USPTO) with query expansion")
    ap.add_argument("query", help="Keyword abstract or invention summary (quote it)")
    ap.add_argument("--limit", type=int, default=10, help="hits per source")
    args = ap.parse_args()

    console.rule("[bold]Running prior art pipeline")
    expanded = expand_query_terms(args.query)
    boolean_q = build_boolean_query(args.query, expanded)
    console.print("[cyan]Expanded boolean query:[/cyan] " + boolean_q)

    hits = run_pipeline(args.query, args.limit)
    out = save_report(args.query, expanded, hits)
    console.print(f"[green]Report saved to:[/green] {out}")

if __name__ == "__main__":
    main()