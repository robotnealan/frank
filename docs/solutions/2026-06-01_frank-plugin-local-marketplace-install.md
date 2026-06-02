---
date: 2026-06-01
tool: meta
area: plugin-install
type: gotcha
mcp: n/a
tags: [frank, plugin, marketplace, claude-code, source-path, reload-plugins, disable-model-invocation]
---

# Installing frank as a local Claude Code marketplace — `source` must start with `./`

> **Schema note (read first):** this is frank's first `tool: meta` learning. The `frank-compound` frontmatter scopes `tool:` to `rhino | houdini` (the two *modeling* tracks), but this is a frank **plugin-dev/install** learning with no modeling track — so it uses a new `meta` value. `frank-learnings-researcher` / `frank-plan` filter on `tool:` and should **exclude `meta`** from modeling-plan grounding so a build is never grounded on it. Until that's wired, this doc is discoverable by grep/tags, not by tool-filtered retrieval. **Roadmap:** add `meta` to the schema enum and teach the researcher to skip it. (frank-compound currently has no proper home for learnings about frank itself.)

## Symptom

`claude plugin marketplace add /path/to/frank` succeeds — the marketplace registers fine — but `claude plugin install frank@frank-marketplace` immediately fails with:

> This plugin uses a source type your Claude Code version does not support. Update Claude Code and try again.

The error blames your Claude Code version, so the instinct is to upgrade. That's a red herring — the `marketplace.json` plugin entry had `"source": "."`.

## Root cause

On Claude Code **2.1.160**, a relative plugin `source` **must start with `./`**. Bare `"."` (the idiomatic "plugin lives at the marketplace root") is parsed as an *unsupported source type*, not as a relative path — hence the misleading "update Claude Code" message.

Supported `source` forms:
- **Relative-path strings starting with `./`** — `./plugins/<name>` for a subdir, or `./` for a plugin at the marketplace root.
- **Object forms** — `{ "source": "github" | "url" | "git-subdir" | "npm", ... }`.

Every working marketplace inspected used `./plugins/<name>` or a git object form; **none used `"."`**. The dot is the trap.

## Fix

Set `"source": "./"` (with the slash) in the `marketplace.json` plugin entry, then update and install:

```bash
claude plugin marketplace update frank-marketplace
claude plugin install frank@frank-marketplace
```

Minimal working `marketplace.json` for a plugin-at-root layout (the plugin's `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` both live at the repo root):

```json
{
  "name": "frank-marketplace",
  "owner": { "name": "Robert Nealan" },
  "plugins": [
    {
      "name": "frank",
      "source": "./",
      "description": "Plan, build, and review 3D models with Claude Code and modeling MCPs."
    }
  ]
}
```

Activate the installed plugin with `/reload-plugins` — **no Claude Code restart needed**. Re-run `/reload-plugins` after editing skills/agents during development.

## Verified facts (2026-06-01)

- ✅ After the `"."` → `"./"` fix, `frank` installs and shows **enabled** at user scope.
- ✅ `claude plugin details frank@frank-marketplace` lists all **5 skills + 6 agents** with their token costs — proof the components parse and are recognized.
- ⛔ `"source": "."` is rejected with the "source type your Claude Code version does not support" error. The slash is load-bearing.
- ℹ️ `/reload-plugins` printed `4 plugins · 0 skills · 61 agents`. The `0 skills` is a **delta counter** (zero *newly added* skills on this reload), **not** a failure — frank's skills are active (proven by invoking `/frank-build` etc.). Don't read `0 skills` as "skills broke."
- ℹ️ A skill with `disable-model-invocation: true` (here, `frank-setup`) is **user-command-only**. The model trying to call it through the Skill tool errors `cannot be used ... due to disable-model-invocation`. This is **intended** — it's a slash-command-only skill, not a bug.

## Cross-References

- `README.md` (Installation section) — the install commands + the resolved `source: "./"` note; links back here for the "why."
- `skills/frank-setup/SKILL.md` — the canonical `disable-model-invocation: true` example (a user-command-only skill).
- `docs/houdini-setup.md` — sibling install/setup guide (the HoudiniMCP *bridge*, a different layer than the plugin).
- `docs/solutions/2026-06-01_houdini-mcp-setup-gotchas.md` — sibling setup gotcha, but about a third-party MCP server, not the Claude Code plugin layer (Low overlap; kept separate by design).
