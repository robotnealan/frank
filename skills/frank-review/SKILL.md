---
name: frank-review
description: "Capture the built model from a pinned camera, compare it adversarially against the reference via two reviewer agents, and iterate toward human-accepted fidelity. Use when the user says 'review this model', 'does it match the reference', 'check the build', 'critique the render', or after `frank-build` produces geometry that needs to be judged against a target."
argument-hint: "[optional: reference image path/URL, a target-view name, or working notes from a prior review iteration]"
---

# Review Model

**Note: The current year is 2026.** Use this when dating review notes and searching for recent documentation.

`frank-review` closes the loop. `frank-plan` decided **WHAT** to model and listed the verification assertions; `frank-build` wrote and ran the generator. This skill **captures** the built geometry from a recorded camera, dispatches two adversarial reviewers to **compare** it against the reference, merges their findings, presents a side-by-side to the **human** (the sole acceptance authority), and **iterates** until accepted or the iteration cap is reached. It judges the model against a target — it does not author or run the generator. If a finding requires changing a parameter, `frank-review` *proposes* the tweak and hands it back to `frank-build`; the build owns the runnable code.

The capture is the load-bearing artifact. A review is only as good as a comparable capture, so the single non-negotiable discipline here is a **pinned camera** — recorded once, reused every iteration — and the human, not the agent, signs off on fidelity (an agent judging its own viewport capture is circular).

## Interaction Method

When asking the user a question, use the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_user` in Gemini, `ask_user` in Pi (requires the `pi-ask-user` extension). Fall back to numbered options in chat only when no blocking tool exists in the harness or the call errors (e.g., Codex edit modes) — not because a schema load is required. Never silently skip the question.

Ask one question at a time. Prefer a concise single-select choice when natural options exist.

## Core Principles

1. **Pin the camera once, reuse it every iteration.** A capture is only comparable across iterations if the camera is identical each time. Record the camera's `position`, `target`, and `lens`/focal-length (or a named view) in the review's working notes on iteration 1, and reuse those exact values for every subsequent capture. A moved camera makes the silhouette comparison meaningless and silently invalidates the whole loop.
2. **The human is the acceptance authority.** The reviewer agents surface mismatches; they do not decide "done." Fidelity sign-off is a human decision — the agent presents the side-by-side and asks. Self-certifying the fidelity target is circular and forbidden.
3. **Reviewers judge files, not geometry.** `frank-review` holds the MCP and does the capturing; it passes the reviewers *file paths* (the capture and the reference), never MCP tools. The reviewers are structurally incapable of mutating geometry — that is the safety model. Do not hand them a viewport or an MCP grant.
4. **Findings drive parameter tweaks, not direct edits.** A merged finding is a proposal. `frank-review` translates it into a concrete parameter change and routes it back to `frank-build` to apply, re-run, and re-capture. The review never edits the generator itself.
5. **Cap the loop; do not auto-accept at the cap.** Iterating forever is worse than stopping and asking. Cap at ~6 iterations. At the cap *without* acceptance, present the latest state and unresolved findings to the human for an accept/override decision — never silently accept because the budget ran out.
6. **Honor user-named resources.** When the user names a reference image, a target view, or prior working notes, treat them as authoritative. Read/discover them before assuming they're unavailable; if a named resource fails to load, say so explicitly rather than substituting silently.

## When to Use

Use `frank-review` when:

- `frank-build` has produced geometry and you need to know whether it matches the reference.
- You want an adversarial second opinion on a render before declaring a model done.
- You're iterating a parametric build toward a faithful silhouette and need a repeatable capture-compare-adjust loop with a fixed camera.

Do **not** use `frank-review` to write or run the generator (that's `frank-build`), to produce the modeling plan or its assertions (that's `frank-plan`), or to record a solved gotcha after the fact (that's `frank-compound`).

## Review Quality Bar

A review is complete when:

- The capture was taken from a **recorded** camera (position/target/lens noted) that matches the reference framing, and every iteration reused it.
- Both reviewers ran (or an absent reviewer was noted) and their JSON findings were **merged and deduplicated** into one finding set.
- The merged findings were presented **side by side with the reference** to the human, who made the accept/iterate/override call — not the agent.
- Either: the human accepted, **or** the iteration cap was reached, the unresolved findings were listed by reviewer lane, and the human was asked to accept or override.
- On Houdini, the capture used `render_single_view`, read the render **from disk**, cleaned the scaffolding nodes, and **never** called `render_quad_views`.

## Reviewers

Two adversarial reviewers, each in its own lane. They share one pinned JSON findings contract (see Stage 4) so the merge step works.

| Agent | Lane | Judges |
|-------|------|--------|
| `frank-silhouette-critic` | `silhouette` | Visual comparison of the captured render vs the reference — silhouette, proportion, framing, feature placement/count. **Vision task** — dispatched on a vision-capable model (override at the dispatch site). |
| `frank-geometry-reviewer` | `geometry` | The geometry summary / inspection data — topology, scale, units, naked edges, self-intersection, manifoldness. Reasons over the data `frank-review` passes it. |

Both receive only `Read, Grep, Glob, Bash` (+ `Write` for their JSON artifact) — **no MCP grant**. They get the capture as a file path and the reference image as a file path in their Task payload; `frank-review` does the capturing.

## Workflow

### Stage 1: Detect the tool and gather the inputs

#### 1.1 Detect the active modeling MCP family

The capture branch is entirely tool-specific, so resolve the connected family before anything else.

- Inspect which MCP tools are present in your available toolset: an `mcp__rhino__*` family means **Rhino**; an `mcp__houdini__*` family means **Houdini** (deferred tools surface by name and load via `ToolSearch`).
- **Confirm** the family is live by issuing its survey call — `get_document_summary` for Rhino, `get_scene_info` for Houdini. A successful response proves a live, responsive connection.
- **Both families present** → ask the user which to target (see Interaction Method).
- **Neither present** → halt and point the user at setup: `docs/houdini-setup.md` for Houdini, or the Rhino MCP setup for Rhino. Suggest `/frank-setup`. There is nothing to capture without a live modeler.

Record the chosen family — it selects the capture branch in Stage 3 and which `references/<tool>-mcp.md` pack the STOP-gate in Stage 2 loads.

#### 1.2 Gather the reference and the target view

<inputs> #$ARGUMENTS </inputs>

**If the input above is empty, ask the user:** "What should I compare the model against? Share the reference image (path or URL) and, if you have one in mind, the view to capture from." Then wait for their response.

- **Reference image** — read/fetch it now; it is the source of truth `frank-silhouette-critic` compares against. If the model is being reviewed against a *described intent* rather than an image (per the plan), note that and tell the reviewers what "done" means in words.
- **Target view / framing** — the camera the reference is shot from (front-orthographic is the usual silhouette-comparison view). If the plan or prior working notes recorded a camera, reuse it (see Stage 3). If not, you'll pick and record one in Stage 3.
- **Prior working notes** — if this is a continuing review, load the recorded camera and the running iteration count so the loop resumes rather than restarts.

### Stage 2: Load the capture POLICY

**STOP. Before capturing anything, read the Capture POLICY section of `references/<tool>-mcp.md` (the connected family's pack — `rhino-mcp.md` for Rhino, `houdini-mcp.md` for Houdini).** Skipping it means you won't know that Rhino's `capture_viewport` returns the image **inline** (no scaffolding) while Houdini's `render_single_view` writes to **disk** and leaves three scaffolding nodes that must be cleaned — and that `render_quad_views` is **banned** because it deadlocks the server. Getting the capture branch wrong produces an uncomparable image, a wedged Houdini session, or a polluted scene that the next `frank-build` run trips over. Load **only** the connected family's pack; never load the absent family's.

Also load `knowledge/verification.md` for the pinned-camera discipline, silhouette-comparison method, and the human-acceptance doctrine the loop enforces.

### Stage 3: Capture from the pinned camera

Record the camera **once**, on the first iteration, and reuse it for every capture in the loop. Note the viewport/camera `position`, `target`, and `lens`/focal-length (or the named view) in the review's working notes. On every later iteration, re-capture from those exact values — never let the camera drift, or the comparison is meaningless.

Pick the camera so the capture frames the subject the way the reference does (front-orthographic is the standard silhouette view). Capture additional canonical views (left, top, perspective) only if a finding needs a second angle; each extra view also gets a pinned camera recorded once.

Then capture per the connected family's branch:

#### Rhino branch — inline capture

1. Call `capture_viewport(...)` from the pinned camera / named view. It returns the image **inline** (no scaffolding nodes, no banned quad tool — Rhino's capture path is the simpler half).
2. **Write the inline image to a file path** under the run directory (e.g. `/tmp/frank/frank-review/$RUN_ID/capture.png`) so the reviewers can `Read` it. The reviewers receive the *path*, not the inline bytes.
3. That written file path is the `capture_path` you pass to both reviewers in Stage 4.

#### Houdini branch — render to disk, read back, clean scaffolding

1. Call `render_single_view(orthographic=..., rotation=<pinned>, render_path=<run-dir path>)` at the pinned rotation. **Never call `render_quad_views`** — it stacks four unbounded main-thread OpenGL ROP renders and deadlocks the server (see the Capture POLICY you loaded in Stage 2).
2. **`Read` the file at `render_path`** — that is the capture. **Ignore the inline `image_base64`** the call also returns; it is large (~56 KB for 512×512) and overflows tool-result buffers. Rely on the file on disk.
3. **Delete the three scaffolding nodes** `render_single_view` adds to the scene, for scope isolation so the next `frank-build` run starts clean:
   - `/obj/MCP_CAMERA`
   - `/obj/MCP_CAM_CENTER`
   - `/out/MCP_OGL_RENDER`
4. The path you `Read` is the `capture_path` you pass to both reviewers in Stage 4.

In both branches, also gather the **geometry summary / inspection data** `frank-geometry-reviewer` needs (from the survey call in 1.1 plus per-object inspection — `get_object_info` on Rhino, `get_scene_info`/introspection on Houdini): object/topology counts, bounding-box extents, units, and any naked-edge / self-intersection signals the tool exposes. The reviewer reasons over this data, not the live document.

### Stage 4: Dispatch the reviewers

#### 4.1 Generate the RUN_ID

Generate a unique run identifier **before** dispatching any reviewer. It scopes both reviewers' JSON artifacts to one directory so the merge step in Stage 5 can find them.

```bash
RUN_ID=$(date +%Y%m%d-%H%M%S)-$(head -c4 /dev/urandom | od -An -tx1 | tr -d ' ')
mkdir -p "/tmp/frank/frank-review/$RUN_ID"
```

Pass `RUN_ID` as a named field in **each** reviewer's Task payload (alongside the capture path and the reference path). The reviewers **read** `RUN_ID` from the payload — they do not generate their own — and write their findings to `/tmp/frank/frank-review/$RUN_ID/<reviewer>.json`. A mismatch here silently breaks the merge.

#### 4.2 Dispatch both reviewers in parallel

`frank-silhouette-critic` is a **vision task** — it compares two images — so override its dispatch model to a vision-capable tier **at the dispatch site** (its frontmatter stays `model: inherit`). `frank-geometry-reviewer` reasons over the geometry data and inherits the session model.

Run these agents in parallel:

- Task frank-silhouette-critic(Adversarially compare the captured render against the reference and flag silhouette/proportion/framing/feature mismatches. capture_path={path written in Stage 3}; reference_path={the reference image}; RUN_ID={the value generated in 4.1}; framing notes={the pinned view, e.g. "front-orthographic"} and intent={what the model is supposed to be}. Write your JSON to /tmp/frank/frank-review/{RUN_ID}/frank-silhouette-critic.json per your output contract.)  — *dispatch on a vision-capable model (override at this site).*
- Task frank-geometry-reviewer(Reason over the geometry summary/inspection data and flag topology/scale/units/naked-edge/self-intersection/manifoldness issues. capture_path={path written in Stage 3}; reference_path={the reference image}; geometry data={the summary + inspection gathered in Stage 3}; RUN_ID={the value generated in 4.1}; units/tolerance={from the survey}. Write your JSON to /tmp/frank/frank-review/{RUN_ID}/frank-geometry-reviewer.json per your output contract.)

Dispatch both by their bare, frank-prefixed names — `Task frank-silhouette-critic(...)` and `Task frank-geometry-reviewer(...)` — never strip the prefix and never add a path namespace. Omit the `mode` parameter so the user's permission settings apply.

The reviewers hold no MCP tools by design; they `Read` the capture and reference files you wrote and return JSON. They do not touch the live model.

### Stage 5: Merge the findings

After both reviewers complete, read their JSON artifacts from `/tmp/frank/frank-review/$RUN_ID/` and merge them into one finding set. Each reviewer wrote the pinned envelope:

```json
{
  "reviewer": "silhouette-critic",
  "findings": [ { "title": "...", "severity": "P1", "lane": "silhouette", "confidence": 75, "...": "..." } ],
  "residual_risks": [],
  "testing_gaps": []
}
```

`reviewer` is `silhouette-critic` / `geometry-reviewer`; `lane` is `silhouette` / `geometry`; `confidence` is exactly one of `100`, `75`, `50`, `25`. Merge steps:

1. **Validate.** Check each artifact has the top-level keys `reviewer`, `findings`, `residual_risks`, `testing_gaps`, and that each finding carries `title`, `severity` (`P0`–`P3`), `lane`, and `confidence` (one of the four anchors). Drop malformed findings and record the drop count.
2. **Handle an absent artifact.** If a reviewer's file is missing (the reviewer errored or timed out), **note the missing reviewer and proceed with what's present** — a one-reviewer merge is degraded but valid. Do not block the loop on a missing artifact; record "geometry lane unreviewed this iteration" (or whichever) for the human.
3. **Deduplicate across lanes.** The two reviewers police separate lanes (silhouette vs geometry) and a finding usually carries the `lane` of its author, so cross-lane duplicates are rare — but when both flag the *same* observable defect (e.g. silhouette notes a render gap that geometry confirms as a naked edge), merge them: keep the higher severity, keep the higher confidence anchor, and note both lanes flagged it (stronger signal).
4. **Confidence gate.** Suppress findings at anchor `25` (the reviewers already self-suppress these). Keep `50`-anchor findings as soft signal — surface them with the residual risks rather than dropping them, and never drop a P0/P1 just because it's at `50`.
5. **Collect coverage.** Union the `residual_risks` and `testing_gaps` arrays across both reviewers — these tell the human which views couldn't be compared and which concerns one lane handed to the other.

### Stage 6: Present to the human, propose tweaks, iterate

Present the result to the human — the acceptance authority — as a side-by-side:

1. **Side-by-side.** Show the reference and the latest capture together (file paths, and the pinned view they were compared at), so the human sees what the reviewers saw.
2. **Merged findings, by lane.** List the merged findings grouped by reviewer lane (silhouette / geometry), each with its severity, confidence, the concrete observation, and the proposed fix. Surface the residual risks and testing gaps from Stage 5 (including any unreviewed lane from an absent reviewer).
3. **Propose parameter tweaks.** For each actionable finding, translate it into a concrete **parameter change** for `frank-build` (e.g. "raise `P['turns']` from 2.0 to 2.4 to add the missing half-coil"; "close the top profile curve to a point, not a fillet"). `frank-review` proposes; `frank-build` applies, re-runs, and produces the next geometry — the review never edits the generator itself.
4. **Ask the human (see Interaction Method).** Single-select: **Accept** (fidelity target met — done), **Iterate** (apply the proposed tweaks via `frank-build`, then re-capture and re-review), or **Override / adjust** (the human changes the target, the tweaks, or the camera). Never self-certify; never silently skip this question.

On **Iterate**: hand the proposed parameter tweaks to `frank-build`, then return to **Stage 3** and re-capture **from the same pinned camera** recorded on iteration 1 (do not re-record it). Generate a fresh `RUN_ID` for the new reviewer dispatch (Stage 4). Increment the iteration count.

**Cap the loop at ~6 iterations.** Track the count in the working notes.

### Stage 7: At the iteration cap without acceptance

If the loop reaches the cap and the human has not accepted, **do not auto-accept** — the budget running out is not a sign-off. Instead:

1. **Present the latest capture** alongside the reference (the same side-by-side).
2. **State the cap was reached** — name the iteration count and that the fidelity target was not met within it.
3. **List the unresolved findings by reviewer lane** — what silhouette still flags, what geometry still flags, and the residual risks/testing gaps — so the human sees exactly what's outstanding.
4. **Ask the human to accept or override** (see Interaction Method): accept the current state despite the open findings, raise the cap and continue, change the target/tweaks/camera, or stop.
5. **If a systematic blocker surfaced** — a repeating mismatch the parameter loop can't resolve, a primitive that fights the form, a recurring guard warning — **suggest `/frank-compound`** to record the learning so the next build doesn't rediscover it.

## Cross-References

- Reference packs (Capture POLICY this STOP-gate-loads): `references/rhino-mcp.md` (inline `capture_viewport`), `references/houdini-mcp.md` (`render_single_view` to disk, clean scaffolding, `render_quad_views` banned)
- Canon this loop enforces: `knowledge/verification.md` (pinned-camera, silhouette comparison, human acceptance), `knowledge/parametric-scripting.md` (the param tweaks route back to the build)
- Reviewers dispatched (and the shared JSON envelope/path contract): `agents/frank-silhouette-critic.agent.md`, `agents/frank-geometry-reviewer.agent.md`
- Upstream / downstream skills: `frank-plan` (wrote the verification assertions this checks), `frank-build` (applies the proposed parameter tweaks and re-runs), `frank-compound` (records a systematic blocker the loop couldn't resolve)
