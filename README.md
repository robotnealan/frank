# frank

**Plan, build, and review 3D models with Claude Code.**

`frank` is a Claude Code plugin that turns a modeling MCP server (Rhino today, Houdini next) into a disciplined design partner. It plans the form before touching geometry, builds it as a re-runnable parametric generator, and reviews the result against your reference — and it's *frank* about what's wrong with your geometry.

Named for Frank Gehry. Honest about your topology.

## Why

LLM-driven CAD usually fails the same ways: hallucinated API calls, magic-number scripts you can't tune, geometry that duplicates or stomps your existing model, and "looks done" with no actual verification. `frank` encodes the opposite as a workflow:

- **Parametric, not one-off** — every build is a named parameter block you can re-run and tune.
- **Idempotent & scoped** — rebuilds clear only their own layer/namespace; your existing model is never touched.
- **Grounded, not guessed** — primitive signatures are fetched live from the MCP, not recalled from memory.
- **Verified, not vibes** — a capture → compare → adjust loop with geometric assertions, not "looks good."
- **Compounding** — every gotcha gets written down so the next model doesn't repeat it.

## Getting started

1. Install a supported modeling MCP and connect it to Claude Code (see **Tool support**).
2. Install this plugin from the marketplace.
3. Run `/frank-setup` to verify the connection and capture your document's units, tolerance, and existing layers.
4. `/frank-plan` your form → `/frank-build` it → `/frank-review` against your reference.

## Components

- **Skills** — the slash-command workflow (`setup`, `plan`, `build`, `review`, `compound`).
- **Agents** — reviewer & researcher personas the skills spawn.
- **Knowledge** — the durable craft canon (parametric scripting, geometry quality, fabrication, verification).
- **References** — per-tool MCP toolboxes, idioms, and gotchas.

## Skills

| Command | Purpose |
|---|---|
| `/frank-setup` | Verify the modeling MCP is connected; record units, tolerance, existing layers; scaffold a workspace. |
| `/frank-plan` | Produce a structured modeling plan: artifact type, fidelity target, reference intake, primitive selection, parameter-block & verification-assertion design. |
| `/frank-build` | Write and run an idempotent, scoped, re-runnable parametric generator; capture the viewport. |
| `/frank-review` | Capture → compare → adjust loop: multi-view capture, compare to reference/requirements, run geometric assertions, propose parameter tweaks. |
| `/frank-compound` | Capture a solved modeling problem (gotcha + fix) into the learnings store so it compounds. |

## Agents

| Agent | Lens |
|---|---|
| `frank-silhouette-critic` | Adversarial visual comparison of captured views against the reference. |
| `frank-geometry-reviewer` | Units/scale, naked & non-manifold edges, self-intersection, degenerate faces, continuity. |
| `frank-fabrication-reviewer` | Wall thickness, overhangs, watertightness, undercuts, real-world scale. |
| `frank-parametric-architect` | Parameter-block design: named, validated, idempotent, no magic numbers. |
| `frank-rhino-docs-researcher` | Confirms exact RhinoScript / RhinoCommon signatures via live MCP introspection. |
| `frank-houdini-docs-researcher` | Confirms Houdini node/VEX usage. |
| `frank-learnings-researcher` | Retrieves relevant past learnings before each plan/build. |

## Knowledge

The durable craft canon, loaded as context by skills and agents. Authored with citations; principles that don't go stale. Volatile API signatures are deliberately *not* baked here — they're fetched live (see `references/`).

- `parametric-scripting.md`, `geometry-quality.md`, `fabrication.md`, `verification.md`

## Tool support

| Tool | Status |
|---|---|
| **Rhino** (RhinoMCP) | ✅ Proven — primary, validated against a live document. |
| **Houdini** (HoudiniMCP) | 🚧 In progress — track documented; flow being validated. |

## Installation

_Marketplace publishing TBD. For local development, add this directory as a plugin source in Claude Code._

## License

MIT © Robert Nealan
