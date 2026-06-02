# Resolution Template — frank learning

The section structure and frontmatter schema for a learning written to `docs/solutions/` by `/frank-compound`. One template for all frank learnings — the `type` field (`gotcha` | `pattern` | `decision`) distinguishes them, not separate templates.

**Filename:** `docs/solutions/YYYY-MM-DD_<slug>.md` — ISO date, lowercase kebab `<slug>` naming the problem (e.g. `2026-06-01_rhino-sweep1-framing-twist.md`).

---

## Frontmatter schema

| Field | Required | Value |
|-------|----------|-------|
| `date` | yes | ISO date `YYYY-MM-DD` the learning was captured. |
| `tool` | yes | `rhino` \| `houdini` — the modeling tool the problem occurred on. **This is how `frank-learnings-researcher` and `frank-plan` scope by track.** |
| `area` | yes | A concise kebab slug for the sub-domain: `sweep`, `curve-fitting`, `scope-isolation`, `rendering`, `setup`, `booleans`, `units`, etc. |
| `type` | yes | `gotcha` (a behavior that bit you + its fix) \| `pattern` (a reusable build/verify approach) \| `decision` (a tooling/modeling choice + durable rationale). |
| `mcp` | yes | The MCP this concerns — `jingcheng-chen/rhinomcp` for Rhino, `capoomgit/houdini-mcp` for Houdini (or `n/a` for a tool-craft learning that isn't MCP-specific). |
| `tags` | yes | Flow-style array of lowercase keywords; always include the tool name and `frank`. |

**YAML safety:** any array item (a `tags` entry) that starts with a YAML indicator character (`[ ] { } , & * # ? \| - < > = ! % @ :`) or contains `": "` must be wrapped in double quotes, or the parser silently mis-reads it.

---

## Section structure

```markdown
---
date: YYYY-MM-DD
tool: rhino            # or houdini
area: <kebab-slug>     # sweep | curve-fitting | scope-isolation | rendering | setup | ...
type: gotcha           # or pattern | decision
mcp: jingcheng-chen/rhinomcp   # or capoomgit/houdini-mcp | n/a
tags: [<tool>, mcp, <area-keyword>, <symptom-keyword>, frank]
---

# <Clear, specific title — name the failure and the fix in one line>

<One-paragraph lede: what broke, in what context, and the one-line takeaway. This is
what a future session reads first to decide whether this learning is the one they want.>

## Symptom
<The observable failure. What the geometry / render / MCP actually did wrong —
a twist, a fold, curvature overshoot, a self-intersection, a deadlock, wrong units/scale.
Be concrete: name the view it showed up in, the object, the error text if any.>

## Root cause
<The underlying mechanism. Why it happened — default sweep framing, uniform knots over a
density swing, adjacent-turn radial spacing below the cross-section extent, a main-thread
GL render pumping the event loop. Distinguish failures that look similar but have distinct
causes (e.g. overshoot vs. kinks) when relevant.>

## Fix
<The verified resolution, with a code snippet when it is load-bearing. Show the proven
approach — the RhinoCommon SweepOneRail up-vector route, chord-length knots + arc-length
resampling, the orientation-aware guard, render_single_view + read-from-disk. If there
were dead ends, note what did NOT work and why, so the next session skips them.>

## Verified facts (YYYY-MM-DD)
- ✅ <something confirmed live>
- ⛔ <something confirmed broken / banned>
- ℹ️ <a caveat or nuance worth recording>

## Cross-References
- Reference pack: `references/<tool>-mcp.md` (the tool surface + verified policy this concerns).
- Patterns enforced: `knowledge/<canon>.md` (the canon principle this learning instantiates —
  `parametric-scripting.md`, `verification.md`, `geometry-quality.md`, or `fabrication.md`).
- Related learnings: `docs/solutions/YYYY-MM-DD_<sibling>.md` (sibling gotchas/patterns).
- Origin: <where this came from — the session, plan, or project that surfaced it>.
```

---

## Notes

- **Bidirectional linking is mandatory.** When the learning links a reference pack or sibling learning, update that target's Cross-References to link back to this learning. A one-way link is a dead end.
- **`type` chooses the emphasis, not the sections.** A `pattern` learning leans on **Fix** as "the approach"; a `decision` leans on **Root cause** as "why this over the alternatives"; a `gotcha` leads with **Symptom**. The five sections are always present.
- **Verified facts must be real.** Only list ✅/⛔/ℹ️ items that were actually observed or run — this section is the trust anchor of the whole knowledge store.
- **The `tool:` field is load-bearing.** It is the sole mechanism that scopes a learning to its track; `/frank-compound` does not load any reference pack to determine it — it reads the field you write here.
