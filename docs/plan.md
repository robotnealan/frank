---
title: "feat: frank — a Claude Code plugin for planning, building, and reviewing 3D models via MCP"
type: feat
status: in-progress
date: 2026-06-01
---

# feat: frank — a Claude Code plugin for 3D modeling via MCP

## Summary

`frank` packages a **plan → build → review** workflow for 3D modeling into an installable Claude Code plugin, modeled on the [`compound-engineering`](https://github.com/EveryInc/compound-engineering-plugin) plugin's structure (manifest + `skills/` + `agents/` + `references/`). It drives modeling MCP servers — **Rhino** (proven) and **Houdini** (in progress) — to build form as re-runnable parametric generators, verify it against a reference through a capture-compare-adjust loop, and compound every lesson learned so the next model is easier.

The design generalizes a real, working project: the spiral-ribbon sculpture built in HAL (`data/rhino/spiral-sculpture-generator.py` + `docs/plans/2026-05-29-001-feat-spiral-ribbon-sculpture-plan.md`), which already demonstrates the patterns frank codifies — idempotent layer-scoped rebuild, named parameter block, live primitive introspection, and geometric/visual "tests."

---

## Problem Frame

LLM-driven CAD fails in repeatable ways: hallucinated API signatures, magic-number scripts that can't be tuned, geometry that duplicates or overwrites the existing model, and "looks done" with no real verification. frank turns the opposite into an enforced workflow and ships the domain knowledge needed to do it well — so the value isn't a clever one-off script, but a reusable discipline that gets smarter with use.

---

## Requirements

- **R1.** Installable as a Claude Code plugin (valid `.claude-plugin/plugin.json`; resolvable via a marketplace entry).
- **R2.** A coherent skill workflow: `frank-setup`, `frank-plan`, `frank-build`, `frank-review`, `frank-compound`, invocable as slash commands.
- **R3.** Reviewer/researcher **agents** that the skills spawn: silhouette-critic, geometry-reviewer, fabrication-reviewer, parametric-architect, rhino-docs-researcher, houdini-docs-researcher, learnings-researcher.
- **R4.** A three-layer **knowledge architecture** (below): authored canon, live API grounding, compounding memory.
- **R5.** **Rhino** track fully validated against a live document this session; **Houdini** track ([`capoomgit/houdini-mcp`](https://github.com/capoomgit/houdini-mcp)) documented from source now and **validated live** once its MCP is connected to a session (Rob is setting it up).
- **R6.** Every build the plugin produces is **idempotent, scope-isolated** (own layer/namespace), **re-runnable**, and driven by a **named parameter block** with **input validation/guards**.
- **R7.** Verification is **geometric/visual assertions** (capture viewport, query object info, compare silhouette), not unit tests — because the medium has no test runner.

---

## Knowledge Architecture (the heart of frank)

How real expertise is instilled and grown — three layers:

### Layer 1 — The Canon (authored, durable craft)
Curated knowledge packs of principles that don't go stale, loaded as context by skills/agents. Authored with **citations** to authoritative sources (McNeel/RhinoCommon, SideFX/Houdini, Pottmann *Architectural Geometry*, the Grasshopper Primer, *The Nature of Code*). Bootstrapped via a research-and-synthesis pass using researcher agents.
- `knowledge/parametric-scripting.md` — named param blocks; no magic numbers; validation + guards that warn vs. emit broken geometry; idempotent, scope-isolated rebuilds; determinism (seed randomness); units/tolerance discipline; generator-vs-result separation; re-runnability.
- `knowledge/geometry-quality.md` — continuity (G0/G1/G2), curve fairness, NURBS degree/knots, manifold/watertight, naked & non-manifold edges, degenerate faces, mesh density, curvature/zebra analysis.
- `knowledge/fabrication.md` — wall thickness, overhangs/support, watertightness (print); kerf, tool access, undercuts (CNC/mold); real-world scale.
- `knowledge/verification.md` — which views to capture, shaded vs. wireframe vs. curvature, silhouette comparison method, assertion patterns.

### Layer 2 — Live grounding (current API truth)
**Author the stable craft; fetch the volatile API.** Primitive signatures are never baked into the canon — they're confirmed live so they can't rot or hallucinate. Rhino MCP already exposes introspection (`list_rhinoscript_modules`, `search_rhinoscript_functions`, `get_rhinoscript_docs`, `get_module_functions`); `frank-build` confirms signatures before writing code. `frank-rhino-docs-researcher` / `frank-houdini-docs-researcher` encapsulate this.

### Layer 3 — Compounding memory (earned experience)
`frank-compound` writes each gotcha/win to `docs/solutions/` with structured frontmatter (tool, primitive, failure-mode, fix). `frank-learnings-researcher` retrieves relevant ones before each plan/build. **Seed entries from the spiral project (ship day one):**
1. Sweep1 framing-twist on tightly-curved planar rails → fixed-up-vector `SweepOneRail` route.
2. knotstyle overshoot vs. tangent kink — distinct failures, distinct fixes (chord-length knots + arc-length resampling vs. tangent control).
3. Adjacent-turn self-intersection guard — orientation-aware in-plane extent check, warn vs. emit tangled geometry.

Cross-cutting: **agents are instilled expertise too** — each reviewer's prompt is a best-practice checklist, run adversarially (try to falsify the match / break the geometry).

---

## Scope Boundaries

- Not a Grasshopper/`.gh` generator. Implementation is scripting via the MCP (RhinoScript-Python / RhinoCommon C#; Houdini Python/VEX).
- Not a renderer. Captures are for verification, not presentation.
- Houdini is **supported in design but unvalidated in execution** until its MCP is wired up (see Open Questions).
- Cross-platform mirrors (`.codex-plugin/`, `.cursor-plugin/`) deferred to a later version.

---

## File Tree (target)

```
frank/
  .claude-plugin/plugin.json        # manifest (done)
  README.md  LICENSE  .gitignore     # (done)
  CHANGELOG.md
  skills/
    frank-setup/SKILL.md
    frank-plan/SKILL.md
    frank-build/SKILL.md
    frank-review/SKILL.md
    frank-compound/SKILL.md
  agents/
    frank-silhouette-critic.agent.md
    frank-geometry-reviewer.agent.md
    frank-fabrication-reviewer.agent.md
    frank-parametric-architect.agent.md
    frank-rhino-docs-researcher.agent.md
    frank-houdini-docs-researcher.agent.md
    frank-learnings-researcher.agent.md
  knowledge/
    parametric-scripting.md
    geometry-quality.md
    fabrication.md
    verification.md
  references/
    rhino-mcp.md
    houdini-mcp.md                   # UNVALIDATED until confirmed
  examples/
    rhino/spiral-ribbon-sculpture.py # golden pattern (generalized from HAL)
  docs/
    plan.md                          # this file
    solutions/                       # compounding learnings store (seeded)
```

## Build Order (milestones)

- **M0 — Skeleton** ✅ dirs, manifest, README, LICENSE, .gitignore, plan.
- **M1 — Rhino spine (proven).** `frank-setup`, `frank-plan`, `frank-build`, `frank-review` + `references/rhino-mcp.md` + `frank-rhino-docs-researcher`. Validate end-to-end against the live Rhino document.
- **M2 — Core agents.** silhouette-critic, geometry-reviewer, parametric-architect.
- **M3 — Knowledge canon.** Author the four `knowledge/*.md` packs (research-and-synthesis pass, cited).
- **M4 — Compounding.** `frank-compound` + `frank-learnings-researcher` + seed `docs/solutions/` with the three spiral learnings.
- **M5 — Fabrication.** `fabrication-reviewer` + `knowledge/fabrication.md`.
- **M6 — Houdini track.** `references/houdini-mcp.md` (✅ drafted from source) + `frank-houdini-docs-researcher` + `docs/houdini-setup.md`. **Validate live** once `mcp__houdini__*` tools are connected: run the smoke test (below), resolve the `⟂ VALIDATE` list in the reference pack, compound any surprises.
- **M7 — Distribution.** `marketplace.json` entry, CHANGELOG, install docs; dogfood by rebuilding the spiral with frank end-to-end.

## Open Questions

### Houdini (resolved)
- **MCP:** [`capoomgit/houdini-mcp`](https://github.com/capoomgit/houdini-mcp), socket `localhost:9876`. Tool surface captured in `references/houdini-mcp.md`.
- **Introspection (Layer 2):** ✅ available via `execute_houdini_code` (arbitrary `hou` Python).
- **Capture (review):** ✅ via `render_single_view` / `render_quad_views` → image files we read.
- **Remaining:** Rob is connecting it to a session so `mcp__houdini__*` tools load; then run the live smoke test and resolve the `⟂ VALIDATE` list. No static example needed — we validate by direct experiment.

### Deferred
- Marketplace hosting (own repo's `.claude-plugin/marketplace.json` vs. submit to an existing marketplace like `every-marketplace`).
- Codex/Cursor mirrors.
- Whether `frank-build` should support C# (RhinoCommon) from day one or add it when sweeps need framing control.

## Cross-References

- Worked example: HAL `data/rhino/spiral-sculpture-generator.py`, plan `docs/plans/2026-05-29-001-feat-spiral-ribbon-sculpture-plan.md`.
- Structural model: `compound-engineering` plugin (skills/agents/manifest pattern).
