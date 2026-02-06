
[![Tests](https://github.com/mbenhaddou/optimisation_service/actions/workflows/tests.yml/badge.svg)](https://github.com/mbenhaddou/optimisation_service/actions/workflows/tests.yml)

# Mentis Optimization Library

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [Routing](#routing)
  - [Scheduling](#scheduling)
- [Configuration Options](#configuration-options)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)
- [Version Changes Tracking](#version-changes-tracking)


## Introduction

Welcome to the Mentis Optimization Library! This library offers robust solutions for complex optimization problems in both **Routing** and **Scheduling**. Designed for scalability and efficiency, our library enables organizations to make data-driven decisions in allocating resources and planning tasks.

For a more detailed introduction, refer to the [Introduction.md](./documentation/Introduction.md) in the documentation.

## Features
- **Routing**: Optimize routes for teams and resources.
- **Scheduling**: Assign tasks to work centers based on various constraints.

## Phase 1 API Service (FastAPI + Worker)

Phase 1 introduces a split-services architecture:
- `services/api_service` for HTTP API + job submission
- `services/worker_service` for async job execution

### Local Run (SQLite + Redis)
1. Create `.env` from `.env.example` and adjust values if needed.
2. Install dependencies:
```bash
python -m venv .venv
./.venv/bin/pip install -r requirements.txt
```
3. Start Redis (or point `REDIS_URL` to an existing instance).
4. Start the API:
```bash
PYTHONPATH=. ./.venv/bin/uvicorn services.api_service.app.main:app --reload --port 8000
```
5. Start the worker:
```bash
PYTHONPATH=. ./.venv/bin/celery -A services.worker_service.app.celery_app.celery_app worker --loglevel=info
```

### Docker Compose (Postgres + Redis)
```bash
docker compose up --build
```
API will be available at `http://localhost:8000`.

### Submit a Solve Job
```bash
curl -X POST http://localhost:8000/v1/solve \\
  -H \"Content-Type: application/json\" \\
  -d @optimise/routing/request_offline_deterministic.json
```

Check status:
```bash
curl http://localhost:8000/v1/jobs/<job_id>
```

### Admin API Keys
Set `ADMIN_API_KEY` in `.env`, then create keys:
```bash
curl -X POST http://localhost:8000/v1/admin/api-keys \\
  -H \"Content-Type: application/json\" \\
  -H \"X-Admin-Key: <ADMIN_API_KEY>\" \\
  -d '{\"name\": \"default\"}'
```

### Free Tier Usage Units
Usage is computed as `node_count * node_count` (distance matrix size). Configure:
- `FREE_TIER_UNITS` for per-month free-tier cap (per API key)
- `ENFORCE_USAGE_LIMITS=true` to enforce

### Rate Limiting
Configure:
- `ENABLE_RATE_LIMITING=true`
- `API_RATE_LIMIT_PER_MINUTE=60`

### Mapping Service
If you run a mapping server, set `MAPPING_SERVICE_URL` (or `ROUTING_ENGINE`) in `.env`.

## OSRM Mapping Server (Belgium)

Setup scripts live in `services/mapping_server`.

```bash
./services/mapping_server/download_belgium.sh
./services/mapping_server/prepare_belgium.sh
./services/mapping_server/start_osrm.sh
```

The OSRM service will run on `http://localhost:5000`.

## Phase 2 Web Portal (Next.js)

Portal lives in `services/web_portal`.

### Local Run
```bash
cd services/web_portal
npm install
npm run dev
```

Set `.env.local` with:
```
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

## Phase 3 Auth & User Profiles

### Register
```bash
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{ "email": "owner@example.com", "password": "changeme", "organization": "Acme Ops" }'
```

### Login
```bash
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{ "email": "owner@example.com", "password": "changeme" }'
```

### Profile
```bash
curl http://localhost:8000/v1/portal/me \
  -H "Authorization: Bearer <token>"
```

### Org API Keys
```bash
curl -X POST http://localhost:8000/v1/portal/api-keys \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{ "name": "default" }'
```

## Requirements
- Python 3.9
- JSON for data input

## Installation

As part of Mentis team, `git clone` this project.

[//]: # (There is no pip install at the moment. Could be something 
to aim for but can we then really sell that service?)
[//]: # (```bash
pip install ....
```)

## Usage

### Routing

To perform routing optimization, the library needs a JSON file containing 
information about teams, depots, work orders, and workers. 
For a detailed schema, refer to the [Routing Documentation](./documentation/Routing.md).

Start the application by running [`application.py`](./application.py)
This will start a server that you can query :
```python
# get the input file 
with open("tests/routing_functional/inputs/basic_1.json",encoding='utf8') as f :
    basic1 = json.load(f)
# send the request to the server
r = requests.post('http://localhost:5051/soa/routing', data=json.dumps(basic1))
# check the status 
print(r.status_code)
# explore the results
results = r.json()
```


[//]: # (These line of code do not work at the moment.)
[//]: # (
```python
from mentis import Routing
routing = Routing('path/to/your/input.json'
routing.optimize(
```)

### Scheduling

To optimize scheduling, a separate JSON file containing work orders, work centers, and time constraints is required.
Detailed schema can be found in [Scheduling Documentation](./documentation/Scheduling.md).

```python
from optimise.scheduling.job_scheduler import JobShopOptimizer
from optimise.scheduling.data_model import preprocess_request, create_data_model
request=preprocess_request("path/to/Config.json")

data_model=create_data_model(request)

scheduling = JobShopOptimizer(data_model)
scheduling.solve()

res = scheduling.get_results()

```

## Configuration Options

The library supports a variety of options to fine-tune the optimization process.
These options can be specified in the input JSON file. 

[//]: # (TODO : add the configuration.md file to the documentation folder)

[//]: # (See [Configuration Documentation](./documentation/Configuration.md for details.)


## Examples

Sample JSON files and code snippets can be found in the [Examples](./examples) directory.

## Contributing

We welcome contributions! Please see our [Contributing Guide](./CONTRIBUTING.md) for more details.


## Contact

For any questions or support, please contact `mbenhaddou@mentis-consulting.be`.

---

This README file aims to be comprehensive yet concise, giving users all the necessary information they need to understand and get started with your project. Feel free to adjust this template to suit the specific needs of your project.

## Version Changes Tracking

For a more detailed changelog, please check the [CHANGELOG.md](./CHANGELOG.md) file in the repository.

### [1.0.1] - 2023-09-01
#### Added
- Support for minimizing distance in the routing algorithm.
- Documentation for `minimize_distance` parameter.

#### Fixed
- Bug causing scheduling optimization to fail for certain configurations.

### [1.0.0] - 2023-08-01
#### Added
- Initial release.
- Features for routing and scheduling optimization.
