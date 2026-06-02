# Knowledge: Fabrication

> **Layer 1 (Canon).** Durable craft for *geometry that has to become a physical object* — the constraints that apply once a model leaves the screen and goes to a printer, mill, laser, or mold. This is the strictest fidelity tier: a render-only study can tolerate defects a fabrication-ready part cannot. Tool-specific calls live in `references/<tool>-mcp.md`.

**Status: stub** — not yet authored; covers fabrication-readiness across processes: real-world units and scale verification, wall thickness and minimum-feature-size constraints, watertight/manifold solid requirements for 3D printing, overhang/support and orientation considerations, tolerance and clearance for assemblies and fits, export-format hygiene (STL/3MF/STEP — mesh density, units-on-export), draft angles and undercuts for molding, and material/process-specific limits. Grow via `frank-compound` — each time a model goes to fabrication and a constraint bites (a wall too thin to print, an unprintable overhang, a unit-on-export mismatch, a press-fit that came out loose), compound a learning here and promote the recurring ones into authored sections below.

This canon is the home of the deferred **`frank-fabrication-reviewer`** agent and the `fabrication-ready` artifact tier referenced by `frank-plan`; both land when this file is authored (M5).

---

## 1. Units and real-world scale

*(stub — verifying the model is at true physical scale before export; the units/tolerance discipline from `knowledge/parametric-scripting.md` §5 carried through to the fabricator.)*

## 2. Watertight, manifold solids

*(stub — the non-negotiable for 3D printing; naked/non-manifold edges as hard blockers, not warnings; the strictest application of `knowledge/geometry-quality.md`.)*

## 3. Wall thickness and minimum feature size

*(stub — process-dependent minimums; thin-wall and small-feature detection as a guard.)*

## 4. Tolerance, clearance, and fits

*(stub — clearance for assemblies and moving parts; process tolerance vs. designed clearance; the `clearance_mm` knob pattern from the proven generator.)*

## 5. Process-specific constraints

*(stub — overhangs/supports and orientation for FDM/SLA; draft angles and undercuts for molding; kerf for laser/CNC; export-format hygiene STL/3MF/STEP.)*

---

## Cross-References

- **Sibling canon:** `knowledge/geometry-quality.md` (stub — fabrication is its strictest application: watertight, manifold, tolerance-clean), `knowledge/parametric-scripting.md` (units/tolerance/clearance knobs carried through to physical scale), `knowledge/verification.md` (the fidelity-bar discussion, §7 — fabrication-ready is the highest tier).
- **Tool reference packs:** `references/rhino-mcp.md`, `references/houdini-mcp.md`.
- **Agents that will load this canon (when authored):** `frank-fabrication-reviewer` (deferred to M5).
- **Skills that will STOP-gate-load this canon (when authored):** `frank-plan` (the `fabrication-ready` artifact tier), `frank-review` (fabrication fidelity bar).
- **Grow via:** `frank-compound` — promote recurring fabrication learnings from `docs/solutions/` into the sections above.
