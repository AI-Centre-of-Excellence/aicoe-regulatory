# Repository Guidelines

## Project Overview

`aicoe-regulatory` is a public, docs-first regulatory knowledge base for the AI Centre of Excellence. It catalogues authoritative regulations, standards, frameworks, and guidance across regulated domains. The same source content is published as a static human-readable website and as machine-readable indexes for AI agents.

Do not place secrets, personal data, client material, or unpublished drafts in tracked files. Local-only material belongs under `private/`, which is gitignored and must never be committed or deployed.

## Architecture & Data Flow

```text
docs/*.md ───────────────┐
meta/<slug>.json ────────┼─> wiki/build_wiki.py ─> wiki/*.html
meta/cross-refs.json ────┤                         wiki/index.html
assets/* ────────────────┘                         wiki/regulatory-horizon.html
                                                   wiki/wiki-manifest.json
                                                   wiki/search-index.json
                                                   wiki/cross-refs.json
                                                   wiki/llms.txt, styles.css, wiki.js
```

- `docs/*.md` is the source of truth for published prose and standards tables.
- `meta/*.json` supplies routing and regulatory metadata; `document` keys bind to table-row names by exact text match.
- `meta/cross-refs.json` models relationships between standards.
- `wiki/build_wiki.py` parses Markdown, merges metadata, injects badges and stable anchors, builds navigation/search, and emits the complete static site.
- `wiki/` is generated and deployed, but its files must not be hand-edited. Rebuild and commit regenerated artefacts after source changes.
- The generated Regulatory Horizon page is derived from metadata statuses, supersession fields, and future effective/enforcement dates rather than from a Markdown topic.
- `private/audit.py`, when present locally, validates the content graph and maintains upstream-source watch state under `private/watch/`. All of `private/` is local-only.

The implementation is deliberately simple: synchronous, file-oriented Python; plain dictionaries/lists as data models; vanilla browser JavaScript; no service layer, database, dependency-injection container, or application state framework.

## Key Directories

- `docs/` — one published topic per kebab-case Markdown file; `docs/README.md` is the hand-maintained topic index.
- `meta/` — one `<slug>.json` file per topic plus `cross-refs.json`.
- `wiki/` — generated deployable HTML, CSS, JavaScript, indexes, manifest, and AI query contract.
- `assets/` — source static assets copied into `wiki/` during builds.
- `private/` — gitignored audit tooling, snapshots, diffs, and internal material; never publish.

## Development Commands

Run commands from the repository root unless noted otherwise.

```bash
# Install the sole required build dependency; no dependency manifest is provided.
python3 -m pip install markdown

# Regenerate all deployable files after changing docs/, meta/, assets/, or the generator.
python3 wiki/build_wiki.py

# Local-only QA, if private/audit.py is available.
python3 private/audit.py check
python3 private/audit.py fix
python3 private/audit.py stale-links --timeout 10
python3 private/audit.py watch --slug air-quality --timeout 15
python3 private/audit.py history --slug air-quality --limit 20
```

`audit.py fix` mutates known-fixable source data, rebuilds the wiki, and re-checks it; inspect the reported fixes before retaining them. `stale-links` and `watch` make network requests. `watch` accepts `--json`, `--limit`, and `--no-browser`.

There is no repository-defined dev server, package-manager script, lint command, or Vercel build command. Vercel serves `wiki/` directly according to `vercel.json`.

## Code Conventions & Common Patterns

### Content and metadata

- Topic filenames are kebab-case: `docs/data-protection-privacy.md` and `meta/data-protection-privacy.json`.
- Topic front matter uses `domain`, `label`, and `order`:

  ```yaml
  ---
  domain: Environment & Air Quality
  label: Air quality
  order: 1
  ---
  ```

- Use one `#` title, a short introductory paragraph, then `##` sections.
- Standards tables use exactly `Document | Issuer | Link | Notes`; put the issuer's canonical URL directly in the Link cell.
- Primary sources only. Cite the issuing body for regulatory claims. Note paid catalogue pages and confirmed bot-blocked canonical links honestly.
- Keep one row per document. Document names are identifiers: metadata entries and cross-reference `from`/`to` values must match the Markdown table text exactly, including punctuation and case.
- Metadata entries normally include `document`, `jurisdiction`, `legal_force`, `applies_to`, `tags`, `status`, `supersedes`, `superseded_by`, `equivalents`, and `triggers`.
- Cross-reference mappings use `from`, `to`, `type`, `scope`, and `bidirectional`. Directional relationships such as `supersedes`, `implements`, `extends`, `part-of`, and `references` must use `bidirectional: false`.
- When adding a topic, add `docs/<slug>.md`, `meta/<slug>.json`, and a link in `docs/README.md`; update `DOMAIN_ORDER` in `wiki/build_wiki.py` only when a new domain needs explicit placement.

### Python and browser code

- Follow existing Python patterns: `from __future__ import annotations`, `pathlib.Path`, module-level constants, small typed functions, and UTF-8 JSON/text I/O.
- Resolve repository paths from `__file__`; do not depend on the caller's current directory inside scripts.
- Keep the build deterministic and synchronous. Let build failures surface rather than producing partial fallback output.
- Preserve audit exit semantics: `0` clean/success, `1` reported issues, `2` unexpected/build error.
- Client code is dependency-free vanilla JavaScript generated from the `SCRIPT` constant in `wiki/build_wiki.py`. It uses IIFEs, lazy `fetch(...).then(...).catch(...)`, escaped rendered text, and `localStorage` only for theme preference.
- Change generated CSS/JavaScript in `wiki/build_wiki.py`, not in `wiki/styles.css` or `wiki/wiki.js`.

## Important Files

- `README.md` — project purpose and top-level workflow.
- `docs/README.md` — complete human-maintained domain/topic index.
- `CLAUDE.md` — existing public-repository and generated-site rules.
- `wiki/build_wiki.py` — sole build entry point; contains parsing, rendering, styles, and client script.
- `meta/cross-refs.json` — cross-standard relationship graph.
- `wiki/wiki-manifest.json` — generated structured catalogue for agents.
- `wiki/search-index.json` — generated client-side page/section/document search data.
- `wiki/llms.txt` — generated AI-agent query contract.
- `vercel.json` — static deployment config: no framework/build/install command, output directory `wiki`, clean URLs enabled.
- `private/audit.py` — optional local-only validator, fixer, link checker, and change monitor.

## Runtime/Tooling Preferences

- Use Python 3; no exact Python version is pinned.
- The build requires the third-party `markdown` package. There is no `requirements.txt`, `pyproject.toml`, or lockfile.
- No Node.js or Bun runtime is required. There is no `package.json`, bundler, or frontend framework.
- `private/audit.py watch` can optionally use `curl_cffi` and Playwright/Chromium for WAF or JavaScript challenges; it degrades when optional tiers are unavailable.
- Deployment is a static Vercel project. `vercel.json` points directly at the committed `wiki/` output.

## Testing & QA

There is no conventional automated test suite, test framework, linter, formatter, coverage configuration, pre-commit setup, or CI workflow. Do not claim test coverage that does not exist.

For every content, metadata, or generator change:

1. Run `python3 wiki/build_wiki.py`.
2. If the local private tool exists, run `python3 private/audit.py check`; treat warnings as failures because its exit code is non-zero for errors or warnings.
3. Verify the affected generated page plus `wiki/wiki-manifest.json` and `wiki/search-index.json` contain the intended change.
4. For changed source URLs, run a targeted `stale-links` or `watch --slug <slug>` check. A bot-blocked response is not automatically a dead link; verify canonical URLs before replacing them.
5. Commit source changes and all corresponding generated `wiki/` changes together. Never commit `private/` watch state.
