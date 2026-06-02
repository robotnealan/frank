# Reference: Houdini MCP

> **Source:** [`capoomgit/houdini-mcp`](https://github.com/capoomgit/houdini-mcp) (the repo `capoom/houdini-mcp` redirects here). Third-party, not by SideFX. MIT.
>
> **Validation status:**
> - ✅ **Bridge install confirmed** (2026-06-01, Houdini 21.0.559 / macOS): registered at user scope; a live MCP `initialize` + `tools/list` handshake returned `HoudiniMCP 1.4.1` and all 12 tools below. See `docs/houdini-setup.md` + `docs/solutions/2026-06-01_houdini-mcp-setup-gotchas.md`.
> - 🚧 **In-Houdini behavior pending** — the `⟂ VALIDATE` items require Houdini actually running the `9876` socket server; confirm by experiment, then promote to confirmed and feed surprises to `frank-compound`.

## Architecture

Same pattern as RhinoMCP/BlenderMCP: an in-app **socket server** running inside Houdini + an **MCP server process** that bridges Claude ↔ Houdini over TCP.

- **Socket bridge:** `localhost:9876` (Houdini-side server, started via shelf tool).
- **MCP process:** `houdini_mcp_server.py`, launched by the client (`uv run python …`), speaks MCP over stdio and forwards commands to the socket.
- Houdini version: capoom docs reference **19.5**; paths adapt to your installed version. Find yours in Houdini's Python shell with `import hou; print(hou.homeHoudiniDirectory())`.

## Tool inventory (from source)

| Tool | Signature | Purpose |
|---|---|---|
| `get_scene_info` | `()` | Returns JSON scene/node info. **Survey tool** — run first, like Rhino's `get_document_summary`. |
| `create_node` | `(node_type, parent_path="/obj", name=None)` | Create a node at a network path. |
| `execute_houdini_code` | `(code: str)` | Run arbitrary Python in Houdini's `hou` environment. **The primary build & introspection tool.** |
| `render_single_view` | `(orthographic=False, rotation=[0,90,0], render_path, render_engine, karma_engine)` | Render one view to an image file. |
| `render_quad_views` | `(render_path, render_engine, karma_engine)` | Render four canonical views at once. **Primary review capture.** |
| `render_specific_camera` | `(camera_path, render_path, render_engine, karma_engine)` | Render from a named camera. |
| `opus_get_model_names` | `()` | List OPUS procedural-asset names (optional). |
| `opus_get_model_params_schema` | `(structure)` | OPUS model param schema (optional). |
| `opus_create_model` | `(structure, parameters: Dict, count=1)` | Batch-generate assets via OPUS API (optional). |
| `opus_variate_model` | `(result_id, count=12)` | Variations of an OPUS result (optional). |
| `opus_check_job_status` | `(batch_id)` | Poll OPUS batch status (optional). |
| `opus_import_model_url` | `(download_url, node_name=None)` | Import a USD asset from URL (optional). |

## How frank's spine maps onto Houdini

- **`frank-setup`** → `get_scene_info`; confirm units (`hou.setUnitLength`), `$HIP`, existing `/obj` network, and which network frank may write to. Record a dedicated subnet name (the Houdini analog of a Rhino layer) so rebuilds stay scope-isolated.
- **Layer 2 live grounding** → `execute_houdini_code` to introspect the API instead of guessing, e.g. list available SOP types, confirm a parm name, check a node's outputs:
  ```python
  import hou, json
  cat = hou.sopNodeTypeCategory()
  print(json.dumps(sorted(cat.nodeTypes().keys())[:50]))
  ```
  Pair with `frank-houdini-docs-researcher` for SideFX docs when introspection isn't enough.
- **`frank-build`** → procedural network built via `create_node` + `execute_houdini_code`. **Parametric** = node parameters / a controlling `null` of spare parms (or an HDA), not magic numbers. **VEX** = create an `attribwrangle` SOP and set its `snippet` parm:
  ```python
  geo = hou.node("/obj").createNode("geo", "frank_build")
  wr  = geo.createNode("attribwrangle", "frank_displace")
  wr.parm("snippet").set('@P.y += sin(@P.x*3.0)*0.2;')
  ```
  **Idempotency** = delete and rebuild only frank's own subnet each run; never touch sibling networks.
- **`frank-review`** → `render_quad_views` (or `render_single_view` at a matched `rotation`) to a temp path, then Read the image(s) and compare to the reference via `frank-silhouette-critic`. Houdini renders to **files** (no inline screenshot return), so capture = render-to-path → read file.

## ⟂ VALIDATE (confirm live, then compound)

1. ⟂ Does `execute_houdini_code` return `print()` stdout, or must results be assigned to a known variable / returned a specific way? (Determines how we read introspection output.)
2. ⟂ `render_*` requires a render engine — does it default to Karma/OpenGL, and what's the fastest engine for quick verification renders (likely OpenGL/Houdini-GL, not Karma)?
3. ⟂ Camera/rotation control: can we get a repeatable front-orthographic that matches a reference image's framing for silhouette comparison?
4. ⟂ Units handling — does the scene default to meters? Confirm before any fabrication-scale work.
5. ⟂ Error reporting — how do Python exceptions surface through the MCP (so `frank-build` can self-correct)?
6. ⟂ Scope isolation — confirm deleting a subnet by name is clean and doesn't orphan dependencies.

## Setup (to expose to a Claude Code session)

Full reproducible guide: **`docs/houdini-setup.md`**. Confirmed environment + the two required patches (add `requests`; make OPUS optional) are documented there and in the setup-gotchas learning. After the one-time install, each session needs only: `import houdinimcp` in Houdini (starts the `9876` server) + a Claude Code restart to load `mcp__houdini__*`.

## frank-review capture POLICY (render — confirmed 2026-06-01)

**Use `render_single_view`; NEVER `render_quad_views`.** `render_quad_views` renders four OpenGL ROP views *sequentially on Houdini's main thread*, and OpenGL rendering pumps the UI event loop. Under `hou.ui.addEventLoopCallback`, that re-enters the socket poll loop mid-render and (pre-hardening) permanently wedged the server — view 1 wrote (`MCP_OGL_RENDER_front_ortho.jpg`), views 2–4 never ran, and every subsequent command (even `1/0`) timed out until Houdini was restarted. Banned for frank.

Capture recipe (front-orthographic, matches a reference image's framing for `frank-silhouette-critic`):

```python
# one short, single-view render — returns fast, watermarked under Apprentice
render_single_view(
    orthographic=True,
    rotation=[0, 0, 0],          # front; vary per axis for other canonical views
    render_path="$HIP/frank_review_front.jpg",
)
```

Then **Read the written file back from `render_path`** — `render_single_view` *also* returns the image inline as `{"status":"success","format":"jpg","resolution":[512,512],"image_base64":"…"}`, but that base64 blob is large (~56 KB for 512×512) and overflows tool-result buffers, so rely on the file on disk, not the inline return. Note the render also adds scaffolding nodes to the scene — `/obj/MCP_CAMERA`, `/obj/MCP_CAM_CENTER`, and an `opengl` ROP at `/out/MCP_OGL_RENDER`; `frank-build`/`frank-review` should expect these and clean them for scope isolation. For multiple canonical views, call `render_single_view` four times (front/left/top/persp) with matched `rotation`; each call is short and the event-loop callback drains the socket between renders. This is strictly safer than one quad call (1 render vs 4, ~4x less main-thread occupancy, and on any failure the server now self-heals rather than wedging).

Even with the hardened server, prefer single-view: the server-side re-entrancy guard + client-reset guarantee **recovery** (a slow/abandoned render can no longer permanently deafen the accept loop), but a single render still occupies the main thread for its duration, so the UI briefly stalls. Quad would stack four such stalls into one unbounded main-thread block.

## ⟂ VALIDATE — resolved from observed evidence (2026-06-01)

1. ✅ **stdout returns: YES.** `execute_houdini_code` returns `print()` stdout (the plugin redirects stdout/stderr around the exec). Introspect by `print(...)` and read the returned text.
2. ✅ **opengl single-view: works, fast, watermarked.** OpenGL/Houdini-GL is the fast engine for verification renders; under **Apprentice** the output carries a license **watermark** (acceptable for silhouette/framing checks). Karma is slower; not needed for quick review.
3. ✅ **Repeatable front-orthographic: works.** `render_single_view(orthographic=True, rotation=[0,0,0], ...)` gives a repeatable front-ortho that can be matched to a reference image's framing for silhouette comparison.
4. ✅ **Units: Houdini is unitless** (dimensionless world units); the working convention is **~1 unit = 1 meter**. Confirm/set with `hou.setUnitLength` before any fabrication-scale work; no implicit meters default.
5. ✅ **Error surfacing: confirmed.** `execute_houdini_code("1/0")` returns a clean, prompt error (`Error (houdini): Code execution error: division by zero`) — no timeout, no wedge. `frank-build` gets the exception message back and can self-correct. (Verified live 2026-06-01, smoke step 4.)
6. ✅ **Scope isolation: works.** Deleting a named subnet is clean and does not orphan sibling networks; rebuild only frank's own subnet each run.
7. ⛔ **quad render: DEADLOCKS — BANNED.** See capture policy above. Root cause + server hardening: `docs/solutions/2026-06-01_houdini-mcp-render-deadlock.md`.

> Note: the **Tool inventory** above lists `render_quad_views` as "Primary review capture" — that label is now **superseded**. The primary review capture is `render_single_view`; `render_quad_views` is banned.

## Cross-References

- Sibling pack: `references/rhino-mcp.md`
- Render deadlock + server hardening: `docs/solutions/2026-06-01_houdini-mcp-render-deadlock.md`
- Setup gotchas: `docs/solutions/2026-06-01_houdini-mcp-setup-gotchas.md`
- Patterns this enforces: `knowledge/parametric-scripting.md`, `knowledge/verification.md`
