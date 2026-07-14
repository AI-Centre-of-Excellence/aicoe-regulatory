#!/usr/bin/env python3
"""Generate the aicoe-regulatory HTML site from the Markdown in ../docs.

The Markdown under docs/ is the source of truth. This script renders it into
AICOE-themed, cross-linked HTML pages plus a machine-readable manifest, so the
same content reads well for humans (sidebar nav, tables, icons) and for AI
agents (clean semantic HTML, stable anchor IDs, wiki-manifest.json).

Usage:
    python3 wiki/build_wiki.py          # regenerate the site from docs/

Do not hand-edit the HTML output or styles.css — edits are overwritten on the
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
META = ROOT / "meta"          # per-topic <slug>.json routing metadata (agent layer)
OUT = ROOT / "wiki"

# legal_force values grouped for badge styling.
FORCE_MANDATORY = {"law", "regulation", "directive", "binding-standard"}
FORCE_GUIDANCE = {"guidance", "framework"}
FORCE_VOLUNTARY = {"voluntary-standard", "best-practice"}

SITE_NAME = "AI Centre of Excellence Regulatory List"
SITE_TAGLINE = "Curated regulatory guidances, standards & best practices"
CONTACT_EMAIL = "hi@aicoe.io"
DEFAULT_DOMAIN = "General"

# Generated "Regulatory horizon" page (built from routing metadata, not a docs/*.md).
HORIZON_URL = "regulatory-horizon.html"
HORIZON_TITLE = "Regulatory horizon"
HORIZON_INTRO = (
    "What's changing across the index: draft and proposed rules, recently "
    "superseded standards, and instruments phasing in on future dates. "
    "Generated automatically from the routing metadata, so it never goes stale."
)

# Display order for domains in the sidebar and on the home page. Domains not
# listed here appear after these, alphabetically.
DOMAIN_ORDER = [
    "AI Agents",
    "Life Sciences",
    "Financial Services",
    "Manufacturing",
    "Automotive & Mobility",
    "Aerospace & Defense",
    "Energy & Utilities",
    "Hi-Tech / Technology",
    "Logistics & Supply Chain",
    "Food & Agriculture",
    "Consumer Protection",
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
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>',
    "moon": '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>',
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


def _render_body(body_lines: list[str], meta_map: dict) -> tuple[str, list[dict], list[dict], int]:
    """Markdown body -> (html, sections, rows, link_count) with badges + autolinks.

    Shared by parse_doc (file-backed pages) and generated pages (e.g. the
    Regulatory horizon), so styling and metadata handling stay identical.
    """
    md = markdown.Markdown(
        extensions=["tables", "toc", "fenced_code", "attr_list", "sane_lists"],
        extension_configs={"toc": {"toc_depth": "2-3"}},
    )
    body_html = md.convert("\n".join(body_lines))
    sections = [
        {"title": html.unescape(t["name"]), "id": t["id"]}
        for t in getattr(md, "toc_tokens", [])
    ]
    body_html = _postprocess(body_html)
    link_count = len(re.findall(r'<a\s+[^>]*href="https?://', body_html))
    rows = _extract_rows(body_lines, sections)
    for r in rows:
        r["meta"] = meta_map.get(r["document"])
    if meta_map:
        body_html = _inject_badges(body_html, rows)
    return body_html, sections, rows, link_count


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

    rel = path.relative_to(DOCS).with_suffix("")
    body_html, sections, rows, link_count = _render_body(body_lines, _load_meta(rel))

    try:
        order = int(meta.get("order", "100"))
    except ValueError:
        order = 100

    # Country sub-pages live under docs/countries/<country>/<topic>.md
    # Their output URL is countries/<country>/<slug>.html; top-level pages
    # output as <slug>.html.
    parts = rel.parts
    if len(parts) >= 3 and parts[0] == "countries":
        country = meta.get("country", parts[1].capitalize())
        url = f"countries/{parts[1]}/{path.stem}.html"
    else:
        country = meta.get("country", "")
        url = f"{path.stem}.html"

    return {
        "slug": path.stem,
        "url": url,
        "title": title,
        "intro": intro,
        "html": body_html,
        "sections": sections,
        "rows": rows,
        "link_count": link_count,
        "source": str(rel.with_suffix(".md")).replace("\\", "/"),
        "domain": meta.get("domain", DEFAULT_DOMAIN),
        "country": country,
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
        rows.append({
            "document": cells[0],
            "issuer": cells[1],
            "url": cells[2],
            "notes": cells[3] if len(cells) > 3 else "",
            "section": current or "",
            "anchor": current_id or "",
        })
    return rows


def _load_meta(rel: Path) -> dict:
    """Load per-topic routing metadata keyed by exact document name.

    rel is the path relative to DOCS (without .md extension).
    For top-level docs, reads meta/<slug>.json.
    For country sub-pages, reads meta/countries/<country>/<slug>.json.
    """
    path = META / f"{rel}.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}
    return {e["document"]: e for e in data.get("entries", []) if e.get("document")}

def _force_label(force: str) -> tuple[str, str]:
    """Return (display label, css modifier) for a legal_force value."""
    if force in FORCE_MANDATORY:
        return force.replace("-", " "), "badge-mandatory"
    if force in FORCE_VOLUNTARY:
        return force.replace("-", " "), "badge-voluntary"
    return force.replace("-", " "), "badge-guidance"


def _badges(meta: dict | None) -> str:
    if not meta:
        return ""
    out = []
    jur = meta.get("jurisdiction")
    if jur:
        out.append(f'<span class="badge badge-jur">{html.escape(jur)}</span>')
    force = meta.get("legal_force")
    if force:
        label, cls = _force_label(force)
        out.append(f'<span class="badge {cls}">{html.escape(label)}</span>')
    return f'<span class="badges">{"".join(out)}</span>' if out else ""


def _inject_badges(body: str, rows: list[dict]) -> str:
    """Append jurisdiction / legal-force badges to each table row's first cell.

    Data <tr> elements are matched in document order, the same order as `rows`.
    """
    it = iter(rows)

    def repl(m: re.Match) -> str:
        try:
            row = next(it)
        except StopIteration:
            return m.group(0)
        badges = _badges(row.get("meta"))
        if not badges:
            return m.group(0)
        return f"{m.group(1)}{m.group(2)}{badges}{m.group(3)}{m.group(4)}"

    return re.sub(
        r"(<tr>\s*<td>)(.*?)(</td>)(.*?</tr>)", repl, body, flags=re.DOTALL
    )


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


def _topic_node(p: dict, active_url: str | None, base: str = "") -> str:
    is_active = p["url"] == active_url
    icon = _icon(_section_icon(p["title"]), "icon nav-icon")
    href = f"{base}{p['url']}"
    children = [f'<li><a class="tree-sub" href="{href}">Overview</a></li>']
    for s in p["sections"]:
        if s["title"].lower() in ("scope & maintenance",):
            continue
        children.append(
            f'<li><a class="tree-sub" href="{href}#{s["id"]}">'
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


def _country_node(country: str, topics: list[dict], active_url: str | None,
                  base: str = "") -> str:
    """Render a country as a nested expandable with its topic pages inside."""
    has_active = any(t["url"] == active_url for t in topics)
    children = "\n".join(_topic_node(t, active_url, base) for t in topics)
    summary = (
        f'<summary class="tree-top{" active" if has_active else ""}">'
        f'<span class="tree-top-label">{_icon("globe", "icon nav-icon")}'
        f'<span>{html.escape(country)}</span></span>{CHEVRON}</summary>'
    )
    return (
        f'<details class="tree-node"{" open" if has_active else ""}>'
        f'{summary}<ul class="tree-children">{children}</ul></details>'
    )


def nav_html(pages: list[dict], active_url: str | None, base: str = "") -> str:
    """Home, then domain groups; each topic expands to its sections.

    The Countries domain renders countries as an extra nesting level, each
    containing its topic pages. base prefixes all nav links (for sub-pages).
    """
    home_cls = "tree-link home" + (" active" if active_url is None else "")
    items = [
        f'<a class="{home_cls}" href="{base}index.html">'
        f'{_icon("home", "icon nav-icon")}<span>Home</span></a>'
    ]
    hz_cls = "tree-link home" + (" active" if active_url == HORIZON_URL else "")
    items.append(
        f'<a class="{hz_cls}" href="{base}{HORIZON_URL}">'
        f'{_icon("activity", "icon nav-icon")}<span>{html.escape(HORIZON_TITLE)}</span></a>'
    )
    groups = group_by_domain(pages)
    single = len(groups) <= 1
    for domain, topics in groups:
        if not single:
            items.append(f'<div class="nav-domain">{html.escape(domain)}</div>')
        if domain == "Countries":
            # Group country pages by country, then render each as a nested node.
            by_country: dict[str, list[dict]] = {}
            for p in topics:
                c = p.get("country") or "Other"
                by_country.setdefault(c, []).append(p)
            for country in sorted(by_country):
                items.append(_country_node(country, by_country[country], active_url, base))
        else:
            for p in topics:
                items.append(_topic_node(p, active_url, base))
    return "\n".join(items)


def shell(*, title: str, body: str, pages: list[dict], active_url: str | None,
          description: str) -> str:
    year = "2026"
    # Country sub-pages live in a subdirectory; they need a ../ prefix for
    # shared assets (styles.css, logo.png, wiki.js, index.html).
    depth = active_url.count("/") if active_url else 0
    base = "../" * depth if depth else ""
    nav = nav_html(pages, active_url, base)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)} · {SITE_NAME}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="icon" type="image/png" href="{base}logo.png">
<link rel="apple-touch-icon" href="{base}logo.png">
<link rel="stylesheet" href="{base}styles.css">
<script>(function(){{var t=localStorage.getItem('wiki-theme')||'light';document.documentElement.setAttribute('data-theme',t);}})();</script>
</head>
<a class="skip-link" href="#content">Skip to content</a>
<div id="scroll-progress"></div>
<div class="layout">
  <aside class="sidebar">
    <div class="brand-row">
      <a class="brand" href="{base}index.html">
        <img class="brand-logo" src="{base}logo.png" alt="AICOE logo" width="34" height="34">
        <span class="brand-text">
          <span class="brand-mark">AI Centre of Excellence</span>
          <span class="brand-sub">Regulatory List</span>
        </span>
      </a>
      <button class="theme-toggle" id="theme-toggle" aria-label="Toggle theme" title="Toggle light / dark">
        {_icon('sun','icon icon-sun')}{_icon('moon','icon icon-moon')}
      </button>
    </div>
    <div class="search">
      {_icon('search', 'icon search-icon')}
      <input id="wiki-search" type="search" placeholder="Search standards…"
             autocomplete="off" spellcheck="false" aria-label="Search the list">
      <kbd class="search-kbd">/</kbd>
    </div>
    <div id="search-results" class="search-results" hidden role="listbox"
         aria-label="Search results"></div>
    <nav class="nav" aria-label="Regulatory list">
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
        <p>Suggest a resource or correction: <a href="mailto:{CONTACT_EMAIL}?subject=Regulatory%20List%20%E2%80%94%20new%20resource">{CONTACT_EMAIL}</a></p>
        <p class="foot-rights">This list is a curated index of third-party materials. All guidances and standards remain the property of their respective issuers; every link points to the issuing body's official source. The index and its descriptions are provided for reference only and are not legal advice.</p>
        <p>{SITE_NAME} · {SITE_TAGLINE}</p>
        <p>Generated from <code>docs/</code> by <code>build_wiki.py</code>. Do not hand-edit these HTML files.</p>
        <p>© {year} AI Centre of Excellence · Text licensed MIT; linked standards are © their issuers</p>
      </footer>
    </main>
  </div>
</div>
<script src="{base}wiki.js" defer></script>
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
        active_url=doc["url"], description=doc["intro"],
    )


def _topic_card(p: dict) -> str:
    icon = _icon(_section_icon(p["title"]), "icon card-icon")
    return (
        f'<a class="topic-card" href="{p["url"]}">'
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

<a class="horizon-callout" href="{HORIZON_URL}">
  <div class="usage-head">{_icon('activity','icon')}<h3>Regulatory horizon</h3></div>
  <p>What's changing across the index — draft &amp; proposed rules, recently superseded standards, and instruments phasing in on future dates. Auto-generated, always current.</p>
  <span class="horizon-cta">View the horizon {_icon('external-link','icon')}</span>
</a>

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
      <p>Start with <a href="llms.txt"><code>llms.txt</code></a>, then read <a href="wiki-manifest.json"><code>manifest.json</code></a>. Each entry carries routing metadata (jurisdiction, legal force, applies-to, tags, status) so you can filter to the standards that apply. It is factual metadata only, never the standard's text.</p>
    </div>
    <div class="usage-card">
      <div class="usage-head">{_icon('check-circle','icon')}<h3>Provenance</h3></div>
      <p>Primary sources only, one row per document. Links are verified before a row is added.</p>
    </div>
    <div class="usage-card">
      <div class="usage-head">{_icon('link','icon')}<h3>Suggest a resource</h3></div>
      <p>Know a guidance or standard that belongs here? Email <a href="mailto:{CONTACT_EMAIL}?subject=Regulatory%20List%20%E2%80%94%20new%20resource">{CONTACT_EMAIL}</a> with the document, issuer, and a link to the authoritative source.</p>
    </div>
  </div>
</div>
"""
    return shell(
        title="Home", body=body, pages=pages, active_url=None,
        description=SITE_TAGLINE,
    )


def _llms_txt(grouped: list[tuple[str, list[dict]]], manifest: dict) -> str:
    """A query contract telling AI agents how to use the routing dataset."""
    lines = [
        f"# {SITE_NAME}",
        "",
        f"> {SITE_TAGLINE}. A curated index of regulatory guidances, standards,",
        "> and best practices, organised so an agent can identify which standards",
        "> apply to a given situation. Every link points to the issuing body's",
        "> official source. This index contains factual metadata only; it does not",
        "> reproduce the text of any standard. Standards remain © their issuers.",
        "",
        "## Machine-readable data",
        "",
        "- `wiki-manifest.json` — the authoritative dataset. `pages[].entries[]`",
        "  is one record per document with routing metadata (see fields below).",
        "- `cross-refs.json` — cross-reference map of equivalent, related, and",
        "  referenced standards across jurisdictions. Each mapping has `from`,",
        "  `to`, `type`, `scope`, and `bidirectional` fields.",
        "- `search-index.json` — flat search index for keyword lookups.",
        "",
        "## Entry fields (all factual, for routing — not the standard's text)",
        "",
        "- `document`, `issuer`, `section` — identity",
        "- `link` — the issuing body's official URL; `url` — anchor in this list",
        "- `jurisdiction` — where it has force (US, EU, UK, India, Global, International)",
        "- `legal_force` — law, regulation, directive, binding-standard,",
        "  guidance, framework, voluntary-standard, best-practice",
        "- `applies_to` — descriptive scope text",
        "- `triggers` — machine-readable tags for what brings it into scope",
        "  (e.g. processes-pii, federal-agency, cardholder-data, eu-market)",
        "- `tags` — controlled keywords for topical filtering",
        "- `status` — current, superseded, draft, proposed",
        "- `supersedes` — document names this standard replaces (array or null)",
        "- `superseded_by` — document names that replace this (array or null)",
        "- `equivalents` — document names functionally equivalent in other",
        "  frameworks/jurisdictions (array or null)",
        "- `notes` — short factual note (version, successor, access)",
        "",
        "## Cross-reference types (in cross-refs.json)",
        "",
        "Types: adoption, builds-on, companion, complementary, equivalent, extended-by, extends, implemented-by, implements, part-of, references, sector-specific, supersedes.",
        "sector-specific, part-of."
        "",
        "## How to route",
        "",
        "1. Identify jurisdiction + domain. 2. Filter entries by `jurisdiction`",
        "and `tags`/`section`. 3. Filter by `triggers` for machine-readable scope.",
        "4. Rank by `legal_force` (law/regulation/binding-standard = mandatory;",
        "guidance/framework/voluntary-standard = advisory). 5. Prefer `status:",
        "current`; check `superseded_by` for successors. 6. Use `equivalents` and",
        "`cross-refs.json` to find the same standard in other jurisdictions. 7.",
        "Always consult the `link` for authoritative text.",
        "",
        "## Domains & topics",
        "",
    ]
    for domain, topics in grouped:
        lines.append(f"### {domain}")
        for p in topics:
            lines.append(f"- {_short_title(p)} — /{p['url']} ({p['link_count']} links)")
        lines.append("")
    lines.append(f"Contact: {CONTACT_EMAIL}")
    return "\n".join(lines) + "\n"


def build_horizon(pages: list[dict]) -> dict:
    """Generate the Regulatory horizon page from routing metadata across all
    topics: draft/proposed instruments, recently superseded standards, and
    documents phasing in on future dates. Rebuilt on every run, never stale.
    """
    FUTURE = re.compile(
        r"\b(?:applies? from|effective|enters? into force|phas\w*|transition|"
        r"(?:from|by|in) 20(?:2[6-9]|3\d))\b",
        re.I,
    )
    horizon: list[tuple[dict, dict]] = []
    superseded: list[tuple[dict, dict]] = []
    phasing: list[tuple[dict, dict]] = []
    seen: set[str] = set()
    for p in pages:
        for r in p["rows"]:
            doc = r["document"]
            if doc in seen:
                continue
            meta = r.get("meta") or {}
            status = meta.get("status")
            note = r.get("notes", "")
            if status in ("draft", "proposed"):
                horizon.append((p, r)); seen.add(doc)
            elif status == "superseded" or meta.get("superseded_by"):
                superseded.append((p, r)); seen.add(doc)
            elif FUTURE.search(note):
                phasing.append((p, r)); seen.add(doc)

    body_lines: list[str] = []
    meta_map: dict[str, dict] = {}

    def add_section(heading: str, recs: list[tuple[dict, dict]]) -> None:
        if not recs:
            return
        body_lines.append(f"## {heading}")
        body_lines.append("")
        body_lines.append("| Document | Topic | Source | Notes |")
        body_lines.append("|---|---|---|---|")
        for p, r in recs:
            topic = f'[{_short_title(p)}]({p["url"]}#{r["anchor"]})'
            body_lines.append(f'| {r["document"]} | {topic} | {r["url"]} | {r["notes"]} |')
            if r.get("meta"):
                meta_map[r["document"]] = r["meta"]
        body_lines.append("")

    add_section("On the horizon — draft & proposed", horizon)
    add_section("Recently superseded", superseded)
    add_section("Phasing in — future effective dates", phasing)

    body_html, sections, rows, link_count = _render_body(body_lines, meta_map)
    return {
        "slug": "regulatory-horizon",
        "url": HORIZON_URL,
        "title": HORIZON_TITLE,
        "intro": HORIZON_INTRO,
        "html": body_html,
        "sections": sections,
        "rows": rows,
        "link_count": link_count,
        "source": "(generated from meta/*.json)",
        "domain": "Overview",
        "country": "",
        "order": 0,
        "label": HORIZON_TITLE,
        "generated": True,
    }


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
    horizon = build_horizon(docs)

    for doc in docs:
        out_path = OUT / doc["url"]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(render_page(doc, docs), encoding="utf-8")
    (OUT / HORIZON_URL).write_text(render_page(horizon, docs), encoding="utf-8")
    (OUT / "index.html").write_text(render_index(docs), encoding="utf-8")
    (OUT / "styles.css").write_text(STYLES, encoding="utf-8")
    (OUT / "wiki.js").write_text(SCRIPT, encoding="utf-8")

    # Full search index: one entry per document row, plus sections and pages.
    search: list[dict] = []
    for d in docs:
        page_url = d["url"]
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
            meta = r.get("meta") or {}
            extra = " ".join([
                meta.get("applies_to", ""),
                " ".join(meta.get("tags", [])),
                meta.get("jurisdiction", ""),
                meta.get("legal_force", ""),
            ])
            hay = f"{r['document']} {r['issuer']} {r['notes']} {r['section']} {extra}".lower()
            search.append({
                "kind": "doc", "title": r["document"],
                "sub": f"{r['issuer']} · {r['section']}",
                "url": f"{page_url}#{r['anchor']}", "link": r["url"], "hay": hay,
            })
    # Regulatory horizon (generated page): index the page + its sections,
    # but not its rows — those documents are already indexed on their home pages.
    search.append({
        "kind": "page", "title": horizon["title"], "sub": "Overview",
        "url": horizon["url"], "hay": f"{horizon['title']} {horizon['intro']}".lower(),
    })
    for s in horizon["sections"]:
        search.append({
            "kind": "section", "title": s["title"], "sub": horizon["title"],
            "url": f"{horizon['url']}#{s['id']}", "hay": s["title"].lower(),
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
            {"name": domain, "topics": [p["url"] for p in topics]}
            for domain, topics in grouped
        ],
        "pages": [
            {
                "slug": d["slug"],
                "title": d["title"],
                "domain": d["domain"],
                "country": d.get("country", ""),
                "url": d["url"],
                "source": d["source"],
                "intro": d["intro"],
                "link_count": d["link_count"],
                "sections": d["sections"],
                "entries": [
                    {
                        "document": r["document"],
                        "issuer": r["issuer"],
                        "link": r["url"],
                        "url": f"{d['url']}#{r['anchor']}",
                        "section": r["section"],
                        "notes": r["notes"],
                        **{k: v for k, v in (r.get("meta") or {}).items()
                           if k in ("jurisdiction", "legal_force", "applies_to",
                                    "tags", "status", "function", "id",
                                    "supersedes", "superseded_by",
                                    "equivalents", "triggers")},
                    }
                    for r in d["rows"]
                ],
            }
            for d in docs
        ],
    }
    (OUT / "wiki-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    # Cross-reference map of equivalent, related, and referenced standards.
    cross_refs_path = META / "cross-refs.json"
    if cross_refs_path.is_file():
        shutil.copy2(cross_refs_path, OUT / "cross-refs.json")
    (OUT / "llms.txt").write_text(_llms_txt(grouped, manifest), encoding="utf-8")

    print(f"Built {len(docs)} topic page(s) + horizon + index + manifest into {OUT}")
    for d in docs:
        print(f"  · {d['url']}  ({d['link_count']} links, {len(d['sections'])} sections)")
    print(f"  · {horizon['url']}  (generated: {len(horizon['rows'])} entries, {len(horizon['sections'])} sections)")


# --- Styles (AICOE design system: editorial regulatory) -----------------------
STYLES = """/* GENERATED by build_wiki.py — do not hand-edit. AICOE design system. */
@import url('https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
:root{
  --black:#000;--white:#fff;
  --gray-100:#f7f7f5;--gray-200:#ebe9e4;--gray-300:#d4d0c8;
  --gray-500:#737373;--gray-700:#3a3a38;--gray-800:#242422;--gray-900:#141412;
  --accent:#0066ff;--accent-soft:rgba(0,102,255,.08);--accent-glow:rgba(0,102,255,.15);
  /* Pill badge palette (soft, positive) */
  --ok-bg:#e6f7ef;--ok-fg:#0a8f52;--ok-bd:#bce9d3;
  --info-bg:#e8f0fe;--info-fg:#1a56db;--info-bd:#c9dbfb;
  --warn-bg:#fff3e0;--warn-fg:#b3620a;--warn-bd:#ffe1b3;
  --jur-bg:#eef1f5;--jur-fg:#475569;--jur-bd:#dde3ea;
  --bg:#fff;--bg-alt:#f7f7f5;--bg-warm:#faf9f6;--border:#e0ddd6;--border-dark:#c9c5be;
  --text:#141412;--text-muted:#6b6b68;
  --display:'Hanken Grotesk',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  --font:'Hanken Grotesk',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  --mono:'JetBrains Mono','SF Mono',Monaco,Consolas,monospace;
  --sidebar-w:272px;--content-max:880px;
  --shadow-sm:0 1px 2px rgba(0,0,0,.04);
  --shadow-md:0 4px 16px rgba(0,0,0,.06),0 1px 4px rgba(0,0,0,.03);
  --shadow-lg:0 12px 48px rgba(0,0,0,.08),0 4px 16px rgba(0,0,0,.04);
  --ease:cubic-bezier(.22,.61,.36,1);
}
*{box-sizing:border-box;}
html{scroll-behavior:smooth;}
body{margin:0;font-family:var(--font);font-size:16px;line-height:1.7;
  color:var(--text);background:var(--bg);-webkit-font-smoothing:antialiased;
  text-rendering:optimizeLegibility;font-feature-settings:'kern' 1,'liga' 1;}
a{color:inherit;text-decoration:none;}
code{font-family:var(--mono);font-size:.82em;background:var(--bg-alt);
  padding:2px 7px;border:1px solid var(--border);border-radius:3px;}
.icon{width:1em;height:1em;flex:none;vertical-align:-.125em;}
.icon.ext{width:.72em;height:.72em;margin-left:.35em;opacity:.5;}
.skip-link{position:absolute;left:-9999px;}
.skip-link:focus{left:1rem;top:1rem;z-index:100;background:var(--black);
  color:var(--white);padding:.5rem 1rem;border-radius:3px;}

/* Scroll progress */
#scroll-progress{position:fixed;top:0;left:0;height:2px;background:var(--accent);
  width:0;z-index:999;transition:width .15s linear;}

.layout{display:flex;min-height:100vh;}

/* Sidebar */
.sidebar{width:var(--sidebar-w);flex:none;background:var(--bg-warm);
  border-right:1px solid var(--border);position:sticky;top:0;height:100vh;
  display:flex;flex-direction:column;overflow-y:auto;
  scrollbar-width:thin;scrollbar-color:var(--gray-300) transparent;}
.sidebar::-webkit-scrollbar{width:4px;}
.sidebar::-webkit-scrollbar-thumb{background:var(--gray-300);border-radius:2px;}
.brand-row{display:flex;align-items:center;justify-content:space-between;
  padding:1.5rem 1.5rem 1.25rem;border-bottom:1px solid var(--border);}
.brand{display:flex;align-items:center;gap:.75rem;padding:0;}
.brand-logo{width:36px;height:36px;flex:none;object-fit:contain;
  border:1px solid var(--border);border-radius:6px;background:var(--white);padding:2px;}
.brand-text{display:flex;flex-direction:column;gap:.1rem;min-width:0;}
.brand-mark{font-weight:700;letter-spacing:-.01em;font-size:.9rem;line-height:1.2;
  color:var(--text);font-family:var(--display);font-optical-sizing:auto;}
.brand-sub{font-size:.6rem;text-transform:uppercase;letter-spacing:.16em;
  color:var(--text-muted);font-weight:500;}

/* Theme toggle */
.theme-toggle{display:flex;align-items:center;justify-content:center;
  width:34px;height:34px;flex:none;background:none;border:1px solid var(--border);
  color:var(--text);cursor:pointer;border-radius:6px;
  transition:border-color .2s var(--ease),background .2s var(--ease);}
.theme-toggle:hover{border-color:var(--accent);background:var(--accent-soft);color:var(--accent);}
.theme-toggle .icon{width:1.05rem;height:1.05rem;}
[data-theme="light"] .theme-toggle .icon-moon{display:block;}
[data-theme="light"] .theme-toggle .icon-sun{display:none;}
[data-theme="dark"] .theme-toggle .icon-moon{display:none;}
[data-theme="dark"] .theme-toggle .icon-sun{display:block;}

/* Search */
.search{display:flex;align-items:center;gap:.5rem;margin:1rem 1rem .5rem;
  border:1px solid var(--border);padding:.5rem .7rem;background:var(--white);
  border-radius:7px;box-shadow:var(--shadow-sm);
  transition:border-color .2s var(--ease),box-shadow .2s var(--ease);}
.search:focus-within{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft);}
.search-icon{width:1rem;height:1rem;color:var(--text-muted);flex:none;}
#wiki-search{border:none;outline:none;background:none;font:inherit;font-size:.88rem;
  width:100%;color:var(--text);}
#wiki-search::placeholder{color:var(--text-muted);}
#wiki-search::-webkit-search-cancel-button{-webkit-appearance:none;}
.search-kbd{font-family:var(--mono);font-size:.65rem;color:var(--text-muted);
  border:1px solid var(--border);padding:1px .35rem;border-radius:3px;flex:none;
  background:var(--bg-alt);}
.search-results{margin:0 .75rem .5rem;max-height:calc(100vh - 180px);overflow-y:auto;flex:1;
  scrollbar-width:thin;scrollbar-color:var(--gray-300) transparent;}
.search-results::-webkit-scrollbar{width:4px;}
.search-results::-webkit-scrollbar-thumb{background:var(--gray-300);border-radius:2px;}
.search-results[hidden]{display:none;}
.sr-item{display:flex;flex-direction:column;gap:.12rem;padding:.6rem .75rem;
  border-left:2px solid transparent;border-radius:0 4px 4px 0;
  transition:background .15s,border-color .15s;}
.sr-item:hover,.sr-item:focus{background:var(--bg-alt);border-left-color:var(--accent);outline:none;}
.sr-title{font-size:.85rem;font-weight:600;color:var(--gray-900);display:flex;
  align-items:center;gap:.4rem;line-height:1.3;}
.sr-tag{font-size:.58rem;text-transform:uppercase;letter-spacing:.1em;
  color:var(--text-muted);border:1px solid var(--border);padding:0 .3rem;
  border-radius:3px;font-weight:500;background:var(--bg-alt);}
.sr-sub{font-size:.74rem;color:var(--text-muted);}
.sr-empty{padding:.75rem;font-size:.85rem;color:var(--text-muted);}

/* Tree nav */
.nav{display:flex;flex-direction:column;padding:.25rem .75rem 1rem;gap:0;flex:1;overflow-y:auto;
  scrollbar-width:thin;scrollbar-color:var(--gray-300) transparent;}
.nav::-webkit-scrollbar{width:4px;}
.nav::-webkit-scrollbar-thumb{background:var(--gray-300);border-radius:2px;}
.nav[hidden]{display:none;}
.nav-domain{font-size:.6rem;text-transform:uppercase;letter-spacing:.18em;
  color:var(--text-muted);font-weight:600;padding:1.1rem .75rem .35rem;margin-top:.1rem;
  font-family:var(--font);}
.nav-domain:first-of-type{margin-top:0;}
.nav-icon{width:1.05rem;height:1.05rem;color:var(--text-muted);flex:none;}
.tree-link{display:flex;align-items:center;gap:.7rem;padding:.55rem .75rem;
  font-size:.88rem;color:var(--gray-700);border-left:2px solid transparent;
  border-radius:0 5px 5px 0;transition:background .15s,color .15s,border-color .15s;}
.tree-link:hover{background:var(--bg-alt);color:var(--text);border-left-color:var(--gray-300);}
.tree-link.active{color:var(--accent);font-weight:600;border-left-color:var(--accent);background:var(--accent-soft);}
.tree-node{border:none;}
.tree-node>summary{display:flex;align-items:center;justify-content:space-between;
  gap:.5rem;padding:.55rem .75rem;font-size:.88rem;color:var(--gray-700);cursor:pointer;
  list-style:none;border-left:2px solid transparent;border-radius:0 5px 5px 0;
  transition:background .15s,color .15s,border-color .15s;}
.tree-node>summary::-webkit-details-marker{display:none;}
.tree-node>summary::marker{content:"";}
.tree-node>summary:hover{background:var(--bg-alt);color:var(--text);border-left-color:var(--gray-300);}
.tree-top-label{display:flex;align-items:center;gap:.7rem;min-width:0;}
.tree-top-label>span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.tree-top.active{color:var(--accent);font-weight:600;}
.chev{color:var(--text-muted);transition:transform .2s var(--ease);flex:none;}
.tree-node[open]>summary .chev{transform:rotate(90deg);}
.tree-children{list-style:none;margin:0 0 .3rem;padding:.05rem 0;}
.tree-sub{display:block;padding:.35rem .75rem .35rem 2rem;font-size:.81rem;
  color:var(--text-muted);border-left:2px solid var(--border);margin-left:1.15rem;
  transition:background .15s,color .15s,border-color .15s;}
.tree-sub:hover{color:var(--accent);border-left-color:var(--accent);background:var(--accent-soft);}
.sidebar-foot{padding:1rem 1.5rem;border-top:1px solid var(--border);
  font-size:.68rem;color:var(--text-muted);letter-spacing:.05em;}

/* Main */
.main-wrap{flex:1;min-width:0;display:flex;flex-direction:column;}
.topbar{display:none;align-items:center;gap:.75rem;padding:.75rem 1rem;
  border-bottom:1px solid var(--border);position:sticky;top:0;background:var(--bg-warm);z-index:20;}
.menu-toggle{background:none;border:1px solid var(--border);padding:.4rem;
  cursor:pointer;display:flex;color:var(--text);border-radius:5px;}
.topbar-title{font-weight:600;font-size:.9rem;font-family:var(--display);}
.content{max-width:var(--content-max);width:100%;margin:0 auto;
  padding:3.5rem 3rem 5rem;}

/* Doc header */
.eyebrow{display:inline-flex;align-items:center;gap:.5rem;font-size:.68rem;
  text-transform:uppercase;letter-spacing:.2em;color:var(--text-muted);
  margin-bottom:1.25rem;font-weight:600;}
.eyebrow .icon{color:var(--accent);}
.doc-header h1,.hero h1{font-size:2.8rem;line-height:1.05;font-weight:700;
  letter-spacing:-.025em;margin:0 0 .75rem;font-family:var(--display);
  font-optical-sizing:auto;}
.lede{font-size:1.1rem;color:var(--gray-700);max-width:60ch;margin:0 0 1.75rem;
  line-height:1.65;font-weight:400;}
.doc-meta{display:flex;flex-wrap:wrap;gap:1.25rem;padding:1rem 0;
  border-top:1px solid var(--border);border-bottom:1px solid var(--border);
  font-size:.8rem;color:var(--text-muted);}
.doc-meta span{display:inline-flex;align-items:center;gap:.4rem;}
.doc-meta span .icon{color:var(--accent);opacity:.7;}
.doc-meta code{background:none;border:none;padding:0;color:var(--gray-700);font-size:.78rem;}

/* On-page toc */
.page-toc{margin:2rem 0;background:var(--bg-alt);border:1px solid var(--border);
  border-radius:8px;padding:1.25rem 1.5rem;box-shadow:var(--shadow-sm);}
.toc-label{display:inline-flex;align-items:center;gap:.5rem;font-size:.68rem;
  text-transform:uppercase;letter-spacing:.18em;color:var(--text-muted);
  font-weight:600;}
.toc-label .icon{color:var(--accent);}
.page-toc ul{list-style:none;margin:.75rem 0 0;padding:0;
  display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:.3rem;}
.page-toc a{font-size:.85rem;color:var(--gray-700);border-bottom:1px solid transparent;
  transition:color .15s,border-color .15s;padding:.2rem 0;}
.page-toc a:hover{color:var(--accent);border-bottom-color:var(--accent);}

/* Doc body */
.doc-body{margin-top:2.5rem;}
.doc-body h2{font-size:1.55rem;font-weight:700;letter-spacing:-.015em;
  margin:3.5rem 0 1rem;padding-top:2rem;border-top:1px solid var(--border);
  scroll-margin-top:1.5rem;font-family:var(--display);font-optical-sizing:auto;}
.doc-body h2:first-child{border-top:none;padding-top:0;margin-top:0;}
.h2-inner{display:inline-flex;align-items:center;gap:.65rem;}
.section-icon{width:1.3rem;height:1.3rem;color:var(--accent);}
.doc-body h3{font-size:1.1rem;font-weight:600;margin:2rem 0 .75rem;
  letter-spacing:-.01em;}
.doc-body p{max-width:68ch;}
.doc-body blockquote{margin:2rem 0;padding:1rem 1.5rem;background:var(--bg-alt);
  border-left:3px solid var(--accent);border-radius:0 6px 6px 0;
  color:var(--gray-700);font-size:.95rem;box-shadow:var(--shadow-sm);}
.doc-body blockquote p{margin:0;}
.doc-body ul{padding-left:1.25rem;}
.doc-body li{margin:.35rem 0;}
.doc-body a[href^="http"]{color:var(--text);border-bottom:1px solid var(--gray-300);
  transition:color .15s,border-color .15s;word-break:break-word;font-weight:500;}
.doc-body a[href^="http"]:hover{color:var(--accent);border-bottom-color:var(--accent);}

/* Tables */
.table-wrap{overflow-x:auto;margin:1.5rem 0;border:1px solid var(--border);
  border-radius:8px;box-shadow:var(--shadow-sm);}
table{width:100%;border-collapse:collapse;font-size:.88rem;}
thead th{background:var(--bg-alt);text-align:left;font-weight:600;
  text-transform:uppercase;letter-spacing:.08em;font-size:.66rem;
  color:var(--text-muted);padding:.85rem 1rem;border-bottom:1px solid var(--border-dark);
  white-space:nowrap;}
tbody td{padding:.8rem 1rem;border-bottom:1px solid var(--border);vertical-align:top;
  line-height:1.55;}
tbody tr:last-child td{border-bottom:none;}
tbody tr{transition:background .12s;}
tbody tr:hover{background:var(--bg-alt);}
tbody td:first-child{font-weight:600;color:var(--gray-900);min-width:180px;}
.badges{display:flex;flex-wrap:wrap;gap:.4rem;margin-top:.5rem;}
.badge{display:inline-flex;align-items:center;font-size:.6rem;font-weight:600;
  text-transform:uppercase;letter-spacing:.05em;padding:.18rem .55rem;
  border-radius:999px;border:1px solid transparent;white-space:nowrap;line-height:1.4;}
.badge-jur{background:var(--jur-bg);color:var(--jur-fg);border-color:var(--jur-bd);}
.badge-mandatory{background:var(--ok-bg);color:var(--ok-fg);border-color:var(--ok-bd);}
.badge-guidance{background:var(--info-bg);color:var(--info-fg);border-color:var(--info-bd);}
.badge-voluntary{background:var(--warn-bg);color:var(--warn-fg);border-color:var(--warn-bd);}

/* Home / hero */
.hero{padding:1rem 0 3rem;border-bottom:1px solid var(--border);margin-bottom:3rem;
  position:relative;}
.hero .eyebrow .icon{color:var(--accent);}
.hero h1{font-size:3.2rem;}
.hero-stats{display:flex;gap:3rem;margin-top:2.5rem;flex-wrap:wrap;}
.stat{display:flex;flex-direction:column;}
.stat-num{font-size:2.8rem;font-weight:300;line-height:1;letter-spacing:-.03em;
  font-family:var(--display);font-optical-sizing:auto;color:var(--text);}
.stat-label{font-size:.66rem;text-transform:uppercase;letter-spacing:.16em;
  color:var(--text-muted);margin-top:.5rem;font-weight:600;}
.section-title{font-size:1.25rem;font-weight:700;margin:0 0 1.25rem;
  font-family:var(--display);letter-spacing:-.01em;}
.topic-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));
  gap:1rem;margin-bottom:3.5rem;}
.topic-card{border:1px solid var(--border);padding:1.5rem;display:flex;
  flex-direction:column;gap:.6rem;transition:border-color .2s var(--ease),
  box-shadow .25s var(--ease),transform .25s var(--ease);background:var(--white);
  border-radius:8px;position:relative;overflow:hidden;}
.topic-card::before{content:"";position:absolute;top:0;left:0;right:0;height:2px;
  background:var(--accent);transform:scaleX(0);transform-origin:left;
  transition:transform .3s var(--ease);}
.topic-card:hover{border-color:var(--border-dark);
  box-shadow:var(--shadow-md);transform:translateY(-3px);}
.topic-card:hover::before{transform:scaleX(1);}
.card-top{display:flex;}.card-icon{width:1.6rem;height:1.6rem;color:var(--accent);}
.topic-card h3{font-size:1.05rem;font-weight:700;margin:.25rem 0 0;
  font-family:var(--display);letter-spacing:-.01em;}
.topic-card p{font-size:.86rem;color:var(--gray-700);margin:0;flex:1;line-height:1.55;}
.card-meta{display:flex;gap:1rem;font-size:.66rem;text-transform:uppercase;
  letter-spacing:.12em;color:var(--text-muted);padding-top:.6rem;
  border-top:1px solid var(--border);font-weight:600;}
.usage-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:1rem;}
.usage-card{border:1px solid var(--border);padding:1.5rem;background:var(--white);
  border-radius:8px;box-shadow:var(--shadow-sm);
  transition:box-shadow .2s var(--ease),transform .2s var(--ease);}
.usage-card:hover{box-shadow:var(--shadow-md);transform:translateY(-2px);}
.usage-head{display:flex;align-items:center;gap:.6rem;margin-bottom:.6rem;}
.usage-head h3{margin:0;font-size:.95rem;font-weight:700;font-family:var(--display);}
.usage-head .icon{width:1.25rem;height:1.25rem;color:var(--accent);}
.usage-card p{font-size:.86rem;color:var(--gray-700);margin:0;line-height:1.55;}
.horizon-callout{display:block;border:1px solid var(--accent);border-radius:8px;
  padding:1.5rem 1.75rem;margin:0 0 3rem;background:var(--surface,var(--white));
  box-shadow:var(--shadow-sm);position:relative;overflow:hidden;
  transition:box-shadow .2s var(--ease),transform .2s var(--ease);}
.horizon-callout:hover{box-shadow:var(--shadow-md);transform:translateY(-2px);}
.horizon-callout p{font-size:.9rem;color:var(--gray-700);margin:.2rem 0 .8rem;
  line-height:1.55;max-width:70ch;}
.horizon-cta{display:inline-flex;align-items:center;gap:.35rem;font-weight:600;
  font-size:.85rem;color:var(--accent);}
.horizon-cta .icon{width:1rem;height:1rem;}

.page-foot{margin-top:4rem;padding-top:1.5rem;border-top:1px solid var(--border);
  font-size:.78rem;color:var(--text-muted);line-height:1.6;}
.page-foot p{margin:.3rem 0;}
.page-foot a,.usage-card a{color:var(--text);border-bottom:1px solid var(--gray-300);
  transition:color .15s,border-color .15s;}
.page-foot a:hover,.usage-card a:hover{color:var(--accent);border-bottom-color:var(--accent);}

/* Staggered reveal */
@keyframes reveal{from{opacity:0;transform:translateY(8px);}
  to{opacity:1;transform:translateY(0);}}
.doc-header,.page-toc,.doc-body h2,.topic-card,.usage-card,
.hero,.section-title{animation:reveal .5s var(--ease) backwards;}
.doc-header{animation-delay:.05s;}
.page-toc{animation-delay:.12s;}
.doc-body h2:nth-child(1){animation-delay:.15s;}
.doc-body h2:nth-child(2){animation-delay:.2s;}
.doc-body h2:nth-child(3){animation-delay:.25s;}
.topic-card:nth-child(1){animation-delay:.05s;}
.topic-card:nth-child(2){animation-delay:.1s;}
.topic-card:nth-child(3){animation-delay:.15s;}
.topic-card:nth-child(4){animation-delay:.2s;}
.topic-card:nth-child(5){animation-delay:.25s;}
.topic-card:nth-child(6){animation-delay:.3s;}
.topic-card:nth-child(7){animation-delay:.35s;}
.topic-card:nth-child(8){animation-delay:.4s;}
.topic-card:nth-child(9){animation-delay:.45s;}
.topic-card:nth-child(10){animation-delay:.5s;}
.topic-card:nth-child(11){animation-delay:.55s;}
.topic-card:nth-child(12){animation-delay:.6s;}

/* Responsive */
@media(max-width:880px){
  .sidebar{position:fixed;left:0;top:0;transform:translateX(-100%);
    transition:transform .25s var(--ease);z-index:40;box-shadow:var(--shadow-lg);}
  body.nav-open .sidebar{transform:translateX(0);}
  .topbar{display:flex;}
  .content{padding:2rem 1.25rem 3rem;}
  .doc-header h1,.hero h1{font-size:2.2rem;}
  .hero h1{font-size:2.5rem;}
}

/* Dark mode (manual toggle; light is default) */
[data-theme="dark"]{
  --black:#f5f5f5;--white:#131313;
  --gray-100:#1a1a1a;--gray-200:#222;--gray-300:#2a2a2a;
  --gray-500:#8a8a8a;--gray-700:#c4c4c4;--gray-800:#d4d4d4;--gray-900:#f5f5f5;
  --accent:#4d94ff;--accent-soft:rgba(77,148,255,.12);--accent-glow:rgba(77,148,255,.2);
  --ok-bg:rgba(16,185,129,.16);--ok-fg:#4ade80;--ok-bd:rgba(16,185,129,.32);
  --info-bg:rgba(59,130,246,.16);--info-fg:#7cb0fb;--info-bd:rgba(59,130,246,.32);
  --warn-bg:rgba(245,158,11,.16);--warn-fg:#fbbf24;--warn-bd:rgba(245,158,11,.32);
  --jur-bg:rgba(255,255,255,.07);--jur-fg:#cbd5e1;--jur-bd:rgba(255,255,255,.14);
  --bg:#0d0d0d;--bg-alt:#161616;--bg-warm:#111;--border:#262626;--border-dark:#333;
  --text:#f5f5f5;--text-muted:#a3a3a3;
  --shadow-sm:0 1px 2px rgba(0,0,0,.3);
  --shadow-md:0 4px 16px rgba(0,0,0,.4),0 1px 4px rgba(0,0,0,.2);
  --shadow-lg:0 12px 48px rgba(0,0,0,.5),0 4px 16px rgba(0,0,0,.3);
}
[data-theme="dark"] .topic-card:hover{box-shadow:var(--shadow-md);}
[data-theme="dark"] .brand-logo{background:var(--white);}

@media print{
  .sidebar,.topbar,.page-toc,.menu-toggle,#scroll-progress{display:none!important;}
  .content{max-width:100%;padding:0;}
  .table-wrap{overflow:visible;box-shadow:none;border:1px solid #ccc;}
  tbody tr,.topic-card,.table-wrap{break-inside:avoid;}
  a[href^="http"]{border:none;}
  .topic-card,.usage-card,.page-toc{box-shadow:none;}
}
"""


# --- Client search (vanilla JS, no dependencies) -------------------------------
SCRIPT = r"""/* GENERATED by build_wiki.py — do not hand-edit. */
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
/* Theme toggle */
(function () {
  var btn = document.getElementById('theme-toggle');
  if (!btn) return;
  btn.addEventListener('click', function () {
    var cur = document.documentElement.getAttribute('data-theme') || 'light';
    var next = cur === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    try { localStorage.setItem('wiki-theme', next); } catch (e) {}
  });
})();
/* Scroll progress */
(function () {
  var bar = document.getElementById('scroll-progress');
  if (!bar) return;
  function update() {
    var h = document.documentElement.scrollHeight - window.innerHeight;
    bar.style.width = (h > 0 ? (window.scrollY / h * 100) : 0) + '%';
  }
  window.addEventListener('scroll', update, { passive: true });
  update();
})();
"""


if __name__ == "__main__":
    build()
