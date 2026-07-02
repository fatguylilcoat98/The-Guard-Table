#!/usr/bin/env bash
# PathBack — auto-update script
# Built by Christopher Hughes · Sacramento, CA
# Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
# Truth · Safety · We Got Your Back
#
# Checks GitHub for new commits on the deploy branch; when found, pulls,
# reinstalls backend deps, rebuilds the frontend only if it changed, and
# restarts the service. Run it by hand or on the systemd timer in this
# folder — that's what makes "edit on my phone in GitHub → site updates
# itself" work.

set -euo pipefail

REPO_DIR="${REPO_DIR:-$HOME/pathback}"
BRANCH="${BRANCH:-main}"
SERVICE="${SERVICE:-pathback}"
# systemd by default; PM2 users: RESTART_CMD="pm2 restart pathback"
RESTART_CMD="${RESTART_CMD:-sudo systemctl restart $SERVICE}"

cd "$REPO_DIR"

git fetch origin "$BRANCH" --quiet
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse "origin/$BRANCH")

if [ "$LOCAL" = "$REMOTE" ]; then
    exit 0  # already up to date — the timer calls this every few minutes
fi

echo "PathBack update: $LOCAL -> $REMOTE"
git checkout "$BRANCH" --quiet
git reset --hard "origin/$BRANCH" --quiet

.venv/bin/pip install --quiet -r backend/requirements.txt

# Rebuild the React app only when frontend files actually changed
if ! git diff --quiet "$LOCAL" "$REMOTE" -- frontend/; then
    echo "Frontend changed — rebuilding"
    (cd frontend && npm ci --silent && npm run build)
fi

bash -c "$RESTART_CMD"
echo "PathBack deployed at $(git rev-parse --short HEAD)"
