---
name: frank-build
description: "Write and run an idempotent, scope-isolated, named-parameter-block generator that builds the planned model through the connected modeling MCP, then capture the result. Use when the user says 'build this model', 'generate the geometry', 'run the build', 'make the sculpture/part/scene', or when a frank-plan modeling plan is ready to execute."
argument-hint: "[optional: a plan path to build, or a form description to build directly]"
---

# Build the Model

**Note: The current year is 2026.** Use this when dating any learning you compound and when searching for recent documentation.

`frank-build` writes and **runs** the generator. `frank-plan` decided **WHAT** to model and **HOW**; this skill emits the runnable generator that realizes those decisions, executes it through the connected modeling MCP, and captures the result so `frank-review` can compare it to the reference. This skill is the one that touches geometry — so it carries the discipline that keeps a live document safe: every generator it emits is idempotent, scope-isolated to a single named layer/subnet, driven by one named parameter block, and re-runnable without accumulating geometry or disturbing anything frank does not own.

**When directly invoked, always build.** Never classify a direct invocation as "not a modeling task" and abandon the workflow. If there is no plan and the form is unclear, ask one or two clarifying questions to establish enough context — but always stay in the build workflow. If a plan exists, read it and build it; do not re-decide what the plan already settled.

## Interaction Method

When asking the user a question, use the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_user` in Gemini, `ask_user` in Pi (requires the `pi-ask-user` extension). Fall back to numbered options in chat only when no blocking tool exists in the harness or the call errors (e.g., Codex edit modes) — not because a schema load is required. Never silently skip the question.

Ask one question at a time. Prefer a concise single-select choice when natural options exist.

## Core Principles

1. **Ground signatures live, before emitting calls.** Hallucinated API calls are the #1 LLM-CAD failure, and a wrong call here runs immediately against a real document. Confirm every primitive, parm name, and enum the generator leans on through the docs-researcher (live MCP introspection) *before* it appears in emitted code — never from memory. If a signature can't be confirmed, the build surfaces that gap rather than guessing.
2. **One named parameter block, no magic numbers.** Every literal that affects geometry is a named entry in the `P = {...}` block (Rhino) or a controlling null/spare-parm node / HDA (Houdini), or a value *derived* from one. A human can retune the whole model from the block alone, without editing the body.
3. **Scope isolation is non-negotiable.** The generator owns exactly one named scope — a layer (Rhino) or a subnet (Houdini) — and touches nothing outside it. A clear broader than frank's own scope is the single most dangerous defect a generator can have. The **foreign-object invariant** holds: object/node counts on every scope frank does not own are identical before and after every run.
4. **Re-runnable, deterministic, convergent.** Running the generator twice leaves the document in the same state as running it once — clear-then-rebuild the owned scope, no accumulation, no unseeded randomness, transient construction geometry cleaned in `try/finally`. Same parameter block → same geometry.
5. **Guards WARN, never emit garbage.** Geometric guards (self-overlap, bbox/scale, per-scope counts) surface a clear WARNING naming the offending parameter — they do not silently push suspect geometry into the document. A guard that logs-and-continues into emission is a guard in name only.
6. **Capture per the tool's policy — exactly.** Rhino: `capture_viewport` returns inline; pin the camera and write the image to a file. Houdini: `render_single_view` only → **Read the render from disk** → delete the scaffolding nodes; **`render_quad_views` is BANNED** (it deadlocks the server). These are hard rules, not preferences.
7. **Honor user-named resources and the plan.** When a plan, a target layer, a specific primitive, or a reference is named, treat it as authoritative. Read/discover it before assuming it's unavailable. If it fails or doesn't exist, say so explicitly rather than silently substituting.

## When to Use

Use `frank-build` when:

- A `frank-plan` modeling plan is ready and the geometry needs to be generated.
- A form is well-enough specified to emit a re-runnable generator (a named parameter surface, a chosen primitive set, a scope to own).
- You want the geometry built *and captured* so `frank-review` can compare it to the reference.

Do **not** use `frank-build` to decide what to model or which primitives to use (that's `frank-plan`), to run the capture→compare→adjust acceptance loop (that's `frank-review` — `frank-build` produces the *first* capture; the iterative compare-and-tune loop is `frank-review`'s), or to record a solved gotcha (that's `frank-compound`).

## Build Quality Bar

A build is done when:

- Every emitted primitive/parm/enum was **confirmed live** before it was written, with its confirming source noted.
- The generator carries **one named parameter block** with no magic numbers; derived values are computed from the block.
- The generator is **scope-isolated** (owns one named layer/subnet) and **idempotent** (clears only its own scope; the foreign-object invariant holds across re-runs — verified, not assumed).
- **Guards WARN** for the failure modes this geometry can hit; none silently emit bad geometry.
- The generator **ran clean** through the MCP (or its error surfaced and the build self-corrected), and a **capture** was produced per the tool's POLICY and written to a known file path for `frank-review`.

## Workflow

### Phase 0: Detect Tool and Source the Plan

#### 0.1 Detect the active modeling MCP family

Determine which modeling MCP is connected before anything else — the generator's primitives, scope unit, and capture policy are tool-specific. This is the **same detection recipe** `frank-setup` and `frank-plan` use (MCP-family detection is the dispatch primitive — distinct from harness detection).

- Inspect which MCP tools are present in your available toolset: an `mcp__rhino__*` family means **Rhino**; an `mcp__houdini__*` family means **Houdini** (deferred tools surface by name and load via `ToolSearch`).
- **Confirm** the family is live and responsive by issuing its survey call — `get_document_summary` for Rhino, `get_scene_info` for Houdini. A successful response proves a live, responsive connection; a failure (e.g. Rhino's `Could not connect to Rhino. Make sure the Rhino addon is running.`) means the app isn't actually reachable.
- **Both families present** → ask the user which to target (see Interaction Method).
- **Neither present, or the survey call fails** → halt and point the user at setup: `docs/houdini-setup.md` for Houdini, or the Rhino MCP setup for Rhino. Suggest `/frank-setup`. Do not emit generator code against a tool that isn't connected.

If a plan recorded the chosen family, prefer it — but still confirm the survey call succeeds now (a recorded family is not a live connection). Record the chosen family: it selects which `references/<tool>-mcp.md` pack and which docs-researcher (`frank-rhino-docs-researcher` for Rhino, `frank-houdini-docs-researcher` for Houdini) the rest of the workflow uses.

#### 0.2 Source the plan and the parameter surface

<plan> #$ARGUMENTS </plan>

- **If the input names a plan in `docs/plans/`,** read it completely. The plan's parameter-block sketch, chosen primitives (with their grounding source), scope/idempotency contract, and verification assertions are your build inputs — do not re-decide them. Carry the plan's named scope (layer/subnet) and its acceptance criteria forward.
- **If the input is a form description with no plan,** you may build directly for small, well-understood forms — but if the form is organic, fabrication-bound, or otherwise non-trivial, recommend `/frank-plan` first so the primitives are grounded and the param surface is designed before geometry exists. Honor the user's choice.
- **If the input is empty,** ask: "What would you like to build? Point me at a `frank-plan` plan, or describe the form." Then wait for their response.

Survey the live document once for build context (already issued in 0.1): record **units and tolerance** (Rhino) or **unit length** (Houdini — it is unitless; ~1 unit = 1 m by convention), the **existing layers/networks** (the foreign-object invariant the build must hold identical), and **the dedicated scope** the build will own. Do **not** create, modify, or delete geometry while surveying.

### Phase 1: Layer-2 Live Grounding — Confirm Signatures Before Emitting Calls

The plan named the primitives; this phase confirms their **exact, currently-valid** signatures against the live, connected app — *before* a single call is written into the generator. The running app is the ground truth; a signature recalled from memory or carried stale from an old plan is a build failure (or worse, a call that mutates the wrong geometry).

Dispatch the connected family's docs-researcher to confirm the exact signatures. Use the bare, frank-prefixed name; do not strip the prefix and do not add a path namespace.

- Task frank-<tool>-docs-researcher(Confirm live, in-session, the exact signatures of the primitives this build emits — {primitive list from the plan, e.g. AddInterpCurve / AddSweep1 / CapPlanarHoles for Rhino, or the SOP types / parm names / VEX functions for Houdini}. For each, return the confirmed signature (name, parameter order, defaults, enum values, return) and how it was confirmed — live MCP introspection or official docs — or flag that it could not be confirmed. Restate any recorded gotcha (e.g. sweep1 framing twist, knotstyle overshoot) so the build inherits the fix. Survey context: {units, tolerance, existing layers/scope from Phase 0}.)

Replace `<tool>` with the connected family — `Task frank-rhino-docs-researcher(...)` or `Task frank-houdini-docs-researcher(...)`.

Consolidate the return:

- For each primitive: the **confirmed signature** and its source, or a flagged "could not confirm." **Do not emit a call for an unconfirmed signature** — either confirm it via the family's own introspection (`get_rhinoscript_docs` / `search_rhinoscript_functions` for Rhino; `execute_houdini_code` reflection for Houdini — the reference pack names these idioms), or surface the gap to the user. A flagged "I couldn't confirm this" is far more useful than a fabricated parameter list that fails at runtime.
- Fold any **recorded gotcha** the researcher surfaced into the generator (the fix, not just the signature).

> The Rhino server itself flags `get_rhinoscript_docs(topic)` as **required** before `execute_rhinoscript_python_code` — skipping it causes signature-guess syntax errors. Live introspection precedes code emission, always.

### Phase 2: Load the Build Canon and the Tool's Build + Capture Policy

**STOP. Before emitting any generator, read `knowledge/parametric-scripting.md`.** It is the rubric the generator must satisfy — one named parameter block, no magic numbers, idempotent scope-isolated rebuild, determinism, units/tolerance respect, generator-vs-result separation, and guards that warn rather than emit. Building from memory instead of the canon produces a script that works once but is not a re-runnable parametric instrument, and it drifts from the standard `frank-parametric-architect` grades against.

**STOP. Before you build or capture, read the build + capture POLICY section of `references/<tool>-mcp.md` (the connected family's pack — `rhino-mcp.md` or `houdini-mcp.md`).** This is where the tool-specific contract lives: which build tool to drive, the exact scope-isolation idiom, and — critically — the capture POLICY. Skipping it on the Houdini track risks calling `render_quad_views`, which **deadlocks the server** (it stacks four unbounded main-thread OpenGL ROP renders); skipping it on either track risks an unpinned-camera capture that makes `frank-review`'s silhouette comparison meaningless. The pack also marks which high-level helpers are **proven** versus **present-but-unverified** (verify the latter live before relying on them; prefer the proven `execute_rhinoscript_python_code` path when in doubt).

The reference pack is the *only* place tool-specific calls and policies live — load it here, do not carry tool detail in the skill body.

### Phase 3: Emit the Generator

Write a generator that is **idempotent, scope-isolated, driven by one named parameter block, and re-runnable** — the contract `examples/rhino/spiral-ribbon-sculpture.py` makes concrete (read it for the *pattern*, not the sculpture). The shape is identical across tools; only the scope unit and call surface differ.

**Both tracks share this structure:**

- **One named parameter block** at the top — the entire tunable surface, no magic numbers in the body. Derived quantities are computed *from* the block, never declared beside it.
- **Snapshot foreign-scope counts before any mutation**, then **assert them unchanged after** — the foreign-object invariant, observable as a printed per-scope count check. Use a generic loop over the existing scopes, **not** project-specific names.
- **Guards that WARN, not emit** — for the failure modes this geometry can actually hit (orientation-aware self-overlap for sweeps/ribbons, bbox/scale sanity, per-scope object count). Each WARN names the offending parameter and points at the knob to turn.
- **`try/finally` transient cleanup** — scratch/construction geometry consumed mid-build is removed even if a later step raises, so nothing escapes the rebuild and drifts across re-runs.

**Rhino — the three idempotent layer helpers + the foreign-layer invariant:**

- `_ensure_layer(name)` — create the owned layer if absent, make it current. Idempotent.
- `_clear_layer(name)` — delete **only** `rs.ObjectsByLayer(name)` — never iterate the whole document, never touch any other layer. This is what makes a re-run converge instead of accumulate.
- `_to_layer(obj_ids, name)` — assign every created object back to the owned layer explicitly, so nothing lands off-layer and escapes the delete-by-layer rebuild.
- `build()` calls `_ensure_layer(layer)` then `_clear_layer(layer)` at the top; the **foreign-layer object-count invariant** is the safety contract — every layer *other than* `P["layer"]` has the identical object count before and after the run.

**Houdini — own-named-subnet delete + rebuild:**

- The generator owns exactly one named subnet (the Houdini analog of a Rhino layer). At the top of each run it **deletes its own subnet and rebuilds it** — it never touches a sibling network. Deleting a named subnet is clean and orphans no dependencies (confirmed; see the reference pack).
- **Parametric** = node parameters / a controlling null of spare parms (or an HDA), not magic numbers. **VEX** = an `attribwrangle` SOP with its `snippet` parm set. The same foreign-scope invariant applies: every `/obj` network frank does not own has the same node count before and after.

**Optionally consult `frank-parametric-architect` on the param-block shape** — dispatch it to audit the drafted generator's parametric integrity (named block, scope isolation, re-runnability, guard discipline) *before* you run the script through the MCP, so structural defects (an over-broad clear, a magic-number-riddled body, a missing guard) are caught at design time rather than after they've mutated a live document. Use it for non-trivial generators or when the param surface is large; skip it for a small, obviously-clean build.

- Task frank-parametric-architect(Audit this drafted generator's parametric shape before it runs against the live document: {the generator source}. Grade it against knowledge/parametric-scripting.md — named param block / no magic numbers, idempotent scope isolation (the foreign-object invariant), re-runnability/determinism, and guard discipline (warn-not-emit). Return a prose report with concrete fixes ordered by risk; flag anything that endangers the foreign-object invariant or commits unguarded geometry first.)

Apply its must-fix recommendations before running.

### Phase 4: Run the Generator Through the MCP

Run the generator via the connected family's build tool — `execute_rhinoscript_python_code` (Rhino) or `create_node` + `execute_houdini_code` (Houdini) — exactly as the reference pack's build section specifies.

- **Read the run output.** Both servers surface Python exceptions cleanly (Rhino returns the error text; Houdini's `execute_houdini_code` returns the exception message, e.g. `Code execution error: division by zero`). On an error, **self-correct** — re-confirm the failing signature via Phase 1 introspection, fix the call, and re-run. Do not paper over a failure.
- **Confirm the invariant printed clean.** The generator's foreign-scope count check should report "invariant OK" (or name the drift). If it reports drift, the generator touched a scope it does not own — fix the clear/scope logic before proceeding; this is the load-bearing safety property.
- **Confirm the guards.** Read any WARN lines the generator printed (self-overlap, bbox/scale). A WARN is not a build failure — it is a signal for the human to retune — but surface it; don't bury it.
- Re-run once to **prove idempotency** when the build is parametric: a second run must leave every foreign-scope count identical and the owned scope rebuilt to the same state, not doubled.

### Phase 5: Capture the Result

Produce the first capture so `frank-review` has something to compare. Capture **per the POLICY loaded in Phase 2** — the two tracks differ, and the Houdini track carries a hard ban.

**Rhino — inline capture:**

- `capture_viewport` from a **pinned / recorded camera** → the image returns **inline**. Record the camera (viewport name, `position`, `target`, lens/focal length, or a named view) so `frank-review` can reuse the exact frame.
- Write the inline image to a known file path (e.g. under `/tmp/frank/...`) and note that path for `frank-review`. There is no render-to-disk dance and no scaffolding to clean — Rhino's capture path is the strictly simpler half.

**Houdini — render to disk, then read and clean:**

- `render_single_view(orthographic=True, rotation=[...], render_path=...)` at a pinned rotation that matches the reference's framing. **Call `render_single_view` — NEVER `render_quad_views`.** Quad stacks four unbounded main-thread OpenGL ROP renders and deadlocks the server; it is **BANNED for frank**. For multiple canonical views, call `render_single_view` once per view (front/left/top/persp) with matched `rotation` — each call is short and the event-loop callback drains the socket between renders.
- **`Read` the image file at `render_path`** — `render_single_view` *also* returns the image inline as `image_base64`, but that blob (~56 KB for 512×512) overflows tool-result buffers; **ignore the inline base64 and read the file on disk.**
- **Delete the three scaffolding nodes** the render adds — `/obj/MCP_CAMERA`, `/obj/MCP_CAM_CENTER`, and the `opengl` ROP at `/out/MCP_OGL_RENDER` — to keep the scene scope-isolated. Note the render output path for `frank-review`.

> **STOP-GATE BAN — restated, because it is tempting in-session:** `render_quad_views` is a loaded tool, but it **DEADLOCKS the server** and is **BANNED for frank**. Use `render_single_view` only, on every Houdini capture, every time. (Root cause + server hardening: `docs/solutions/2026-06-01_houdini-mcp-render-deadlock.md`.)

### Phase 6: Hand Off to Review

Report what was built and captured:

- The generator's outcome — the printed bbox/scale, the foreign-scope invariant result ("OK" or named drift), and any guard WARNs the human should see.
- The **capture file path(s)** and the **pinned camera/rotation** used, so `frank-review` can reuse the exact frame.
- Whether idempotency was proven (the second-run check).

Then offer the handoff via the Interaction Method: review it now with `/frank-review` (capture → compare → adjust against the reference, with human sign-off), tune a parameter and re-build, or — if the build surfaced a surprising tool gotcha — record it with `/frank-compound`. Never silently skip the question.

All file references you record use repo-relative paths in any artifact; absolute paths only for the live capture files `frank-review` must read.

## Cross-References

- Golden example (the canonical idempotent layer-scoped generator `frank-build` emits): `examples/rhino/spiral-ribbon-sculpture.py`
- Reference packs (build + capture POLICY, scope unit, proven-vs-unverified tools): `references/rhino-mcp.md`, `references/houdini-mcp.md`
- Canon the generator must satisfy: `knowledge/parametric-scripting.md` (named block, idempotent scope-isolated rebuild, guards-that-warn), `knowledge/verification.md` (the capture the build produces feeds the pinned-camera compare loop)
- Agents dispatched: `frank-rhino-docs-researcher` / `frank-houdini-docs-researcher` (live signature confirmation), `frank-parametric-architect` (param-block + scope-isolation shape audit)
- Upstream skill: `frank-plan` (decides the primitives, param surface, and scope this skill builds)
- Downstream skills: `frank-review` (capture → compare → adjust against the reference), `frank-compound` (record a surprising gotcha)
- Houdini capture hard rule + root cause: `docs/solutions/2026-06-01_houdini-mcp-render-deadlock.md`
