# Changelog

All notable changes to `frank` are documented here. This project adheres to
[Semantic Versioning](https://semver.org/) and the
[Keep a Changelog](https://keepachangelog.com/) format.

## [0.2.0] — 2026-06-01

The **skill spine** — frank becomes a usable plugin, not just scaffolding.

### Added

- **5 workflow skills** (slash commands): `/frank-setup`, `/frank-plan`,
  `/frank-build`, `/frank-review`, `/frank-compound`. Tool-agnostic — each
  detects the connected MCP family (`mcp__rhino__*` vs `mcp__houdini__*`) and
  STOP-gate-loads the matching `references/<tool>-mcp.md` pack.
- **6 agents**: `frank-silhouette-critic`, `frank-geometry-reviewer`,
  `frank-parametric-architect`, `frank-rhino-docs-researcher`,
  `frank-houdini-docs-researcher`, `frank-learnings-researcher`. The two
  reviewers share one pinned JSON findings contract consumed by `/frank-review`.
- **Knowledge canon (hybrid)**: `knowledge/parametric-scripting.md` and
  `knowledge/verification.md` authored with citations;
  `knowledge/geometry-quality.md` and `knowledge/fabrication.md` ship as
  self-describing labeled stubs that grow via `/frank-compound`.
- **`references/rhino-mcp.md`** — the Rhino MCP reference pack (mirrors the
  `houdini-mcp.md` 8-section contract).
- **`examples/rhino/spiral-ribbon-sculpture.py`** — the golden parametric
  generator pattern (named param block, idempotent layer helpers,
  foreign-layer object-count invariant) that `/frank-build` emits.
- **Three Rhino seed learnings** in `docs/solutions/` (sweep1 framing-twist,
  knotstyle overshoot vs. kink, adjacent-turn self-intersection), retrievable
  by `frank-learnings-researcher`.
- **`.claude-plugin/marketplace.json`** — local marketplace entry for
  development install.

### Changed

- `README.md` and `docs/plan.md` reconciled to the shipped surface — **six
  agents** (the 7th, `frank-fabrication-reviewer`, is deferred to M5) and the
  hybrid canon status (2 authored, 2 stub).
- `.claude-plugin/plugin.json` bumped to `0.2.0`; keywords refreshed. Loading
  relies on directory convention (no `skills`/`agents` registration keys),
  matching `compound-engineering` 3.8.1.

### Deferred

- `frank-fabrication-reviewer` agent + full `knowledge/fabrication.md` (M5).
- Broader marketplace publishing (M7).
- Live Houdini end-to-end dogfood (requires `mcp__houdini__*` connected).

## [0.1.0] — 2026-06-01

Initial scaffolding.

### Added

- `.claude-plugin/plugin.json`, `README.md`, `LICENSE`, `.gitignore`.
- `docs/plan.md` design spec; `docs/houdini-setup.md`.
- `references/houdini-mcp.md` (validated) and two Houdini learnings in
  `docs/solutions/`.
