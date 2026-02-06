#!/usr/bin/env bash
set -euo pipefail

OSRM_URL=${OSRM_URL:-http://localhost:5000}

curl -s "${OSRM_URL}/version" | head -c 200

echo ""

curl -s "${OSRM_URL}/nearest/v1/driving/4.3517,50.8503" | head -c 200

echo ""
