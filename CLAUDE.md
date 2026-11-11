# Working on Project Susanoo

Susanoo is a simulation-first demonstrator: a human-piloted walker (SUS-M1) and a dockable PX4 observation UAV (SUS-A1), developed as Product Development as Code against **MIL-STD-882E (11 May 2012, base edition)**. The project lead is the safety authority. Nothing here is certified, and every authority is simulated until the lead says otherwise.

## Records are the source of truth

- The records are the YAML under `standards/`, `architecture/`, `safety/`, `requirements/`, `verification/`, `changes/`, `reviews/` and `decisions/`.
- The hand-written SysML files in `models/sysml/model/` are checked against those records. Files starting `// GENERATED` are not hand-written.
- Built from the records: pages under `docs/wiki/` marked `GENERATED`, `docs/wiki/images/sus-i1-*.svg` and `sysml-*.svg`, `safety/generated/`, and the generated `.sysml` files. **Never edit a generated file**; edit the record and regenerate.
- Before handing over any change, run:

  ```bash
  python -m tools.pdac.validate
  python -m tools.figures.fig_item
  python -m tools.pdac.report
  python -m unittest discover -s tools/pdac/tests -t .
  python -m unittest discover -s tools/figures/tests -t .
  python -m tools.sysml.gen_requirements
  python -m tools.sysml.check
  python -m tools.sysml.views
  python -m unittest discover -s tools/sysml/tests -t .
  tools/sysml/pilot/validate.sh        # SysML v2 conformance; needs JDK 21 and zstandard
  ```

  CI runs the same commands with `--check` and fails on errors or stale output.
- After changing a figure, render it and look at it before handing over.
- Never weaken a rule, raise a threshold, lower a severity or delete a hazard to make a check pass. If a rule is wrong, say so and ask.

## What the AI may and may not do

AI work is independence level **I0**: it is drafting, never review or acceptance.

| You may | You may not |
|---|---|
| Draft hazards, mitigations, requirements, SSFs, events, item-definition entries and analyses with status `open`, `draft`, `candidate` or `in-work` | Set a hazard to `verified`, `accepted` or `closed`; set a task record to `approved`; set a requirement to `baselined`; set any approval to `approved` |
| Propose severity, probability, SCC and target risk, with the rationale marked preliminary | Add or edit an entry under `acceptances`, or a `review_id` |
| Write a review record as a reviewer with `human: false, independence: I0` and outcome `in-progress` or `returned` | Write a review record with a human reviewer, or with outcome `accepted` |
| Record the lead's answer to a decision, quoting it, and apply it | Answer a `decider: lead` decision, or move one to `answered` without the lead's words |
| Decide `decider: claude` questions (reversible technical choices), apply them and record them as `applied` with `by: claude` | Freeze a baseline, tick a gate pass, or mark simulation results as verification evidence |

Rule R13 enforces the acceptance rows: only a review record with a named human reviewer in the right role accepts anything. CI passing, tests passing, a file existing or an AI review never do.

## Decisions for the lead

Every question for the lead lives in [`decisions/register.yaml`](decisions/register.yaml); the [Decision Inbox](docs/wiki/Decision-Inbox.md) page is generated from it.

1. **Sort before asking.** Ask the lead only what they alone can decide: risk acceptance and authorities, hazard scope and severity basis, architecture baselines, money and hardware, roles and independence, repository settings, and gate go/no-go. A reversible technical choice gets `decider: claude`: take the recommendation, apply it and record it. A task is not a decision.
2. **Every question stands on its own.** Never send a bare ID. An entry has:
   - the question in plain words;
   - context with the deciding fact in bold;
   - two to four options, each saying what it does and what it costs, with the recommendation first;
   - how hard it is to undo, what it blocks, and its sources.
3. **About ten open at a time.** Keep the rest `queued`, and open the next ones when a batch is answered.
4. **At the start of a session,** check the register for answered entries that are not yet applied, and apply them before asking anything new.
5. **In chat,** name a decision by its question, not its ID. Ask in chat only when blocked right now: multiple choice, with the recommendation first.
