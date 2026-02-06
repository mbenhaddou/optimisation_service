#!/usr/bin/env bash
set -euo pipefail

DATA_DIR=${DATA_DIR:-./data/osrm}
PBF_NAME=${PBF_NAME:-belgium-latest.osm.pbf}
PBF_URL=${PBF_URL:-https://download.geofabrik.de/europe/belgium-latest.osm.pbf}

mkdir -p "${DATA_DIR}"

if [ -f "${DATA_DIR}/${PBF_NAME}" ]; then
  echo "PBF already exists at ${DATA_DIR}/${PBF_NAME}"
  exit 0
fi

if command -v curl >/dev/null 2>&1; then
  curl -L "${PBF_URL}" -o "${DATA_DIR}/${PBF_NAME}"
elif command -v wget >/dev/null 2>&1; then
  wget -O "${DATA_DIR}/${PBF_NAME}" "${PBF_URL}"
else
  echo "Neither curl nor wget found. Install one to download the PBF."
  exit 1
fi

ls -lh "${DATA_DIR}/${PBF_NAME}"
