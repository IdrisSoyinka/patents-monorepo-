#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, html, json, os, pathlib, re, textwrap, time
import hashlib
from dataclasses import dataclass
from typing import List, Optional, Iterable

import requests
import arxiv
from rich.console import Console

try:  # pragma: no cover - GUI is optional in tests
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    from tkinter import scrolledtext as tk_scrolledtext
    _TK_AVAILABLE = True
except Exception:  # pragma: no cover - tkinter may not be installed
    tk = None  # type: ignore
    filedialog = None  # type: ignore
    messagebox = None  # type: ignore
    ttk = None  # type: ignore
    tk_scrolledtext = None  # type: ignore
    _TK_AVAILABLE = False

if _TK_AVAILABLE:  # pragma: no cover - optional drag and drop extension
    try:
        from tkinterdnd2 import DND_FILES, TkinterDnD  # type: ignore
    except Exception:  # pragma: no cover - dependency optional
        DND_FILES = None  # type: ignore
        TkinterDnD = None  # type: ignore
else:  # pragma: no cover - tkinter missing
    DND_FILES = None  # type: ignore
    TkinterDnD = None  # type: ignore

console = Console()

TEXT_FILE_TYPES = ["txt", "md", "rtf", "csv", "json"]


def _decode_bytes_to_text(data: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")
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
class PriorArtGUI:
    """Offline desktop window with drag-and-drop support for text files."""

    def __init__(self, default_limit: int = 10):
        if not _TK_AVAILABLE:
            raise RuntimeError("Tkinter is required for the GUI mode but is not available.")
        self.seen_fingerprints: set[str] = set()
        self.default_limit = default_limit
        self.root = (TkinterDnD.Tk() if TkinterDnD is not None else tk.Tk())  # type: ignore[call-arg]
        self.root.title("Prior Art Search")
        self.root.geometry("960x720")
        self._build_layout()

    # --- UI construction -------------------------------------------------
    def _build_layout(self) -> None:
        assert tk is not None and ttk is not None and tk_scrolledtext is not None
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(3, weight=1)

        header = ttk.Label(self.root, text="Prior Art Search", font=("TkDefaultFont", 16, "bold"))
        header.grid(row=0, column=0, pady=(10, 0))

        desc_frame = ttk.Frame(self.root, padding=10)
        desc_frame.grid(row=1, column=0, sticky="nsew")
        desc_frame.columnconfigure(0, weight=1)

        self.drop_label = ttk.Label(
            desc_frame,
            text=self._drop_label_text(),
            relief="ridge",
            padding=20,
            anchor="center",
            justify="center",
            wraplength=400,
        )
        self.drop_label.grid(row=0, column=0, sticky="ew")
        if TkinterDnD is not None and DND_FILES is not None:
            self.drop_label.drop_target_register(DND_FILES)  # type: ignore[attr-defined]
            self.drop_label.dnd_bind("<<Drop>>", self._handle_drop)  # type: ignore[attr-defined]

        button_row = ttk.Frame(desc_frame)
        button_row.grid(row=1, column=0, pady=10, sticky="ew")
        button_row.columnconfigure(1, weight=1)

        self.add_button = ttk.Button(button_row, text="Add files…", command=self._add_files_dialog)
        self.add_button.grid(row=0, column=0, padx=(0, 10))

        ttk.Label(button_row, text="Results per source:").grid(row=0, column=1, sticky="w")
        self.limit_var = tk.IntVar(value=self.default_limit)
        self.limit_spin = ttk.Spinbox(
            button_row,
            from_=5,
            to=25,
            textvariable=self.limit_var,
            width=5,
        )
        self.limit_spin.grid(row=0, column=2, padx=(5, 10))

        self.search_button = ttk.Button(button_row, text="Search", command=self._run_search)
        self.search_button.grid(row=0, column=3)

        self.reset_button = ttk.Button(button_row, text="Clear", command=self._clear_description)
        self.reset_button.grid(row=0, column=4, padx=(10, 0))

        self.description = tk_scrolledtext.ScrolledText(desc_frame, height=10, wrap="word")
        self.description.grid(row=2, column=0, sticky="nsew")

        desc_frame.rowconfigure(2, weight=1)

        query_frame = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        query_frame.grid(row=2, column=0, sticky="ew")
        query_frame.columnconfigure(0, weight=1)
        ttk.Label(query_frame, text="Expanded boolean query:").grid(row=0, column=0, sticky="w")
        self.query_preview = tk_scrolledtext.ScrolledText(query_frame, height=4, wrap="word", state="disabled")
        self.query_preview.grid(row=1, column=0, sticky="ew")

        results_frame = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        results_frame.grid(row=3, column=0, sticky="nsew")
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(1, weight=1)

        self.status_var = tk.StringVar(value="Drop files or paste text to begin.")
        ttk.Label(results_frame, textvariable=self.status_var).grid(row=0, column=0, sticky="w")
        self.results_view = tk_scrolledtext.ScrolledText(results_frame, wrap="word", state="disabled")
        self.results_view.grid(row=1, column=0, sticky="nsew")

    def _drop_label_text(self) -> str:
        if TkinterDnD is not None and DND_FILES is not None:
            return (
                "Drag and drop text files here (" + ", ".join(TEXT_FILE_TYPES) + ")\n"
                "or use the Add files button."
            )
        return "Drag-and-drop support unavailable. Use the Add files button to import text."  # pragma: no cover

    # --- File ingestion --------------------------------------------------
    def _add_files_dialog(self) -> None:
        if filedialog is None:
            return
        paths = filedialog.askopenfilenames(
            title="Select text files",
            filetypes=[("Text", [f"*.{ext}" for ext in TEXT_FILE_TYPES]), ("All files", "*.*")],
        )
        if paths:
            self._ingest_paths(list(paths))

    def _handle_drop(self, event: "tk.Event") -> str:
        data = event.data
        if not data:
            return "break"
        paths = self.root.tk.splitlist(data)
        self._ingest_paths([path.strip("{}") for path in paths])
        return "break"

    def _ingest_paths(self, paths: list[str]) -> None:
        added = 0
        for raw_path in paths:
            if not raw_path:
                continue
            path = pathlib.Path(raw_path)
            if not path.exists() or path.is_dir():
                continue
            if path.suffix.lower().lstrip(".") not in TEXT_FILE_TYPES:
                continue
            try:
                data = path.read_bytes()
            except Exception:
                continue
            fingerprint = hashlib.sha1(data).hexdigest()
            if fingerprint in self.seen_fingerprints:
                continue
            text = _decode_bytes_to_text(data).strip()
            if not text:
                continue
            if self.description.get("1.0", "end-1c"):
                self.description.insert("end", "\n\n")
            self.description.insert("end", text)
            self.seen_fingerprints.add(fingerprint)
            added += 1
        if added:
            self.status_var.set(f"Added content from {added} file{'s' if added != 1 else ''}.")
        else:
            self.status_var.set("No new readable content detected.")

    # --- Actions ---------------------------------------------------------
    def _clear_description(self) -> None:
        self.description.delete("1.0", "end")
        self.query_preview.configure(state="normal")
        self.query_preview.delete("1.0", "end")
        self.query_preview.configure(state="disabled")
        self.results_view.configure(state="normal")
        self.results_view.delete("1.0", "end")
        self.results_view.configure(state="disabled")
        self.status_var.set("Cleared description.")
        self.seen_fingerprints.clear()

    def _run_search(self) -> None:
        description = self.description.get("1.0", "end").strip()
        if not description:
            if messagebox is not None:
                messagebox.showwarning("Prior Art Search", "Please enter a description or import a text file first.")
            else:  # pragma: no cover - messagebox unavailable
                self.status_var.set("Description is empty.")
            return
        limit = max(1, int(self.limit_var.get()))
        expanded_terms = expand_query_terms(description)
        boolean_query = build_boolean_query(description, expanded_terms)

        self.query_preview.configure(state="normal")
        self.query_preview.delete("1.0", "end")
        self.query_preview.insert("end", boolean_query)
        self.query_preview.configure(state="disabled")

        self.status_var.set("Searching across sources…")
        self.root.update_idletasks()

        try:
            hits = run_pipeline(description, limit)
        except Exception as exc:  # pragma: no cover - network failure not deterministic
            self.status_var.set(f"Search failed: {exc}")
            return

        self.results_view.configure(state="normal")
        self.results_view.delete("1.0", "end")
        if not hits:
            self.results_view.insert("end", "No results found. Try refining the description.")
            self.status_var.set("Search complete – no results.")
        else:
            for idx, hit in enumerate(hits, 1):
                snippet = hit.snippet.strip() if hit.snippet else ""
                meta = [f"Source: {hit.source}"]
                if hit.year:
                    meta.append(f"Year: {hit.year}")
                if hit.location:
                    meta.append(f"Location: {hit.location}")
                if hit.id:
                    meta.append(f"ID: {hit.id}")
                block = (
                    f"{idx}. {hit.title}\n"
                    f"    URL: {hit.url}\n"
                    f"    {'; '.join(meta)}\n"
                    f"    Exact point: {snippet}\n\n"
                )
                self.results_view.insert("end", block)
            self.status_var.set(f"Search complete – {len(hits)} result(s).")
        self.results_view.configure(state="disabled")

    def run(self) -> None:
        self.root.mainloop()

def main(argv: Optional[Iterable[str]] = None) -> None:
    ap = argparse.ArgumentParser(
        description="Unified prior-art search (arXiv + PubMed + USPTO) with query expansion",
    )
    ap.add_argument("query", nargs="?", help="Keyword abstract or invention summary (quote it)")
    ap.add_argument("--limit", type=int, default=10, help="hits per source")
    ap.add_argument(
        "--gui",
        action="store_true",
        help="Launch the drag-and-drop desktop window (default when no query provided).",
    )
    args = ap.parse_args(list(argv) if argv is not None else None)

    use_gui = args.gui or (args.query is None)
    if use_gui:
        if not _TK_AVAILABLE:
            ap.error("GUI mode requires tkinter. Install tkinter or provide a query for CLI mode.")
        app = PriorArtGUI(default_limit=args.limit)
        app.run()
        return

    query = args.query or ""
    console.rule("[bold]Running prior art pipeline")
    expanded = expand_query_terms(query)
    boolean_q = build_boolean_query(query, expanded)
    console.print("[cyan]Expanded boolean query:[/cyan] " + boolean_q)

    hits = run_pipeline(query, args.limit)
    out = save_report(query, expanded, hits)
    console.print(f"[green]Report saved to:[/green] {out}")


if __name__ == "__main__":
    main()
