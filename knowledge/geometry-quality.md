# Knowledge: Geometry Quality

> **Layer 1 (Canon).** Durable craft for *well-formed geometry* — the structural health of the model itself, independent of whether it looks right (that's `knowledge/verification.md`) or how it was generated (that's `knowledge/parametric-scripting.md`). Tool-specific calls live in `references/<tool>-mcp.md`.

**Status: stub** — not yet authored; covers the quality of the geometry as a data structure rather than as an image: NURBS continuity (G0/G1/G2) and degree/knot health, watertightness and naked/non-manifold edges, mesh quality (manifoldness, normals, degenerate faces, watertight closure), surface fairness and isocurve distribution, self-intersection and overlap, tolerance-clean topology, and the difference between geometry that *renders* fine and geometry that is *structurally* fine. Grow via `frank-compound` — each modeling session that surfaces a geometry-health gotcha (a sweep that won't cap, a boolean that fails on a near-tangent, a mesh that won't print) should compound a learning here and promote the recurring ones into authored sections below.

---

## 1. Continuity and surface fairness

*(stub — G0/G1/G2 continuity across joined surfaces; isocurve distribution; fairness/control-point health; what shaded vs. curvature analysis reveals.)*

## 2. Watertightness and topology

*(stub — closed vs. open breps; naked edges, non-manifold edges; `IsSolid`/`IsManifold`; tolerance-clean joins.)*

## 3. Mesh quality

*(stub — manifoldness, consistent normals, degenerate/zero-area faces, watertight closure, density vs. tolerance.)*

## 4. Self-intersection and overlap

*(stub — detecting and resolving self-intersecting surfaces/solids; the relationship to the generator-side WARN guards in `knowledge/parametric-scripting.md`.)*

## 5. "Renders fine" vs. "is structurally fine"

*(stub — the failure mode where geometry passes visual verification but fails a boolean, mesh, or fabrication step; why the geometric-assertion track in `knowledge/verification.md` §5 exists.)*

---

## Cross-References

- **Sibling canon:** `knowledge/parametric-scripting.md` (generator-side guards that pre-empt geometry-quality defects), `knowledge/verification.md` (the geometric-assertion track, §5, that *detects* these defects), `knowledge/fabrication.md` (stub — where geometry-quality requirements get strictest).
- **Tool reference packs:** `references/rhino-mcp.md`, `references/houdini-mcp.md`.
- **Agents that will load this canon (when authored):** `frank-geometry-reviewer` (topology/manifold/self-intersection findings).
- **Skills that will STOP-gate-load this canon (when authored):** `frank-review`, `frank-build`.
- **Grow via:** `frank-compound` — promote recurring geometry-health learnings from `docs/solutions/` into the sections above.
