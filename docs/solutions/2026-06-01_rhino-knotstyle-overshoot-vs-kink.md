---
date: 2026-06-01
tool: rhino
area: curve-fitting
type: gotcha
mcp: jingcheng-chen/rhinomcp
tags: [rhino, mcp, curve-fitting, addinterpcurve, knotstyle, overshoot, kink, chord-length, frank]
---

# Curve overshoot (density-transition) vs. tangent kinks are two distinct AddInterpCurve failures — chord-length knots + arc-length resampling fix overshoot, blend points fix kinks

Fitting one smooth rail through a point list whose density jumps ~10× between segments (a densely-sampled volute concatenated with a sparsely-sampled descent) made `rs.AddInterpCurve` with default **uniform** knots (`knotstyle=0`) produce **curvature overshoot / lumps at the density transitions** — bulges where the chord lengths suddenly change. This is a *separate* failure from a **tangent kink** at a segment junction, and the two have different fixes: overshoot is a knot/spacing problem (fix: chord-length knots + arc-length resampling); a kink is a tangent-continuity problem (fix: matched junction tangents / blend points). Conflating them sends you chasing the wrong fix.

## Symptom
- **Overshoot:** the fitted rail bulged or lumped right where a dense segment met a sparse one (volute→descent, descent→hook). A `CurvatureGraph` (or sampled second derivative) showed a **curvature spike** at those junctions even though the rail had no sharp corner there.
- **Kink (the look-alike):** a *sharp corner* — a curvature discontinuity — at a junction where two segments' end tangents didn't agree. Visually a crease, not a bulge.
- Both show up "at a junction," which is why they get confused; the discriminator is **bulge (overshoot) vs. crease (kink)**.

## Root cause
- **Overshoot** comes from feeding a uniform-knot interpolation a point list with **uneven chord lengths**. `knotstyle=0` (uniform) assumes equal parameter spacing between points, so when the actual chord lengths jump ~10× at a density transition, the spline must accelerate through the parameterization to keep up — and a degree-3 interpolating curve overshoots (Runge-style lumps) exactly at that mismatch. It is a **parameterization/spacing** defect, not a tangent defect.
- **Kink** comes from the **tangent directions** of two adjacent segments not agreeing at their shared junction point. Even with perfect knots, mismatched tangents force a curvature discontinuity. It is a **continuity** defect, independent of knot style.

Because the volute is sampled by `samples_per_turn` (dense) while the descent/hook use a few well-placed points (sparse), the concatenated list has both risks — and they must be diagnosed and fixed separately.

## Fix
**For overshoot — chord-length knots + arc-length resampling:**

```python
# 1) Resample each segment to roughly uniform arc-length spacing BEFORE concatenating,
#    so adjacent-point chords don't jump ~10x at the junctions.
def _resample_arclen(pts, target_spacing):
    crv = rs.AddInterpCurve(pts, degree=3, knotstyle=1)   # temp, chord-length
    try:
        length = rs.CurveLength(crv)
        n = max(2, int(round(length / target_spacing)))
        ts = rs.DivideCurve(crv, n)        # equal arc-length stations
        return ts
    finally:
        rs.DeleteObject(crv)               # transient cleanup

vol = _resample_arclen(gen_volute_points(P),  P["rail_spacing"])
des = _resample_arclen(gen_descent_points(P), P["rail_spacing"])
hk  = _resample_arclen(gen_hook_points(P),    P["rail_spacing"])
pts = vol + des[1:] + hk[1:]               # drop duplicate junction points

# 2) Fit with chord-length knots, NOT uniform.
rail = rs.AddInterpCurve(pts, degree=3, knotstyle=1)   # knotstyle=1 = chord-length
```

**For a kink (different fix entirely):** order the points so adjacent segments share direction at the junction (volute-outer-end tangent ≈ descent-start tangent); if a crease remains, **insert 1–2 blend points** between the segments rather than raising the curve degree or joining separate curves. Do **not** reach for chord-length knots to fix a kink — it won't, because the defect is tangents, not spacing.

What did **not** work: bumping `knotstyle` alone without resampling — chord-length knots help, but if the raw points still jump 10× in spacing the residual overshoot persists; the resampling is what removes the spacing swing the knots then parameterize.

## Verified facts (2026-06-01)
- ✅ Uniform knots (`knotstyle=0`) over a ~10× point-density swing produce curvature overshoot/lumps at the density transitions.
- ✅ Chord-length knots (`knotstyle=1`) **plus** arc-length resampling of each segment removes the overshoot.
- ✅ Overshoot (a curvature *bulge*) and a kink (a curvature *discontinuity / crease*) are distinct failures with distinct fixes — check for them separately (curvature-spike check vs. sharp-corner check).
- ℹ️ Blend points fix kinks; arc-length resampling + chord-length knots fix overshoot. Applying one to the other's symptom wastes an iteration.

## Cross-References
- Reference pack: `references/rhino-mcp.md` (`get_rhinoscript_docs` before emitting `AddInterpCurve` — confirm the exact `knotstyle` argument live; `try/finally` transient cleanup for the temp resampling curves).
- Patterns enforced: `knowledge/parametric-scripting.md` (named param block drives `samples_per_turn` / `rail_spacing`; transient curves cleaned in `finally`), `knowledge/verification.md` (curvature checked at the junctions as a geometric assertion, separate from the kink/sharp-corner check).
- Related learnings: `docs/solutions/2026-06-01_rhino-sweep1-framing-twist.md` (a fair rail is the *precondition* for a clean sweep — overshoot/kink must be fixed before framing twist can be isolated), `docs/solutions/2026-06-01_rhino-adjacent-turn-self-intersection.md` (the coil spacing guard — a third, distinct geometric failure).
- Origin: the spiral-ribbon-sculpture project (`~/Documents/projects/HAL/docs/plans/2026-05-29-001-feat-spiral-ribbon-sculpture-plan.md`, Key Technical Decisions + U2 edge cases), which called out overshoot-vs-kink as separate problems requiring separate fixes.
