#!/bin/sh
set -e
mkdir -p "$HOME" "$PROJECTS_ROOT"
git config --global --add safe.directory '*'
git config --global init.defaultBranch main
if [ -n "$GH_TOKEN" ]; then
  gh auth setup-git || echo "warning: gh auth setup-git failed"
else
  echo "warning: GH_TOKEN not set - GitHub sync will be unavailable"
fi
[ -z "$CLAUDE_CODE_OAUTH_TOKEN" ] && [ -z "$ANTHROPIC_API_KEY" ] && echo "warning: no CLAUDE_CODE_OAUTH_TOKEN / ANTHROPIC_API_KEY - Claude Code can't sign in"
exec python /app/nas_bot.py
