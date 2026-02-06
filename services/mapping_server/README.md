# OSRM Mapping Server (Belgium)

This setup uses Docker + OSRM to serve Belgium map data with the MLD workflow.

## 1) Download Belgium PBF
```bash
./services/mapping_server/download_belgium.sh
```

This creates `./data/osrm/belgium-latest.osm.pbf`.

## 2) Prepare OSRM Graph
```bash
./services/mapping_server/prepare_belgium.sh
```

This runs:
- `osrm-extract`
- `osrm-partition`
- `osrm-customize`

## 3) Start OSRM Server
```bash
./services/mapping_server/start_osrm.sh
```

Server will listen on `http://localhost:5000`.

## 4) Verify
```bash
./services/mapping_server/verify_osrm.sh
```

## 5) Configure the API
Set `.env`:
```
MAPPING_SERVICE_URL=http://localhost:5000
```

The API will default to OSRM when this is set.

## Notes
- Data lives in `./data/osrm` (ignored by git).
- If you change routing profiles, re-run the prepare step.
