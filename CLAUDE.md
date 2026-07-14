# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this repo is

`aicoe-regulatory` is a **public, docs-first** repository holding regulatory
content and reference material for the AI Centre of Excellence — regulatory
guidance, frameworks, and notes for regulated domains (clinical/pharma, data
governance, AI compliance).

## Layout

- `docs/` — **source of truth**: published Markdown notes and references. One topic per file, kebab-case.
- `wiki/` — generated HTML site (AICOE design system). Build artifacts.
- `private/` — internal-only material. **Gitignored**; never committed or pushed.

## The site is generated

`wiki/*.html`, `wiki/styles.css`, and `wiki/wiki-manifest.json` are produced by
`wiki/build_wiki.py` from the Markdown in `docs/`. **Do not hand-edit them** —
edits are overwritten on the next build. To change the site, edit the Markdown
in `docs/` (or the generator), then run `python3 wiki/build_wiki.py` and commit
the regenerated `wiki/`. Adding a `docs/<topic>.md` auto-creates a page for
it. The generator only depends on the `markdown` package (tables/toc extensions).

## Rules

- This repo is **public** — do not put drafts, deal material, secrets, or
  personally identifying information in tracked files. Internal material goes
  under `private/`.
- Cite the authoritative source for any regulatory claim; link to the primary text.
- Markdown-first. Keep files focused and cross-link related notes.
