# Complete OSRM Mapping Server Installation & Testing Guide

This guide provides a comprehensive, step-by-step walkthrough for installing and configuring an OSRM (Open Source Routing Machine) mapping server on a Linux host using Docker. We cover system prerequisites, data preparation, graph processing (extract, partition, customize), server startup (MLD workflow), and basic API testing.

## 1. System Prerequisites

Ensure you have a clean Linux environment (Ubuntu/Debian/CentOS) with administrative (sudo) access. You will install Python, Docker, and necessary tools.

```bash
sudo apt-get update
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.10 python3-pip -y
sudo apt install docker.io -y
sudo systemctl start docker
sudo systemctl enable docker
docker --version
```

* **software-properties-common**: Allows adding PPAs.
* **deadsnakes/ppa**: Provides Python 3.10.
* **docker.io**: Docker Engine package.

## 2. Create Working Directory

Choose a folder to store your map data and OSRM files:

```bash
mkdir -p ~/osrm/maps
cd ~/osrm/maps
```

This directory (`~/osrm/maps`) will hold all downloads, intermediate files, and server data.

## 3. Download & Merge OSM Data

Download the latest OpenStreetMap PBF extracts for Belgium and Switzerland from Geofabrik, then merge them:

```bash
wget https://download.geofabrik.de/europe/belgium-latest.osm.pbf
wget https://download.geofabrik.de/europe/switzerland-latest.osm.pbf
sudo apt-get install osmium-tool -y
osmium merge belgium-latest.osm.pbf switzerland-latest.osm.pbf -o belgium-switswitzerland-latest.osm.pbf
```

* **osmium merge**: Combines multiple `.osm.pbf` files into one, preserving metadata.

## 4. Extract the Raw Graph

Use the OSRM Docker image to parse the merged PBF into OSRM’s internal format:

```bash
sudo docker run --rm \
  -v "$(pwd):/data" \
  osrm/osrm-backend \
  osrm-extract -p /opt/car.lua /data/belgium-switswitzerland-latest.osm.pbf
```

* **--rm**: Automatically removes the container after completion.
* **-v "\$(pwd):/data"**: Mounts the current directory to `/data` in the container.
* **osrm-extract**: Parses the PBF according to `car.lua` profile, outputting a `.osrm` file.

## 5. Build the Routing Graph (MLD Workflow)

The MLD (Multi-Level Dijkstra) workflow improves query speed but requires two preprocessing steps.

1. **Partition:** Splits the graph into multiple levels:

   ```bash
   sudo docker run --rm \
     -v "$(pwd):/data" \
     osrm/osrm-backend \
     osrm-partition /data/belgium-switswitzerland-latest.osrm
   ```

2. **Customize:** Precomputes metrics (travel time, weight) for each level:

   ```bash
   sudo docker run --rm \
     -v "$(pwd):/data" \
     osrm/osrm-backend \
     osrm-customize /data/belgium-switswitzerland-latest.osrm
   ```

After these steps, you will have additional files (`*.osrm.partition`, `*.osrm.hsgr`, `*.osrm.ramIndex`, etc.) in your working directory.

## 6. Start the OSRM Routing Server

Launch the routing service in detached mode on port 5000, using the MLD algorithm:

```bash
sudo docker run -d --rm \
  -p 5000:5000 \
  --name osrm \
  -v "$(pwd):/data" \
  osrm/osrm-backend \
  osrm-routed --algorithm mld /data/belgium-switswitzerland-latest.osrm
```

* **-d**: Detaches the container (runs in background).
* **--name osrm**: Assigns a friendly name to the container.
* **-p 5000:5000**: Exposes port 5000 from container to host.

Verify it is running:

```bash
docker ps
# Look for 'osrm' with 'Up' status and port mapping 0.0.0.0:5000->5000/tcp
```

## 7. Test the Server

### 7.1 Version Check

```bash
curl -i http://localhost:5000/version
```

A successful response starts with `HTTP/1.1 200 OK` and includes `{ "osrm_version": ... }`.

### 7.2 Nearest-Node Lookup

```bash
curl -s "http://localhost:5000/nearest/v1/driving/4.3517,50.8503" | jq .
```

Expect `"code":"Ok"` and a `"waypoints"` array with snapped coordinates.

### 7.3 Simple Routing Query

```bash
curl -G \
  "http://localhost:5000/route/v1/driving/4.3517,50.8503;4.4025,51.2194" \
  --data-urlencode "overview=false" | jq .
```

A valid response has:

* `"code":"Ok"`
* a `"routes"` array containing `distance` and `duration`
* the `"waypoints"` array

## 8. Cleanup & Shutdown

When you’re done testing:

```bash
docker stop osrm
docker rm osrm
rm -f *.osrm*
```

This stops/removes the server container and cleans up generated files.

---

**Tip:** If you ever change the routing profile (e.g., to `bicycle.lua`), re-run **extract** & **partition/customize** (or **contract** for CH). Always match your `osrm-routed` flags (`--algorithm mld` vs no flag) to the preprocessing workflow used.

