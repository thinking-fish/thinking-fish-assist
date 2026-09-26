#!/usr/bin/env bash
# Developer ID sign + notarise + staple a Thinking Fish Assist Mac build.
# Run ON A MAC that has the "Developer ID Application: Thinking Fish Ltd (23KVDDE8NA)"
# identity in its login keychain and an App Store Connect API key for notarytool.
#
#   tfa/macos/sign_and_notarize.sh <unsigned.dmg> <out-dir>
#
# Env: ASC_KEY_PATH (AuthKey_XXXX.p8), ASC_KEY_ID, ASC_ISSUER_ID
#      SIGN_ID (default "Developer ID Application: Thinking Fish Ltd (23KVDDE8NA)")
# Output: <out-dir>/<same name>.dmg, signed, notarised and stapled. Upload it with
# tfa/release_upload.sh from a machine with the GitHub token.
# Mirrors the in-CI signing step in .github/workflows/tfa-build.yml (same flags).
set -euo pipefail
IN="${1:?unsigned dmg}"; OUT="${2:?output dir}"
SIGN_ID="${SIGN_ID:-Developer ID Application: Thinking Fish Ltd (23KVDDE8NA)}"
: "${ASC_KEY_PATH:?}" "${ASC_KEY_ID:?}" "${ASC_ISSUER_ID:?}"
security find-identity -v -p codesigning | grep -q "$SIGN_ID" || { echo "identity '$SIGN_ID' not in keychain"; exit 1; }
W=$(mktemp -d); MNT="$W/mnt"; mkdir -p "$MNT" "$OUT"
trap 'hdiutil detach "$MNT" -quiet 2>/dev/null || true; rm -rf "$W"' EXIT
hdiutil attach "$IN" -nobrowse -readonly -mountpoint "$MNT" -quiet
ditto "$MNT/ThinkingFishAssist.app" "$W/ThinkingFishAssist.app"
hdiutil detach "$MNT" -quiet
xattr -cr "$W/ThinkingFishAssist.app"
codesign --force --options runtime --timestamp -s "$SIGN_ID" --deep --strict "$W/ThinkingFishAssist.app" -v
codesign --verify --deep --strict -v "$W/ThinkingFishAssist.app"
NAME=$(basename "$IN")
mkdir "$W/stage" && ditto "$W/ThinkingFishAssist.app" "$W/stage/ThinkingFishAssist.app" && ln -s /Applications "$W/stage/Applications"
hdiutil create -volname "Thinking Fish Assist" -srcfolder "$W/stage" -ov -format UDZO "$OUT/$NAME" -quiet
codesign --force --timestamp -s "$SIGN_ID" "$OUT/$NAME"
xcrun notarytool submit "$OUT/$NAME" --key "$ASC_KEY_PATH" --key-id "$ASC_KEY_ID" --issuer "$ASC_ISSUER_ID" --wait --timeout 30m
xcrun stapler staple "$OUT/$NAME"
spctl -a -t open --context context:primary-signature -vv "$OUT/$NAME"
echo "signed + notarised: $OUT/$NAME"
