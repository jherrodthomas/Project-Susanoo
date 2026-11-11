# MIL-STD-882E controlled work products

Baseline: **MIL-STD-882E, 11 May 2012 (base edition)**. The standard is modeled as data in [`standards/mil-std-882e/model.yaml`](../../standards/mil-std-882e/model.yaml) and tailored for this project in [`standards/tailoring/mil-std-882e.yaml`](../../standards/tailoring/mil-std-882e.yaml).

| What | Where |
|---|---|
| Hazard Tracking System (Task 106), one record per hazard | [`safety/hazards/`](../hazards/) |
| Safety-significant software functions (4.4) | [`safety/software/`](../software/) |
| Test and demonstration events (event risk, Task 303) | [`safety/events/`](../events/) |
| Task work-product records | [`tasks/`](tasks/) |
| Templates | [`templates/`](templates/) |
| Generated HTS export | [`safety/generated/hts.csv`](../generated/hts.csv) |
| Procedures | [Wiki task handbook](../../docs/wiki/MIL-STD-882E-Handbook.md) |

Run `python -m tools.pdac.validate` and `python -m tools.pdac.report` (see [`tools/pdac/README.md`](../../tools/pdac/README.md)).

**Status:** Preliminary hazard list (Task 201) in work. Severities and probabilities are preliminary qualitative judgements on a concept with no selected hardware. No verified mitigation, risk acceptance, approval or certification is claimed. All authorities are simulated.
