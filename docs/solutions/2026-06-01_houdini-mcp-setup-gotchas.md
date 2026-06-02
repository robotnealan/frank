---
date: 2026-06-01
tool: houdini
area: setup
type: gotcha
mcp: capoomgit/houdini-mcp
tags: [houdini, mcp, setup, uv, opus]
---

# Wiring capoomgit/houdini-mcp into Claude Code (macOS) — three gotchas

Setting up [`capoomgit/houdini-mcp`](https://github.com/capoomgit/houdini-mcp) as a Claude Code MCP server, the README (Windows + Claude Desktop) hides three things that break a clean install.

## Confirmed working environment
- Houdini **21.0.559** (`/Applications/Houdini/Current`), `hython` = Python **3.11**.
- Bridge (external MCP process) run by **uv** on its own Python **3.12** venv — independent of Houdini's 3.11. The `pyproject` `requires-python >=3.12` applies only to the bridge; the in-Houdini socket server (`server.py`) is stdlib-only and runs fine on 3.11.
- Package cloned into the Houdini user dir: `~/Library/Preferences/houdini/21.0/scripts/python/houdinimcp/` (find yours with `hou.homeHoudiniDirectory()` — **not** the Windows `Documents/houdiniXX.X` path).

## Gotcha 1 — `uv run` needs `--directory`
`uv run python <abspath>` resolves the project from **cwd**, so launching from anywhere but the package dir gives `ModuleNotFoundError: No module named 'mcp'`. Register the server with an explicit project dir:
```bash
claude mcp add houdini --scope user -- \
  uv run --directory <pkg_dir> python <pkg_dir>/houdini_mcp_server.py
```

## Gotcha 2 — undeclared `requests` dependency
`houdini_mcp_server.py` imports `requests` (OPUS path) but `pyproject.toml` only lists `mcp[cli]`. → `ModuleNotFoundError: No module named 'requests'`. Fix: `uv add requests`. (`langchain` is also imported but properly guarded with try/except, so it's genuinely optional.)

## Gotcha 3 — OPUS keys are a HARD startup requirement
`main()` calls `sys.exit(1)` if `RAPIDAPI_HOST_URL/HOST/KEY` aren't set — meaning you **cannot create a box without a paid RapidAPI OPUS subscription**. That's wrong; OPUS is an optional third-party asset API. Patch the guard in `main()` to warn-and-continue instead of exiting:
```python
if not RAPIDAPI_HOST_URL or not RAPIDAPI_HOST or not RAPIDAPI_KEY:
     logger.warning("OPUS RapidAPI keys not set -- opus_* tools disabled. Core Houdini tools will run.")
# (removed: logger.critical(...); sys.exit(1))
```
Core tools (`get_scene_info`, `create_node`, `execute_houdini_code`, `render_*`) then work; `opus_*` tools just error if called. **Note:** this edits a vendored clone — a future `git pull` reverts it; re-apply or fork.

## Gotcha 4 — PySide2 import breaks on Houdini 20+/21
`server.py` (the in-Houdini side) does `from PySide2 import QtWidgets, QtCore`, but Houdini 20+/21 ship **PySide6 (Qt6)** — so `import houdinimcp` fails with `ModuleNotFoundError: No module named 'PySide2'`. The only Qt usage is a single `QtCore.QTimer` (identical across bindings; `QtWidgets` is imported but unused). Fix — prefer PySide6, fall back to PySide2:
```python
try:
    from PySide6 import QtWidgets, QtCore  # Houdini 20+/21 (Qt6)
except ImportError:
    from PySide2 import QtWidgets, QtCore  # Houdini 19.5 (Qt5)
```

## Gotcha 5 — License Administrator points at the online server by default
Symptom: "Your sidefx.com account is not associated with a customer account." The Administrator defaults to the `www.sidefx.com` enterprise server (paid customers only). For **free Apprentice**: in License Administrator, switch the account dropdown to **"Switch to on-premise license server (sesinetd)"**, remove `www.sidefx.com`, add **Local Server**, UPDATE, then **General ▸ "Activate Apprentice"**. Do **not** use File ▸ Login. Re-activate every 30 days. Diagnose with `sesictrl print-server` (shows configured server) and `sesictrl print-license` (shows installed keys).

## Validation without Houdini
You can confirm the bridge end-to-end before Houdini is even running — feed it an MCP `initialize` + `tools/list` over stdio and check the response. Tool listing doesn't touch the `localhost:9876` socket, so a healthy handshake proves the install:
```
INIT OK -> HoudiniMCP 1.4.1 | protocol 2024-11-05  → 12 tools listed
```

## Still requires the human
- **Start the in-Houdini socket server** (GUI): `import houdinimcp` in Houdini's Python Shell (auto-starts via `__init__.py`) → listens on `localhost:9876`.
- **Restart the MCP client** so it loads the newly-registered server.

## Cross-references
- `references/houdini-mcp.md`, `docs/houdini-setup.md`
