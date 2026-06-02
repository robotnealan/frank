# frank

**Plan, build, and review 3D models with Claude Code — through a modeling MCP (Rhino or Houdini).**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
&nbsp;Claude Code plugin · 5 skills · 6 agents

`frank` is a Claude Code plugin that turns a modeling MCP server into a disciplined design partner. It plans the form before touching geometry, builds it as a re-runnable parametric generator, reviews the result against your reference — and it's *frank* about what's wrong with your geometry.

Honest about your topology.

## Why

LLM-driven CAD usually fails the same ways: hallucinated API calls, magic-number scripts you can't tune, geometry that duplicates or stomps your existing model, and "looks done" with no actual verification. `frank` encodes the opposite as a workflow:

- **Parametric, not one-off** — every build is a named parameter block you can re-run and tune.
- **Idempotent & scoped** — rebuilds clear only their own layer/namespace; your existing model is never touched (a foreign-object-count invariant is checked every run).
- **Grounded, not guessed** — primitive signatures are confirmed live from the MCP before code is emitted, not recalled from memory.
- **Verified, not vibes** — a capture → compare → adjust loop with geometric assertions and *your* sign-off, not "looks good."
- **Compounding** — every solved gotcha gets written down so the next model doesn't repeat it.

## Requirements

frank drives a **modeling application through an MCP server** — it does nothing on its own. You need:

1. **[Claude Code](https://claude.com/claude-code)** (CLI, desktop, or IDE).
2. **A modeling MCP server connected to Claude Code** — one of:

   | Modeler | MCP server | What frank needs |
   |---|---|---|
   | **Rhino** | a RhinoMCP server, e.g. [`jingcheng-chen/rhinomcp`](https://github.com/jingcheng-chen/rhinomcp) | `mcp__rhino__*` tools available; Rhino running with its MCP addon started |
   | **Houdini** | [`capoomgit/houdini-mcp`](https://github.com/capoomgit/houdini-mcp) | `mcp__houdini__*` tools available; Houdini running with the socket server started — see **[docs/houdini-setup.md](docs/houdini-setup.md)** for a hardened, step-by-step setup (the upstream has a few install gotchas frank documents and patches) |

   Confirm a server is live with `claude mcp list` — you should see `rhino` or `houdini` as **✓ Connected**.

frank is tool-agnostic: the same `plan → build → review` flow drives whichever modeler is connected, by loading that tool's reference pack.

## Install

```bash
claude plugin marketplace add robotnealan/frank      # add the marketplace from GitHub
claude plugin install frank@frank-marketplace        # install the plugin
```

Then run **`/reload-plugins`** in Claude Code to activate the skills and agents — no restart needed. Verify with:

```bash
claude plugin details frank@frank-marketplace        # lists 5 skills + 6 agents
```

> `/reload-plugins` may print `0 skills` — that's a *delta* counter (zero **newly** added), not a failure; the skills are active. See [the install learning](docs/solutions/2026-06-01_frank-plugin-local-marketplace-install.md) for this and other gotchas.

<details>
<summary><b>Local / development install</b> (clone and iterate)</summary>

```bash
git clone https://github.com/robotnealan/frank
claude plugin marketplace add /path/to/frank         # add by local path
claude plugin install frank@frank-marketplace
```

Re-run `/reload-plugins` after editing any skill or agent to pick up changes. The plugin's `marketplace.json` uses `"source": "./"` (plugin at the marketplace root) — on Claude Code a relative `source` must start with `./`; bare `"."` is rejected.
</details>

## Quick start

With a modeling MCP connected, the workflow is five slash commands:

```text
/frank-setup     # verify the connection; record units, tolerance, existing layers/networks
/frank-plan      # design the form: artifact type, fidelity, primitives, the param block + assertions
/frank-build     # emit + run an idempotent, scope-isolated parametric generator; capture the result
/frank-review    # capture → compare → adjust against your reference, with your sign-off
/frank-compound  # record a solved gotcha so the next model doesn't rediscover it
```

You don't have to use all five — `/frank-build "a parametric helical coil"` works on its own. `frank-plan` and `frank-review` add rigor for harder or reference-driven forms.

## Skills

| Command | Purpose |
|---|---|
| `/frank-setup` | Verify the modeling MCP is connected; record units, tolerance, existing layers/networks. *(User-run: it's a `disable-model-invocation` skill.)* |
| `/frank-plan` | Produce a structured modeling plan: artifact type, fidelity target, reference intake, primitive selection, parameter-block & verification-assertion design. |
| `/frank-build` | Confirm primitive signatures live, then write and run an idempotent, scope-isolated, re-runnable parametric generator; capture the result. |
| `/frank-review` | Capture → compare → adjust loop: pinned-camera capture, two adversarial reviewers, merged findings, parameter tweaks — with you as the acceptance authority. |
| `/frank-compound` | Capture a solved modeling problem (gotcha + fix) into the learnings store so it compounds. |

## Agents

Six agents ship today. `frank-fabrication-reviewer` (wall thickness, overhangs, watertightness, undercuts) is planned alongside `knowledge/fabrication.md`.

| Agent | Lens |
|---|---|
| `frank-silhouette-critic` | Adversarial visual comparison of captured views against the reference (dispatched on a vision-capable model). |
| `frank-geometry-reviewer` | Units/scale, naked & non-manifold edges, self-intersection, degenerate faces, continuity. |
| `frank-parametric-architect` | Parameter-block design: named, validated, idempotent, no magic numbers. |
| `frank-rhino-docs-researcher` | Confirms exact RhinoScript / RhinoCommon signatures (live MCP introspection, or official docs with the evidence tier flagged). |
| `frank-houdini-docs-researcher` | Confirms Houdini node / VEX usage. |
| `frank-learnings-researcher` | Retrieves relevant past learnings from `docs/solutions/` before each plan/build. |

## How it works — three layers of knowledge

frank keeps *durable craft* separate from *volatile API*:

1. **Canon** (`knowledge/*.md`) — what good looks like (named param blocks, scope isolation, verification discipline). Authored with citations; doesn't go stale.
2. **Reference packs** (`references/<tool>-mcp.md`) — which calls and which verified policies on *this* tool. The only place tool-specific detail lives.
3. **Live grounding** — the `*-docs-researcher` agents confirm exact signatures in-session, so the canon never bakes an API that can rot or hallucinate.

| Canon pack | Status |
|---|---|
| `parametric-scripting.md` | ✅ Authored — named param blocks, idempotent scope-isolated rebuilds, guards that warn, determinism, units/tolerance. |
| `verification.md` | ✅ Authored — which views to capture, pinned-camera discipline, silhouette comparison, geometric assertions, human acceptance. |
| `geometry-quality.md` | 🚧 Stub — continuity, watertightness/manifoldness, mesh quality. Grows via `/frank-compound`. |
| `fabrication.md` | 🚧 Stub — wall thickness, overhangs, watertight solids, tolerance/clearance, export hygiene. |

And it **compounds**: every solved gotcha is written to `docs/solutions/` (via `/frank-compound`) and retrieved before future work, so the system gets smarter with use.

## Tool support

| Tool | Status |
|---|---|
| **Rhino** (RhinoMCP) | ✅ **Proven** — full `plan → build → review` validated live (rebuilt a parametric ribbon sculpture end to end, idempotent and scope-isolated). |
| **Houdini** (HoudiniMCP) | ✅ **Wired & hardened** — MCP connection proven; the upstream render-deadlock and install gotchas are fixed and documented (`docs/solutions/`). Full build/review loop validation in progress. |

## Contributing

Issues and PRs welcome. frank is designed to *compound*: if you solve a modeling or tooling gotcha, capture it with `/frank-compound` (or add a `docs/solutions/YYYY-MM-DD_<slug>.md` learning by hand) so the next person inherits it. Adding a new modeler is mostly a new `references/<tool>-mcp.md` pack plus a `*-docs-researcher` agent — the skill spine is already tool-agnostic.

## License

MIT © Robert Nealan
