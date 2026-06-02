---
name: frank-setup
description: "Check the modeling MCP connection and tell frank which tool it's driving. Detects the Claude Code harness and the connected modeling MCP family (Rhino vs Houdini), confirms a live connection, and records units/tolerance/scope so frank knows what it may write to. Use when 'set up frank', 'connect my modeler', or 'check the modeling MCP'."
disable-model-invocation: true
---

# Frank Setup

## Interaction Method

Ask the user each question below using the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded). Fall back to presenting the question as a numbered list in chat only when no blocking tool exists in the harness or the call errors — not because a schema load is required. Ask one question at a time. Never silently skip the question.

Interactive setup for frank — confirms which modeling MCP is connected, proves the connection is live, and records the document/scene facts (units, tolerance, scope) so `frank-plan`, `frank-build`, and `frank-review` know exactly what they may touch. This is a deliberate, user-run check; it does not auto-fire and it does not modify any geometry.

## Two detection steps (run in order, independent)

Setup is **two sequential, independent** checks. The first identifies the **harness** (which Claude Code session frank is running in); the second identifies the **connected modeling MCP** (which app frank will drive). They are not the same thing — the harness can be Claude Code while no modeler is connected, and a modeler can be connected without frank being able to write to it.

Run Step 1, then Step 2. Do not collapse them.

## Step 1: Harness detection

**Plugin root (pre-resolved):** !`echo "${CLAUDE_PLUGIN_ROOT}"`

If the line above resolved to an absolute path (starts with `/` and contains no `${`), this is a Claude Code session and the frank slash commands (`/frank-plan`, `/frank-build`, `/frank-review`, `/frank-compound`) are available. Anything else — empty, the literal `${CLAUDE_PLUGIN_ROOT}` token, or an unresolved command string like `echo "${CLAUDE_PLUGIN_ROOT}"` left in place by a non-Claude harness that doesn't process `!` pre-resolution — means this is not a Claude Code session that loaded frank as a plugin; report that frank's slash commands may not resolve and stop, since the rest of setup assumes the plugin's MCP toolset is available.

This step identifies the harness **only**. It says nothing about whether a modeler is connected — that is Step 2.

## Step 2: MCP-family detection

frank is tool-agnostic: it drives whichever modeling MCP family is connected. Determine the connected family by inspecting which tools are present in this session's toolset, then **confirm** with that family's survey call.

### 2.1 Inspect the toolset

Check which MCP tool family is present:

- **Rhino** — `mcp__rhino__*` tools (e.g. `mcp__rhino__get_document_summary`, `mcp__rhino__execute_rhinoscript_python_code`, `mcp__rhino__capture_viewport`).
- **Houdini** — `mcp__houdini__*` tools (e.g. `mcp__houdini__get_scene_info`, `mcp__houdini__execute_houdini_code`, `mcp__houdini__render_single_view`).

Claude Code surfaces a connected MCP server's tools in the available toolset; deferred tools appear by name and load via `ToolSearch`. A family being **present in the toolset** means the MCP *server* is registered — it does **not** yet prove the modeling app is running and responsive. That is what 2.2 confirms.

### 2.2 Confirm with the family's survey call

Presence in the toolset is necessary but not sufficient. Issue the family's survey call — a successful response proves a live, responsive connection to the running app:

- **Rhino** → `mcp__rhino__get_document_summary()` (the analog of Houdini's `get_scene_info`).
- **Houdini** → `mcp__houdini__get_scene_info()`.

A connection error (e.g. Rhino's `Could not connect to Rhino. Make sure the Rhino addon is running.`) means the **server is registered but the app is not listening** — treat this family as *registered-but-not-live* and tell the user to start the app's in-app MCP server, then re-run `/frank-setup`. Do not record facts from a family that failed its survey call.

### 2.3 Resolve the target family

- **Exactly one family present and live** → that is the target. Proceed to Step 3.
- **Both families present and live** → ask the user which one this setup is for, using the **Interaction Method** above (AskUserQuestion; numbered fallback only if the tool is unavailable or errors). Offer **Rhino** and **Houdini** as the options. Record the choice as the target family.
- **Neither family present (or both registered-but-not-live)** → halt and point the user at setup. For **Houdini**, the reproducible guide is `docs/houdini-setup.md`; for **Rhino**, the Rhino MCP plugin must be installed and its in-app server started (see `references/rhino-mcp.md` → Architecture / Setup). Do not proceed to Step 3 without a live family.

## Step 3: Load the chosen pack and record the scope

**STOP. Before recording any document facts, read the Architecture and survey/connection sections of the chosen tool's reference pack — `references/rhino-mcp.md` for Rhino or `references/houdini-mcp.md` for Houdini.** Skipping this means you won't know which survey/state calls are authoritative, what "scope" means on this tool (a Rhino **layer** vs a Houdini **subnet**), or the tool's capture/units quirks — and you'll guess facts that `frank-build`/`frank-review` then trust. Load **only** the connected family's pack; never load the absent family's pack, and never error on the absent family.

With the pack loaded, record the facts frank's downstream skills depend on. These come from the survey call in 2.2 (re-query as needed); do **not** modify the document or scene to gather them.

### Rhino

Record:

- **Units** — the document's model units (e.g. millimeters, inches).
- **Absolute tolerance** — the document tolerance (governs `frank-build` precision and verification assertions).
- **Existing layers** — the current layer list and per-layer object counts. This is the **foreign-layer baseline**: `frank-build` must leave every layer it does not own with an *identical object count* before and after a run. Note which layer(s) frank may write to (frank owns its own named layer; everything else is foreign and read-only).

### Houdini

Record:

- **Scene / `$HIP`** — the current scene file and the `/obj` network state.
- **frank's subnet** — a dedicated, named subnet (the Houdini analog of a Rhino layer) that frank owns and rebuilds each run; everything outside it is foreign and untouched. Note its path/name (or that one needs creating).
- **Unit length** — Houdini is unitless (~1 unit = 1 meter by convention); confirm or note the working unit length (`hou.setUnitLength`) before any fabrication-scale work.

## Step 4: Report

Tell the user, concisely:

1. **Harness** — whether this is a Claude Code session with frank's slash commands available (from Step 1).
2. **Connected family** — which modeling MCP is live (`rhino` or `houdini`), confirmed via its survey call. If a family was registered-but-not-live, say so and give the re-run instruction.
3. **Recorded facts** — units + tolerance + existing layers (Rhino) or scene + frank's subnet + unit length (Houdini).
4. **What frank may write to** — the single scope frank owns (its named layer / subnet), and the explicit reminder that every foreign layer/network is read-only and its object count is invariant across `frank-build` runs.

Then point the user to the next step: with a live connection recorded, `/frank-plan` is the place to start a modeling task.

## Cross-References

- Rhino reference pack: `references/rhino-mcp.md`
- Houdini reference pack: `references/houdini-mcp.md`
- Houdini connection guide: `docs/houdini-setup.md`
- Scope/idempotency contract this records: `knowledge/parametric-scripting.md`
- Downstream consumers of the recorded facts: `skills/frank-plan/SKILL.md`, `skills/frank-build/SKILL.md`, `skills/frank-review/SKILL.md`
