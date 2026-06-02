# Connecting HoudiniMCP to Claude Code

A reproducible setup for the [`capoomgit/houdini-mcp`](https://github.com/capoomgit/houdini-mcp) bridge so `frank` can drive Houdini. Written from a verified macOS install (Houdini 21.0). Windows/Linux differ only in paths.

> See `docs/solutions/2026-06-01_houdini-mcp-setup-gotchas.md` for *why* several of these steps are needed (undeclared deps, OPUS hard-fail, `uv` cwd).

## Prerequisites
- SideFX Houdini installed (any license: Apprentice/Indie/Core/FX).
- [`uv`](https://docs.astral.sh/uv/) and `git`.
- Claude Code (`claude` CLI).

## One-time install

1. **Find your Houdini user dir.** In Houdini's Python Shell:
   ```python
   import hou; print(hou.homeHoudiniDirectory())
   ```
   macOS example: `~/Library/Preferences/houdini/21.0`. The Python path is `<that>/scripts/python`.

2. **Clone the bridge into it** (the folder must be named `houdinimcp`):
   ```bash
   PKG="$HOME/Library/Preferences/houdini/21.0/scripts/python/houdinimcp"
   mkdir -p "$(dirname "$PKG")"
   git clone --depth 1 https://github.com/capoomgit/houdini-mcp "$PKG"
   ```

3. **Build the bridge env** (uv provisions Python 3.12 + deps; Houdini's own 3.11 is used only for the in-app server, so there's no conflict):
   ```bash
   cd "$PKG" && uv sync && uv add requests
   ```

4. **Make OPUS optional** (otherwise the bridge `sys.exit`s without a paid RapidAPI key). In `houdini_mcp_server.py`, change the OPUS check inside `main()` from `logger.critical(...) / sys.exit(1)` to a `logger.warning(...)` that falls through to `mcp.run()`. (`frank-setup` automates this.)

5. **Register with Claude Code** (user scope → available in every project; `--directory` is required so `uv` finds the right venv):
   ```bash
   claude mcp add houdini --scope user -- \
     uv run --directory "$PKG" python "$PKG/houdini_mcp_server.py"
   ```

6. **Verify the bridge** without Houdini (a healthy `initialize` + `tools/list` proves the install):
   ```bash
   printf '%s\n%s\n%s\n' \
     '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}' \
     '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
     '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
   | uv run --directory "$PKG" python "$PKG/houdini_mcp_server.py" 2>/dev/null
   ```
   Expect `HoudiniMCP 1.4.1` and a `tools` array (`get_scene_info`, `create_node`, `execute_houdini_code`, `render_*`).

## Every session

1. **Start the in-Houdini socket server.** In Houdini's Python Shell:
   ```python
   import houdinimcp        # auto-starts; listens on localhost:9876
   # houdinimcp.stop_server()  # to stop
   ```
   *(Optional: add a shelf tool that toggles `houdinimcp.start_server()` / `stop_server()`.)*
2. **Restart Claude Code** so it loads the `houdini` server (only needed the first time after step 5, then whenever Houdini's server is freshly started in a new client session).
3. Run `/frank-setup` to confirm `mcp__houdini__*` tools are live and survey the scene.

## OPUS (optional)
The `opus_*` tools need a RapidAPI OPUS subscription. Put the key in `houdinimcp/urls.env` (`RAPIDAPI_KEY=...`). Not required for any core modeling.
