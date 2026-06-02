# Knowledge: Verification

> **Layer 1 (Canon).** Durable craft for *checking that the geometry frank built is actually right* — independent of whether the target is Rhino or Houdini. Tool-specific capture calls live in `references/<tool>-mcp.md`; this file is the *method*, never the *which API*. The modeling medium has no unit-test runner: verification here is **geometric, visual, and behavioral assertion**, with a human as the final acceptance authority.

You cannot `assert geometry == expected`. A sculpture is right when it *looks* right and *measures* right, and "looks right" is a human judgment. So frank verifies on two tracks that meet at a human decision: a **visual track** (capture an image of what was built, compare it to the reference, attribute the difference to a parameter) and a **geometric track** (assert measurable properties — scale, topology, manifoldness — that a picture can hide). The whole thing runs as a **capture → compare → adjust** loop, proven on the spiral-ribbon project and encoded in `frank-review`.

---

## 1. The capture → compare → adjust loop

Verification is iterative, not a single pass. One turn of the loop:

1. **Build** the generator (deterministic, scope-isolated — see `knowledge/parametric-scripting.md`).
2. **Capture** the result from the *pinned* camera (§2).
3. **Compare** the capture to the reference — silhouette and surface (§3, §4) — and assert geometric properties (§5).
4. **Adjust** by changing a **parameter in `P`**, never the geometry by hand, and re-run.

The loop terminates when a **human accepts** the result (§6) or an iteration cap is hit (frank-review caps at ~6 iterations, then escalates to the human rather than auto-accepting). Each turn changes one thing, so each visual diff is attributable. This is only valid because the generator is deterministic: a pinned camera over a deterministic generator means the *only* thing that moved between captures is the parameter you changed.

This loop is the proven discipline from the spiral project — capture from a fixed Front view, compare the rendered silhouette to the reference photo, tweak a phase/radius/winding parameter, re-capture — and it is exactly what `frank-review` automates.

## 2. Which views to capture, and pin the camera

**Capture the views that disambiguate the form.** A single view lies — a flat strap and a deep ribbon can share a silhouette from the front. The canonical set:

- **The reference-matched view first.** If the reference is a front photo, the *first and primary* capture is a front-orthographic that matches the reference's framing, because that is the comparison the human will make. The spiral was authored to stand up in world Z and be "faced from −Y (Front)" precisely so this match is exact.
- **Orthographic over perspective for comparison.** Perspective foreshortening makes two different forms look the same (or two same forms look different) depending on distance. Use orthographic for the silhouette comparison; reserve perspective for a final "does it read in 3D" gut check.
- **Enough additional canonical views to pin depth and topology:** typically front, side (left/right), top, and one perspective. The side view is what catches a depth/thickness error the front hides. Capture additional views only when a finding is ambiguous from the primary set — don't pay for views that don't disambiguate.

**Pin / record the camera — this is non-negotiable.** Record the camera's `position`, `target`, and `lens`/focal length **once** and reuse the identical values on every iteration, storing them in the review's working notes. Two captures from even slightly different cameras are not comparable, and the entire compare loop silently degrades into noise. `frank-review` records the pinned camera at loop start and re-uses it for every capture.

- **Rhino:** capture via the viewport from a recorded named view / camera; `capture_viewport` returns the image inline (simpler than Houdini — no render-to-file, no scaffolding). Still mandate the pinned-camera discipline: same view, every iteration.
- **Houdini:** render via `render_single_view` with a fixed `rotation` (e.g. `orthographic=True, rotation=[0,0,0]` for front), **read the image from `render_path` on disk** (not the inline `image_base64`), then **clean the scaffolding nodes** the render leaves behind. **Never `render_quad_views`** — it deadlocks the server (see `references/houdini-mcp.md` and the render-deadlock learning). A pinned `rotation` is the Houdini analog of the pinned camera.

## 3. Silhouette comparison — the primary visual assertion

The fastest, highest-signal visual check is **silhouette**: the outline of the captured form against the outline of the reference. Most modeling errors that matter — wrong proportion, missing or extra turn, a hook that curls the wrong way, a coil too tight or too loose — show up first in the silhouette.

- **Compare outlines, not pixels.** You are matching shape, proportion, and topology of the outline (does the volute coil inward the same number of turns? does the hook open to the same angle? is the descent the same length relative to the coil?), not lighting or color.
- **Name the discrepancy and attribute it to a parameter.** "The volute is one half-turn short" → `volute_turns`. "The hook curls the wrong way" → `hook_winding`. "There's a notch where the descent meets the hook" → `hook_phase_deg` (entry tangent mismatch). A silhouette finding is only useful if it points at the knob that fixes it — this is the bridge from `frank-review`'s visual track back to a parametric adjustment.
- **This is a vision task.** Comparing two rendered images is genuinely a perceptual judgment, so `frank-review` dispatches `frank-silhouette-critic` on a **vision-capable model**. The critic receives the capture file and the reference file as paths and adversarially reports where the outlines diverge.

## 4. Surface analysis — shaded, wireframe, curvature

The silhouette is necessary but not sufficient. Three complementary surface views catch what the outline cannot:

- **Shaded** shows form, continuity, and obvious surface defects — kinks, pinches, self-shadowing folds where the surface crosses itself. A kink that reads as a hard crease in shaded view is the symptom the knot-style learning is about (`docs/solutions/2026-06-01_rhino-knotstyle-overshoot-vs-kink.md`).
- **Wireframe** exposes topology the shaded view hides: isocurve density, where control points bunch (overshoot from uneven sampling — the spiral's resample fix), seams, and degenerate spans.
- **Curvature / surface analysis** (zebra, environment-map, Gaussian/mean curvature) reveals continuity — whether two surfaces meet tangent (G1) or curvature-continuous (G2), or only touch (G0). For sweeps and lofts, this is where a framing twist shows up as a sudden stripe discontinuity (`docs/solutions/2026-06-01_rhino-sweep1-framing-twist.md`). Use it when smoothness is part of the design intent.

Pick the analysis that targets the *suspected* failure: silhouette for proportion/topology, shaded for folds/kinks, wireframe for sampling/seams, curvature for continuity. Don't run all four reflexively — run the one the current finding calls for.

## 5. Geometric assertion patterns — what a picture hides

A render can look perfect and the geometry still be unfabricatable or wrong. The geometric track asserts measurable properties on the data, not the image. `frank-review` passes a geometry summary / inspection data to `frank-geometry-reviewer`, which reasons over these:

- **Scale / bounding box.** Assert the overall extent matches intent. The spiral prints `bbox X[..] Z[..] height=..` every run — a one-line check that catches unit errors (height `0.265` vs `265`) and gross-scale mistakes before any visual review. This is the cheapest assertion and should always be present.
- **Object / scope counts.** Assert frank's scope has the expected number of objects and **every foreign scope is unchanged** (the foreign-scope invariant from `knowledge/parametric-scripting.md` §3). A surprise count is a scope leak or a duplication bug.
- **Topology and manifoldness.** For anything heading toward a solid or fabrication: closed vs. open, **naked edges** (boundary edges that should be shared — a sign the surface isn't watertight), non-manifold edges (more than two faces meeting an edge), and self-intersection. A ribbon that visually "looks solid" but has naked edges won't boolean, mesh, or print cleanly.
- **Self-intersection / collision.** Assert features that shouldn't touch don't (adjacent spiral turns colliding — the self-overlap guard). Some of these are cheap to compute *in the generator* as a WARN (see parametric-scripting §6); the reviewer confirms them on the built result.
- **Units/tolerance consistency.** Assert the built geometry respects the document tolerance — degenerate spans shorter than tolerance, gaps a boolean can't close.

Each assertion is named, measurable, and either passes or produces a specific finding. These are the modeling-domain analog of unit tests: not `assert ==`, but `assert this measurable property holds`.

## 6. Human acceptance authority — self-judging is circular

**The human is the acceptance authority. frank does not sign off on its own work.** The model that built the geometry comparing it to a reference and declaring it good is circular — the same blind spot that produced an error will excuse it. So:

- **Present, don't pronounce.** `frank-review` presents a side-by-side (capture vs. reference) plus the merged reviewer findings to the human and asks for the call. The reviewers *find*; the human *decides*.
- **The loop ends on human acceptance**, or at the iteration cap — and at the cap, frank presents the latest capture, the unresolved findings by reviewer lane, states the cap was reached, and asks the human to accept or override. It **does not auto-accept**. If a systematic blocker surfaced, it suggests `/frank-compound` to record the learning.
- **Reviewers report; they don't fix and they don't merge.** Each adversarial reviewer (`frank-silhouette-critic`, `frank-geometry-reviewer`) emits findings as JSON to a run-scoped path; `frank-review` merges/dedups and surfaces them. Keeping finding-generation separate from the accept decision is what preserves the human's authority over both.

## 7. Confidence calibration — don't cry wolf

Verification findings are only useful if they're trustworthy. A reviewer that flags everything trains the human to ignore it.

- **Calibrate to confidence and suppress noise.** High-confidence, consequential findings (wrong topology, naked edges on a part meant to be solid, silhouette off by a whole turn) are worth raising. Cosmetic-at-this-fidelity nitpicks at the lowest confidence anchor are suppressed — the fidelity target set in `frank-plan` governs what counts as a defect.
- **Stay in your lane.** The silhouette critic judges *outline/proportion* and defers *topology/manifoldness* to the geometry reviewer; the geometry reviewer judges *measurable geometric properties* and defers *visual proportion* to the silhouette critic. Lane discipline prevents two reviewers double-flagging the same issue from different angles and keeps the merge clean.
- **Match scrutiny to fidelity.** A quick visual study and a fabrication-ready part have different bars. A naked edge is a non-issue on a render-only study and a blocker on something headed to a printer. Verify to the *declared* fidelity target, not to an absolute ideal.

---

## The contract, in one breath

frank verifies by **capturing the built form from a pinned camera, comparing its silhouette and surfaces to the reference, asserting measurable geometric properties a picture hides, and adjusting a parameter (never the geometry by hand) — looping until a human accepts or the cap escalates to the human.** The model finds; the human decides.

---

## Sources

- **Proven loop:** the spiral-ribbon project's capture-compare-adjust discipline (`~/Documents/projects/HAL/docs/plans/2026-05-29-001-feat-spiral-ribbon-sculpture-plan.md` + `examples/rhino/spiral-ribbon-sculpture.py`) — fixed Front-orthographic capture matched to the reference photo, silhouette comparison, parameter-only adjustment, bbox/scale and foreign-scope assertions printed every run.
- **Houdini capture policy (validated live 2026-06-01):** `references/houdini-mcp.md` and `docs/solutions/2026-06-01_houdini-mcp-render-deadlock.md` — `render_single_view` + read-from-disk + scaffolding cleanup; `render_quad_views` banned; pinned `rotation` as the camera analog.
- **Rhino surface-analysis tooling** (McNeel) — shaded/wireframe display modes, zebra and curvature analysis, naked-edge/manifold checks (`ShowEdges`, `Brep.IsSolid`/`IsManifold`, edge analysis). <https://developer.rhino3d.com/api/rhinocommon/> and the Rhino analysis-command guides.

## Cross-References

- **Tool reference packs that supply the capture calls + verified policy:** `references/rhino-mcp.md` (inline `capture_viewport`, pinned-camera discipline), `references/houdini-mcp.md` (`render_single_view` → read-from-disk → scaffolding cleanup; `render_quad_views` ban).
- **Sibling canon:** `knowledge/parametric-scripting.md` (determinism is the precondition that makes the compare loop valid; the foreign-scope invariant this file asserts), `knowledge/geometry-quality.md` (stub — deepens the topology/manifold checks of §5), `knowledge/fabrication.md` (stub — the fidelity bar of §7 for fabrication-ready parts).
- **Agents that load this canon:** `frank-silhouette-critic` (the visual/silhouette track, §3, dispatched on a vision model), `frank-geometry-reviewer` (the geometric-assertion track, §5).
- **Skills that STOP-gate-load this canon:** `frank-review` (the capture→compare→adjust loop owner), `frank-plan` (designs the verification assertions up front), `frank-build` (cleans capture scaffolding; sets up for review).
- **Learnings grounded in this canon:** `docs/solutions/2026-06-01_rhino-knotstyle-overshoot-vs-kink.md` (shaded-view kink), `docs/solutions/2026-06-01_rhino-sweep1-framing-twist.md` (curvature/continuity stripe), `docs/solutions/2026-06-01_rhino-adjacent-turn-self-intersection.md` (self-intersection assertion), `docs/solutions/2026-06-01_houdini-mcp-render-deadlock.md` (capture policy).
