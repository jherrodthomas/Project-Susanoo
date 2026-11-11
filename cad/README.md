# Concept layouts (FreeCAD) — review and alignment

**ID:** SUS-CAD-001 · **Revision:** 0.11-draft · **Status:** Draft, not reviewed

*Changes in 0.11:* AI concept art generated from the CL-05 renders, filed separately and labelled (§2a, [`concept-art/`](concept-art/README.md)).

*Changes in 0.10:* photoreal Blender renders of the CL-05 reference layout (§2a).

*Changes in 0.9:* CL-05 UAV dock raised 0.45 m: docked rotors 1.09 m from the pilot's head, over the 1 m review flag.

*Changes in 0.8:* CL-05 heel spurs lengthened (0.68 m behind the ankle, 0.30 m wide): static margin 0.38 m standing and 0.35 m kneeling, above the 0.30 m review flag in every posture.

*Changes in 0.7:* CL-05 shoulder plates reshaped into exit steps for the side hatches (tread flush with the sill, non-slip strips, toe lip, grab rails); new metrics: shoulder-step height and step-to-ladder gap.

*Changes in 0.6:* CL-05 emergency exit: side-window hatches with internal release handles, a fold-out davit and rope ladder, shown deployed in a new emergency posture; new metrics: hatch sill, clear opening, escape-ladder clearance.

*Changes in 0.5:* CL-05 access aids: fold-down ladder (stowed standing, deployed kneeling) and grab handles at the front opening; new metrics: front-opening sill height, ladder treads and largest step rise.

*Changes in 0.4:* CL-05 kneel posture for ingress and egress: built, measured, rendered and drawn alongside the standing pose; new metric: arm ground clearance.

*Changes in 0.3:* CL-05 is the reference layout (chosen by the project lead) and its solids are now authored in build123d code-CAD: tapered lofted limbs, swept claws, hoses and roll bar, a pod shell with a chamfered chin, window frames and panel grooves; ground contacts come from the real foot solids.

*Changes in 0.2:* layouts CL-04 (armoured pod) and CL-05 (reverse-jointed pod) added; an eye-level view per layout; dimensioned A3 drawing sheets (§3, [`drawings/`](drawings/)).

> **Concept mockups, not designs.** Every layout below is built from primitive solids placed by placeholder parameters. Dimensions, masses and every metric are properties of that placeholder geometry. They exist so the team can look at the same picture, compare the trade-study alternatives side by side, and see early where an option makes a hazard worse. They select nothing: the trade studies (TS-001 to TS-004) are decided by the lead.

![Concept line-up: open-frame bipeds with the UAV docked on the back (CL-01), on the shoulder (CL-02) and on a separate ground station (CL-03), the armoured pod (CL-04) and the reverse-jointed pod (CL-05), each with a 1.75 m person for scale](renders/lineup.png)

## 1. What the layouts compare

Each layout (`CL-nn`) is one combination of trade-study alternatives. Locomotion is **bipedal** (TS-003, decided by the project lead). CL-01 to CL-03 share the same open-frame biped, the actuation hypothesis (centralized hydraulic, drawn as yellow cylinders) and the seated protected cockpit, so they differ only in where the UAV docks (TS-004). CL-04 is an armoured-pod restyle in the form language of the lead's reference image: an enclosed hull with the pilot at an arched front opening, shoulder plates, roll bar and plated legs. CL-05 takes its proportions from the lead's AI-generated Industrial Utility Walker: a tall pod with front and side windows, reverse-jointed legs and long claw arms. Neither reuses the source mesh or image; both are original parametric geometry. Standing and remote-pilot alternatives (TS-002) and electric actuation (TS-001) are not modelled yet.

What to look for in the review:

| Question | Where it shows | Records it informs |
|---|---|---|
| Can it stand without active balance? | Plan view: centre of gravity against the support polygon; static margin and tip angle | HAZ-006, HAZ-021, SYS-008, SYS-009 |
| How far does the pilot drop on egress? | Side view: cockpit floor height | HAZ-008, SYS-012 |
| How close are docked rotors to the pilot? | Dock view: shortest rotor-to-pilot distance | HAZ-011, HAZ-012, SYS-003 |
| How big is it next to a person? | Every view: the 1.75 m figure | HAZ-009 |

Metric definitions: *static margin* is the shortest horizontal distance from the centre of gravity to the edge of the support polygon (the convex hull of the ground contacts); *static tip angle* is the angle whose tangent is margin ÷ CG height; *placeholder mass* comes from solid volumes times the effective densities in [`params/common.yaml`](params/common.yaml). Values in red on the images are below 0.3 m static margin or 1.0 m rotor clearance, the project's provisional review flags. They are not requirements.

## 2a. Reference layout CL-05, photoreal renders

Rendered with Blender 5.3 (Cycles) by [`tools/cad/blender_render.py`](../tools/cad/blender_render.py) from exactly the meshes the metrics and drawing sheets use; only materials, daylight and camera are added. Concept renders for communication: placeholder geometry, not a design, and not AI-generated.

| | |
|---|---|
| ![CL-05 standing, front three-quarter view from eye height, with a 1.75 m person for scale](renders/blender/CL-05-hero.jpg) | ![CL-05 from the rear: power pack, raised UAV dock and roll bar](renders/blender/CL-05-rear.jpg) |
| ![CL-05 kneeling for egress with the fold-down ladder deployed and the claws stowed](renders/blender/CL-05-kneel.jpg) | ![CL-05 emergency exit: side hatch open, shoulder step and rope ladder deployed](renders/blender/CL-05-emergency.jpg) |

**AI concept art** made from these renders (Higgsfield, image-to-image) is kept apart in [`concept-art/`](concept-art/README.md), each image labelled with its source render and where it departs from the CAD. It is for communication, never for dimensions.

## 2. Layouts

<!-- BEGIN GENERATED: cad-concepts (tools/pdac/generate.py) -->
*Metrics from [`metrics.json`](metrics.json) (FreeCAD 1.1.3); ⚠ marks the provisional review flags of §1.*

| | CL-01 | CL-02 | CL-03 | CL-04 | CL-05 |
|---|---|---|---|---|---|
| Locomotion (TS-003) | bipedal | bipedal | bipedal | bipedal | bipedal |
| UAV dock (TS-004) | rear backpack dock | shoulder-mounted dock | separate portable station | rear backpack dock | rear backpack dock |
| Envelope L × W × H | 3.4 × 2.4 × 4.1 m | 3.4 × 2.4 × 4.2 m | 3.4 × 2.4 × 3.9 m | 3.4 × 2.5 × 3.9 m | 3.3 × 2.3 × 4.5 m |
| Overall height | 4.08 m | 4.20 m | 3.85 m | 3.94 m | 4.48 m |
| Pilot eye height | 3.54 m | 3.54 m | 3.54 m | 3.15 m | 3.62 m |
| Cockpit floor (egress drop) | 2.33 m | 2.33 m | 2.33 m | 1.94 m | 2.41 m |
| CG height | 2.63 m | 2.63 m | 2.63 m | 2.24 m | 2.72 m |
| Static margin | 0.14 m ⚠ | 0.14 m ⚠ | 0.14 m ⚠ | 0.23 m ⚠ | 0.38 m |
| Static tip angle | 3.1° | 3.2° | 3.1° | 5.7° | 7.9° |
| Rotor ↔ pilot (docked) | 0.79 m ⚠ | 0.63 m ⚠ | 3.14 m | 0.92 m ⚠ | 1.09 m |
| Rotor ↔ own structure (docked) | 0.22 m | 0.41 m | off-board | 0.26 m | 0.29 m |
| Placeholder mass | ~5.0 t | ~5.0 t | ~5.0 t | ~6.3 t | ~4.6 t |

### CL-01 · Biped, seated protected cockpit, rear backpack dock

Options: TS-001 centralized hydraulic; TS-002 seated protected cockpit; TS-003 bipedal; TS-004 rear backpack dock. Informs: HAZ-005, HAZ-006, HAZ-008, HAZ-011, HAZ-021, SYS-003, SYS-008, SYS-009, SYS-010, SYS-012. Parameters: [`params/CL-01.yaml`](params/CL-01.yaml).

- Common to every biped layout: the static margin is small and the CG is high above two feet, so standing still depends on active balance. Loss of actuation energy or a zero-torque stop means a fall unless SYS-008 holds posture (HAZ-005, HAZ-021).
- Common to every biped layout: the cockpit floor is above the head of a standing person, so egress and extraction (SYS-012) need a ladder, a lowered posture or a kneel mode.
- The rear dock sits above the cockpit roof line, so the docked rotors still come within the provisional 1 m flag of the pilot's head.

Drawing sheet: [SUS-CAD-001-CL-01](drawings/CL-01.svg) (A3, 1:50, dimensioned side, plan and front views).

![CL-01 front view from eye height](renders/CL-01-hero.png)

| | |
|---|---|
| ![CL-01 three-quarter view](renders/CL-01-iso.png) | ![CL-01 side elevation](renders/CL-01-side.png) |
| ![CL-01 plan view with support polygon and centre of gravity](renders/CL-01-top.png) | ![CL-01 UAV dock and rotor clearance to the pilot](renders/CL-01-dock.png) |

### CL-02 · Biped, seated protected cockpit, shoulder-mounted dock

Options: TS-001 centralized hydraulic; TS-002 seated protected cockpit; TS-003 bipedal; TS-004 shoulder-mounted dock. Informs: HAZ-006, HAZ-011, HAZ-012, SYS-003, SYS-006. Parameters: [`params/CL-02.yaml`](params/CL-02.yaml).

- The shoulder dock puts the docked rotors beside the cage at pilot head height, the closest of the three layouts: HAZ-011 and HAZ-012 dominate, and SYS-003 rotor inhibit plus a rotor guard would be needed if this option is kept.
- The UAV is light against the walker: the dock position changes the CG by millimetres, so TS-004 is decided by rotor clearance, access and approach geometry, not by stability.

Drawing sheet: [SUS-CAD-001-CL-02](drawings/CL-02.svg) (A3, 1:50, dimensioned side, plan and front views).

![CL-02 front view from eye height](renders/CL-02-hero.png)

| | |
|---|---|
| ![CL-02 three-quarter view](renders/CL-02-iso.png) | ![CL-02 side elevation](renders/CL-02-side.png) |
| ![CL-02 plan view with support polygon and centre of gravity](renders/CL-02-top.png) | ![CL-02 UAV dock and rotor clearance to the pilot](renders/CL-02-dock.png) |

### CL-03 · Biped, seated protected cockpit, separate portable station

Options: TS-001 centralized hydraulic; TS-002 seated protected cockpit; TS-003 bipedal; TS-004 separate portable station. Informs: HAZ-011, HAZ-013, HAZ-016, SYS-005, SYS-006, SYS-016. Parameters: [`params/CL-03.yaml`](params/CL-03.yaml).

- The off-board station keeps rotors metres from the pilot and removes dock-retention loads while walking (HAZ-013), at the cost of launching and recovering only where the station is.
- Nothing is mounted on top of the walker, so this is the lowest of the three bipeds and its hull top stays free for sensors or a beacon.

Drawing sheet: [SUS-CAD-001-CL-03](drawings/CL-03.svg) (A3, 1:50, dimensioned side, plan and front views).

![CL-03 front view from eye height](renders/CL-03-hero.png)

| | |
|---|---|
| ![CL-03 three-quarter view](renders/CL-03-iso.png) | ![CL-03 side elevation](renders/CL-03-side.png) |
| ![CL-03 plan view with support polygon and centre of gravity](renders/CL-03-top.png) | ![CL-03 UAV dock and rotor clearance to the pilot](renders/CL-03-dock.png) |

### CL-04 · Biped armoured pod, seated cockpit, rear dock

Options: TS-001 centralized hydraulic; TS-002 seated protected cockpit; TS-003 bipedal; TS-004 rear backpack dock. Informs: HAZ-006, HAZ-008, HAZ-009, HAZ-011, HAZ-017, SYS-010, SYS-012, SYS-017. Parameters: [`params/CL-04.yaml`](params/CL-04.yaml).

- Form language from the project lead's reference image: an enclosed armoured pod with the pilot visible at an arched front opening, heavy shoulder plates, roll bar and hunched, plated legs. The geometry is original and parametric.
- Lowest CG and lowest cockpit floor of the four layouts, and the best static margin of the bipeds, though still under the 0.3 m review flag: the shorter, more bent legs pull the mass down.
- The enclosed pod protects the pilot better in a fall or overturn (SYS-010) than an open cage, but the single front opening is the only way out: a forward fall blocks egress and extraction (HAZ-008, SYS-012), and a fire inside the pod (HAZ-017) has one exit. A second exit or a release panel is needed.
- The armour around the opening narrows the pilot's view down and to the sides, toward the feet and manipulators (HAZ-009).

Drawing sheet: [SUS-CAD-001-CL-04](drawings/CL-04.svg) (A3, 1:50, dimensioned side, plan and front views).

![CL-04 front view from eye height](renders/CL-04-hero.png)

| | |
|---|---|
| ![CL-04 three-quarter view](renders/CL-04-iso.png) | ![CL-04 side elevation](renders/CL-04-side.png) |
| ![CL-04 plan view with support polygon and centre of gravity](renders/CL-04-top.png) | ![CL-04 UAV dock and rotor clearance to the pilot](renders/CL-04-dock.png) |

### CL-05 · Reverse-jointed pod biped, claw arms, rear dock

Options: TS-001 centralized hydraulic; TS-002 seated protected cockpit; TS-003 bipedal; TS-004 rear backpack dock. Informs: HAZ-006, HAZ-008, HAZ-009, HAZ-011, HAZ-012, HAZ-013, HAZ-017, HAZ-021, HAZ-022, HAZ-023, SYS-003, SYS-006, SYS-008, SYS-009, SYS-010, SYS-012, SYS-013, SYS-019. Parameters: [`params/CL-05.yaml`](params/CL-05.yaml).

- Proportions from the project lead's AI-generated Industrial Utility Walker (one three-quarter view so far): tall pod with front and side windows, reverse-jointed legs, long arms ending in curved claws. The geometry is original, authored in build123d; the generated mesh is not used.
- Reverse-jointed knees sit behind the hips: the walker is the tallest of the five, its centre of gravity sits behind the hips, and a backward fall puts the knees first. Fall direction, kneel-for-egress and SYS-009 stability limits need their own analysis for this leg geometry.
- The side windows give the pilot a view to the sides and are a candidate for the second exit CL-04 lacks, if they are sized and openable for egress (SYS-012); at concept size they are close to a minimum emergency opening.
- The long claws hang low beside the legs, inside the walking envelope: a strike and pinch zone for anyone near the walker (HAZ-009) unless manipulation is inhibited and the arms are stowed while walking (SYS-013).
- Kneel posture for egress (SYS-019): with the feet planted and the knees folded back, the hip drops from 2.34 m to 0.95 m and the cockpit floor from 2.41 m to about 1.0 m, a two-step climb instead of a ladder. The CG drops by more than a metre, so the tip angle improves, but the folded knees move mass rearward and the static margin shrinks: the kneel needs its own stability check. Lowering and rising create a crush zone under the pod and knees (HAZ-022). Kneeling is also a candidate controlled safe posture on loss of actuation energy (SYS-008, HAZ-021).
- Access aids: the pilot leaves over the front-opening sill, which sits 0.62 m above the cockpit floor, so the real climb is from the sill (about 1.64 m when kneeling, 3.03 m standing), not from the floor. A fold-down ladder hinged under the sill deploys in the kneel with four treads at an even 0.33 m rise (placeholder limit 0.40 m), and grab handles beside and above the opening give three points of contact. Standing, the ladder is stowed folded on the hull: egress without kneeling is not possible, so a failure that prevents kneeling also blocks normal egress (HAZ-008). The ladder must be interlocked against deployment while walking, and ISO 2867 (access systems for earth-moving machinery) is a candidate reference for access dimensions; its applicability is not yet decided.
- Emergency exit (SYS-012): both side windows are push-out hatches (clear opening 0.62 x 0.72 m) with red release handles inside, so the pilot can leave standing, without power and without kneeling, and has a second way out if the front opening is blocked (HAZ-008) or there is a fire in the pod (HAZ-017). A fold-out davit carries a rope ladder 0.60 m out from the hull; deployed, it clears the walker by 0.25 m. The hatch sill is 3.2 m up when standing: the descent is a fall-from-height hazard (HAZ-023). The shoulder plate under each hatch is now the exit step: a tread flush with the hatch sill, 0.42 m deep, with non-slip strips, a toe lip, an armour skirt over the shoulder joint and grab rails either side of the hatch; the pilot steps out onto it and across a 0.18 m gap to the escape ladder. The treads add mass behind the hips: static margin fell from 0.12 to 0.10 m standing and from 0.09 to 0.07 m kneeling, which the longer heel spurs (next finding) then recovered. Whether the clear opening is large enough for a pilot in protective equipment is TBD.
- Heel spurs: the rear edge of the support polygon limited stability (CG 0.20 m behind the hips standing, 0.23 m kneeling, with the heels ending 0.30 m behind them). Spurs reaching 0.68 m behind the ankle (was 0.40 m) and 0.30 m wide move the rear edge to 0.58 m behind the hips: static margin 0.38 m standing (tip angle 7.9 deg) and 0.35 m kneeling (13.2 deg), above the 0.30 m review flag in every posture and now the largest of the five layouts. Static margin is a standstill measure only: walking needs the dynamic stability analysis of SYS-009, and long heels add a trip and toe-strike risk on rough ground and a crush zone behind each foot for anyone standing close (HAZ-009).
- Rotor clearance: with the dock on short struts above the power pack the docked rotors came within 0.86 m of the pilot's head, under the 1 m flag (HAZ-011, SYS-003). Raising the platform 0.45 m on taller struts gives 1.09 m for 8 cm of extra overall height (4.48 m) and no measurable change in static margin; 0.30 m would give only 0.99 m. The measure is straight-line distance: the hull wall and roll bar already stand between rotor and pilot in the seat, so the clearance matters most while the pilot is outside the pod (ingress, egress, maintenance) and the rotor inhibit (SYS-003) remains the primary control. Taller struts are a longer lever for dock loads while walking (HAZ-013). Raising the dock also brings the rotors to 0.29 m from the roll bar, the nearest part of the walker's own structure: launch and recovery must clear it (HAZ-012, SYS-006), now tracked as the rotor-to-structure metric for every layout.

Drawing sheet: [SUS-CAD-001-CL-05](drawings/CL-05.svg) (A3, 1:50, dimensioned side, plan and front views).

**Emergency posture** (emergency exit).

| | Standing | Emergency |
|---|---|---|
| Cockpit floor (egress drop) | 2.41 m | 2.41 m |
| Hip height | 2.34 m | 2.34 m |
| Overall height | 4.48 m | 4.48 m |
| CG height | 2.72 m | 2.73 m |
| Static margin | 0.38 m | 0.38 m |
| Static tip angle | 7.9° | 7.9° |
| Claws above ground | 0.93 m | 0.93 m |
| Front-opening sill (actual climb height) | 3.03 m | 3.03 m |
| Ladder treads | 0 | 0 |
| Largest step rise | 3.03 m | 3.03 m |
| Emergency hatch sill | 3.21 m | 3.21 m |
| Emergency hatch clear opening | 0.62 × 0.72 m | 0.62 × 0.72 m |
| Escape ladder clearance to the walker | — | 0.16 m |
| Shoulder step height (flush with the hatch sill) | 3.21 m | 3.21 m |
| Gap from shoulder step to escape ladder | 0.18 m | 0.18 m |

| | |
|---|---|
| ![CL-05 emergency, front view](renders/CL-05-emergency-hero.png) | ![CL-05 emergency, side elevation](renders/CL-05-emergency-side.png) |

Drawing sheet: [SUS-CAD-001-CL-05-emergency](drawings/CL-05-emergency.svg).

**Kneel posture** (kneeling for egress).

| | Standing | Kneel |
|---|---|---|
| Cockpit floor (egress drop) | 2.41 m | 1.02 m |
| Hip height | 2.34 m | 0.95 m |
| Overall height | 4.48 m | 3.10 m |
| CG height | 2.72 m | 1.49 m |
| Static margin | 0.38 m | 0.35 m |
| Static tip angle | 7.9° | 13.1° |
| Claws above ground | 0.93 m | 1.14 m |
| Front-opening sill (actual climb height) | 3.03 m | 1.64 m |
| Ladder treads | 0 | 4 |
| Largest step rise | 3.03 m | 0.33 m |
| Emergency hatch sill | 3.21 m | 1.82 m |
| Emergency hatch clear opening | 0.62 × 0.72 m | 0.62 × 0.72 m |
| Shoulder step height (flush with the hatch sill) | 3.21 m | 1.82 m |
| Gap from shoulder step to escape ladder | 0.18 m | 0.18 m |

| | |
|---|---|
| ![CL-05 kneel, front view](renders/CL-05-kneel-hero.png) | ![CL-05 kneel, side elevation](renders/CL-05-kneel-side.png) |

Drawing sheet: [SUS-CAD-001-CL-05-kneel](drawings/CL-05-kneel.svg).

![CL-05 front view from eye height](renders/CL-05-hero.png)

| | |
|---|---|
| ![CL-05 three-quarter view](renders/CL-05-iso.png) | ![CL-05 side elevation](renders/CL-05-side.png) |
| ![CL-05 plan view with support polygon and centre of gravity](renders/CL-05-top.png) | ![CL-05 UAV dock and rotor clearance to the pilot](renders/CL-05-dock.png) |
<!-- END GENERATED: cad-concepts -->

## 3. How the layouts are made

| Step | Tool | Output |
|---|---|---|
| Parameters | [`params/CL-nn.yaml`](params/), [`params/common.yaml`](params/common.yaml) | One file per layout; placeholders, metres |
| Reference layout geometry (CL-05) | [`tools/cad/b3d/cl05.py`](../tools/cad/b3d/cl05.py) in build123d 0.9 ([`environment.yml`](../tools/cad/b3d/environment.yml)) | `build/cad-src/CL-05/`: one STEP file per part class and `info.json`, imported by the step below |
| Geometry and metrics | [`tools/cad/build_concepts.py`](../tools/cad/build_concepts.py) under FreeCAD 1.1 | `build/cad/CL-nn/`: `.FCStd`, `.step`, STL per part class; [`metrics.json`](metrics.json) (committed) |
| Drawing sheets | [`tools/cad/drawings.py`](../tools/cad/drawings.py) (FreeCAD TechDraw hidden-line projection) | [`drawings/CL-nn.svg`](drawings/) and [`drawings/concept-layouts.pdf`](drawings/concept-layouts.pdf) (committed): A3, 1:50, third-angle side, plan and front views with dimensions, CG and support polygon |
| Photoreal renders (CL-05) | [`tools/cad/blender_render.py`](../tools/cad/blender_render.py), Blender 5.3 `bpy` module, Cycles | [`renders/blender/`](renders/blender/) (committed; not run in CI, about 5 minutes of CPU for the set) |
| Review images | [`tools/cad/render.cjs`](../tools/cad/render.cjs) and [`viewer.html`](../tools/cad/viewer.html) (three.js in headless Chromium) | [`renders/`](renders/) (committed) |
| This page | `tools/pdac/generate.py` | Section 2, from the layout records and `metrics.json` |

Run everything with `tools/cad/make.sh` (it needs a FreeCAD 1.1 environment, see [`tools/cad/environment.yml`](../tools/cad/environment.yml), and Node with Playwright). CI ([`.github/workflows/cad.yaml`](../.github/workflows/cad.yaml)) rebuilds the geometry on every change to `cad/` or `tools/cad/`, fails if `metrics.json` or a drawing sheet is out of date, and attaches the STEP, FCStd and STL files and the drawing PDF to the run. CAD files are not committed; they are reproducible from the parameters.

The layout records are in [`pdac/items/concept-layouts.yaml`](../pdac/items/concept-layouts.yaml); the validator checks that each layout names real trade-study alternatives, that its parameter file exists and that `metrics.json` is current for it.

## 4. Next

1. Review the layouts with the systems, safety and human-factors leads; record what each one rules in or out against the trade-study criteria.
2. Add the missing alternatives: standing and remote pilot (TS-002), electromechanical actuation (TS-001).
3. Replace effective densities with a mass budget once a parts breakdown exists, and add a kneel or lowered-egress posture to each layout.
4. Decide the licence for hardware design files (CERN-OHL-P proposed) before the first design-level CAD.
