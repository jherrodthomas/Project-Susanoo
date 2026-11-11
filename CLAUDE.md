# Working on Project Susanoo

Project Susanoo is a simulation-first product-development demonstrator: a human-piloted, **unarmed** mechanized walker (SUS-M1), a dockable observation UAV (SUS-A1) and their integration (SUS-I1). Its method is Product Development as Code (PDaC): typed records in [`pdac/`](pdac/README.md), executable checks, generated views and recorded human decisions. The project lead is the safety authority.

## Before you finish any change

```bash
python3 tools/pdac/generate.py          # regenerate views after editing records
python3 tools/pdac/validate.py          # checks P1-P9
python3 tools/check_links.py
python3 -m unittest discover -s tools -p 'test_*.py'
python3 tools/wiki/build_wiki.py --out build/wiki
```

All must pass. CI (`.github/workflows/checks.yaml`) runs the same commands.

## Rules for assistants (AI-authored work)

1. **AI-drafted work is I0.** It is the author's own work for independence purposes and earns no review credit. Record it as `provenance: {author: "Claude (AI-drafted)", independence: I0, reviewed: false}`.
2. **Never accept, approve or close.** Do not write an `approval` record with `authority_type: real`, do not set a hazard to `closed`, a rating to `reviewed`, a requirement to `baselined` or a document to `approved`. Propose; the lead decides.
3. **Never weaken to pass.** Do not lower a severity, probability, risk level or failure-condition class, delete a hazard, or relax a check to clear a finding. Raise the finding instead.
4. **Keep the risk scales apart.** MIL-STD-882E ratings belong on hazards; ARP4761A classifications on failure conditions. Never convert one into the other.
5. **Do not invent.** No made-up measurements, thresholds, test results, reviews, signatures or standards clauses. Unknown values stay `TBD` with the open parameter named.
6. **No standards text.** Cite standards by number and clause; describe obligations in the project's own words.
7. **Generated means generated.** Never hand-edit between `BEGIN GENERATED` / `END GENERATED` markers or in a generated page; edit the records and run `generate.py`.
8. **Revisions move together.** A content change to a controlled document raises its revision in the document header and in `pdac/documents.yaml`.
9. **Scope.** The project is unarmed. Do not add weapon, targeting or offensive capabilities in any form.

## Independence levels (interim, until a System Safety Program Plan defines them)

| Level | Meaning |
|---|---|
| I0 | Author's own work, including all AI drafting and AI-run checklists |
| I1 | Review by another person |
| I2 | Review by a person from a different team or role than the author |
| I3 | Review by a person independent of the project's management and budget |

## Decisions for the lead

Ask the lead only what they alone can decide: risk acceptance, hazard severity, scope and operating limits, money or hardware, roles and independence, gate go/no-go. Make reversible technical choices yourself and say so. Each question stands on its own: plain words, what is at stake, two to four options with the recommendation first, and how hard it is to undo.

## Licensing

Code, schemas and records: Apache-2.0 ([LICENSE](LICENSE)). Documentation: CC BY 4.0 ([LICENSE-docs](LICENSE-docs)). New Python files start with `# SPDX-License-Identifier: Apache-2.0`.
