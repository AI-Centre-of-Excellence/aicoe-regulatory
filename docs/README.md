# Regulatory docs

Source of truth for the wiki. One Markdown file per topic (kebab-case), each with
YAML front matter (`domain`, `label`, `order`) that places it in the taxonomy.
Run `python3 wiki/build_wiki.py` after any change to regenerate `wiki/`.

> Browse the rendered wiki (tree navigator + search) under [`wiki/`](../wiki/).
> Live: https://aicoe-regulatory.vercel.app

## Domains & topics

**Life Sciences**
- [Clinical research](clinical-research.md) — ICH, ethics, FDA/EMA/MHRA/WHO, pharmacovigilance, CDISC, GxP/CSV, reporting, industry.
- [Healthcare](healthcare.md) — health data privacy, interoperability (HL7 FHIR/DICOM), terminologies (ICD/SNOMED/LOINC), medical devices & SaMD.

**Financial Services**
- [Financial services](financial-services.md) — Basel/prudential, securities & markets, AML/CFT/sanctions, payments, accounting & disclosure.

**Manufacturing**
- [Manufacturing](manufacturing.md) — quality (ISO 9001/IATF/AS9100), product safety (GPSR/RoHS/REACH), industrial & functional safety, environmental/energy.

**Aerospace & Defense**
- [Aerospace & defense](aerospace-defense.md) — airworthiness & certification, aviation safety, aerospace quality, space systems, export control & defense.

**Hi-Tech / Technology**
- [Data protection & privacy](data-protection-privacy.md) — GDPR/UK GDPR, US state laws, international principles, ISO 27701 / NIST Privacy.
- [Cybersecurity](cybersecurity.md) — NIST CSF/800-series, ISO 27001, CIS, FISMA/FedRAMP/CISA, NIS2/CRA/DORA, SOC 2.
- [AI governance](ai-governance.md) — EU AI Act, NIST AI RMF, ISO/IEC 42001, OECD/UNESCO/G7/CoE, sector cross-refs.

**Logistics & Supply Chain**
- [Logistics & supply chain](logistics-supply-chain.md) — trade & customs, dangerous goods & transport, due diligence, traceability.

**Sustainability & ESG**
- [Sustainability & ESG](sustainability-esg.md) — reporting frameworks (GRI/ISSB/TCFD), EU regulation (CSRD/ESRS/Taxonomy/SFDR), GHG accounting, UN principles.

All links point to the issuing body's official source and were verified 2026-07-07.
Primary sources only, one row per document.
