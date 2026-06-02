---
name: frank-compound
description: Document a recently solved modeling problem to compound frank's craft knowledge. Use when 'that worked', 'it's fixed', 'the geometry is clean now', 'document this gotcha', or after frank-build/frank-review surfaces and resolves a modeling failure worth recording.
argument-hint: "[optional: brief context]"
---

# /frank-compound

Capture a recently solved modeling problem as a durable learning in `docs/solutions/`, while the context is fresh. Each learning makes the next occurrence of the same gotcha a lookup, not a re-investigation.

## Purpose

Writes structured documentation to `docs/solutions/` with YAML frontmatter so `frank-learnings-researcher` can retrieve it, and `frank-plan`/`frank-build` can ground future work on it. The artifact records a **modeling** failure (a sweep that twists, a coil that self-intersects, an MCP capture that deadlocks) and its verified fix — the kind of tool-and-craft knowledge that is expensive to rediscover and cheap to look up.

**Why "compound"?** The first time you hit a Sweep1 framing twist on a tight rail, it costs an investigation. Document it, and the next time it costs a grep. Knowledge compounds — each solved problem makes subsequent modeling work easier, not harder. The learning's `tool:` frontmatter (`rhino` | `houdini`) is what scopes it to the right track, so this skill never needs to load a tool reference pack — tool identity lives in the frontmatter you write, not in the MCP surface.

## Usage

```bash
/frank-compound                  # Document the most recent fix
/frank-compound [brief context]  # Provide an additional context hint
```

## Interaction Method

When you need a blocking decision from the user (Full vs. Lightweight, "What's next?"), ask via `AskUserQuestion` — call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded. Fall back to numbered options in chat **only** when no blocking tool exists in the harness or the call errors — not because a schema load is required. Ask one question at a time. Never silently skip the question.

## Core Principles

- **One file per invocation.** The only deliverable is a single learning written to `docs/solutions/`. Subagents return TEXT to the orchestrator; they never use Write, Edit, or create files. **Only the orchestrator writes.**
- **The fix must be verified.** Document a problem that has been *solved and confirmed working* — not an in-progress hypothesis. A learning that records an unverified guess poisons the knowledge store.
- **Tool identity lives in the frontmatter.** Every frank learning is scoped to a tool (`rhino` | `houdini`) via its `tool:` field. That is how `frank-learnings-researcher` and `frank-plan` filter by track — so this skill writes markdown and does **not** STOP-gate-load any `references/<tool>-mcp.md` pack.
- **Non-trivial only.** Don't document a typo or an obvious one-liner. Document the gotchas, patterns, and decisions whose root cause was not obvious — the things a future session would otherwise re-investigate.

## When to Use

Invoke after frank (or Rob) solves a modeling problem worth recording:

- A **gotcha** — a tool or geometry behavior that bit you and has a non-obvious fix (Sweep1 twists on a tight rail; `render_quad_views` deadlocks the server; uniform knots overshoot at density transitions).
- A **pattern** — a reusable build/verify approach proven to work (the idempotent layer-helper contract; the pinned-camera capture-compare loop).
- A **decision** — a tooling or modeling choice with durable rationale (single interpolated rail vs. spiral-plus-join; `execute_rhinoscript_python_code` over the unproven high-level helpers).

Do **not** invoke for in-progress work, unverified fixes, or trivial errors.

## Quality Bar

A finished learning:

- Parses against the frontmatter schema below (`date`, `tool`, `area`, `type`, `mcp`, `tags`).
- Has a filename `YYYY-MM-DD_<slug>.md` — ISO date, lowercase kebab slug.
- Carries the full body: **Symptom → Root cause → Fix → Verified facts → Cross-References**.
- Cross-references the relevant `references/<tool>-mcp.md` pack and the `knowledge/*.md` canon it enforces, **bidirectionally** — if this learning links a reference pack, the reference pack should list this learning (update it when it doesn't).

## Support Files

Read on-demand at the step that needs them — do not bulk-load at skill start.

- `assets/resolution-template.md` — the frontmatter schema + section structure for a frank learning (read in Phase 2 when assembling the doc).

When spawning subagents, pass the relevant file contents into the task prompt so they have the contract without needing cross-skill paths.

## Execution Strategy

Present the user with two modes before proceeding, using the Interaction Method above:

```
1. Full (recommended) — researches the conversation, finds related learnings,
   and cross-references before writing. Detects overlap with existing docs so
   you update rather than duplicate.

2. Lightweight — same document, single pass. Faster and fewer tokens, but won't
   detect duplicates or cross-reference existing learnings. Best for a simple,
   self-contained gotcha or a long session nearing its context limit.
```

Do not pre-select a mode; wait for the user's choice.

---

### Full Mode

<critical_requirement>
**The primary output is ONE file — the final learning.**

Phase 1 subagents return TEXT DATA to the orchestrator. They must NOT use Write, Edit, or create any files. Only the orchestrator writes — the single learning in Phase 2.
</critical_requirement>

#### Phase 0.5: Auto Memory Scan

Before launching Phase 1 subagents, check the auto-memory block injected into your system prompt for notes relevant to the problem being documented.

1. Look for a block labeled "user's auto-memory" already present in your system prompt context.
2. If the block is absent or empty, skip this step and proceed to Phase 1 unchanged.
3. Scan the entries for anything related to the problem being documented — use semantic judgment, not keyword matching.
4. If relevant entries are found, pass a labeled excerpt block to the Phase 1 subagents as supplementary context. Treat it as additional context, not primary evidence — conversation history and the verified fix take priority. Tag any memory-sourced content that lands in the final doc with "(auto memory [claude])" so its origin is clear.

#### Phase 1: Research

Launch research subagents in parallel. Each returns text data to the orchestrator — **no file writes**.

<parallel_tasks>

1. **Context Analyzer** — Extracts the problem and fix from conversation history. Determines the **tool track** (`rhino` | `houdini`) from which MCP family was exercised, the `area` (e.g. `sweep`, `curve-fitting`, `rendering`, `setup`, `scope-isolation`), and the `type` (`gotcha` | `pattern` | `decision`). Reads `assets/resolution-template.md` for the schema. Returns: a frontmatter skeleton, a suggested filename `YYYY-MM-DD_<slug>.md`, and which track applies. Incorporates auto-memory excerpts (if provided) as supplementary evidence. Does not invent enum values — uses the schema's `type` set and a concise `area` slug.

2. **Solution Extractor** — Adapts the body to the **Symptom → Root cause → Fix → Verified facts → Cross-References** structure. Returns each section as text:
   - **Symptom**: the observable failure — what the geometry/render/MCP did wrong (twist, overshoot, self-intersection, deadlock, wrong units).
   - **Root cause**: the underlying mechanism (default sweep framing, uniform knots over a density swing, adjacent-turn radial spacing < cross-section extent, main-thread GL render pumping the event loop).
   - **Fix**: the verified resolution with a code snippet when useful (the RhinoCommon `SweepOneRail` up-vector route; chord-length knots + arc-length resampling; the orientation-aware guard; `render_single_view` + read-from-disk).
   - **Verified facts**: a checklist of what was confirmed (✅ / ⛔ / ℹ️), dated.

3. **Related Docs Finder** — Greps `docs/solutions/` for related learnings (frontmatter-first; see search strategy). Returns links, refresh candidates, and an **overlap assessment** (High / Moderate / Low) across problem statement, root cause, fix, referenced tool, and the canon enforced.

   **Search strategy (grep-first for efficiency):**
   1. Extract keywords: tool name, `area`, the geometric/MCP term (twist, knot, self-intersect, deadlock).
   2. Pre-filter candidate files with content search over frontmatter BEFORE reading bodies — run these in parallel, case-insensitive (template patterns; substitute real keywords):
      - `tool:.*<rhino|houdini>`
      - `area:.*<area>`
      - `tags:.*(<keyword1>|<keyword2>)`
   3. Read only the frontmatter (first ~15 lines) of candidates to score relevance; fully read only strong matches.
   4. Return distilled links, not raw file contents.

</parallel_tasks>

#### Phase 2: Assembly & Write

<sequential_tasks>

**WAIT for all Phase 1 subagents to complete before proceeding.**

The orchestrator (main conversation) performs these steps:

1. Collect all text results from Phase 1 subagents.
2. **Check the overlap assessment** before deciding what to write:

   | Overlap | Action |
   |---------|--------|
   | **High** — an existing learning covers the same tool, symptom, and fix | **Update the existing doc** with fresher context rather than duplicating. Preserve its path and frontmatter; add `last_updated: YYYY-MM-DD`. |
   | **Moderate** — same area, different angle or fix | **Create the new doc.** Flag the overlap so the two can be reconciled later. |
   | **Low / none** | **Create the new doc.** |

3. Assemble the markdown file, reading `assets/resolution-template.md` for the exact frontmatter fields and the **Symptom → Root cause → Fix → Verified facts → Cross-References** section order.
4. **Write the Cross-References block** — link the relevant `references/<tool>-mcp.md` pack and the `knowledge/*.md` canon this learning enforces. Then **update those targets to link back** (bidirectional linking is mandatory): if the reference pack's "Cross-References" / learnings list doesn't yet name this new learning, add it.
5. Validate the YAML frontmatter against the schema (all five fields present; `type` is one of `gotcha`/`pattern`/`decision`; `tool` is `rhino`/`houdini`; array items that start with a YAML indicator or contain `": "` are double-quoted).
6. Write the file: `docs/solutions/YYYY-MM-DD_<slug>.md` (or the updated existing doc).

</sequential_tasks>

#### Phase 2.5: Discoverability Check

After the learning is written, check whether the project's instruction files (`CLAUDE.md` / `README.md`) would lead an agent to discover and search `docs/solutions/` before modeling work in a documented area. If the awareness is already present, do nothing. If not, draft the smallest informational addition (not imperative — "relevant when building or reviewing in documented areas") and, in Full interactive mode, get consent via the Interaction Method before editing.

---

### Lightweight Mode

<critical_requirement>
**Single-pass alternative — same document, fewer tokens. No subagents. One file written.**
</critical_requirement>

The orchestrator performs all of the following in one sequential pass:

1. **Extract** the problem and verified fix from conversation history (and the auto-memory block, if present — tag memory-sourced content "(auto memory [claude])").
2. **Classify** — read `assets/resolution-template.md`; determine `tool` (rhino/houdini), `area`, `type` (gotcha/pattern/decision), and a kebab `<slug>`.
3. **Write** `docs/solutions/YYYY-MM-DD_<slug>.md` with the schema frontmatter and the **Symptom → Root cause → Fix → Verified facts → Cross-References** body, linking the relevant reference pack + canon (and updating the reference pack to link back).

The overlap check is skipped in lightweight mode (no Related Docs Finder), so a lightweight run may create a doc that overlaps an existing one — acceptable; reconcile later.

---

## What It Captures

- **Symptom** — the observable modeling failure (twist, fold, overshoot, self-intersection, deadlock, wrong scale/units).
- **Root cause** — the geometric or tool mechanism behind it.
- **Fix** — the verified resolution, with a code snippet when load-bearing.
- **Verified facts** — a dated ✅/⛔/ℹ️ checklist of what was confirmed live.
- **Cross-references** — bidirectional links to the reference pack, the canon enforced, and sibling learnings.

## Preconditions

<preconditions enforcement="advisory">
  <check condition="problem_solved">Problem has been solved (not in-progress)</check>
  <check condition="solution_verified">Fix has been verified working in the live document/scene</check>
  <check condition="non_trivial">Non-trivial problem (not a typo or an obvious one-liner)</check>
</preconditions>

## What It Creates

A single learning at `docs/solutions/YYYY-MM-DD_<slug>.md` with:

- **Frontmatter:** `date`, `tool` (`rhino` | `houdini`), `area`, `type` (`gotcha` | `pattern` | `decision`), `mcp`, `tags`.
- **Body:** Symptom → Root cause → Fix → Verified facts → Cross-References.

## Common Mistakes to Avoid

| Wrong | Correct |
|-------|---------|
| Subagents write `context.md`, `draft.md` | Subagents return text; the orchestrator writes one final learning |
| Research and assembly run interleaved | Phase 1 research completes → then Phase 2 assembly |
| Documenting an unverified hypothesis | Document only a solved, confirmed fix |
| New doc when an existing one covers it | Check overlap; update the existing learning when overlap is high |
| Linking forward only | Bidirectional — update the reference pack / sibling learnings to link back |
| STOP-gate-loading a tool reference pack | Not needed — tool identity is the `tool:` frontmatter field |

## Auto-Invoke

<auto_invoke> <trigger_phrases> - "that worked" - "it's fixed" - "the geometry is clean now" - "no more twist" - "problem solved" </trigger_phrases>

<manual_override> Use /frank-compound [context] to document immediately without waiting for auto-detection. </manual_override> </auto_invoke>

## Output

Writes the final learning directly into `docs/solutions/`. `frank-learnings-researcher` retrieves it for future `frank-plan` / `frank-build` runs.

## Cross-References

- Schema + section structure: `skills/frank-compound/assets/resolution-template.md`
- Retrieval agent: `agents/frank-learnings-researcher.agent.md` (greps `docs/solutions/` by tool/area/topic)
- Reference packs a learning links: `references/rhino-mcp.md`, `references/houdini-mcp.md`
- Canon a learning enforces: `knowledge/parametric-scripting.md`, `knowledge/verification.md`
- Existing learnings (schema exemplars): `docs/solutions/2026-06-01_houdini-mcp-render-deadlock.md`, `docs/solutions/2026-06-01_houdini-mcp-setup-gotchas.md`
