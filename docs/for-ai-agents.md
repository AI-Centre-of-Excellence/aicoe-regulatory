---
domain: AI Agents
label: For AI agents
order: 1
---
# For AI agents - knowledge map and query contract

This page is written for AI agents. It describes the machine-readable data
available, the schema for every entry, and how to route a question to the
standards that apply.

## Machine-readable data files

All files are at the site root:

- [llms.txt](llms.txt) - the query contract. Read this first.
- [wiki-manifest.json](wiki-manifest.json) - the authoritative dataset. 550 entries across 23 topics
  and 12 domains. Each entry is one standard, law, or framework with routing
  metadata.
- [search-index.json](search-index.json) - flat full-text index used by the site search. Can be
  consumed programmatically for keyword lookups.
- [cross-refs.json](cross-refs.json) - cross-reference map of equivalent, related, and
  referenced standards across jurisdictions. 98 mappings covering equivalents,
  supersession chains, references, adoptions, and complementary frameworks.

## Entry schema

Every entry in `wiki-manifest.json` has these fields:

| Field | Type | Description |
|---|---|---|
| `document` | string | The standard or regulation name (exact match key) |
| `issuer` | string | The issuing body (e.g. NIST, ISO, W3C, MeitY) |
| `link` | URL | Official source URL - always the issuing body's canonical page |
| `url` | string | Anchor in this site (e.g. `cybersecurity.html#core-frameworks-standards`) |
| `section` | string | Which section of the topic page this appears under |
| `notes` | string | Short factual note (version, successor, access conditions) |
| `jurisdiction` | string | Where it has force (US, EU, UK, India, Global, International, etc.) |
| `legal_force` | string | One of: law, regulation, directive, binding-standard, guidance, framework, voluntary-standard, best-practice |
| `applies_to` | string | Free-text description of who/what it covers |
| `triggers` | array | Machine-readable tags for what brings it into scope (e.g. `processes-pii`, `federal-agency`, `cardholder-data`) |
| `tags` | array | Controlled keywords for topical filtering |
| `status` | string | One of: current, superseded, draft, proposed |
| `supersedes` | array | Document names this standard replaces (or null) |
| `superseded_by` | array | Document names that replace this standard (or null) |
| `equivalents` | array | Document names that are functionally equivalent in other frameworks (or null) |

## Cross-reference types

`cross-refs.json` maps relationships between standards. Each mapping has:

| Field | Type | Description |
|---|---|---|
| `from` | string | Source document name (matches `document` in manifest) |
| `to` | string | Target document name |
| `type` | string | One of: adoption, builds-on, companion, complementary, equivalent, extended-by, extends, implemented-by, implements, part-of, references, sector-specific, supersedes|
| `scope` | string | Explanation of the relationship and its scope/limits |
| `bidirectional` | boolean | Whether the relationship applies in both directions |

## How to route

1. Identify the jurisdiction (US, EU, UK, India, Global, International).
2. Identify the domain (cybersecurity, data protection, healthcare, etc.).
3. Filter `wiki-manifest.json` entries by `jurisdiction` and `section` or `tags`.
4. Filter by `legal_force` - law, regulation, directive, binding-standard are
   mandatory. Guidance, framework, voluntary-standard, best-practice are
   advisory.
5. Filter by `triggers` - machine-readable tags that describe what brings the
   standard into scope.
6. Prefer `status: current`. Check `superseded_by` for successor versions.
7. Use `equivalents` to find the same standard in another jurisdiction.
8. Consult `cross-refs.json` for detailed relationship descriptions.
9. Always read the `link` for the authoritative text - do not rely on this
   index for wording. This index contains factual metadata only; it does not
   reproduce the text of any standard.

## Example queries

**Which cybersecurity standards apply to a US federal cloud provider?**

Filter: jurisdiction=US, tags includes cybersecurity, triggers includes federal-agency or cloud-service.
Returns: NIST CSF 2.0, SP 800-53 Rev 5, SP 800-171 Rev 3, FedRAMP, FISMA, Section 508.

**Which data protection law applies to processing EU residents' data in India?**

Filter: jurisdiction=EU or India, triggers includes processes-pii.
Check equivalents: GDPR equivalent to DPDP Act (India).
Returns: GDPR (for EU data), DPDP Act (for India data), cross-refs mapping.

**Which accessibility standards must a UK public-sector website meet?**

Filter: jurisdiction=UK, triggers includes public-sector-website.
Returns: UK PSB Accessibility Regulations 2018, which references WCAG 2.2 AA.
Check references in cross-refs.json: PSB Regs reference WCAG 2.2.

**What is the successor to ICH E6(R2)?**

Filter: document="ICH E6(R2)", check superseded_by.
Returns: ICH E6(R3).

## Limits

- This is a routing index, not the standards themselves. Always consult the
  `link` for authoritative text.
- Metadata is factual (jurisdiction, legal force, status) - not legal advice.
- The `applies_to` field is descriptive; use `triggers` for machine filtering.
- Cross-references are curated, not exhaustive. Gaps exist.
- Paid standards (ISO, IEC, BIS) link to catalogue pages, not full text.