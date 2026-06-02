# Reference: Rhino MCP

> **Source:** [`jingcheng-chen/rhinomcp`](https://github.com/jingcheng-chen/rhinomcp) — the Rhino MCP plugin (in-Rhino socket server + bridged MCP process). Third-party, not by McNeel. See the plugin's repo for the authoritative server surface; this pack records frank's verified policy over it.
>
> **Validation status:**
> - ✅ **PROVEN** (grounded by the spiral-ribbon-sculpture project, 2026-05/06) — the build/introspect/capture loop frank actually exercised. These five tools are the load-bearing surface and are confirmed against real use:
>   - `execute_rhinoscript_python_code` — the primary build + introspection tool (ran the entire spiral generator).
>   - `get_document_summary` — the survey tool (units, tolerance, layer hierarchy, per-layer counts).
>   - `get_object_info` — per-object state query (type, layer, bbox).
>   - `get_rhinoscript_docs` — Layer-2 signature confirmation before emitting code.
>   - `capture_viewport` — review capture (returns the image **inline** — no quad/scaffolding problem; see Capture POLICY).
> - 🚧 **PRESENT ON SERVER — verify against live `tools/list` before relying on.** The high-level helpers below appear in the server's tool surface but were **not** exercised by the spiral project frank cites as Rhino proof. Treat them as conveniences over RhinoScript/RhinoCommon, **confirm the exact current signature live** (`get_rhinoscript_docs` or a `tools/list`) before a build emits a call, and feed any surprise to `frank-compound`:
>   - `loft`, `sweep1`, `pipe`, `extrude_curve`, `boolean_difference` / `boolean_intersection` / `boolean_union`, `create_object` / `create_objects`, `create_layer`, and `execute_rhinocommon_csharp_code` (the C#/RhinoCommon fallback).
>   - Do **not** assert proven status for any tool no captured evidence exercised. When in doubt, prefer the proven `execute_rhinoscript_python_code` path (it calls the same RhinoCommon underneath and is the surface frank already trusts).

## Architecture

Same pattern as HoudiniMCP/BlenderMCP: an in-app **socket server** running inside Rhino + an **MCP server process** that bridges Claude ↔ Rhino over TCP.

- **Socket bridge:** the Rhino-side server runs inside a live Rhino **document session** (started by the rhinomcp plugin). All calls operate on *whatever document is open* — there is no headless mode; frank reads and writes the user's active model.
- **MCP process:** the rhinomcp server speaks MCP over stdio and forwards commands to the in-Rhino socket. Connected tools surface as `mcp__rhino__*`.
- **Document, not files:** unlike Houdini (which renders to image files on disk), Rhino's `capture_viewport` returns the image **inline** — there is no render-to-path + read-back step and no scaffolding-node cleanup. This makes the Rhino capture path strictly simpler than Houdini's (see Capture POLICY).
- A failed survey call (`get_document_summary` returns `Could not connect to Rhino. Make sure the Rhino addon is running.`) means the plugin/socket isn't live — that is the canonical "Rhino not connected" signal `frank-setup` keys on.

## Tool inventory (from server surface)

> **PROVEN** = exercised by the spiral project. **PRESENT** = on the server, verify live before relying on.

| Tool | Signature | Purpose | Status |
|---|---|---|---|
| `get_document_summary` | `()` | Document metadata, units, **tolerance**, total + per-type + per-layer object counts, full layer hierarchy, model bbox. **Survey tool — run first**, like Houdini's `get_scene_info`. | ✅ PROVEN |
| `execute_rhinoscript_python_code` | `(code: str)` | Run arbitrary `rhinoscriptsyntax` / `scriptcontext` / `Rhino.Geometry` Python in the live document. **The primary build & introspection tool.** | ✅ PROVEN |
| `execute_rhinocommon_csharp_code` | `(code: str)` | Run RhinoCommon C# — the fallback when Python `rhinoscriptsyntax` lacks the control you need (e.g. sweep framing). | 🚧 PRESENT |
| `get_rhinoscript_docs` | `(topic, include_examples=True, max_functions=5)` | **Layer-2 signature confirmation.** Returns full RhinoScript docs (signatures, params, examples) for a topic. **Call before writing code** — the server itself flags this as required before `execute_rhinoscript_python_code`. | ✅ PROVEN |
| `capture_viewport` | `(...)` | Capture the active viewport → returns the image **inline**. Review-capture tool (front-ortho or a pinned camera; see Capture POLICY). | ✅ PROVEN |
| `get_object_info` | `(id)` | Per-object state: type, layer, bbox, attributes. | ✅ PROVEN |
| `get_objects` / `get_selected_objects_info` | `(...)` | Query objects (optionally by filter) / inspect the current selection. | 🚧 PRESENT |
| `get_or_set_current_layer` / `create_layer` / `delete_layer` | `(...)` | Current-layer get/set; create/delete a layer. *(frank manages layers via the idempotent helpers below, not these directly — verify before use.)* | 🚧 PRESENT |
| `create_object` / `create_objects` / `modify_object` / `modify_objects` / `delete_object` | `(...)` | Direct object create / modify / delete helpers. | 🚧 PRESENT |
| `loft` / `sweep1` / `pipe` / `extrude_curve` | `(...)` | High-level surface builders (loft between curves, sweep a profile along a rail, pipe a curve, extrude). **Verify signatures live** — frank's spiral built its sweep via `rs.AddSweep1` inside `execute_rhinoscript_python_code`, not these. | 🚧 PRESENT |
| `boolean_difference` / `boolean_intersection` / `boolean_union` | `(...)` | Solid booleans. | 🚧 PRESENT |
| `offset_curve` / `project_curve` / `split_curve` / `intersect_curves` | `(...)` | Curve operations. | 🚧 PRESENT |
| `select_objects` | `(...)` | Programmatic selection. | 🚧 PRESENT |
| `run_command` / `get_commands` | `(...)` | Run a raw Rhino command string / list available commands. | 🚧 PRESENT |
| `undo` / `redo` | `()` | Document undo / redo. | 🚧 PRESENT |
| `list_rhinoscript_modules` / `search_rhinoscript_functions` / `get_module_functions` | `(...)` | **Layer-2 introspection** — list RhinoScript modules, search functions by keyword, list a module's functions. | ✅ PROVEN (idiom) |

## How frank's spine maps onto Rhino

- **Scope unit = LAYER.** A Rhino **layer** is frank's unit of scope isolation — the analog of a Houdini subnet. Every frank build owns exactly one named layer (`P["layer"]`, e.g. `"Sculpture-Spiral"`) and writes *only* there. Rebuilds clear and regenerate that layer; **no other layer is ever touched**. This is the invariant that makes a generator safe to re-run against a model that already contains the user's other work.

- **`frank-setup`** → `get_document_summary`; record **units** and **tolerance** (Rhino is document-unit'd — mm, in, etc. — not unitless like Houdini), the existing layer hierarchy, and which layer frank will own. Confirm a live connection: a successful summary proves the addon is running.

- **Layer 2 live grounding** → confirm the API instead of guessing. The server *requires* `get_rhinoscript_docs(topic)` before `execute_rhinoscript_python_code`, and offers `search_rhinoscript_functions("loft")` → `AddLoftSrf`, `list_rhinoscript_modules`, `get_module_functions` to find the exact function name and signature:
  ```python
  # find the right function before writing code
  search_rhinoscript_functions("sweep profile along rail")   # -> AddSweep1, AddSweep2, ...
  get_rhinoscript_docs("sweep1 surface", max_functions=3)     # exact signature + examples
  ```
  Pair with `frank-rhino-docs-researcher` for McNeel/RhinoCommon docs when introspection isn't enough.

- **`frank-build`** → emit an **idempotent, scope-isolated, named-parameter-block** generator and run it via `execute_rhinoscript_python_code`. The proven contract (from the spiral project) is **three idempotent layer helpers**:
  ```python
  def _ensure_layer(name):
      if not rs.IsLayer(name):
          rs.AddLayer(name)
      rs.CurrentLayer(name)

  def _clear_layer(name):
      objs = rs.ObjectsByLayer(name)   # ONLY this layer's objects — never the whole doc
      if objs:
          rs.DeleteObjects(objs)

  def _to_layer(obj_ids, name):
      if obj_ids is None:
          return
      if not isinstance(obj_ids, list):
          obj_ids = [obj_ids]
      for o in obj_ids:
          if o:
              rs.ObjectLayer(o, name)
  ```
  `build()` calls `_ensure_layer(layer)` then `_clear_layer(layer)` at the top, so re-running wipes and rebuilds **only the owned layer**. **Parametric** = one named `P = {...}` block at the top, no magic numbers; derived quantities are computed from `P`, not hardcoded. **Idempotency** = the **foreign-layer object-count invariant**: every layer *other than* `P["layer"]` has the identical object count before and after a run. The generator should print per-foreign-layer counts so the invariant is observable (use a generic loop over the existing layers, not project-specific names). See `examples/rhino/spiral-ribbon-sculpture.py` for the canonical pattern.

- **`frank-review`** → `capture_viewport` from a **pinned/recorded camera** → the inline image; write it to a file path and hand that path to `frank-silhouette-critic` / `frank-geometry-reviewer`. No render-to-disk dance, no scaffolding cleanup (see Capture POLICY).

## Layer-2 introspection idioms (confirm live, then build)

Rhino's server is introspection-rich — **always confirm a signature before emitting a call.** The proven workflow:

1. **Search** for the function by intent:
   `search_rhinoscript_functions("boolean")` → `BooleanUnion`, `BooleanDifference`, `BooleanIntersection`.
2. **Read** its full doc before using it:
   `get_rhinoscript_docs("boolean difference solids")` → exact signature, params, return, examples. *(The server flags this as **required** before `execute_rhinoscript_python_code` — skipping it causes syntax errors.)*
3. **Explore** a module when unsure where a function lives:
   `list_rhinoscript_modules()` → modules + counts; `get_module_functions("rhinoscriptsyntax")` → that module's surface.
4. **Survey the live doc** with `get_document_summary()` and **inspect specific objects** with `get_object_info(id)` / `get_objects(...)` before deciding what to clear or build.

This is Layer 2 (live API grounding) in frank's three-layer model: the **reference pack** says *which calls + which verified policies on Rhino*; **`get_rhinoscript_docs` / `frank-rhino-docs-researcher`** give *the exact current signature, confirmed live*; **canon** (`knowledge/*.md`) says *what good looks like*.

## frank-review capture POLICY (viewport capture — Rhino is simpler than Houdini)

**Capture = `capture_viewport`, which returns the image INLINE.** There is no render-to-path step, no `image_base64`-vs-disk tradeoff, and **no scaffolding nodes to clean** — Rhino has no analog of Houdini's `MCP_CAMERA` / `MCP_OGL_RENDER` nodes, and no banned quad-render tool. This is the strictly-simpler half of frank's dual capture story; the Houdini half (`render_single_view` only, read-from-disk, clean scaffolding, **never `render_quad_views`**) is in `references/houdini-mcp.md`.

**The one non-negotiable discipline carries over: a PINNED / RECORDED CAMERA.** A capture is only comparable across iterations if the camera is identical each time. So:

1. **Record the camera once** at the start of a review — viewport name, camera `position`, `target`, and lens/focal length (or set a named view) — and store it in the review's working notes.
2. **Reuse that exact camera** for every capture in the loop. Never let the viewport drift between iterations; a moved camera makes the silhouette comparison meaningless.
3. **Match the reference framing.** Pick the camera so the capture frames the subject the way the reference image does (front-orthographic is the usual silhouette-comparison view), so `frank-silhouette-critic` is comparing like to like.
4. **Write the inline image to a file path** and pass that path to the reviewer agents — they receive a file, not an MCP grant (they cannot mutate geometry).

```python
# capture_viewport returns the image inline; pin the camera so iterations are comparable.
# (Confirm the exact capture_viewport signature live before relying on named args.)
capture_viewport(...)   # pinned camera / named view -> inline image -> write to /tmp/frank/.../capture.png
```

Because the image is inline, the failure modes that plague Houdini capture (disk path, base64 buffer overflow, main-thread render deadlock) **do not exist here**. The only way to get an unusable Rhino capture is to let the camera move — which the pinned-camera rule forbids.

## Verified facts (Rhino-specific)

1. ✅ **Units = the document's units + tolerance** (not unitless). Rhino models carry an explicit unit system (mm / in / m / …) and an absolute tolerance; read both from `get_document_summary` and respect them — coordinates in `P` are in document units. Confirm before any fabrication-scale work. *(Contrast: Houdini is unitless, ~1 unit = 1 m.)*
2. ✅ **Scope isolation = LAYER.** Deleting `rs.ObjectsByLayer(name)` removes **only** that layer's objects and orphans nothing on other layers; this is the proven basis of the idempotent rebuild. The foreign-layer object-count invariant holds across re-runs.
3. ✅ **`get_rhinoscript_docs` before `execute_rhinoscript_python_code`** is required by the server, not optional — it prevents signature-guess syntax errors. Live introspection precedes code emission, always.
4. ✅ **Guards WARN, never emit.** Geometric guards (self-overlap, bbox/scale, per-layer counts) `print("WARN ...")` and continue — they surface a problem for the human without silently mangling or refusing to build geometry. (See the spiral generator's `min_interturn_spacing` self-overlap warning.)
5. ✅ **`try/finally` transient cleanup.** Temporary construction geometry (profile curves, resample polylines) is deleted in a `finally` so a build failure doesn't leave litter on the layer.
6. 🚧 **High-level helpers unproven.** `loft` / `sweep1` / `pipe` / `extrude_curve` / `boolean_*` / `create_object(s)` / `create_layer` / `execute_rhinocommon_csharp_code` are present but unexercised — **verify the live signature before relying on**, and prefer `execute_rhinoscript_python_code` (the proven path) when in doubt.

## Cross-References

- Sibling pack: `references/houdini-mcp.md` (the Houdini analog; its capture POLICY is the more complex render-to-disk case)
- Golden example (the canonical idempotent layer-scoped generator): `examples/rhino/spiral-ribbon-sculpture.py`
- Patterns this enforces: `knowledge/parametric-scripting.md` (named param block, idempotent scope-isolated rebuild, guards-that-warn), `knowledge/verification.md` (pinned-camera capture-compare loop)
- Rhino learnings seeded from the spiral project: `docs/solutions/2026-06-01_rhino-sweep1-framing-twist.md`, `docs/solutions/2026-06-01_rhino-knotstyle-overshoot-vs-kink.md`, `docs/solutions/2026-06-01_rhino-adjacent-turn-self-intersection.md`
