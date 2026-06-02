---
name: frank-plan
description: "Produce a structured modeling plan before any geometry is built — intake the reference, choose the artifact type and fidelity target, survey the live document, ground primitive choices via researcher dispatch, and design the named parameter block plus geometric verification assertions. Use when the user says 'plan this model', 'how should we model X', 'plan the sculpture/part/scene', or when a reference image is ready to turn into a build."
argument-hint: "[optional: reference image path/URL, a form description, or a plan path to revise]"
---

# Create Modeling Plan

**Note: The current year is 2026.** Use this when dating plans and searching for recent documentation.

`frank-plan` defines **WHAT** to model and **HOW** to approach it. `frank-build` writes and runs the generator. `frank-review` captures and compares the result. This skill produces a durable, decision-bearing modeling plan — it does **not** write or run generator code, touch geometry, or capture viewports. If the answer depends on running a script and seeing what the geometry does, that belongs in `frank-build`, not here.

**When directly invoked, always plan.** Never classify a direct invocation as "not a modeling task" and abandon the workflow. If the input is unclear, ask one or two clarifying questions to establish enough context — but always stay in the planning workflow.

## Interaction Method

When asking the user a question, use the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_user` in Gemini, `ask_user` in Pi (requires the `pi-ask-user` extension). Fall back to numbered options in chat only when no blocking tool exists in the harness or the call errors (e.g., Codex edit modes) — not because a schema load is required. Never silently skip the question.

Ask one question at a time. Prefer a concise single-select choice when natural options exist.

## Core Principles

1. **Decisions, not generator code.** Capture the artifact type, fidelity target, surveyed document state, chosen primitives, the named parameter block, and the geometric verification assertions. Do **not** pre-write the RhinoScript/VEX generator — that is `frank-build`'s job. A directional parameter-block sketch (names + indicative defaults) and an assertion list are welcome; a runnable script is not.
2. **Ground primitives, never guess.** Hallucinated API calls are the #1 LLM-CAD failure. Confirm the primitives the plan leans on through the docs-researcher (live MCP introspection), not from memory. If a primitive can't be confirmed, the plan names that as an open question rather than asserting a signature.
3. **Survey before you design.** Read the live document (units, tolerance, existing layers/networks) before choosing a layer name or a scale. Never touch existing geometry while surveying — `frank-plan` is read-only over the model.
4. **Right-size the artifact.** A quick visual study gets a compact plan. A fabrication-ready part gets scope boundaries, a self-overlap/wall-thickness guard list, and tighter verification. The philosophy is identical at every depth.
5. **Verification is geometric, not vibes.** The modeling medium has no unit-test runner. Every plan ends with concrete verification *assertions* — input → action → observable geometric/visual outcome — and a human acceptance gate, because an agent judging its own viewport capture is circular.
6. **Honor user-named resources.** When the user names a reference image, a specific primitive, a target layer, or a prior artifact, treat it as authoritative input. Read/discover it before assuming it's unavailable. If it fails or doesn't exist, say so explicitly rather than silently substituting.

## When to Use

Use `frank-plan` when:

- A reference image, sketch, or described form needs to become a buildable model.
- The form is organic, freeform, or parametric enough that hand-modeling is tedious and a re-runnable generator pays off.
- You want the decisions — primitives, parameter surface, scope isolation, verification — settled **before** geometry exists.

Do **not** use `frank-plan` to write or run the generator (that's `frank-build`), to capture and compare a built result (that's `frank-review`), or to record a solved gotcha (that's `frank-compound`).

## Plan Quality Bar

A modeling plan is ready when `frank-build` can start without re-deciding. Every plan should contain:

- A clear **artifact type** (visual study / parametric & tunable / fabrication-ready) and **fidelity target**, both confirmed with the user.
- The **surveyed document state** — units, tolerance, existing layers/networks the build must not disturb — and the **dedicated scope** (layer/subnet name) the build will own.
- The **chosen primitives**, each grounded by the docs-researcher (named with their confirming source), and the rejected alternatives with rationale.
- A **named parameter block** sketch — the single tunable surface, with indicative defaults and any derived/constraint relationships called out (e.g., "inner radius MUST exceed half the band width + clearance").
- An enumerated list of **geometric verification assertions** — specific enough that `frank-review` knows exactly what to check without inventing coverage.
- **Scope isolation + idempotency** stated as a requirement (rebuild clears only its own layer/subnet; foreign-object counts invariant).

## Workflow

### Phase 0: Detect Tool and Source the Reference

#### 0.1 Detect the active modeling MCP family

Determine which modeling MCP is connected before anything else — the plan's primitives, scope unit, and capture policy are tool-specific.

- Inspect which MCP tools are present in your available toolset: an `mcp__rhino__*` family means **Rhino**; an `mcp__houdini__*` family means **Houdini** (deferred tools surface by name and load via `ToolSearch`).
- **Confirm** the family is live and responsive by issuing its survey call — `get_document_summary` for Rhino, `get_scene_info` for Houdini. A successful response proves a live connection (this is also Phase 1's survey, so reuse the result).
- **Both families present** → ask the user which to target (see Interaction Method).
- **Neither present** → halt and point the user at setup: `docs/houdini-setup.md` for Houdini, or the Rhino MCP setup for Rhino. Suggest `/frank-setup`. Do not paper-plan against a tool that isn't connected unless the user explicitly asks for a tool-agnostic plan.

Record the chosen family — it selects which `references/<tool>-mcp.md` pack and which docs-researcher the rest of the workflow uses (`frank-rhino-docs-researcher` for Rhino, `frank-houdini-docs-researcher` for Houdini).

#### 0.2 Source the reference and the form

<reference> #$ARGUMENTS </reference>

**If the input above is empty, ask the user:** "What would you like to model? Share a reference image (path or URL), a sketch, or describe the form." Then wait for their response before continuing.

If a reference image path or URL is provided, read/fetch it now — the silhouette you're planning toward is the source of truth for fidelity. If the input is a description with no image, note that there is no visual reference and that `frank-review`'s comparison will be against the described intent (or requirements) rather than an image.

If the user references an existing plan in `docs/plans/`, read it and confirm whether to revise it in place or create a new one.

### Phase 1: Survey the Live Document

**STOP. Before surveying, read the Architecture + survey-tool section of `references/<tool>-mcp.md` (the connected family's pack — `rhino-mcp.md` or `houdini-mcp.md`).** Load *only* the architecture/connection and survey-tool portions — `frank-plan` does not emit build, capture, or policy MCP calls, so loading the full build+capture+POLICY content would pull in tooling this skill never uses and risks leaking generator-shaped detail into a decisions-only plan. The survey section names the one read-only call you need.

Run the survey call (already issued in 0.1) and record:

- **Units and tolerance** — Rhino: document units + absolute tolerance. Houdini: unit length (it is unitless; ~1 unit = 1 m by convention). These set the plan's scale defaults and any fabrication thresholds.
- **Existing layers / networks** — every layer (Rhino) or `/obj` network (Houdini) already in the document, with object counts. These are the **foreign-object invariant** the build must hold identical before/after every run.
- **The dedicated scope** the build will own — a new, named layer (Rhino) or subnet (Houdini) that does not collide with anything surveyed. Name it in the plan.

Do **not** create, modify, or delete any geometry in this phase. Surveying is read-only.

### Phase 2: Choose Artifact Type and Fidelity Target

These two choices shape every downstream decision (the param surface, the guard list, the verification assertions), so resolve them with the user before grounding primitives.

#### 2.1 Artifact type

Ask the user which of these the model is (see Interaction Method — single-select):

- **Visual study** — a form to *look* right from a chosen angle. No watertightness or real-world-scale requirement. Lightest plan; verification is silhouette-only.
- **Parametric & tunable** — a re-runnable generator driven by a named parameter block, tuned by editing parameters. Verification adds idempotency + cross-section/continuity assertions. *(The default for most frank work.)*
- **Fabrication-ready** — a watertight, manifold, real-world-scale solid suitable for 3D print / CNC. Heaviest plan; verification adds wall-thickness, overhang, undercut, and manifoldness guards. *(Note: `fabrication.md` canon is a stub today — flag any fabrication-specific guard as provisional and route it to `frank-compound` once validated.)*

#### 2.2 Fidelity target

Ask what "done" means against the reference:

- **Faithful silhouette** — the gesture and outline read as the reference from a comparable, pinned camera. Not pixel-perfect; not matching tessellation/lighting. *(Most common.)*
- **Dimensional match** — specific measurements must hold (a part to spec). Verification asserts measured dimensions, not just outline.
- **Loose / inspired-by** — the reference is a starting point, not a target. Verification is the user's eye only.

Record both answers verbatim in the plan's "Resolved during planning" block — they are the acceptance criteria `frank-review` enforces.

### Phase 3: Ground the Build

Dispatch grounding research in parallel — one pass to confirm the primitives exist with the signatures the plan will lean on, one pass to surface any prior learning that changes the approach. Use the connected family's docs-researcher (selected in 0.1).

Run these agents in parallel:

- Task frank-<tool>-docs-researcher(Confirm live, in-session, the exact signatures of the primitives this plan needs — {candidate primitive list, e.g. AddInterpCurve / AddSweep1 for a swept ribbon}. For each, return the confirming source — MCP introspection or official docs — or flag that it could not be confirmed. Survey context: {units, tolerance, existing layers from Phase 1}.)
- Task frank-learnings-researcher(Retrieve any prior learnings in docs/solutions/ relevant to this form and these primitives — {artifact type, fidelity target, candidate primitives}. Flag any learning that conflicts with the present approach.)

Replace `<tool>` with the connected family — `Task frank-rhino-docs-researcher(...)` or `Task frank-houdini-docs-researcher(...)`. Dispatch both by their bare, frank-prefixed names; do not strip the prefix and do not add a path namespace.

Consolidate the returns:

- Which candidate primitives are **confirmed** (with their source) and which are **unconfirmed** (these become open questions, not asserted signatures).
- Any **prior learning** that applies — fold its fix into the approach; if a learning *conflicts* with present evidence, surface the conflict for the user rather than silently following either.

The canon (`knowledge/parametric-scripting.md`, `knowledge/verification.md`) informs the param-block and assertion design in Phase 5; you do not need the full reference pack here — the survey section from Phase 1 plus the researcher returns are sufficient grounding for a decisions-only plan.

### Phase 4: Select Primitives and the Build Strategy

From the grounded candidates, decide the construction strategy and write it down as decisions with rationale:

- **The primitives** the build will use, each confirmed. State *why* this primitive over the alternatives (e.g., "one interpolated rail through all points, not spiral-plus-join — sidesteps tangent-matching kinks at the join").
- **The scope unit and idempotency contract** — Rhino: a dedicated layer with the three idempotent helpers (ensure-layer, clear-only-own-layer, assign-on-creation); Houdini: a named subnet rebuilt each run. Foreign-object counts invariant.
- **The coordinate/orientation convention** if it matters for the form (e.g., build the rail in the world XZ plane so the piece stands in Z with no post-rotation).
- **Rejected alternatives** with one-line rationale, so `frank-build` doesn't re-litigate them.

### Phase 5: Design the Parameter Block and Verification Assertions

This is the heart of the plan — the two artifacts `frank-build` and `frank-review` consume.

#### 5.1 Named parameter block

Design the single tunable surface as a directional sketch (names + indicative defaults), grounded in `knowledge/parametric-scripting.md` (named params, no magic numbers, validation that *warns*). Call out:

- The **knobs** (user-tunable) vs. **derived** values (computed from knobs — never independently set).
- Any **constraint relationship** that must hold, expressed as a guard that warns rather than producing broken geometry (e.g., "min inter-turn radial spacing MUST exceed the in-plane cross-section extent + clearance"). Name *which* parameters the guard reads.
- Units and the dedicated scope (layer/subnet) name as parameters.

Frame the block explicitly as directional — `frank-build` owns the runnable implementation; the plan owns the *shape* of the tunable surface.

#### 5.2 Geometric verification assertions

Enumerate the assertions `frank-review` will check, drawing on `knowledge/verification.md` (which views, pinned-camera discipline, silhouette comparison, geometric guards). Right-size to the artifact type. Each assertion names an **input → action → observable outcome**. Cover the categories that apply:

- **Silhouette / visual** — "from the pinned perspective camera, the captured outline matches the reference checklist: {specific items — e.g., coil sits high, ~2–2.5 inward turns; single graceful descent; open hook at base}."
- **Idempotency invariant** (parametric+) — "running the generator twice leaves every foreign layer/network object count identical; the build's own scope count returns to baseline + expected."
- **Continuity / geometry** — "no visible kinks at segment junctions; cross-section width constant along the rail (no pinching at high curvature); no self-intersection at the tightest turn."
- **Scale** — "the build's bounding-box {axis} extent ≈ {target parameter} within ~10%."
- **Fabrication** (fabrication-ready only) — wall thickness ≥ threshold, no overhangs beyond {angle}, watertight/manifold. *(Provisional — `fabrication.md` is a stub.)*
- **Human acceptance** — "a side-by-side of the pinned capture vs. the reference is presented to the user for explicit sign-off; the agent does not self-certify the fidelity target." Note the iteration cap `frank-review` will enforce.

### Phase 6: Write the Plan File

Write a **compact modeling plan** — decisions, not code — to `docs/plans/YYYY-MM-DD-NNN-<type>-<descriptive-name>-plan.md`:

- Create `docs/plans/` if it does not exist; check existing files for today's date to pick the next zero-padded sequence number (starting at `001`).
- Use a clear title (`feat: Model the spiral-ribbon sculpture via Rhino MCP`), kebab-cased descriptive name (3–5 words), ISO date.

The plan body should carry (mirroring the worked example, the spiral-ribbon-sculpture plan):

- **Summary** + **Problem Frame** — what's being modeled and why a generator.
- **Requirements** — including scope-isolation/idempotency and the surveyed foreign-object invariant.
- **Scope Boundaries** — what this artifact type is *not* (e.g., "not a watertight fabrication solid — user chose parametric & tunable").
- **Context & Research** — surveyed document state (units, tolerance, existing layers); the **confirmed primitives with their grounding source**; relevant prior learnings (or "none on record — worth a `frank-compound` writeup after").
- **Key Technical Decisions** — the construction strategy, the param-block design, the scope/idempotency contract, the coordinate convention, with rationale.
- **The directional parameter block** sketch and the **coordinate convention**.
- **Open Questions** — "Resolved during planning" (artifact type + fidelity target verbatim) and "Deferred to implementation" (any unconfirmed primitive behavior `frank-build` resolves empirically).
- **The geometric verification assertions** (Phase 5.2) and the **human acceptance gate + iteration cap**.

All file references in the plan use repo-relative paths, never absolute.

After writing, confirm with the absolute path (so it's clickable):

```text
Modeling plan written to <absolute path to plan>
```

Then offer the handoff: build it now with `/frank-build`, or revise the plan first. Never silently skip the question — present it via the Interaction Method.

## Cross-References

- Reference packs: `references/rhino-mcp.md`, `references/houdini-mcp.md` (survey/architecture sections)
- Canon this plan's param-block and assertions draw on: `knowledge/parametric-scripting.md`, `knowledge/verification.md`
- Researchers dispatched: `frank-rhino-docs-researcher`, `frank-houdini-docs-researcher`, `frank-learnings-researcher`
- Downstream skills: `frank-build` (executes the plan), `frank-review` (checks the assertions)
- Worked example: the spiral-ribbon-sculpture modeling plan (the shape this skill produces)
