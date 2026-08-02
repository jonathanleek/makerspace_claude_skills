# Makerspace Claude Tooling — Plan & Handoff

Living roadmap for Claude tooling (skills, slash commands, and — only where truly
needed — MCP servers) used around the makerspace. Focus right now: **Westbound
Workshop** (personal shop). Arch Reactor (shared community space) comes later and will
reuse the same tooling.

Primary work at WW: **woodworking, electronics, 3D printing.**

## Architecture — three layers

| Repo | Role | Location |
|---|---|---|
| **`makerspace_claude_skills`** (this repo) | **Tooling** — reusable across both workshops (skills, slash commands, MCP servers, install/scaffold scripts) | `/Users/jonathanleek/Documents/git/makerspace_claude_skills` |
| **`westbound_workshop_vault`** | **Context/data** — WW-specific. Existing **Obsidian vault + git repo**, "Claude-first" with strong conventions (session/project two-layer model, frontmatter schema, document the "why-not", timestamp decisions). Holds the tool inventory. | `/Users/jonathanleek/Documents/git/westbound_workshop/westbound_workshop_vault` |
| **project repos** | The actual builds, each its own git repo | in the workshop dir (to be separated out of the vault over time) |

`arch_reactor` becomes a sibling context repo later, reusing this same tooling.

## Distribution — Option A: global user-level install

- `install.sh` symlinks each `skills/<name>` → `~/.claude/skills/<name>`, so every local
  Claude Code session (Conductor local + terminal) sees them, in any directory.
- **Why global works and is cheap:** a skill is not "always on." Each session only sees
  the skill's name + one-line description (~1 line each); the full body loads only when
  the model judges it relevant or the user types `/name`. So irrelevant repos pay only a
  few description lines.
- `install.sh` **derives its own repo root** (`repo_root="$(cd "$(dirname "$0")" && pwd)"`),
  so it is location-independent — the repo can move without breaking anything.
- Symlinks must point at a **stable checkout** (this new `~/Documents/git/...` clone on
  `main`), never a Conductor worktree (those get archived → broken links).
- Installed skills double as slash commands (`/tool-advisor`, `/gridfinity`); no separate
  commands dir needed.
- **Caveat:** reliably covers Conductor (local) + terminal Claude Code. **Cowork** (used
  for Fusion) is a separate product — verify separately whether it reads `~/.claude/skills`.
  Conductor *cloud* workspaces won't have the symlink; work is local for now.

## MCP posture

Skip custom MCP servers for the current goals. The tool inventory is version-controlled
files → a skill that reads them is simpler and more robust than a server to keep running
(and sidesteps the "MCP is awkward in Conductor" pain). Reserve MCP for genuinely live/
external systems (e.g. the Fusion connection already used in Cowork).

## Planned repo layout

```
install.sh                     # idempotent; symlinks skills/* -> ~/.claude/skills/*; self-locating
README.md
PLAN.md                        # this file
config/
  workshops.toml               # workshop name -> vault absolute path (WW now, AR later)
skills/
  tool-advisor/
    SKILL.md                   # "what tools do I have?" / "can I do X on my Y?"
    references/inventory-format.md
  gridfinity/
    SKILL.md                   # research dims -> parametric bin -> STL
    scripts/                   # openscad glue + vendored gridfinity-rebuilt
    references/gridfinity-spec.md
```

Path resolution: skills read `config/workshops.toml` relative to their own base dir
(single source, no per-project duplication).

## Flagship capabilities

1. **Gridfinity designer** (`/gridfinity`): research object dimensions (by name via web
   search, or from a photo → confirm calipered measurements) → parametric bin sized to
   grid (42 mm footprint units, 7 mm height units, clearances) with cavity(ies) → headless
   **STL** saved into the project repo with a param manifest. v1 handles rectangular /
   cylindrical / multi-compartment cavities from dimensions. Generator: **OpenSCAD +
   `gridfinity-rebuilt`** (headless CLI). Research uses built-in WebSearch/WebFetch (no MCP).
2. **Tool advisor** (`/tool-advisor`): backed by a structured tool inventory in the vault.
   Answers "can I cut X on my Y", "what bit for Z", "do I have something for…", and feeds
   constraints (e.g. print-bed size) to the other skills. NOTE: the vault's
   `Shop Infrastructure/` currently covers shop furniture/storage/jigs — a real power-tool
   inventory still needs to be built.

## Build order

1. **Plumbing** — scaffold repo, `install.sh` (self-locating), `config/workshops.toml`
   (points at the vault), README. Run install; verify a skill registers.
2. **tool-advisor** — define tool-note schema (frontmatter, matching vault conventions),
   seed a couple real tools as examples, then populate together.
3. **gridfinity** — `brew install openscad`, vendor `gridfinity-rebuilt`, build
   research→parametric→STL pipeline, test end-to-end to a real STL.

## Decisions made

- Repo split: tooling here, context in the vault. ✔
- Distribution: Option A (global `~/.claude/skills` symlink). ✔
- Gridfinity generator: OpenSCAD / `gridfinity-rebuilt`. ✔ (OpenSCAD not currently
  installed; install via Homebrew at step 3.)
- Stable checkout relocated to `~/Documents/git/makerspace_claude_skills` (Option 2:
  Conductor remove + re-add from the new clone).

## Open confirms

- **Tool notes location:** proposed `Shop Infrastructure/Tools/` in the vault (one note per
  tool, matching existing conventions) — vs. a top-level `Tooling/`. Not yet confirmed.
- **`brew install openscad`** at step 3 — OK to install. Not yet confirmed.

## Relocation status (in progress)

Moving the Conductor root to `~/Documents/git/makerspace_claude_skills`:
1. [done] Clone created at the new path on `main`.
2. [done] This plan committed + pushed to `origin/main` so it survives the workspace teardown.
3. [user, in Conductor] Archive the `brasilia` workspace, remove the repo, then **Add
   repository** pointing at `/Users/jonathanleek/Documents/git/makerspace_claude_skills`.
4. [user] Delete the old `~/Documents/makerspace_claude_skills/` folder once the re-add works.

Next session: start at **Build order → step 1 (Plumbing)**.
