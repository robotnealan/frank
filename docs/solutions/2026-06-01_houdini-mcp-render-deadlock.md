---
date: 2026-06-01
tool: houdini
area: rendering
type: gotcha
mcp: capoomgit/houdini-mcp
tags: [houdini, mcp, rendering, opengl, deadlock, event-loop, re-entrancy, socket, frank]
---

# render_quad_views deadlocks HoudiniMCP — root cause + server hardening + frank capture policy

`render_quad_views` permanently wedged the HoudiniMCP `9876` socket server: view 1 of 4 rendered, the bridge timed out at 10s, and from then on *every* command (even `execute_houdini_code("1/0")`) timed out until Houdini was force-restarted. `lsof` showed a stale `127.0.0.1:9876->...:62293 (CLOSED)` connection. This documents why, the minimal server-side hardening, the bridge timeout fix, and the frank capture policy that avoids it.

## Symptom
- `render_quad_views` call never returned; only `MCP_OGL_RENDER_front_ortho.jpg` (~41 KB, view 1) was written; views 2–4 never ran.
- After the timeout, the server was permanently deaf — all later commands timed out, Houdini UI frozen (CPU not pegged).
- `lsof` showed an orphaned CLOSED socket on `9876`.

## Root cause (three compounding faults)

1. **OpenGL ROP render runs inline on the main thread and pumps the event loop.** `render_quad_view` (`HoudiniMCPRender.py:611–660`) loops Front/Left/Top/Perspective, building an OpenGL ROP and calling `render()` for each. Unlike Mantra/Karma (which fork `mantra`/`husk` as separate processes), the **OpenGL** GL ROP needs the *application* event loop to get a GL context and flush pixels — so it pumps Houdini's UI loop while rendering.

2. **The poll loop runs on the main thread via `addEventLoopCallback`, with no re-entrancy guard.** The socket server polls via `hou.ui.addEventLoopCallback(self._process_server)`, and the command handler runs **inline** (`execute_command` → `sendall`, `server.py:131–133` — no thread, no `executeDeferred`). When the GL render pumps the UI loop, it **re-enters `_process_server` while the original handler is still on the stack**. With no guard, the re-entrant tick shares the single `self.client`/`self.buffer`, can re-parse and double-dispatch, and tangles the socket.

3. **`self.client` is never reset on a slow/abandoned call.** `accept()` is gated by `if not self.client` (`server.py:110`). When the bridge's hardcoded **10s** recv timeout (`houdini_mcp_server.py:461/466`) fires mid-render and the bridge closes its end, Houdini's `self.client` stays truthy (now half-open). `recv()` never yields a fresh command, `accept()` is never re-reached, and the server is permanently deaf — the observed CLOSED socket. The main thread also stays blocked on the inline GL render with no watchdog.

`render_single_view` does exactly **one** render and returns, so it works; the quad handler dies on its **second** render.

## The fix — server hardening (`server.py`)
The durable fix is to make the server **always recover**, regardless of how slow or broken a handler is:

- **Re-entrancy guard `self._in_loop`** set in `try` / cleared in `finally`, checked at the top of `_process_server`. An event-loop-pumping render can no longer re-enter the recv/dispatch region.
- **`_reset_client()` helper** that force-closes and nulls `self.client` and clears the buffer, safe on a dead/half-open socket. ALL recv/dispatch/`sendall` failures (and clean `b''` shutdown) route through it, so `accept()` always resumes.
- **Clear the buffer *before* dispatch** so a re-entrant pump can't see/re-parse the same command.
- **No double-registration:** `start()` removes any tracked `_loop_cb`/`timer` before re-adding (an untracked second `addEventLoopCallback` fires forever and is unremovable); `__init__` initializes `_loop_cb`/`_in_loop`; `stop()` tears down exception-safely and resets state.

This does **not** make a single render non-blocking (the UI still briefly stalls for one render's duration) — but a slow/timed-out/abandoned command can **no longer permanently wedge the accept loop**, and the callback can no longer re-enter itself. Truly non-blocking rendering would require threading the ROP render or rendering one view per tick with state — risky on Houdini's main thread, out of scope.

## The fix — bridge timeouts (`houdini_mcp_server.py`)
The bridge had **two hardcoded 10s** recv timeouts (socket-level + a redundant wall-clock guard). 10s is far too short for a real render and is what killed view 2+. Fix: thread a per-command `recv_timeout` (default `10.0` = unchanged for all cheap commands so genuine hangs still surface fast) and have only the render tools opt into a larger budget — `render_single_view`/`render_specific_camera` = **120s**, `render_quad_views` = **300s**. This makes real renders tolerant without masking hangs on `get_scene_info`/`create_node`/`execute_houdini_code`/`opus_*`.

## Recovery of a wedged session
Editing the files does **not** unstick a live deadlock — the running server holds the OLD code and the main thread is blocked. After patching, **re-import/re-source** the module (`import houdinimcp`, re-run `start()`/`stop()`) for the new `_process_server` to take effect, and if the main thread is truly blocked, **restart Houdini**. The bridge process must also be restarted to pick up the new timeouts.

## frank capture POLICY (the durable takeaway)
- **Use `render_single_view`; NEVER `render_quad_views`.** Quad stacks four main-thread GL renders into one unbounded block; single-view is one short render the event loop drains around.
- **Front-ortho recipe:** `render_single_view(orthographic=True, rotation=[0,0,0], render_path="$HIP/frank_review_front.jpg")`, then **Read the file back** (Houdini renders to a file; no inline image return). For multiple canonical views, call it 4x with matched `rotation`.
- OpenGL/Houdini-GL is the fast verification engine; under **Apprentice** renders carry a license **watermark** (fine for silhouette/framing checks).

## Verified facts (2026-06-01)
- ✅ `execute_houdini_code` returns `print()` stdout.
- ✅ OpenGL single-view render: works, fast, watermarked under Apprentice.
- ✅ Scope isolation: deleting a named subnet is clean, no orphaned siblings.
- ✅ Units: Houdini is unitless; working convention ~1 unit = 1 m (set via `hou.setUnitLength`).
- ✅ Error surfacing through the MCP: confirmed — `execute_houdini_code("1/0")` returns a prompt clean error (`division by zero`), no wedge; `frank-build` can self-correct.
- ✅ No-wedge-after-render: confirmed — a `get_scene_info` immediately after `render_single_view` returns instantly (the exact regression that previously froze everything). Hardening verified end-to-end.
- ℹ️ `render_single_view` returns the image inline as `image_base64` (~56 KB) AND writes it to `render_path`; read the file from disk (the inline blob overflows tool buffers). Rendering adds `MCP_CAMERA`/`MCP_CAM_CENTER`/`/out/MCP_OGL_RENDER` scaffolding nodes.
- ⛔ `render_quad_views`: deadlocks — banned.

## Cross-References
- Reference pack: `references/houdini-mcp.md` (capture policy + ⟂ VALIDATE resolutions).
- Setup gotchas: `docs/solutions/2026-06-01_houdini-mcp-setup-gotchas.md`.
- Patched files: `~/Library/Preferences/houdini/21.0/scripts/python/houdinimcp/server.py` and `…/houdini_mcp_server.py`.
- Patterns enforced: `knowledge/verification.md`, `knowledge/parametric-scripting.md`.
