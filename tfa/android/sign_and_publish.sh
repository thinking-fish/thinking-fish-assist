#!/usr/bin/env bash
# Sign the CI-built Android APK with the Thinking Fish Assist release key and attach
# it to the GitHub release. Runs on a Thinking Fish admin machine, so the keystore
# never goes to GitHub.
#
#   tfa/android/sign_and_publish.sh <release-tag> <workflow-run-id>
#
# Needs: Android build-tools (apksigner, zipalign), a GitHub token with contents
# write + actions read on thinking-fish/thinking-fish-assist in $GITHUB_TOKEN (or
# ~/.config/github/token), and the keystore + password from the vault:
#   TFA_KEYSTORE (default ~/claudia-vault/keys/thinking-fish-assist/android-release.jks)
#   TFA_KEYSTORE_PASS (default: read from the vault note)
set -euo pipefail
TAG="${1:?release tag, e.g. v1.0.0}"
RUN="${2:?workflow run id that built the APK}"
REPO=thinking-fish/thinking-fish-assist
TOKEN="${GITHUB_TOKEN:-$(cat ~/.config/github/token)}"
BT="${ANDROID_BUILD_TOOLS:-$(ls -d ~/android-sdk/build-tools/* | sort -V | tail -1)}"
KS="${TFA_KEYSTORE:-$HOME/claudia-vault/keys/thinking-fish-assist/android-release.jks}"
PASS="${TFA_KEYSTORE_PASS:-$(grep -o 'store + key password `[^`]*`' ~/claudia-vault/services/thinking-fish-assist.md | sed 's/.*`\(.*\)`/\1/')}"
[ -n "$PASS" ] || { echo "no keystore password"; exit 1; }
W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
api() { curl -fsSL -H "Authorization: token $TOKEN" -H "Accept: application/vnd.github+json" "$@"; }

# 1. fetch the unsigned artifact from that run
AID=$(api "https://api.github.com/repos/$REPO/actions/runs/$RUN/artifacts" |
      python3 -c "import json,sys;print([a['id'] for a in json.load(sys.stdin)['artifacts'] if a['name']=='unsigned-android-universal'][0])")
api -o "$W/a.zip" "https://api.github.com/repos/$REPO/actions/artifacts/$AID/zip"
unzip -q -o "$W/a.zip" -d "$W"

# 2. align + sign (v1-v3 schemes); apksigner replaces the CI debug signature
"$BT/zipalign" -f -p 4 "$W/Thinking-Fish-Assist-android.apk" "$W/aligned.apk"
"$BT/apksigner" sign --ks "$KS" --ks-key-alias tfassist --ks-pass "pass:$PASS" --key-pass "pass:$PASS" \
  --out "$W/Thinking-Fish-Assist-android.apk" "$W/aligned.apk"
"$BT/apksigner" verify --print-certs "$W/Thinking-Fish-Assist-android.apk" | grep -E "SHA-256|Signer #1 certificate DN"
(cd "$W" && sha256sum Thinking-Fish-Assist-android.apk > SHA256SUMS-android.txt && cat SHA256SUMS-android.txt)

# 3. attach to the release (replacing any earlier upload of the same name)
REL=$(api "https://api.github.com/repos/$REPO/releases/tags/$TAG")
RID=$(echo "$REL" | python3 -c "import json,sys;print(json.load(sys.stdin)['id'])")
for f in Thinking-Fish-Assist-android.apk SHA256SUMS-android.txt; do
  OLD=$(echo "$REL" | python3 -c "import json,sys;print(next((a['id'] for a in json.load(sys.stdin)['assets'] if a['name']=='$f'),''))")
  [ -n "$OLD" ] && api -X DELETE "https://api.github.com/repos/$REPO/releases/assets/$OLD" >/dev/null
  api -X POST -H "Content-Type: application/octet-stream" --data-binary @"$W/$f" \
    "https://uploads.github.com/repos/$REPO/releases/$RID/assets?name=$f" >/dev/null
  echo "uploaded $f to $TAG"
done
