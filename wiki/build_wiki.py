#!/usr/bin/env python3
"""Generate the aicoe-regulatory HTML wiki from the Markdown in ../docs.

The Markdown under docs/ is the source of truth. This script renders it into
AICOE-themed, cross-linked HTML pages plus a machine-readable manifest, so the
same content reads well for humans (sidebar nav, tables, icons) and for AI
agents (clean semantic HTML, stable anchor IDs, wiki-manifest.json).

Usage:
    python3 wiki/build_wiki.py          # regenerate wiki/ from docs/

Do not hand-edit wiki/*.html or wiki/styles.css — edits are overwritten on the
next build. Change the Markdown in docs/ (or this generator) and rebuild.
"""

from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
ASSETS = ROOT / "assets"
OUT = ROOT / "wiki"

SITE_NAME = "AI Centre of Excellence Regulatory List"
SITE_TAGLINE = "Curated regulatory guidances, standards & best practices"
CONTACT_EMAIL = "hi@aicoe.io"
DEFAULT_DOMAIN = "General"

# Display order for domains in the sidebar and on the home page. Domains not
# listed here appear after these, alphabetically.
DOMAIN_ORDER = [
    "Life Sciences",
    "Financial Services",
    "Manufacturing",
    "Aerospace & Defense",
    "Hi-Tech / Technology",
    "Logistics & Supply Chain",
    "Sustainability & ESG",
]

# --- Lucide icons (inline SVG, offline-safe; no CDN) ---------------------------
# Only the inner markup; wrapped by _icon() with the standard lucide attributes.
LUCIDE = {
    "book-open": '<path d="M12 7v14"/><path d="M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"/>',
    "scale": '<path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="M7 21h10"/><path d="M12 3v18"/><path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/>',
    "landmark": '<path d="M10 18v-7"/><path d="M11.12 2.198a2 2 0 0 1 1.76.006l7.866 3.847c.476.233.31.949-.22.949H3.474c-.53 0-.695-.716-.22-.949z"/><path d="M14 18v-7"/><path d="M18 18v-7"/><path d="M3 22h18"/><path d="M6 18v-7"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>',
    "activity": '<path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"/>',
    "database": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5V19A9 3 0 0 0 21 19V5"/><path d="M3 12A9 3 0 0 0 21 12"/>',
    "file-text": '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>',
    "briefcase": '<path d="M16 20V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/><rect width="20" height="14" x="2" y="6" rx="2"/>',
    "shield-check": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
    "library": '<path d="m16 6 4 14"/><path d="M12 6v14"/><path d="M8 8v12"/><path d="M4 4v16"/>',
    "external-link": '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
    "list": '<path d="M3 12h.01"/><path d="M3 18h.01"/><path d="M3 6h.01"/><path d="M8 12h13"/><path d="M8 18h13"/><path d="M8 6h13"/>',
    "home": '<path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M9 22V12h6v10"/>',
    "link": '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
    "check-circle": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
}

# Map a section-heading keyword to an icon, first match wins.
SECTION_ICONS = [
    ("ich", "book-open"),
    ("ethic", "scale"),
    ("fda", "landmark"),
    ("united states", "landmark"),
    ("ema", "globe"),
    ("european", "globe"),
    ("mhra", "shield-check"),
    ("united kingdom", "shield-check"),
    ("world health", "globe"),
    ("pharmacovigilance", "activity"),
    ("safety", "activity"),
    ("data standard", "database"),
    ("cdisc", "database"),
    ("reporting", "file-text"),
    ("industry", "briefcase"),
    ("scope", "list"),
    ("maintenance", "list"),
]


def _icon(name: str, cls: str = "icon") -> str:
    inner = LUCIDE.get(name, LUCIDE["file-text"])
    return (
        f'<svg class="{cls}" xmlns="http://www.w3.org/2000/svg" width="24" '
        f'height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
        f'aria-hidden="true">{inner}</svg>'
    )


def _section_icon(title: str) -> str:
    low = title.lower()
    for key, icon in SECTION_ICONS:
        if key in low:
            return icon
    return "file-text"


def slug(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


# --- Markdown parsing ----------------------------------------------------------

def parse_front_matter(raw: str) -> tuple[dict, str]:
    """Split optional `--- key: value ---` front matter from the body."""
    meta: dict[str, str] = {}
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", raw, re.DOTALL)
    if not m:
        return meta, raw
    for line in m.group(1).splitlines():
        if ":" in line and not line.strip().startswith("#"):
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, raw[m.end():]


def parse_doc(path: Path) -> dict:
    """Return {title, intro, html, sections:[{title,id}], link_count, ...}."""
    raw = path.read_text(encoding="utf-8")
    meta, raw = parse_front_matter(raw)

    title = "Untitled"
    intro = ""
    body_lines: list[str] = []
    seen_title = False
    for line in raw.splitlines():
        if not seen_title and line.startswith("# "):
            title = line[2:].strip()
            seen_title = True
            continue
        if seen_title:
            if not intro and line.strip() and not line.startswith(("#", ">", "|")):
                intro = line.strip()
                continue  # lede is rendered from the header; keep it out of the body
            body_lines.append(line)

    md = markdown.Markdown(
        extensions=["tables", "toc", "fenced_code", "attr_list", "sane_lists"],
        extension_configs={"toc": {"toc_depth": "2-3"}},
    )
    body_html = md.convert("\n".join(body_lines))

    # toc token names are already HTML-escaped; store the raw text so the
    # manifest is clean and the render layer escapes exactly once.
    sections = [
        {"title": html.unescape(t["name"]), "id": t["id"]}
        for t in getattr(md, "toc_tokens", [])
    ]

    body_html = _postprocess(body_html)
    link_count = len(re.findall(r'<a\s+[^>]*href="https?://', body_html))
    rows = _extract_rows(body_lines, sections)

    try:
        order = int(meta.get("order", "100"))
    except ValueError:
        order = 100

    return {
        "slug": path.stem,
        "title": title,
        "intro": intro,
        "html": body_html,
        "sections": sections,
        "rows": rows,
        "link_count": link_count,
        "source": f"docs/{path.name}",
        "domain": meta.get("domain", DEFAULT_DOMAIN),
        "order": order,
        "label": meta.get("label", ""),
    }


def _extract_rows(body_lines: list[str], sections: list[dict]) -> list[dict]:
    """Parse the pipe tables into per-row records for the search index.

    Assumes each table is Document | Issuer | Link | Notes under a `##` section.
    """
    id_by_title = {s["title"]: s["id"] for s in sections}
    rows: list[dict] = []
    current, current_id = None, None
    for line in body_lines:
        h = re.match(r"^##\s+(.*)$", line)
        if h:
            current = h.group(1).strip()
            current_id = id_by_title.get(current, slug(current))
            continue
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        if cells[0].lower() == "document":  # header row
            continue
        if set(cells[0]) <= {"-", ":", " "}:  # separator row
            continue
        doc, issuer, link, notes = cells[0], cells[1], cells[2], cells[3]
        m = re.search(r"https?://[^\s|]+", link)
        rows.append({
            "document": doc,
            "issuer": issuer,
            "notes": notes,
            "url": m.group(0) if m else "",
            "section": current or "",
            "anchor": current_id or "",
        })
    return rows


def _postprocess(body: str) -> str:
    # Auto-link bare URLs (the docs put raw URLs in table cells, not md links).
    # URLs may contain parentheses (e.g. ICH "(R3)"); they terminate at
    # whitespace, "<", "|", or the closing quote of an attribute.
    def _autolink(m: re.Match) -> str:
        url = m.group(1)
        trail = ""
        while url and url[-1] in ".,;:":  # keep trailing sentence punctuation out
            trail = url[-1] + trail
            url = url[:-1]
        return f'<a href="{url}">{url}</a>{trail}'

    body = re.sub(r'(?<!")(https?://[^\s<|"]+)', _autolink, body)
    # Wrap tables so wide content scrolls inside its own container.
    body = re.sub(
        r"(<table>)(.*?)(</table>)",
        lambda m: f'<div class="table-wrap">{m.group(0)}</div>',
        body,
        flags=re.DOTALL,
    )
    # External links: open in a new tab, add rel + a trailing icon.
    def _extlink(m: re.Match) -> str:
        attrs, text = m.group(1), m.group(2)
        if "http" not in attrs:
            return m.group(0)
        icon = _icon("external-link", cls="icon ext")
        return f'<a {attrs} target="_blank" rel="noopener noreferrer">{text}{icon}</a>'

    body = re.sub(r"<a ([^>]*?)>(.*?)</a>", _extlink, body, flags=re.DOTALL)
    # Add an icon to each h2 section heading.
    def _h2(m: re.Match) -> str:
        hid, text = m.group(1), m.group(2)
        icon = _icon(_section_icon(text), cls="icon section-icon")
        return f'<h2 id="{hid}"><span class="h2-inner">{icon}<span>{text}</span></span></h2>'

    body = re.sub(r'<h2 id="([^"]+)">(.*?)</h2>', _h2, body, flags=re.DOTALL)
    return body


# --- HTML shell ----------------------------------------------------------------

CHEVRON = (
    '<svg class="chev" width="16" height="16" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
    'stroke-linejoin="round" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg>'
)


def _short_title(page: dict) -> str:
    """The topic label for nav/cards: explicit label, else text before em-dash."""
    if page.get("label"):
        return page["label"]
    return page["title"].split("—")[0].strip()


def group_by_domain(pages: list[dict]) -> list[tuple[str, list[dict]]]:
    """Return [(domain, [pages…]), …] ordered by DOMAIN_ORDER then name."""
    groups: dict[str, list[dict]] = {}
    for p in pages:
        groups.setdefault(p["domain"], []).append(p)

    def domain_key(name: str) -> tuple[int, str]:
        return (DOMAIN_ORDER.index(name) if name in DOMAIN_ORDER else len(DOMAIN_ORDER), name)

    out = []
    for domain in sorted(groups, key=domain_key):
        topics = sorted(groups[domain], key=lambda p: (p["order"], p["title"]))
        out.append((domain, topics))
    return out


def _topic_node(p: dict, active_slug: str | None) -> str:
    is_active = p["slug"] == active_slug
    icon = _icon(_section_icon(p["title"]), "icon nav-icon")
    children = [f'<li><a class="tree-sub" href="{p["slug"]}.html">Overview</a></li>']
    for s in p["sections"]:
        if s["title"].lower() in ("scope & maintenance",):
            continue
        children.append(
            f'<li><a class="tree-sub" href="{p["slug"]}.html#{s["id"]}">'
            f'{html.escape(s["title"])}</a></li>'
        )
    summary = (
        f'<summary class="tree-top{" active" if is_active else ""}">'
        f'<span class="tree-top-label">{icon}'
        f'<span>{html.escape(_short_title(p))}</span></span>{CHEVRON}</summary>'
    )
    return (
        f'<details class="tree-node"{" open" if is_active else ""}>'
        f'{summary}<ul class="tree-children">{"".join(children)}</ul></details>'
    )


def nav_html(pages: list[dict], active_slug: str | None) -> str:
    """Home, then domain groups; each topic expands to its sections."""
    home_cls = "tree-link home" + (" active" if active_slug is None else "")
    items = [
        f'<a class="{home_cls}" href="index.html">'
        f'{_icon("home", "icon nav-icon")}<span>Home</span></a>'
    ]
    groups = group_by_domain(pages)
    single = len(groups) <= 1
    for domain, topics in groups:
        if not single:
            items.append(f'<div class="nav-domain">{html.escape(domain)}</div>')
        for p in topics:
            items.append(_topic_node(p, active_slug))
    return "\n".join(items)


def shell(*, title: str, body: str, pages: list[dict], active_slug: str | None,
          description: str) -> str:
    year = "2026"
    nav = nav_html(pages, active_slug)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)} · {SITE_NAME}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="icon" type="image/png" href="logo.png">
<link rel="apple-touch-icon" href="logo.png">
<link rel="stylesheet" href="styles.css">
</head>
<body>
<a class="skip-link" href="#content">Skip to content</a>
<div class="layout">
  <aside class="sidebar">
    <a class="brand" href="index.html">
      <img class="brand-logo" src="logo.png" alt="AICOE logo" width="34" height="34">
      <span class="brand-text">
        <span class="brand-mark">AI Centre of Excellence</span>
        <span class="brand-sub">Regulatory List</span>
      </span>
    </a>
    <div class="search">
      {_icon('search', 'icon search-icon')}
      <input id="wiki-search" type="search" placeholder="Search standards…"
             autocomplete="off" spellcheck="false" aria-label="Search the wiki">
      <kbd class="search-kbd">/</kbd>
    </div>
    <div id="search-results" class="search-results" hidden role="listbox"
         aria-label="Search results"></div>
    <nav class="nav" aria-label="Wiki sections">
      {nav}
    </nav>
    <div class="sidebar-foot">
      <span>MIT · Primary sources</span>
    </div>
  </aside>
  <div class="main-wrap">
    <header class="topbar">
      <button class="menu-toggle" aria-label="Toggle navigation" onclick="document.body.classList.toggle('nav-open')">{_icon('list','icon')}</button>
      <span class="topbar-title">{html.escape(title)}</span>
    </header>
    <main id="content" class="content">
      {body}
      <footer class="page-foot">
        <p>Suggest a resource or correction: <a href="mailto:{CONTACT_EMAIL}?subject=Regulatory%20Wiki%20%E2%80%94%20new%20resource">{CONTACT_EMAIL}</a></p>
        <p class="foot-rights">This wiki is a curated index of third-party materials. All guidances and standards remain the property of their respective issuers; every link points to the issuing body's official source. The index and its descriptions are provided for reference only and are not legal advice.</p>
        <p>{SITE_NAME} · {SITE_TAGLINE}</p>
        <p>Generated from <code>docs/</code> by <code>wiki/build_wiki.py</code>. Do not hand-edit these HTML files.</p>
        <p>© {year} AI Centre of Excellence · Wiki text licensed MIT; linked standards are © their issuers</p>
      </footer>
    </main>
  </div>
</div>
<script src="wiki.js" defer></script>
</body>
</html>"""


def render_page(doc: dict, pages: list[dict]) -> str:
    # In-page contents (h2 sections) for quick jumping.
    toc_items = "".join(
        f'<li><a href="#{s["id"]}">{html.escape(s["title"])}</a></li>'
        for s in doc["sections"]
        if s["title"].lower() not in ("scope & maintenance",)
    )
    toc = (
        f'<nav class="page-toc" aria-label="On this page"><span class="toc-label">'
        f'{_icon("list","icon")}On this page</span><ul>{toc_items}</ul></nav>'
        if toc_items else ""
    )
    header = (
        f'<div class="doc-header">'
        f'<div class="eyebrow">{_icon("shield-check","icon")}Regulatory reference</div>'
        f'<h1>{html.escape(doc["title"])}</h1>'
        f'<p class="lede">{html.escape(doc["intro"])}</p>'
        f'<div class="doc-meta">'
        f'<span>{_icon("link","icon")}{doc["link_count"]} primary-source links</span>'
        f'<span>{_icon("list","icon")}{len(doc["sections"])} sections</span>'
        f'<span>{_icon("file-text","icon")}source: <code>{doc["source"]}</code></span>'
        f'</div></div>'
    )
    body = header + toc + f'<div class="doc-body">{doc["html"]}</div>'
    return shell(
        title=doc["title"], body=body, pages=pages,
        active_slug=doc["slug"], description=doc["intro"],
    )


def _topic_card(p: dict) -> str:
    icon = _icon(_section_icon(p["title"]), "icon card-icon")
    return (
        f'<a class="topic-card" href="{p["slug"]}.html">'
        f'<div class="card-top">{icon}</div>'
        f'<h3>{html.escape(_short_title(p))}</h3>'
        f'<p>{html.escape(p["intro"])}</p>'
        f'<div class="card-meta"><span>{p["link_count"]} links</span>'
        f'<span>{len(p["sections"])} sections</span></div>'
        f'</a>'
    )


def render_index(pages: list[dict]) -> str:
    groups = group_by_domain(pages)
    single = len(groups) <= 1
    blocks = []
    for domain, topics in groups:
        grid = "\n".join(_topic_card(p) for p in topics)
        heading = "" if single else f'<h2 class="section-title">{html.escape(domain)}</h2>'
        blocks.append(f'{heading}<div class="topic-grid">{grid}</div>')
    if single:  # keep a "Topics" heading when there's only one group
        blocks.insert(0, '<h2 class="section-title">Topics</h2>')
    cards_html = "\n".join(blocks)
    total_links = sum(p["link_count"] for p in pages)
    n_domains = len(groups)
    body = f"""
<div class="hero">
  <div class="eyebrow">{_icon('library','icon')}AI Centre of Excellence</div>
  <h1>Regulatory List</h1>
  <p class="lede">{SITE_TAGLINE}. A curated, primary-source index of the regulations, standards, ethics foundations, and industry best practices that govern regulated research and product development.</p>
  <div class="hero-stats">
    <div class="stat"><span class="stat-num">{n_domains}</span><span class="stat-label">Domain{'s' if n_domains!=1 else ''}</span></div>
    <div class="stat"><span class="stat-num">{len(pages)}</span><span class="stat-label">Topic{'s' if len(pages)!=1 else ''}</span></div>
    <div class="stat"><span class="stat-num">{total_links}</span><span class="stat-label">Verified links</span></div>
    <div class="stat"><span class="stat-num">100%</span><span class="stat-label">Primary sources</span></div>
  </div>
</div>

{cards_html}

<div class="usage">
  <h2 class="section-title">Using this list</h2>
  <div class="usage-grid">
    <div class="usage-card">
      <div class="usage-head">{_icon('home','icon')}<h3>For people</h3></div>
      <p>Browse by topic in the sidebar. Every entry links to the issuing body's own canonical page, grouped by issuer and jurisdiction. Notes flag current versions and successors.</p>
    </div>
    <div class="usage-card">
      <div class="usage-head">{_icon('database','icon')}<h3>For AI agents</h3></div>
      <p>Read <code>wiki/wiki-manifest.json</code> for a structured index of pages, sections, and link counts. The source of truth is Markdown in <code>docs/</code>; anchor IDs are stable across builds.</p>
    </div>
    <div class="usage-card">
      <div class="usage-head">{_icon('check-circle','icon')}<h3>Provenance</h3></div>
      <p>Primary sources only, one row per document. Links are verified before a row is added, and the "verified as of" date is refreshed on each change.</p>
    </div>
    <div class="usage-card">
      <div class="usage-head">{_icon('link','icon')}<h3>Suggest a resource</h3></div>
      <p>Know a guidance or standard that belongs here? Email <a href="mailto:{CONTACT_EMAIL}?subject=Regulatory%20Wiki%20%E2%80%94%20new%20resource">{CONTACT_EMAIL}</a> with the document, issuer, and a link to the authoritative source.</p>
    </div>
  </div>
</div>
"""
    return shell(
        title="Home", body=body, pages=pages, active_slug=None,
        description=SITE_TAGLINE,
    )


def build() -> None:
    OUT.mkdir(exist_ok=True)
    # Copy static source assets (logo, etc.) into the generated output.
    if ASSETS.is_dir():
        for asset in ASSETS.iterdir():
            if asset.is_file():
                shutil.copy2(asset, OUT / asset.name)
    md_files = sorted(
        p for p in DOCS.glob("*.md") if p.stem.lower() != "readme"
    )
    docs = [parse_doc(p) for p in md_files]

    for doc in docs:
        (OUT / f"{doc['slug']}.html").write_text(
            render_page(doc, docs), encoding="utf-8"
        )
    (OUT / "index.html").write_text(render_index(docs), encoding="utf-8")
    (OUT / "styles.css").write_text(STYLES, encoding="utf-8")
    (OUT / "wiki.js").write_text(SCRIPT, encoding="utf-8")

    # Full search index: one entry per document row, plus sections and pages.
    search: list[dict] = []
    for d in docs:
        page_url = f"{d['slug']}.html"
        search.append({
            "kind": "page", "title": d["title"], "sub": "Topic",
            "url": page_url, "hay": f"{d['title']} {d['intro']}".lower(),
        })
        for s in d["sections"]:
            search.append({
                "kind": "section", "title": s["title"],
                "sub": _short_title(d),
                "url": f"{page_url}#{s['id']}", "hay": s["title"].lower(),
            })
        for r in d["rows"]:
            hay = f"{r['document']} {r['issuer']} {r['notes']} {r['section']}".lower()
            search.append({
                "kind": "doc", "title": r["document"],
                "sub": f"{r['issuer']} · {r['section']}",
                "url": f"{page_url}#{r['anchor']}", "link": r["url"], "hay": hay,
            })
    (OUT / "search-index.json").write_text(
        json.dumps(search, ensure_ascii=False), encoding="utf-8"
    )

    grouped = group_by_domain(docs)
    manifest = {
        "site": SITE_NAME,
        "tagline": SITE_TAGLINE,
        "source_of_truth": "docs/*.md",
        "domains": [
            {"name": domain, "topics": [p["slug"] for p in topics]}
            for domain, topics in grouped
        ],
        "pages": [
            {
                "slug": d["slug"],
                "title": d["title"],
                "domain": d["domain"],
                "url": f"{d['slug']}.html",
                "source": d["source"],
                "intro": d["intro"],
                "link_count": d["link_count"],
                "sections": d["sections"],
            }
            for d in docs
        ],
    }
    (OUT / "wiki-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"Built {len(docs)} page(s) + index + manifest into {OUT}")
    for d in docs:
        print(f"  · {d['slug']}.html  ({d['link_count']} links, {len(d['sections'])} sections)")


# --- Styles (AICOE design system: monochrome, sharp corners, system font) ------
STYLES = """/* GENERATED by wiki/build_wiki.py — do not hand-edit. AICOE design system. */
:root{
  --black:#000;--white:#fff;
  --gray-100:#f5f5f5;--gray-200:#e5e5e5;--gray-300:#d4d4d4;
  --gray-500:#737373;--gray-700:#404040;--gray-800:#262626;--gray-900:#171717;
  --accent:#0066ff;
  --bg:#fff;--bg-alt:#f5f5f5;--border:#e5e5e5;--border-dark:#d4d4d4;
  --text:#171717;--text-muted:#737373;
  --font:-apple-system,BlinkMacSystemFont,'Segoe UI','Inter',sans-serif;
  --mono:'SF Mono',Monaco,Consolas,'Liberation Mono',monospace;
  --sidebar-w:264px;--content-max:900px;
}
*{box-sizing:border-box;}
html{scroll-behavior:smooth;}
body{margin:0;font-family:var(--font);font-size:16px;line-height:1.65;
  color:var(--text);background:var(--bg);-webkit-font-smoothing:antialiased;}
a{color:inherit;text-decoration:none;}
code{font-family:var(--mono);font-size:.85em;background:var(--bg-alt);
  padding:2px 6px;border:1px solid var(--border);}
.icon{width:1em;height:1em;flex:none;vertical-align:-.125em;}
.icon.ext{width:.72em;height:.72em;margin-left:.35em;opacity:.5;}
.skip-link{position:absolute;left:-9999px;}
.skip-link:focus{left:1rem;top:1rem;z-index:100;background:var(--black);
  color:var(--white);padding:.5rem 1rem;}

.layout{display:flex;min-height:100vh;}

/* Sidebar */
.sidebar{width:var(--sidebar-w);flex:none;background:var(--white);
  border-right:1px solid var(--border);position:sticky;top:0;height:100vh;
  display:flex;flex-direction:column;overflow-y:auto;}
.brand{display:flex;align-items:center;gap:.75rem;padding:1.35rem 1.5rem;
  border-bottom:1px solid var(--border);}
.brand-logo{width:34px;height:34px;flex:none;object-fit:contain;
  border:1px solid var(--border);background:#fafafa;}
.brand-text{display:flex;flex-direction:column;gap:.15rem;min-width:0;}
.brand-mark{font-weight:700;letter-spacing:.005em;font-size:.92rem;line-height:1.15;}
.brand-sub{font-size:.68rem;text-transform:uppercase;letter-spacing:.13em;
  color:var(--text-muted);}
/* Search */
.search{display:flex;align-items:center;gap:.5rem;margin:1rem 1rem .35rem;
  border:1px solid var(--border);padding:.5rem .65rem;background:var(--white);}
.search:focus-within{border-color:var(--gray-500);}
.search-icon{width:1rem;height:1rem;color:var(--gray-500);flex:none;}
#wiki-search{border:none;outline:none;background:none;font:inherit;font-size:.88rem;
  width:100%;color:var(--text);}
#wiki-search::placeholder{color:var(--gray-500);}
#wiki-search::-webkit-search-cancel-button{-webkit-appearance:none;}
.search-kbd{font-family:var(--mono);font-size:.7rem;color:var(--gray-500);
  border:1px solid var(--border);padding:0 .35rem;flex:none;}
.search-results{margin:0 .75rem .5rem;max-height:calc(100vh - 170px);overflow-y:auto;flex:1;}
.search-results[hidden]{display:none;}
.sr-item{display:flex;flex-direction:column;gap:.12rem;padding:.55rem .7rem;
  border-left:2px solid transparent;}
.sr-item:hover,.sr-item:focus{background:var(--bg-alt);border-left-color:var(--black);outline:none;}
.sr-title{font-size:.85rem;font-weight:600;color:var(--gray-900);display:flex;
  align-items:center;gap:.4rem;line-height:1.3;}
.sr-tag{font-size:.62rem;text-transform:uppercase;letter-spacing:.1em;
  color:var(--gray-500);border:1px solid var(--border);padding:0 .3rem;font-weight:500;}
.sr-sub{font-size:.74rem;color:var(--text-muted);}
.sr-empty{padding:.75rem;font-size:.85rem;color:var(--text-muted);}

/* Tree nav */
.nav{display:flex;flex-direction:column;padding:.35rem .75rem 1rem;gap:1px;flex:1;overflow-y:auto;}
.nav[hidden]{display:none;}
.nav-domain{font-size:.68rem;text-transform:uppercase;letter-spacing:.13em;
  color:var(--gray-500);font-weight:600;padding:1rem .75rem .35rem;margin-top:.15rem;}
.nav-domain:first-of-type{margin-top:0;}
.nav-icon{width:1.05rem;height:1.05rem;color:var(--gray-500);flex:none;}
.tree-link{display:flex;align-items:center;gap:.7rem;padding:.55rem .75rem;
  font-size:.9rem;color:var(--gray-700);border-left:2px solid transparent;
  transition:background .12s,color .12s;}
.tree-link:hover{background:var(--bg-alt);color:var(--black);}
.tree-link.active{color:var(--black);font-weight:600;border-left-color:var(--black);background:var(--bg-alt);}
.tree-node{border:none;}
.tree-node>summary{display:flex;align-items:center;justify-content:space-between;
  gap:.5rem;padding:.55rem .75rem;font-size:.9rem;color:var(--gray-700);cursor:pointer;
  list-style:none;border-left:2px solid transparent;transition:background .12s,color .12s;}
.tree-node>summary::-webkit-details-marker{display:none;}
.tree-node>summary::marker{content:"";}
.tree-node>summary:hover{background:var(--bg-alt);color:var(--black);}
.tree-top-label{display:flex;align-items:center;gap:.7rem;min-width:0;}
.tree-top-label>span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.tree-top.active{color:var(--black);font-weight:600;}
.chev{color:var(--gray-500);transition:transform .15s;flex:none;}
.tree-node[open]>summary .chev{transform:rotate(90deg);}
.tree-children{list-style:none;margin:0 0 .3rem;padding:.05rem 0;}
.tree-sub{display:block;padding:.38rem .75rem .38rem 2rem;font-size:.83rem;
  color:var(--gray-500);border-left:2px solid var(--border);margin-left:1.15rem;
  transition:background .12s,color .12s,border-color .12s;}
.tree-sub:hover{color:var(--black);border-left-color:var(--gray-500);background:var(--bg-alt);}
.sidebar-foot{padding:1rem 1.5rem;border-top:1px solid var(--border);
  font-size:.72rem;color:var(--text-muted);letter-spacing:.04em;}

/* Main */
.main-wrap{flex:1;min-width:0;display:flex;flex-direction:column;}
.topbar{display:none;align-items:center;gap:.75rem;padding:.75rem 1rem;
  border-bottom:1px solid var(--border);position:sticky;top:0;background:var(--white);z-index:20;}
.menu-toggle{background:none;border:1px solid var(--border);padding:.4rem;
  cursor:pointer;display:flex;color:var(--text);}
.topbar-title{font-weight:600;font-size:.95rem;}
.content{max-width:var(--content-max);width:100%;margin:0 auto;
  padding:3rem 3rem 4rem;}

/* Doc header */
.eyebrow{display:inline-flex;align-items:center;gap:.5rem;font-size:.75rem;
  text-transform:uppercase;letter-spacing:.16em;color:var(--text-muted);
  margin-bottom:1rem;}
.doc-header h1,.hero h1{font-size:2.6rem;line-height:1.1;font-weight:700;
  letter-spacing:-.02em;margin:0 0 .75rem;}
.lede{font-size:1.15rem;color:var(--gray-700);max-width:62ch;margin:0 0 1.5rem;}
.doc-meta{display:flex;flex-wrap:wrap;gap:1.25rem;padding:1rem 0;
  border-top:1px solid var(--border);border-bottom:1px solid var(--border);
  font-size:.85rem;color:var(--text-muted);}
.doc-meta span{display:inline-flex;align-items:center;gap:.4rem;}
.doc-meta code{background:none;border:none;padding:0;color:var(--gray-700);}

/* On-page toc */
.page-toc{margin:2rem 0;background:var(--bg-alt);border:1px solid var(--border);
  padding:1.25rem 1.5rem;}
.toc-label{display:inline-flex;align-items:center;gap:.5rem;font-size:.75rem;
  text-transform:uppercase;letter-spacing:.14em;color:var(--text-muted);
  font-weight:600;}
.page-toc ul{list-style:none;margin:.75rem 0 0;padding:0;
  display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:.35rem;}
.page-toc a{font-size:.9rem;color:var(--gray-700);border-bottom:1px solid transparent;}
.page-toc a:hover{color:var(--black);border-bottom-color:var(--black);}

/* Doc body */
.doc-body{margin-top:2.5rem;}
.doc-body h2{font-size:1.5rem;font-weight:700;letter-spacing:-.01em;
  margin:3rem 0 1rem;padding-top:1.5rem;border-top:1px solid var(--border);
  scroll-margin-top:1.5rem;}
.doc-body h2:first-child{border-top:none;padding-top:0;margin-top:0;}
.h2-inner{display:inline-flex;align-items:center;gap:.65rem;}
.section-icon{width:1.35rem;height:1.35rem;color:var(--black);}
.doc-body h3{font-size:1.15rem;font-weight:600;margin:2rem 0 .75rem;}
.doc-body p{max-width:70ch;}
.doc-body blockquote{margin:1.5rem 0;padding:.9rem 1.25rem;background:var(--bg-alt);
  border-left:3px solid var(--black);color:var(--gray-700);font-size:.95rem;}
.doc-body blockquote p{margin:0;}
.doc-body ul{padding-left:1.25rem;}
.doc-body li{margin:.35rem 0;}
.doc-body a[href^="http"]{color:var(--black);border-bottom:1px solid var(--gray-300);
  transition:border-color .12s,color .12s;word-break:break-word;}
.doc-body a[href^="http"]:hover{color:var(--accent);border-bottom-color:var(--accent);}

/* Tables */
.table-wrap{overflow-x:auto;margin:1.25rem 0;border:1px solid var(--border);}
table{width:100%;border-collapse:collapse;font-size:.9rem;}
thead th{background:var(--bg-alt);text-align:left;font-weight:600;
  text-transform:uppercase;letter-spacing:.06em;font-size:.72rem;
  color:var(--gray-700);padding:.75rem 1rem;border-bottom:1px solid var(--border-dark);
  white-space:nowrap;}
tbody td{padding:.75rem 1rem;border-bottom:1px solid var(--border);vertical-align:top;}
tbody tr:last-child td{border-bottom:none;}
tbody tr:hover{background:var(--bg-alt);}
tbody td:first-child{font-weight:600;color:var(--gray-900);min-width:180px;}

/* Home / hero */
.hero{padding:1rem 0 2.5rem;border-bottom:1px solid var(--border);margin-bottom:2.5rem;}
.hero-stats{display:flex;gap:2.5rem;margin-top:2rem;flex-wrap:wrap;}
.stat{display:flex;flex-direction:column;}
.stat-num{font-size:2.5rem;font-weight:200;line-height:1;letter-spacing:-.02em;}
.stat-label{font-size:.72rem;text-transform:uppercase;letter-spacing:.14em;
  color:var(--text-muted);margin-top:.4rem;}
.section-title{font-size:1.35rem;font-weight:700;margin:0 0 1.25rem;}
.topic-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));
  gap:1rem;margin-bottom:3.5rem;}
.topic-card{border:1px solid var(--border);padding:1.5rem;display:flex;
  flex-direction:column;gap:.6rem;transition:border-color .12s,box-shadow .12s,transform .12s;background:var(--white);}
.topic-card:hover{border-color:var(--border-dark);
  box-shadow:0 6px 24px rgba(0,0,0,.06);transform:translateY(-2px);}
.card-top{display:flex;}.card-icon{width:1.6rem;height:1.6rem;color:var(--black);}
.topic-card h3{font-size:1.1rem;font-weight:700;margin:.25rem 0 0;}
.topic-card p{font-size:.9rem;color:var(--gray-700);margin:0;flex:1;line-height:1.55;}
.card-meta{display:flex;gap:1rem;font-size:.72rem;text-transform:uppercase;
  letter-spacing:.1em;color:var(--text-muted);padding-top:.6rem;
  border-top:1px solid var(--border);}
.usage-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:1rem;}
.usage-card{border:1px solid var(--border);padding:1.5rem;background:var(--white);}
.usage-head{display:flex;align-items:center;gap:.6rem;margin-bottom:.6rem;}
.usage-head h3{margin:0;font-size:1rem;font-weight:700;}
.usage-head .icon{width:1.25rem;height:1.25rem;}
.usage-card p{font-size:.9rem;color:var(--gray-700);margin:0;line-height:1.55;}

.page-foot{margin-top:4rem;padding-top:1.5rem;border-top:1px solid var(--border);
  font-size:.8rem;color:var(--text-muted);}
.page-foot p{margin:.25rem 0;}
.page-foot a,.usage-card a{color:var(--text);border-bottom:1px solid var(--gray-300);
  transition:color .12s,border-color .12s;}
.page-foot a:hover,.usage-card a:hover{color:var(--accent);border-bottom-color:var(--accent);}

/* Responsive */
@media(max-width:880px){
  .sidebar{position:fixed;left:0;top:0;transform:translateX(-100%);
    transition:transform .2s;z-index:40;box-shadow:0 0 40px rgba(0,0,0,.12);}
  body.nav-open .sidebar{transform:translateX(0);}
  .topbar{display:flex;}
  .content{padding:2rem 1.25rem 3rem;}
  .doc-header h1,.hero h1{font-size:2rem;}
}

/* Dark mode (monochrome inverted) */
@media(prefers-color-scheme:dark){
  :root{--bg:#0d0d0d;--bg-alt:#171717;--border:#262626;--border-dark:#333;
    --text:#f5f5f5;--text-muted:#a3a3a3;--gray-700:#c4c4c4;--gray-800:#d4d4d4;
    --gray-900:#f5f5f5;--gray-500:#8a8a8a;--gray-300:#3a3a3a;--white:#131313;--accent:#4d94ff;}
  .topic-card:hover{box-shadow:0 6px 24px rgba(0,0,0,.4);}
}

@media print{
  .sidebar,.topbar,.page-toc,.menu-toggle{display:none!important;}
  .content{max-width:100%;padding:0;}
  .table-wrap{overflow:visible;}
  tbody tr,.topic-card,.table-wrap{break-inside:avoid;}
  a[href^="http"]{border:none;}
}
"""


# --- Client search (vanilla JS, no dependencies) -------------------------------
SCRIPT = r"""/* GENERATED by wiki/build_wiki.py — do not hand-edit. */
(function () {
  var input = document.getElementById('wiki-search');
  var results = document.getElementById('search-results');
  var nav = document.querySelector('.nav');
  if (!input || !results || !nav) return;

  var index = [], loaded = false;
  function load() {
    if (loaded) return; loaded = true;
    fetch('search-index.json').then(function (r) { return r.json(); })
      .then(function (d) { index = d; if (input.value.trim()) run(); })
      .catch(function () { index = []; });
  }
  input.addEventListener('focus', load);

  var KIND = { page: 'Topic', section: 'Section', doc: '' };
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function score(hay, toks) {
    var s = 0;
    for (var i = 0; i < toks.length; i++) {
      var pos = hay.indexOf(toks[i]);
      if (pos < 0) return 0;
      s += (pos === 0 ? 3 : 1) + (hay.indexOf(' ' + toks[i]) >= 0 ? 1 : 0);
    }
    return s;
  }
  function run() {
    var q = input.value.trim().toLowerCase();
    if (!q) { results.hidden = true; nav.hidden = false; results.innerHTML = ''; return; }
    var toks = q.split(/\s+/);
    var hits = index.map(function (e) { return { e: e, s: score(e.hay, toks) }; })
      .filter(function (x) { return x.s > 0; })
      .sort(function (a, b) { return b.s - a.s || a.e.title.length - b.e.title.length; })
      .slice(0, 18);
    if (!hits.length) {
      results.innerHTML = '<div class="sr-empty">No matches</div>';
    } else {
      results.innerHTML = hits.map(function (x) {
        var e = x.e;
        var tag = e.kind === 'doc' ? '' : '<span class="sr-tag">' + KIND[e.kind] + '</span>';
        return '<a class="sr-item" href="' + e.url + '"><span class="sr-title">'
          + esc(e.title) + tag + '</span><span class="sr-sub">' + esc(e.sub || '')
          + '</span></a>';
      }).join('');
    }
    results.hidden = false; nav.hidden = true;
  }
  input.addEventListener('input', run);
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { input.value = ''; run(); input.blur(); }
    if (e.key === 'Enter') { var f = results.querySelector('.sr-item'); if (f) f.click(); }
  });
  document.addEventListener('keydown', function (e) {
    var t = document.activeElement;
    var typing = t && /input|textarea|select/i.test(t.tagName);
    if (e.key === '/' && !typing) { e.preventDefault(); input.focus(); }
  });
})();
"""


if __name__ == "__main__":
    build()
