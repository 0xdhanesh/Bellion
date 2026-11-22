#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
environments=(webPTDocker mobilePTDocker reDocker cryptDocker OSINTDocker networkPTDocker adPTDocker cloudPTDocker)
if (( $# )); then environments=("$@"); fi
# Public APK fixture (Appium ApiDemos, Apache-2.0) for the real JADX check, pinned
# by SHA-256 and fetched on the host because smoke containers run with --network=none.
fixture=tests/fixtures/ApiDemos-debug.apk
fixture_sha256=a9eecf37b26cd084855c530db81c2bb1b91f4c1b095a04f47aa7c20e2791f686
fetch_fixture() {
  if [[ ! -f "$fixture" ]]; then
    mkdir -p "$(dirname "$fixture")"
    curl --fail --location --silent --show-error --retry 3 --output "$fixture.part" \
      https://github.com/appium/android-apidemos/releases/download/v6.0.18/ApiDemos-debug.apk
    mv "$fixture.part" "$fixture"
  fi
  python3 -c 'import hashlib,sys; d=hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest(); sys.exit(d!=sys.argv[2] and f"fixture checksum mismatch: {d}")' \
    "$fixture" "$fixture_sha256"
}
for environment in "${environments[@]}"; do
  case "$environment" in
    webPTDocker|mobilePTDocker|reDocker|cryptDocker|OSINTDocker|networkPTDocker|adPTDocker|cloudPTDocker) ;;
    *) echo "Unknown environment: $environment" >&2; exit 2 ;;
  esac
  image="$(echo "$environment" | tr '[:upper:]' '[:lower:]'):latest"
  docker compose -f "$environment/compose.yaml" config --quiet
  docker build -f "$environment/Dockerfile" -t "$image" .
  docker run --rm -i --network=none --cap-drop=ALL \
    --security-opt=no-new-privileges --ulimit fsize=16777216:16777216 \
    "$image" python3 - < tests/smoke_mcp.py
  if [[ "$environment" == OSINTDocker || "$environment" == mobilePTDocker || "$environment" == reDocker ]]; then
    fetch_fixture
    docker run --rm -i --network=none --cap-drop=ALL --security-opt=no-new-privileges \
      --mount "type=bind,src=$PWD/tests/fixtures,dst=/fixtures,readonly" \
      "$image" python3 - < tests/smoke_rea.py
  fi
done
