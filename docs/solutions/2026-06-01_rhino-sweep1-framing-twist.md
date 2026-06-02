---
date: 2026-06-01
tool: rhino
area: sweep
type: gotcha
mcp: jingcheng-chen/rhinomcp
tags: [rhino, mcp, sweep, sweep1, framing, twist, rhinocommon, up-vector, frank]
---

# Sweep1 default framing twists the profile on a tightly-curved planar rail — fix with RhinoCommon SweepOneRail + a fixed up-vector

Sweeping a thin flat ribbon along the spiral-ribbon rail with `rs.AddSweep1` produced a band that **rolled/twisted** as it rounded the tightly-curved volute — the flat face stopped pointing the same direction along the rail, so the ribbon read as a folding/inverting tube near the coil instead of a clean flat band. The fix is to drive the sweep with a **fixed roadlike "up" vector** via RhinoCommon `Brep.CreateFromSweep` / `SweepOneRail`, not the default Sweep1 framing.

## Symptom
- Perspective and front captures of the swept ribbon showed the band **rolling** along the rail: flat-facing ±Y at the start, but rotated toward the rail plane as the rail curvature increased into the volute.
- Near the innermost turns of the coil the profile appeared to **flip / fold**, so the ribbon looked like a pinched tube rather than a flat band on edge.
- The rail itself was correct (single smooth planar XZ curve) — the failure was purely in how the profile frame was carried along it.

## Root cause
`rs.AddSweep1` lets Rhino pick the profile **framing** automatically. On a planar rail with strong, varying curvature (the log-spiral volute), the default frame minimizes twist *relative to the rail's own rotation-minimizing frame* — which is **not** the same as keeping the profile's flat face pointing at a fixed world direction. As the rail curls, the rotation-minimizing frame rolls, and the ribbon's flat face rolls with it. The frame is determined by the rail's geometry, not by an intent ("keep the band flat-facing ±Y"), so there is no parameter on the high-level `AddSweep1` call that pins the orientation. This is framing behavior, **distinct** from a self-intersection (adjacent-turn spacing) or a rail kink (tangent mismatch) — those have their own learnings; this one is purely about how the profile is *carried*, even on a perfectly fair rail.

## Fix
Drop to **RhinoCommon** and run the sweep with an explicit, fixed "up" vector so the profile frame stays roadlike (flat face pinned to a world direction) along the whole rail. In `execute_rhinoscript_python_code` you can reach RhinoCommon directly via `Rhino.Geometry`; `execute_rhinocommon_csharp_code` is the C# fallback when the Python surface is awkward.

```python
import Rhino, scriptcontext as sc
import rhinoscriptsyntax as rs

rail = sc.doc.Objects.FindId(rail_id).Geometry          # the interpolated NURBS rail
profile = sc.doc.Objects.FindId(profile_id).Geometry    # the closed rectangle profile

sweep = Rhino.Geometry.SweepOneRail()
sweep.AngleToleranceRadians = sc.doc.ModelAngleToleranceRadians
sweep.SweepTolerance        = sc.doc.ModelAbsoluteTolerance
sweep.SetToRoadlikeTop()      # roadlike frame: profile up = a fixed world axis, not the rail's RMF
# (SetToRoadlikeTop/Front/Right pin the frame to world +Z / +Y / +X respectively;
#  pick the one whose "up" matches profile_up_axis so the flat face never rolls)

breps = sweep.PerformSweep(rail, profile)
for b in breps:
    obj_id = sc.doc.Objects.AddBrep(b)
    rs.ObjectLayer(obj_id, P["layer"])
sc.doc.Views.Redraw()
```

What did **not** work: tuning `profile_up_axis` and re-running `rs.AddSweep1` — it changes the *initial* profile orientation but the default framing still rolls it along the rail, so the twist returns at the volute regardless of the start orientation. The framing must be pinned for the whole sweep, which only the RhinoCommon roadlike route exposes.

## Verified facts (2026-06-01)
- ✅ `rs.AddSweep1` default framing twists a flat profile on a tightly-curved planar rail (volute) — the flat face rolls as rail curvature increases.
- ✅ RhinoCommon `SweepOneRail` with `SetToRoadlikeTop/Front/Right` pins the profile frame to a fixed world axis, keeping the band flat-facing the whole length.
- ℹ️ `Rhino.Geometry` (incl. `SweepOneRail`) is reachable from `execute_rhinoscript_python_code`; `execute_rhinocommon_csharp_code` is the C# fallback, not a requirement.
- ℹ️ This is **framing**, not self-intersection or a rail kink — confirm the rail is fair first (no kink) and the spacing guard passes (no self-overlap) before attributing a roll to framing.

## Cross-References
- Reference pack: `references/rhino-mcp.md` (the proven build/introspect surface; `execute_rhinocommon_csharp_code` is the C#/RhinoCommon fallback noted there).
- Patterns enforced: `knowledge/parametric-scripting.md` (generator emits the swept ribbon idempotently into its owned layer), `knowledge/verification.md` (the twist was caught by the pinned-camera capture-compare loop, not by trusting the build).
- Related learnings: `docs/solutions/2026-06-01_rhino-knotstyle-overshoot-vs-kink.md` (rail fairness — overshoot vs. kink, a *distinct* failure class), `docs/solutions/2026-06-01_rhino-adjacent-turn-self-intersection.md` (the coil self-overlap guard — also distinct from framing).
- Origin: the spiral-ribbon-sculpture project (`~/Documents/projects/HAL/docs/plans/2026-05-29-001-feat-spiral-ribbon-sculpture-plan.md`, U3 + Risks), where the default-sweep twist was flagged as the most likely failure and resolved via the RhinoCommon roadlike route.
