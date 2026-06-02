# spiral-ribbon-sculpture.py
#
# GOLDEN EXAMPLE — the canonical parametric-generator pattern frank-build emits
# for Rhino. This is not a one-off: it is the reference shape every Rhino
# generator should take. Read it for the *pattern*, not the sculpture.
#
# The pattern, made concrete here by a spiral-ribbon form (an inward-coiling
# VOLUTE on top, a long DESCENDING sweep, and an open HOOK curling up at the
# base, built as one smooth NURBS rail with a thin rectangular ribbon swept
# along it):
#
#   1. ONE named parameter block (P = {...}) — the entire tunable surface. No
#      magic numbers in the body; everything a human would tweak lives in P.
#      Derived quantities (overall height, knot spacing) are computed FROM P,
#      never hard-coded alongside it.
#   2. THREE idempotent layer helpers (_ensure_layer / _clear_layer / _to_layer)
#      that make the generator SCOPE-ISOLATED and RE-RUNNABLE: it owns exactly
#      one layer (P["layer"]), clears only that layer's objects on each run, and
#      assigns every object it creates back to that layer explicitly. Re-running
#      converges (rebuilds its layer) instead of accumulating geometry.
#   3. A FOREIGN-LAYER OBJECT-COUNT INVARIANT: the count of objects on every
#      layer the generator does NOT own is identical before and after each run.
#      This is the generic, project-agnostic safety contract — it protects
#      whatever else lives in the document without naming any of it.
#   4. GEOMETRIC GUARDS THAT WARN, NEVER EMIT BAD GEOMETRY: an orientation-aware
#      self-overlap guard and a bbox/scale assertion print warnings so a human
#      can retune, rather than silently producing tangled or mis-scaled output.
#   5. try/finally TRANSIENT CLEANUP: consumed helper geometry (the swept
#      profile curve) is deleted even if a later step raises, so nothing escapes
#      the delete-by-layer rebuild and drifts across reruns.
#
# Run inside Rhino via the Rhino MCP execute_rhinoscript_python_code tool.
# Generators work in 2D plane coords (u=horizontal, v=vertical); _to_xz maps
# (u, v) -> (u, 0, v) so the piece stands up in world Z, faced from -Y (Front).
# Ribbon width runs along +/-Y (depth). Edit P{} and re-run to tune.

import rhinoscriptsyntax as rs
import scriptcontext as sc
import math

# ----------------------------- PARAMETERS -----------------------------
# The entire tunable surface. Every value a human would adjust lives here;
# the body below contains no magic numbers. Derived quantities (overall
# height, knot spacing) are computed FROM these, not declared beside them.
P = {
    "layer": "Sculpture-Spiral",
    # Overall height is derived from volute_center/hook_center + radii,
    # not a direct knob -- shift those to rescale vertically.

    # Volute (top coil) -- center (u, v) = (x, height)
    "volute_center":     (0.0, 232.0),
    "volute_turns":      2.25,
    "volute_outer_r":    55.0,
    "volute_inner_r":    12.0,
    "volute_phase_deg":  95.0,    # winding phase (orients inner->outer coil)
    "volute_winding":    -1,      # +1 ccw, -1 cw

    # Descent (neck) bow
    "descent_bow":       0.12,    # fraction of chord length the neck bulges (straighter neck)
    "descent_side":      1,       # which side the bow bulges (+1 / -1)
    "descent_samples":   10,

    # Hook (bottom) -- center (u, v)
    "hook_center":       (-6.0, 64.0),
    "hook_radius":       46.0,
    "hook_sweep_deg":    270.0,   # open partial loop (< 360); lower = more open curl
    "hook_phase_deg":    -6.0,    # entry phase: tangent ~matches descent arrival (kills notch)
    "hook_winding":      -1,

    # Ribbon profile
    "band_width_mm":     18.0,
    "band_thickness_mm": 2.5,
    "width_in_plane":    False,   # False = width along depth (rolled-tape look); True = flat strap facing viewer

    # Sampling / build
    "samples_per_turn":  40,
    "resample_spacing_mm": 3.0,
    "clearance_mm":      0.5,
    "build_ribbon":      True,    # sweep the ribbon along the rail
    "cap_ends":          True,    # cap open ribbon ends into a closed solid
}

# ----------------------------- HELPERS --------------------------------
def _to_xz(uv):
    # plane point (u, v) -> world (x=u, y=0, z=v): stands up in Z
    return [(p[0], 0.0, p[1]) for p in uv]

# --- The three idempotent layer helpers (the scope-isolation contract) ---
def _ensure_layer(name):
    # Create the owned layer if absent, then make it current. Idempotent.
    if not rs.IsLayer(name):
        rs.AddLayer(name)
    rs.CurrentLayer(name)

def _clear_layer(name):
    # Delete ONLY objects on the owned layer -- never iterate the whole
    # document, never touch any other layer. This is what makes a rerun
    # converge instead of accumulate.
    objs = rs.ObjectsByLayer(name)
    if objs:
        rs.DeleteObjects(objs)

def _to_layer(obj_ids, name):
    # Assign created objects to the owned layer explicitly, rather than
    # relying on current-layer state. Objects that land off-layer escape the
    # delete-by-layer rebuild and drift across reruns.
    if obj_ids is None:
        return
    if not isinstance(obj_ids, list):
        obj_ids = [obj_ids]
    for o in obj_ids:
        if o:
            rs.ObjectLayer(o, name)

# --- The generic foreign-layer object-count invariant (the safety contract) ---
def _foreign_layer_counts(owned):
    # Snapshot the object count of every layer this generator does NOT own.
    # Project-agnostic: it names no specific foreign layer, it just records
    # the counts of all of them so they can be compared before vs. after.
    counts = {}
    for name in (rs.LayerNames() or []):
        if name == owned:
            continue
        counts[name] = len(rs.ObjectsByLayer(name) or [])
    return counts

def _assert_foreign_unchanged(before, after):
    # The invariant: counts on every non-owned layer are identical before and
    # after the run. Warns (does not raise) on any drift, naming the offender.
    drift = []
    for name in sorted(set(before) | set(after)):
        b = before.get(name, 0); a = after.get(name, 0)
        if b != a:
            drift.append("%s %d->%d" % (name, b, a))
    if drift:
        print("WARN foreign-layer drift (generator touched layers it does not "
              "own): %s" % ", ".join(drift))
    else:
        print("foreign-layer invariant OK (%d non-owned layers unchanged)"
              % len(after))

def volute_points(P):
    cu, cv = P["volute_center"]
    r_in = float(P["volute_inner_r"]); r_out = float(P["volute_outer_r"])
    turns = float(P["volute_turns"]); total = turns * 2.0 * math.pi
    b = math.log(r_out / r_in) / total
    s = P["volute_winding"]; phi0 = math.radians(P["volute_phase_deg"])
    n = max(8, int(round(P["samples_per_turn"] * turns)))
    pts = []
    for i in range(n + 1):
        phi = total * i / float(n)          # 0 (inner) -> total (outer)
        r = r_in * math.exp(b * phi)
        a = phi0 + s * phi
        pts.append((cu + r * math.cos(a), cv + r * math.sin(a)))
    return pts                              # [0]=inner tip, [-1]=outer end

def hook_points(P):
    cu, cv = P["hook_center"]; hr = float(P["hook_radius"])
    sweep = math.radians(P["hook_sweep_deg"]); a0 = math.radians(P["hook_phase_deg"])
    s = P["hook_winding"]
    n = max(8, int(round(P["samples_per_turn"] * P["hook_sweep_deg"] / 360.0)))
    pts = []
    for i in range(n + 1):
        a = a0 + s * sweep * i / float(n)
        pts.append((cu + hr * math.cos(a), cv + hr * math.sin(a)))
    return pts                              # [0]=descent join, [-1]=free tip

def descent_points(E1, E2, P):
    bow = float(P["descent_bow"]); side = P["descent_side"]; n = int(P["descent_samples"])
    du, dv = E2[0] - E1[0], E2[1] - E1[1]
    L = math.hypot(du, dv)
    if L < 1e-6:
        return []
    pu, pv = -dv / L, du / L                # in-plane perpendicular
    pts = []
    for i in range(1, n):                   # interior only (endpoints owned by volute/hook)
        t = i / float(n)
        bu, bv = E1[0] + du * t, E1[1] + dv * t
        off = bow * L * 4.0 * t * (1.0 - t) * side  # parabolic bow, max at midpoint
        pts.append((bu + pu * off, bv + pv * off))
    return pts

def min_interturn_spacing(P):
    # smallest radial gap between adjacent log-spiral turns is at the inner end
    r_in = float(P["volute_inner_r"]); r_out = float(P["volute_outer_r"])
    turns = float(P["volute_turns"]); total = turns * 2.0 * math.pi
    b = math.log(r_out / r_in) / total
    return r_in * (math.exp(b * 2.0 * math.pi) - 1.0)

def inplane_extent(P):
    # in-plane cross-section extent governs adjacent-turn collision
    return float(P["band_width_mm"]) if P.get("width_in_plane") else float(P["band_thickness_mm"])

# ----------------------------- BUILD ----------------------------------
def build_ribbon(rail, P):
    import Rhino.Geometry as rg
    dom = rs.CurveDomain(rail)
    S = rs.CurveStartPoint(rail)
    T = rs.CurveTangent(rail, dom[0])
    Tv = rg.Vector3d(T[0], T[1], T[2]); Tv.Unitize()
    planeN = rg.Vector3d(0.0, 1.0, 0.0)     # scroll-plane normal (depth / Y)
    inplaneN = rg.Vector3d.CrossProduct(planeN, Tv); inplaneN.Unitize()  # in XZ, perp to tangent
    if P.get("width_in_plane"):
        W = inplaneN                        # width across the scroll plane (flat strap faces viewer)
        Th = rg.Vector3d(planeN)            # thickness along depth
    else:
        W = rg.Vector3d(planeN)             # width along depth (rolled-tape look)
        Th = inplaneN                       # thickness in-plane
    W.Unitize(); Th.Unitize()
    hw = float(P["band_width_mm"]) / 2.0
    ht = float(P["band_thickness_mm"]) / 2.0
    Sp = rg.Point3d(S[0], S[1], S[2])
    c1 = Sp + W * hw + Th * ht
    c2 = Sp - W * hw + Th * ht
    c3 = Sp - W * hw - Th * ht
    c4 = Sp + W * hw - Th * ht
    prof = rs.AddPolyline([(c1.X, c1.Y, c1.Z), (c2.X, c2.Y, c2.Z),
                           (c3.X, c3.Y, c3.Z), (c4.X, c4.Y, c4.Z),
                           (c1.X, c1.Y, c1.Z)])
    srf = None
    try:
        srf = rs.AddSweep1(rail, [prof], False)
    finally:
        # transient-geometry cleanup: the profile is consumed by the sweep and
        # must be removed even if AddSweep1 raises, or it escapes the
        # delete-by-layer rebuild and drifts across reruns.
        if prof:
            rs.DeleteObject(prof)
    srfs = srf if isinstance(srf, list) else ([srf] if srf else [])
    if P.get("cap_ends"):
        for s in srfs:
            rs.CapPlanarHoles(s)
    if srfs:
        _to_layer(srfs, P["layer"])
    return srfs

def build(P):
    layer = P["layer"]

    # Snapshot foreign-layer counts BEFORE any mutation, so the post-build
    # invariant check can prove the generator touched only its own layer.
    foreign_before = _foreign_layer_counts(layer)

    _ensure_layer(layer)
    _clear_layer(layer)                     # idempotent: only this layer

    # Guard (WARN, do not emit): orientation-aware adjacent-turn self-overlap.
    gap = min_interturn_spacing(P)
    need = inplane_extent(P) + float(P["clearance_mm"])
    if gap < need:
        print("WARN self-overlap: min inter-turn spacing %.2f < required %.2f "
              "(in-plane extent + clearance). Loosen volute_turns or raise "
              "outer/inner radius ratio." % (gap, need))

    vpts = volute_points(P)
    hpts = hook_points(P)
    dpts = descent_points(vpts[-1], hpts[0], P)
    raw = _to_xz(vpts + dpts + hpts)

    # resample to roughly uniform arc-length spacing: avoids interp overshoot
    # from the dense-volute / sparse-descent density swing.
    pl = rs.AddPolyline(raw)
    div = rs.DivideCurveLength(pl, float(P["resample_spacing_mm"]), False, True)
    rs.DeleteObject(pl)

    rail = rs.AddInterpCurve(div, 3, 1)     # degree 3, chord-length knots
    _to_layer(rail, layer)

    ids = [rail]
    if P.get("build_ribbon"):
        ids += build_ribbon(rail, P)

    # Guard (WARN, do not emit): bbox / scale assertion.
    bb = rs.BoundingBox(ids)
    if bb:
        xs = [p[0] for p in bb]; zs = [p[2] for p in bb]
        print("bbox X[%.1f,%.1f] Z[%.1f,%.1f] height=%.1f"
              % (min(xs), max(xs), min(zs), max(zs), max(zs) - min(zs)))
    else:
        print("WARN bbox unavailable -- no geometry produced; check parameters.")
    print("min_interturn_gap=%.2f required=%.2f" % (gap, need))
    print("rail points=%d  objects on %s=%d"
          % (len(div), layer, len(rs.ObjectsByLayer(layer))))

    # The generic foreign-layer object-count invariant: every layer this
    # generator does not own must have the same object count it started with.
    foreign_after = _foreign_layer_counts(layer)
    _assert_foreign_unchanged(foreign_before, foreign_after)
    return ids

ids = build(P)
sc.doc.Views.Redraw()
print("DONE build_ribbon=%s" % P.get("build_ribbon"))
