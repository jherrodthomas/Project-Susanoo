# SUS-I1 SysML v2 model

Textual SysML v2 model of the integrated walker and UAV. It follows LionDriver's approach: the records stay the source of truth, and the model is checked against them on every pull request.

| File | Source | Content |
|---|---|---|
| `model/SusanooLibrary.sysml` | hand-written | Element, interface and requirement metadata; MIL-STD-882E risk-level and software-control-category vocabulary |
| `model/Functions.sysml` | hand-written | Functions F-01..F-09 as actions |
| `model/Architecture.sysml` | hand-written | The context: external elements, the SUS-I1 part tree, and every interface as a connection |
| `model/Requirements.sysml` | generated from `requirements/SYS-*.yaml` | Requirements with their statement, record and hazards |
| `model/Satisfaction.sysml` | generated from `allocated_to` | `satisfy` relations |

Hand-written files were first scaffolded from `architecture/item-definition.yaml`, then edited by hand. The item definition is still the record. When the two differ, `tools/sysml/check.py` fails and names the field.

## Commands

```bash
python -m tools.sysml.gen_requirements     # regenerate Requirements.sysml and Satisfaction.sysml
python -m tools.sysml.check                # model vs records: M1 M2 M4 M9 R1 R2 R3
python -m tools.sysml.views                # V-02 hierarchy, V-07 satisfaction, V-08 N2 + docs/wiki/SysML-Model.md
python -m unittest discover -s tools/sysml/tests -t .
tools/sysml/pilot/validate.sh              # SysML v2 conformance with the OMG pilot implementation (JDK 21, zstandard)
```

| Rule | Check |
|---|---|
| M1 | Each item-definition element is a part inside SUS-I1, with the same parent, name, kind, safety role, status and decision |
| M2 | Each external element is a part of the context outside SUS-I1, with the same name and assumption |
| M4 | Each interface is a connection with the same ends, direction, kinds, exchange, hazards and status |
| M9 | Each function is an action, performed by exactly the item-definition performers |
| R1 | The generated requirement files are current |
| R2 | Each `satisfy` ends inside SUS-I1 and matches the requirement's `allocated_to` |
| R3 | Each safety-significant requirement names at least one hazard, and every named hazard exists |

The reader, `tools/sysml/model.py`, accepts only the subset of SysML the model uses, and stops with the file and line number at anything else. The OMG pilot implementation, pinned with its SHA-256 in `tools/sysml/pilot/fetch_pilot.py`, checks that the model is valid SysML v2. Passing these checks is not a review.

**Not yet modelled:** CONOPS modes as a state machine, verification cases and the VCRM, and an explorer page. These follow the port plan.
