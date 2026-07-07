# aicoe-regulatory

Regulatory content and reference material for the AI Centre of Excellence (AICOE).

## What this is

A docs-first repository for regulatory guidance, frameworks, and reference notes
relevant to AICOE's work in regulated domains (clinical / pharmaceutical, data
governance, AI compliance).

## Layout

| Path | What it holds |
|------|---------------|
| `docs/` | Source of truth: published regulatory notes and references (Markdown). |
| `wiki/` | Generated HTML wiki (AICOE design system) built from `docs/`. |
| `private/` | Internal-only material. Gitignored — never pushed. |

## The wiki is generated

`wiki/*.html`, `wiki/styles.css`, and `wiki/wiki-manifest.json` are **build
artifacts** produced by `wiki/build_wiki.py`. Do not hand-edit them. Change the
Markdown in `docs/` (or the generator), then rebuild:

```bash
python3 wiki/build_wiki.py
```

The wiki renders the same content two ways: a sidebar-navigated HTML site for
people, and `wiki/wiki-manifest.json` (a structured index of pages, sections,
and link counts with stable anchor IDs) for AI agents.

## Conventions

- Markdown-first. One topic per file, kebab-case filenames. `docs/` is the source of truth.
- Cite sources for any regulatory claim; link to the authoritative text.
- Add a topic by writing `docs/<topic>.md`, then run `python3 wiki/build_wiki.py`.
- Internal / draft material goes under `private/` (gitignored).

## Related

- Org: [AI-Centre-of-Excellence](https://github.com/AI-Centre-of-Excellence)
- Contact: hi@aicoe.io
