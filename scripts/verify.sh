#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
environments=(webPTDocker mobilePTDocker reDocker cryptDocker OSINTDocker)
if (( $# )); then environments=("$@"); fi
for environment in "${environments[@]}"; do
  case "$environment" in
    webPTDocker|mobilePTDocker|reDocker|cryptDocker|OSINTDocker) ;;
    *) echo "Unknown environment: $environment" >&2; exit 2 ;;
  esac
  image="$(echo "$environment" | tr '[:upper:]' '[:lower:]'):latest"
  docker compose -f "$environment/compose.yaml" config --quiet
  docker build -f "$environment/Dockerfile" -t "$image" .
  docker run --rm -i --network=none --cap-drop=ALL \
    --security-opt=no-new-privileges --ulimit fsize=16777216:16777216 \
    "$image" python3 - < tests/smoke_mcp.py
  if [[ "$environment" == OSINTDocker ]]; then
    docker run --rm -i --network=none --cap-drop=ALL \
      --security-opt=no-new-privileges "$image" python3 - < tests/smoke_rea.py
  fi
done
