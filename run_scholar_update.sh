#!/usr/bin/env bash
# Cron entry point: refresh Google Scholar stats and push them to the site.
#
# Installed via crontab; see `crontab -l`. Everything is logged to
# scholar_update.log so a failed run leaves evidence rather than silence.
#
# This duplicates the weekly GitHub Action on purpose. Scholar serves 403 to
# datacenter IPs intermittently, so the hosted runner succeeds only sometimes;
# a residential IP is the reliable path. Whichever runs second sees no change
# and exits quietly.

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="$HERE/scholar_update.log"

# cron runs with a minimal environment and no desktop session. `gh` keeps its
# token in the login keyring, which is reachable only over the session bus.
if [ -z "${DBUS_SESSION_BUS_ADDRESS:-}" ]; then
  export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u)/bus"
fi
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"

exec >>"$LOG" 2>&1
echo "=== $(date -Is) starting run ==="

# Keep the log from growing without bound.
if [ -f "$LOG" ] && [ "$(stat -c%s "$LOG")" -gt 2000000 ]; then
  tail -c 500000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi

cd "$HERE" || exit 1

if [ -n "$(git status --porcelain scholar_stats.json)" ]; then
  echo "FATAL: scholar_stats.json has uncommitted edits — refusing to clobber"
  exit 1
fi

# Sync BEFORE generating new values. The Action may have pushed its own update;
# rebasing first means our fresh numbers are written on top of it, so the commit
# applies cleanly instead of colliding with it.
if ! git pull --rebase --autostash origin main; then
  git rebase --abort 2>/dev/null
  echo "FATAL: could not rebase onto origin/main — resolve by hand"
  exit 1
fi

# No --tolerate-block here: on a residential IP a block is genuinely unexpected
# and should show up as a failure in the log, unlike in CI where it is routine.
if ! python3 update_scholar.py; then
  echo "update_scholar.py failed — stats left unchanged"
  exit 1
fi

if git diff --quiet -- scholar_stats.json; then
  echo "No change in stats; nothing to commit"
  echo "=== $(date -Is) done ==="
  exit 0
fi

# Stage only the stats file: the working tree often holds unrelated edits.
git add scholar_stats.json || exit 1
git commit -m "chore: update Google Scholar stats" || exit 1

# The Action can still push in the window between our pull and our push. Retry a
# few times, re-syncing each round.
for attempt in 1 2 3; do
  if git push origin main; then
    echo "Pushed: $(git rev-parse --short HEAD) — $(python3 -c 'import json;d=json.load(open("scholar_stats.json"));print(d["citations"],"citations, h-index",d["h_index"])')"
    echo "=== $(date -Is) done ==="
    exit 0
  fi

  echo "Push rejected (attempt $attempt/3) — re-syncing"

  # Only auto-resolve when our stats commit is the sole unpushed commit. With
  # other local work in the mix, a blanket conflict resolution could silently
  # discard it, so bail out and let a human look.
  git fetch origin main || exit 1
  ahead="$(git rev-list --count origin/main..HEAD)"
  if [ "$ahead" -ne 1 ]; then
    echo "FATAL: $ahead unpushed commits, expected 1 — not auto-resolving"
    exit 1
  fi

  # -X theirs favours the commit being replayed, which during a rebase is ours.
  # Correct here because we just fetched the newest numbers Scholar has.
  if ! git rebase -X theirs origin/main; then
    git rebase --abort 2>/dev/null
    echo "FATAL: rebase failed — resolve by hand"
    exit 1
  fi
done

echo "FATAL: push still failing after 3 attempts — commit is local"
exit 1
