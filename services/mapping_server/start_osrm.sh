#!/usr/bin/env bash
set -euo pipefail

docker compose --profile mapping up -d osrm
