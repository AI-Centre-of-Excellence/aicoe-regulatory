# Regulatory docs

Source of truth for the site. One Markdown file per topic (kebab-case), each with
YAML front matter (`domain`, `label`, `order`) that places it in the taxonomy.
Run `python3 wiki/build_wiki.py` after any change to regenerate the output.

> Browse the rendered site (tree navigator + search) under [`wiki/`](../wiki/).
> Live: https://aicoe-regulatory.vercel.app

## Domains & topics

**Life Sciences**
- [Clinical research](clinical-research.md) — ICH, ethics, FDA/EMA/MHRA/WHO, pharmacovigilance, CDISC, GxP/CSV, reporting, industry.
- [Healthcare](healthcare.md) — health data privacy, interoperability (HL7 FHIR/DICOM), terminologies (ICD/SNOMED/LOINC), medical devices & SaMD.
- [Medical devices](medical-devices.md) — EU MDR/IVDR, FDA pathways (510(k)/PMA/De Novo), QMS (ISO 13485/QMSR), safety (IEC 60601/62304), risk management (ISO 14971), SaMD.

**Financial Services**
- [Financial services](financial-services.md) — Basel/prudential, securities & markets, AML/CFT/sanctions, payments, accounting & disclosure.
- [Digital assets & crypto](digital-assets-crypto.md) — MiCA, crypto travel rule, FATF VASP guidance, BCBS crypto prudential, IOSCO, US FinCEN/SEC.
- [Insurance](insurance.md) — Solvency II / Solvency UK, IAIS ICPs / ComFrame / ICS, NAIC model laws, IRDAI.

**Manufacturing**
- [Manufacturing](manufacturing.md) — quality (ISO 9001/IATF/AS9100), product safety (GPSR/RoHS/REACH), industrial & functional safety, environmental/energy.

**Automotive & Mobility**
- [Automotive & mobility](automotive-mobility.md) — functional safety (ISO 26262), SOTIF (ISO 21448), vehicle cyber (ISO/SAE 21434, UN R155/R156), automation (SAE J3016), EU GSR.

**Aerospace & Defense**
- [Aerospace & defense](aerospace-defense.md) — airworthiness & certification, aviation safety, aerospace quality, space systems, export control & defense.

**Energy & Utilities**
- [Energy & utilities](energy-utilities.md) — NERC CIP & reliability standards, FERC, IEC 61850/62351, EU electricity market & cybersecurity network code.

**Hi-Tech / Technology**
- [Data protection & privacy](data-protection-privacy.md) — GDPR/UK GDPR, US state laws, international principles, ISO 27701 / NIST Privacy.
- [Cybersecurity](cybersecurity.md) — NIST CSF/800-series, ISO 27001, CIS, FISMA/FedRAMP/CISA, NIS2/CRA/DORA, SOC 2.
- [AI governance](ai-governance.md) — EU AI Act, NIST AI RMF, ISO/IEC 42001, OECD/UNESCO/G7/CoE, sector cross-refs.
- [Accessibility](accessibility.md) — WCAG 2.1/2.2, EN 301 549, European Accessibility Act, Section 508, ADA Title II, WAI-ARIA.
- [Software engineering](software-engineering.md) — lifecycle (ISO/IEC/IEEE 12207/15288), quality (SQuaRE 25010), testing (29119), requirements & documentation (IEEE).
- [Digital markets & platforms](digital-markets-platforms.md) — EU Digital Services Act & Digital Markets Act, P2B Regulation, UK DMCC Act.
- [Online safety & child protection](online-safety.md) — UK Online Safety Act & Children's Code, EU CSAM/AVMSD/BIK+, Australia Online Safety Act.
- [Telecommunications](telecommunications.md) — EU EECC & net neutrality, US Communications Act/FCC, ITU (Radio Regs, ITU-T), 3GPP.

**Logistics & Supply Chain**
- [Logistics & supply chain](logistics-supply-chain.md) — trade & customs, dangerous goods & transport, due diligence, traceability.

**Food & Agriculture**
- [Food safety & agriculture](food-agriculture.md) — Codex/HACCP, ISO 22000 & FSSC 22000, EU General Food Law, EFSA, US FSMA, FSSAI.

**Consumer Protection**
- [Consumer protection & advertising](consumer-protection.md) — EU UCPD/CRD/Product Liability, US FTC Act & advertising guides, UK CAP/BCAP & consumer law.

**Sustainability & ESG**
- [Sustainability & ESG](sustainability-esg.md) — reporting frameworks (GRI/ISSB/TCFD), EU regulation (CSRD/ESRS/Taxonomy/SFDR), GHG accounting, UN principles.

**Environment & Air Quality**
- [Air quality](air-quality.md) — WHO 2021 guidelines, EU Ambient Air Quality Directive (2024/2881), US Clean Air Act & NAAQS, UK air quality regs & PM2.5 targets, ISO 16000 indoor air.

**AI Agents**
- [For AI agents](for-ai-agents.md) — machine-readable knowledge map and query contract (manifest, cross-refs, routing) for programmatic use.

All links point to the issuing body's official source and were verified 2026-07-07.
Primary sources only, one row per document.
