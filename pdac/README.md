# PDaC records

Product Development as Code (PDaC) keeps the product's objects in typed, version-controlled records that a program can check: product, variants, scenarios, components, interfaces, requirements, hazards, trade studies and, later, failure conditions, tests, evidence and approvals. The Markdown documents stay the pages people read and review. Where a document shows record data (the CONOPS trace table, the requirement list, the hazard list), that part is **generated from the records** and is never edited by hand.

The model behind it is described in [SUS-FW-005 PDaC traceability](../framework/traceability.md). This page describes what is implemented.

> A passing check means the records are consistent. It never means that anything has been reviewed, accepted or approved. Only a recorded human approval does that (check P6).

## Layout

| Path | Content |
|---|---|
| [`product.yaml`](product.yaml) | Product identity: variants SUS-M1, SUS-A1, SUS-I1, configuration, release, licences, program status |
| [`documents.yaml`](documents.yaml) | Register of controlled documents with ID and revision (check P8) |
| [`items/concept.yaml`](items/concept.yaml) | Actors (`ACT-`), operating modes (`MOD-`), scenarios (`SCN-`) from the CONOPS |
| [`items/architecture.yaml`](items/architecture.yaml) | Components (`SUS-M1-xxx`, `SUS-A1`, `SUS-GSE`), interfaces (`IF-`), trade studies (`TS-`) |
| [`items/requirements.yaml`](items/requirements.yaml) | System requirement candidates (`SYS-`) |
| [`items/hazards.yaml`](items/hazards.yaml) | Preliminary Hazard List (`HAZ-`), MIL-STD-882E ratings |
| [`schema/pdac.schema.json`](schema/pdac.schema.json) | JSON Schema (2020-12) for the product, file headers and every record kind |
| [`../tools/pdac/`](../tools/pdac/) | `validate.py` (checks), `generate.py` (generated views), `pdaclib.py`, tests |

Defined in the schema but with no records yet: `failure-condition` (`FC-`, ARP4761A, for the SUS-A1 Functional Hazard Assessment) and `approval` (`APR-`).

## Record format

Each file under `items/` (and `documents.yaml`) is a mapping with a header and a list of records:

```yaml
file: hazards                 # name of the file
owner: safety-lead            # role that owns the content
revision: "0.1"
provenance: {author: "...", independence: I0, date: "2026-11-11", reviewed: false}
items:
  - id: HAZ-001
    kind: hazard
    title: "..."
    status: open
    applicability: [SUS-M1, SUS-I1]
    source: SUS-CONOPS-001    # controlled document it comes from
    ...                       # fields of the kind, see the schema
```

Every record has `id`, `kind`, `title`, `status` and `applicability`. IDs are never reused: a withdrawn requirement becomes `status: deleted`, not a gap that a later requirement fills. `independence` is the reviewer independence of the content: I0 is the author's own work, including everything an AI assistant drafts; I1 to I3 are reviews of increasing independence (defined in [CLAUDE.md](../CLAUDE.md) until a safety plan defines them).

## Checks

`python3 tools/pdac/validate.py` runs every check; CI runs it on every pull request.

| Check | Rule |
|---|---|
| P1 | The product, every file header and every record match the schema of their kind; no unknown fields |
| P2 | IDs are unique across all records |
| P3 | Every reference resolves to a record of an allowed kind (for example `mitigated_by` names requirements, `source` names a registered document) |
| P4 | Links agree in both directions: `requirement.mitigates` ↔ `hazard.mitigated_by`; `failure-condition.related_hazards` ↔ `hazard.related_failure_conditions` |
| P5 | Risk scales stay apart: MIL-STD-882E severity, probability and risk level exist only on hazards, and the level must equal the 882E matrix value; ARP4761A classifications exist only on failure conditions, which must apply to SUS-A1 |
| P6 | Only recorded human approvals change acceptance: a closed hazard needs an `accept-risk` approval listing it, a residual rating and a reviewed rating; a baselined requirement needs a verification method and a `baseline` approval; a released release needs a real (not simulated) release approval |
| P7 | Applicability names declared variants; a requirement and the components it is allocated to, and a hazard and its components, share a variant |
| P8 | Registered documents exist and carry `**ID:** … · **Revision:** …` matching the register; every `SCN-`, `MOD-`, `SYS-`, `HAZ-`, `TS-`, `IF-`, `FC-`, `APR-` ID mentioned in any Markdown file exists as a record; every scenario and mode record is described in the CONOPS |
| P9 | Coverage: every scenario derives a hazard; every high or serious hazard has a candidate mitigation; every safety requirement mitigates a hazard; every component has a requirement |

## Generated views

`python3 tools/pdac/generate.py` rewrites them; `--check` (in CI) fails if one is stale.

| View | Where |
|---|---|
| Status line with record counts and a digest of the records | [README](../README.md#status), [wiki Home](../docs/wiki/Home.md) |
| Scenario → hazard → requirement trace | [CONOPS §9](../concept/CONOPS.md) |
| Requirement table | [Architecture](../concept/architecture.md) |
| Preliminary Hazard List page | [safety/preliminary-hazard-list.md](../safety/preliminary-hazard-list.md) |

## Changing a record

1. Edit the YAML. Keep IDs stable; add, do not renumber.
2. Run `python3 tools/pdac/generate.py`, then `python3 tools/pdac/validate.py`.
3. If a controlled document changes, raise its revision in the document and in `documents.yaml` together.
4. Commit records and regenerated views in the same change. The pull request states what was reviewed by whom; nothing in the records says *reviewed* or *approved* without a human approval record.

Not yet implemented, planned: evidence records with integrity hashes (SUS-FW-005 rule 6), change requests and change-impact flags (rule 5), test cases and results, the decision register.
