# Knowledge: Parametric Scripting

> **Layer 1 (Canon).** Durable craft that does not change when the MCP API changes. *What good looks like* when frank emits a generator — independent of whether the target is Rhino or Houdini. Tool-specific calls live in `references/<tool>-mcp.md`; exact live signatures come from the docs-researcher agents. This file is *why* and *what*, never *which API*.

A frank build is never "draw these objects." It is **a generator**: a small, named, deterministic program whose inputs are a parameter block and whose output is geometry. The generator is the artifact of record; the geometry is a *re-derivable* result. Everything below exists to make that generator legible, safe to re-run, and honest about what it does and doesn't know.

The discipline is grounded in two things: (1) the proven Rhino spiral-ribbon generator (`examples/rhino/spiral-ribbon-sculpture.py`), which frank's `frank-build` emits as its golden pattern, and (2) the procedural-modeling tradition codified by McNeel (Grasshopper) and Daniel Shiffman (*The Nature of Code*). Where a principle below was learned the hard way on the spiral, the section says so.

---

## 1. Named parameter block — one source of truth, no magic numbers

Every generator opens with a single named parameter block. In Python that is one dict (`P = {...}`); in Grasshopper it is the set of input sliders/panels; in Houdini it is a controlling `null`'s spare parameters or the HDA interface. **There is exactly one place a knob lives, and the rest of the generator reads from it.**

- **No magic numbers in the body.** A literal `55.0` buried in a build function is unreviewable and untweakable. The spiral generator hoists every dimension — `volute_outer_r`, `band_width_mm`, `samples_per_turn` — into `P` so a reviewer (human or `frank-parametric-architect`) sees the entire design surface in one block. The body computes; it does not decide.
- **Distinguish knobs from derived values.** A *knob* is something a human sets directly. A *derived value* is computed from knobs and must never be set independently, or the two can disagree. The spiral generator documents this explicitly: overall height "is derived from `volute_center`/`hook_center` + radii, not a direct knob — shift those to rescale vertically." If a value can be computed from other knobs, **derive it; do not add a redundant knob.** Two knobs that must agree are a bug waiting to happen.
- **Name for intent, comment the non-obvious.** `volute_phase_deg` with the comment `# winding phase (orients inner->outer coil)` tells the reviewer what the number *means*, not just that it exists. Unit suffixes (`_mm`, `_deg`) make the unit unambiguous at the call site.
- **Group and order by structure.** The spiral's block is sectioned by feature (Volute / Descent / Hook / Ribbon / Build), so the param block doubles as a map of the model's anatomy.

This mirrors the Grasshopper principle that a definition's inputs should be few, named, and exposed — *The Grasshopper Primer* (Mode Lab, 3rd ed.) frames a definition as a function of its sliders, with everything downstream being computation. It is the same idea as a pure function's signature.

## 2. Generator vs. result — keep them separate

The generator is *code you keep*; the geometry is *output you can throw away and regenerate*. This separation is the whole point of parametric work — a value Shiffman makes central in *The Nature of Code* (Chapter 0/1: systems described by their generating rules, not their frozen output).

- **The geometry is downstream of, and reconstructible from, the generator + `P`.** If you cannot delete every object the generator made and recreate it identically by re-running, the generator is incomplete (it depends on hidden manual edits) — fix the generator, not the geometry.
- **Never hand-edit the result and call it done.** A manual nudge in the viewport is invisible to the next run and will be silently destroyed by it. If the form needs the nudge, the nudge belongs in `P` or in the generator's logic. `frank-review`'s job is to find the gap between intent and output and feed a *parameter* change back, never a manual one.
- **The generator is the unit of review and of compounding.** When `frank-compound` records a learning, it records a property of the *generator* (e.g. "adjacent log-spiral turns self-intersect when `volute_turns` is high and `band_thickness` is large"), because that is the durable, transferable fact.

## 3. Idempotent, scope-isolated rebuild

Re-running a generator must be safe *any number of times* and must touch **only frank's own scope**. This is the single most load-bearing operational property, and the one most easily gotten wrong.

**Scope isolation.** frank operates inside exactly one named container and never reaches outside it:

- **Rhino:** the scope unit is a **layer**. The spiral uses three small helpers — `_ensure_layer(name)` (create-if-absent + set current), `_clear_layer(name)` (delete **only** `rs.ObjectsByLayer(name)`), and `_to_layer(ids, name)` (move new objects onto the scope layer). `_clear_layer` deleting *only this layer's objects* is the crux: it is what makes re-running non-destructive to the rest of the document.
- **Houdini:** the scope unit is frank's **own named subnet** (the layer analog). Idempotency = delete and rebuild only that subnet each run; never touch sibling networks (see `references/houdini-mcp.md`).

**Idempotency.** The rebuild order is fixed: *ensure scope → clear scope → build into scope*. The spiral's `build(P)` does exactly this (`_ensure_layer` → `_clear_layer` → emit). Because clear is scoped, the second run produces byte-for-byte the same document state as the first — no accumulation, no duplicates.

**The foreign-scope invariant (the proven guard).** After every run, the object count of every container *other than* frank's must be **identical** to before the run. The spiral generator prints per-layer counts for foreign layers precisely to assert this. frank's golden example generalizes that hardcoded check into a generic foreign-layer-count invariant: if a run changes a count outside frank's scope, the generator has a scope leak and must be fixed before it ships. This invariant is the cheapest, most reliable signal that scope isolation actually holds.

## 4. Determinism — same input, same output

A generator is a function: `geometry = f(P)`. For a given `P` it must produce the same geometry every time, on every machine.

- **No hidden state, no wall-clock, no un-seeded randomness.** If a generator uses randomness (jitter, scatter, noise), the seed is a parameter in `P`. Shiffman's treatment of randomness and Perlin noise in *The Nature of Code* is built on seeded, reproducible pseudo-randomness for exactly this reason: a "random" form you can't reproduce is a form you can't review, tweak, or fabricate twice.
- **Order-independence where it matters.** Two knobs that are conceptually independent should not have results that depend on the order they were applied. When order *does* matter (a fillet after a boolean), make the order explicit in the generator, not incidental.
- **Determinism is what makes `frank-review`'s compare loop valid.** A pinned camera over a *deterministic* generator means the only thing that changes between iterations is the parameter you changed — so a visual diff is attributable to that parameter. Non-determinism poisons the entire capture→compare→adjust loop (see `knowledge/verification.md`).

## 5. Units and tolerance discipline

Geometry without a unit is a number without a meaning. frank records units and tolerance up front and treats them as part of `P`'s context.

- **Establish units before building.** `frank-setup` records the document units and absolute tolerance (Rhino: document units + model absolute tolerance; Houdini: unitless, working convention ~1 unit = 1 m, set via `hou.setUnitLength`). Curve sampling, sweep resolution, and boolean robustness are all relative to that tolerance — RhinoCommon operations like `Curve.Offset`, `Brep.CreateBooleanUnion`, and meshing take a tolerance argument and behave differently across scales.
- **Carry the unit in the name.** `band_width_mm`, `clearance_mm` — the suffix is the contract. A bare `width` invites a mm/cm/inch mismatch that no compiler will catch.
- **Sampling spacing is a tolerance decision, not a free knob.** The spiral resamples to `resample_spacing_mm` because the raw point density swung from dense (volute) to sparse (descent) and the degree-3 interpolation overshot. Sampling resolution should be tied to the model's scale and the document tolerance, not picked arbitrarily.
- **Scale assertions catch unit mistakes early.** A bounding-box print that says `height=265` when you expected ~265 mm is a one-line confirmation the units are right; a `height=0.265` is a caught unit bug. See §7.

## 6. Validation and guards — WARN, don't emit a broken result, don't silently mutate

frank's generators **validate, warn, and continue** — they do not throw the whole build away on a soft violation, and they do not silently "fix" the design by mutating it. The proven rule, taken directly from the spiral generator: **guards WARN; they do not emit.**

- **Warn on soft geometric violations; build anyway.** The spiral checks whether adjacent spiral turns will self-overlap (`min_interturn_spacing` vs `in-plane extent + clearance`) and, if they will, prints a `WARN self-overlap: ...` with a *concrete remedy* ("Loosen volute_turns or raise outer/inner radius ratio") — then proceeds to build. The human sees the warning and the (possibly flawed) geometry together and decides. A guard that *prevents* the build hides the evidence the human needs to judge.
- **Why warn instead of refuse?** Modeling is exploratory. A "violation" is often the point (an intentional overlap, an out-of-scale study). Refusing to build robs the human of the visual that would tell them whether the warning matters. Warn loudly, build, let `frank-review` and the human adjudicate.
- **Why warn instead of silently auto-correcting?** Silently clamping `volute_turns` to a "safe" value changes the design behind the human's back and breaks determinism (the output no longer matches `P`). The generator's job is to *surface* the conflict, not resolve it unilaterally.
- **Good guards to include:** self-intersection / adjacent-feature collision; bounding-box / overall-scale sanity; per-scope and foreign-scope object counts (§3); degenerate-input checks (zero-length chord, `L < 1e-6` in the spiral's `descent_points`). Each prints a one-line, named, actionable message.
- **Hard, structural errors are different.** A genuinely impossible operation (sweep failed, null rail) is not a soft warning — surface the exception cleanly so `frank-build` can self-correct (Houdini's MCP returns Python exceptions promptly for exactly this; see `references/houdini-mcp.md`). The WARN-don't-emit rule is about *design-quality* violations, not *operation* failures.

## 7. Re-runnability and transient cleanup

A generator is run dozens of times during `frank-review`'s iteration loop. It must leave no debris and must be trivially re-runnable.

- **Clean up transient/scratch geometry deterministically.** The spiral builds a temporary profile polyline and a temporary polyline-for-resampling, and disposes of both — the profile via `try/finally` so it is deleted *even if the sweep raises*, the resample polyline immediately after `DivideCurveLength`. **Anything that is scaffolding for the build, not part of the result, gets cleaned up in a `finally`.** Leaked scratch geometry pollutes the scope and breaks the next idempotent run.
- **Tool scaffolding is transient too.** On the capture side, Houdini's render adds `MCP_CAMERA`/`MCP_CAM_CENTER`/`/out/MCP_OGL_RENDER` scaffolding nodes; frank cleans these for the same scope-isolation reason (see `references/houdini-mcp.md` and `knowledge/verification.md`).
- **Re-runnability is the integration test.** Per the spiral generator's contract: re-running the script twice leaves non-frank scope object counts identical, and editing `P` regenerates the form without duplicating geometry. If either fails, one of §3 (scope), §4 (determinism), or §7 (cleanup) is broken.

## 8. Introspect the live API before emitting calls

Parametric craft is durable; the API surface is not. A generator that *assumes* a signature is a generator that breaks on the next version.

- **Confirm signatures live, don't recall them.** Before `frank-build` emits a call, it confirms the exact signature against the running tool — Rhino via `list_rhinoscript_modules` / `search_rhinoscript_functions` / `get_rhinoscript_docs`, Houdini via `execute_houdini_code` introspection — or dispatches the matching docs-researcher agent. This is Layer 2 of the knowledge architecture: canon (this file) says *what good looks like*; the reference pack says *which calls*; the researcher confirms *the exact current signature*.
- **Introspect the document before building, too.** The spiral's discipline includes surveying existing geometry and primitives before writing code, so the generator builds *with* the document's reality (units, tolerance, existing layers/subnets) rather than against an assumed blank slate.

---

## The contract, in one breath

A frank generator is: **a single named parameter block → a deterministic, unit-aware function → that builds only into its own named scope, idempotently, cleaning up after itself, warning (never silently mutating) on soft violations, and confirmed against the live API.** Re-running it twice is a no-op against the rest of the document; editing `P` is the *only* way its output changes.

---

## Sources

- **The Grasshopper Primer**, Mode Lab (3rd ed.) — definitions as functions of named inputs; minimizing and exposing parameters; data-tree discipline. <https://grasshopperprimer.com/>
- **The Nature of Code**, Daniel Shiffman (2024 ed., natureofcode.com) — systems described by generating rules rather than frozen output; seeded/reproducible randomness and Perlin noise (Ch. 0–1). <https://natureofcode.com/>
- **RhinoCommon API** (McNeel) — tolerance-parameterized operations (`Curve.Offset`, `Brep.CreateBooleanUnion`, meshing); document units/tolerance model. <https://developer.rhino3d.com/api/rhinocommon/>
- **RhinoScriptSyntax / Rhino.Python guides** (McNeel) — `rhinoscriptsyntax` patterns used by the proven spiral generator. <https://developer.rhino3d.com/guides/rhinopython/>
- **Proven artifact:** `examples/rhino/spiral-ribbon-sculpture.py` (frank's golden example, generalized from the HAL spiral-ribbon project) — named `P` block, three idempotent layer helpers, foreign-scope count invariant, WARN-not-emit self-overlap guard, `try/finally` transient cleanup.

## Cross-References

- **Tool reference packs that enforce this canon:** `references/rhino-mcp.md` (layer-scope idempotency contract, units/tolerance), `references/houdini-mcp.md` (subnet-scope idempotency, scaffolding cleanup).
- **Sibling canon:** `knowledge/verification.md` (determinism is what makes the capture→compare loop valid), `knowledge/geometry-quality.md` (stub), `knowledge/fabrication.md` (stub).
- **Golden example:** `examples/rhino/spiral-ribbon-sculpture.py`.
- **Agents that load this canon:** `frank-parametric-architect` (audits the param-block + scope-isolation shape against this file), `frank-rhino-docs-researcher` / `frank-houdini-docs-researcher` (confirm the live signatures §8 demands).
- **Skills that STOP-gate-load this canon:** `frank-build` (before emitting a generator), `frank-plan` (when designing the named param block + verification assertions).
- **Learnings grounded in this canon:** `docs/solutions/2026-06-01_rhino-adjacent-turn-self-intersection.md` (the self-overlap guard), `docs/solutions/2026-06-01_rhino-sweep1-framing-twist.md`, `docs/solutions/2026-06-01_rhino-knotstyle-overshoot-vs-kink.md`.
