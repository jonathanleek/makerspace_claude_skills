#!/usr/bin/env bash
#
# install.sh — register this repo's skills with local Claude Code.
#
# Symlinks each skills/<name> -> ~/.claude/skills/<name> so every local Claude
# Code session (Conductor local + terminal) sees them, in any directory. A skill
# only costs its name + one-line description until invoked, so a global install is
# cheap even for unrelated repos.
#
# Self-locating: derives its own repo root, so the repo can move without breaking.
# Idempotent: safe to re-run; refreshes stale/missing links, leaves good ones.
#
# IMPORTANT: run this from a *stable* checkout (e.g. ~/Documents/git/...), never a
# Conductor worktree — worktrees get archived, which would leave broken symlinks.

set -euo pipefail

repo_root="$(cd "$(dirname "$0")" && pwd)"
skills_src="$repo_root/skills"
skills_dst="$HOME/.claude/skills"

if [[ ! -d "$skills_src" ]]; then
  echo "error: no skills/ directory found at $skills_src" >&2
  exit 1
fi

# Warn (don't block) if installing from what looks like a Conductor worktree.
case "$repo_root" in
  */conductor/workspaces/*)
    echo "WARNING: installing from a Conductor worktree:" >&2
    echo "  $repo_root" >&2
    echo "  Worktrees get archived — symlinks will break. Install from a stable" >&2
    echo "  checkout (e.g. ~/Documents/git/makerspace_claude_skills) instead." >&2
    echo >&2
    ;;
esac

mkdir -p "$skills_dst"

installed=0 skipped=0
for skill_dir in "$skills_src"/*/; do
  [[ -d "$skill_dir" ]] || continue
  name="$(basename "$skill_dir")"
  src="${skill_dir%/}"
  link="$skills_dst/$name"

  if [[ ! -f "$src/SKILL.md" ]]; then
    echo "skip: $name (no SKILL.md)"
    skipped=$((skipped + 1))
    continue
  fi

  if [[ -L "$link" ]]; then
    current="$(readlink "$link")"
    if [[ "$current" == "$src" ]]; then
      echo "ok:   $name (already linked)"
      installed=$((installed + 1))
      continue
    fi
    echo "relink: $name (was -> $current)"
    rm "$link"
  elif [[ -e "$link" ]]; then
    echo "skip: $name (a non-symlink already exists at $link — leaving it alone)" >&2
    skipped=$((skipped + 1))
    continue
  fi

  ln -s "$src" "$link"
  echo "link: $name -> $src"
  installed=$((installed + 1))
done

echo
echo "done: $installed installed/ok, $skipped skipped"
echo "skills dir: $skills_dst"
