#!/usr/bin/env bash
set -euo pipefail

DATA_DIR=${DATA_DIR:-./data/osrm}
PBF_NAME=${PBF_NAME:-belgium-latest.osm.pbf}

if [ ! -f "${DATA_DIR}/${PBF_NAME}" ]; then
  echo "Missing ${DATA_DIR}/${PBF_NAME}. Run download_belgium.sh first."
  exit 1
fi

docker compose --profile mapping run --rm osrm-prepare
