---
date: 2026-06-01
tool: rhino
area: scope-isolation
type: pattern
mcp: jingcheng-chen/rhinomcp
tags: [rhino, mcp, self-intersection, coil, guard, orientation-aware, warn-not-emit, frank]
---

# A coil self-intersects when adjacent-turn radial spacing drops below the cross-section's in-plane extent — guard it orientation-aware, and WARN don't refuse

A spiral ribbon's coil tangles not when the innermost point reaches the center, but when the **radial spacing between *adjacent turns*** drops below the cross-section's **in-plane** extent — and *which* cross-section dimension is in-plane depends on the profile's orientation. The durable pattern is an **orientation-aware adjacent-turn guard** that computes the minimum inter-turn spacing from the parameter block and **prints a WARNING** (does not refuse to build, does not silently emit tangled geometry) so the human sees the problem with the geometry still in hand.

## Symptom
- At the tight innermost turns of the volute, the swept ribbon **collided with its own previous turn** — adjacent bands overlapped and the surface self-intersected, even though no single point had reached the spiral center.
- A naive "innermost radius vs. center" check **passed** while the geometry was already tangled — the wrong invariant was being guarded.
- The failure depended on profile orientation: with the band's width perpendicular to the scroll plane it self-intersected at a different turn count than with the width tilted into the plane.

## Root cause
Two adjacent turns of a spiral are separated by a **radial spacing** (for a log spiral `r(θ)=r0·e^(kθ)`, the spacing is smallest near the center). The ribbon has a finite cross-section. The two turns collide when that radial spacing becomes smaller than **the part of the cross-section that lies in the scroll plane** — the *in-plane extent* — plus any clearance. The in-plane extent is **not fixed**: it depends on `profile_up_axis`. With the band width ⟂ the scroll plane (the default), the in-plane extent is `band_thickness`; if the width is tuned *into* the plane, the in-plane extent becomes `band_width`. Guarding "innermost point vs. center" checks the wrong quantity entirely — a coil can be nowhere near the center and still have adjacent turns closer together than the band is thick.

## Fix
An **orientation-aware adjacent-turn guard** computed from the param block, emitting a WARN (not an exception, not silent geometry):

```python
import math

def _in_plane_extent(P):
    # which cross-section dimension lies in the scroll plane depends on profile orientation
    up = P["profile_up_axis"]
    width_in_plane = abs(up[1]) < 0.5          # width ⟂ plane (default) -> thickness is in-plane
    return P["band_thickness_mm"] if width_in_plane else P["band_width_mm"]

def _min_interturn_spacing(P):
    # log spiral r = r0 * e^(k*theta); spacing between adjacent turns is tightest near the center.
    r_out, r_in, turns = P["volute_outer_r"], P["volute_inner_r"], P["volute_turns"]
    total_theta = turns * 2.0 * math.pi
    k = math.log(r_out / r_in) / total_theta            # derived, not a magic number
    # adjacent-turn spacing at the innermost turn (theta near 0 from the inner end)
    r_inner_turn = r_in * math.exp(k * 2.0 * math.pi)
    return r_inner_turn - r_in

def _guard_self_overlap(P):
    needed = _in_plane_extent(P) + P.get("clearance_mm", 0.0)
    have   = _min_interturn_spacing(P)
    if have < needed:
        print("WARN: coil may self-intersect — min adjacent-turn spacing %.2f mm < "
              "in-plane cross-section extent + clearance %.2f mm. "
              "Reduce volute_turns or raise volute_outer_r/volute_inner_r ratio." % (have, needed))
    # NOTE: warn-and-continue. Do not raise; do not skip the build. The human decides.
```

The guard **warns and continues** — it never raises and never silently produces tangled geometry. This is the proven frank discipline: geometric guards surface a problem for the human (who is the acceptance authority) rather than refusing to build or quietly emitting garbage. If the warning fires, the fix is a parameter change (fewer `volute_turns`, or a larger outer/inner radius ratio), which the idempotent rebuild makes cheap.

What did **not** work: the "innermost radius vs. spiral center" check — it guards the wrong invariant and passes while adjacent turns are already overlapping.

## Verified facts (2026-06-01)
- ✅ The coil self-intersects on **adjacent-turn radial spacing < in-plane cross-section extent**, not on innermost-point-vs-center.
- ✅ The in-plane extent is **orientation-dependent**: `band_thickness` when width ⟂ the scroll plane (default), `band_width` when width is tuned into the plane.
- ✅ The guard derives min inter-turn spacing from `volute_outer_r` / `volute_inner_r` / `volute_turns` (no magic numbers) and **WARNs rather than refusing** — warn-and-continue is the frank guard discipline.
- ℹ️ This is a **distinct** failure from sweep framing twist and from rail overshoot/kink — a fair, untwisted ribbon can still self-intersect at the coil if spacing is too tight.

## Cross-References
- Reference pack: `references/rhino-mcp.md` ("Verified facts" #4 — guards WARN, never emit; the layer-scoped idempotent rebuild that makes a param re-tune cheap).
- Patterns enforced: `knowledge/parametric-scripting.md` (derived-from-`P` quantities, no magic numbers, guards-that-warn), `knowledge/geometry-quality.md` (self-intersection is a geometry-quality defect; the orientation-aware spacing check is the assertion that catches it).
- Related learnings: `docs/solutions/2026-06-01_rhino-sweep1-framing-twist.md` (framing twist — distinct failure), `docs/solutions/2026-06-01_rhino-knotstyle-overshoot-vs-kink.md` (rail fairness — distinct failure).
- Origin: the spiral-ribbon-sculpture project (`~/Documents/projects/HAL/docs/plans/2026-05-29-001-feat-spiral-ribbon-sculpture-plan.md`, Key Technical Decisions "Self-overlap guard" + U1 edge case + Risks), where the orientation-aware adjacent-turn guard was specified to warn rather than produce tangled geometry.
