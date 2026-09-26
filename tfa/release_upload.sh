#!/usr/bin/env bash
# Attach (or replace) files on a Thinking Fish Assist GitHub release.
#   tfa/release_upload.sh <tag> <file>...
# Token: $GITHUB_TOKEN or ~/.config/github/token (contents: write).
set -euo pipefail
TAG="${1:?tag}"; shift
REPO=thinking-fish/thinking-fish-assist
TOKEN="${GITHUB_TOKEN:-$(cat ~/.config/github/token)}"
api() { curl -fsSL -H "Authorization: token $TOKEN" -H "Accept: application/vnd.github+json" "$@"; }
REL=$(api "https://api.github.com/repos/$REPO/releases/tags/$TAG")
RID=$(echo "$REL" | python3 -c "import json,sys;print(json.load(sys.stdin)['id'])")
for f in "$@"; do
  n=$(basename "$f")
  OLD=$(echo "$REL" | python3 -c "import json,sys;print(next((a['id'] for a in json.load(sys.stdin)['assets'] if a['name']=='$n'),''))")
  [ -n "$OLD" ] && api -X DELETE "https://api.github.com/repos/$REPO/releases/assets/$OLD" >/dev/null
  api -X POST -H "Content-Type: application/octet-stream" --data-binary @"$f" \
    "https://uploads.github.com/repos/$REPO/releases/$RID/assets?name=$n" >/dev/null
  echo "uploaded $n to $TAG"
done
