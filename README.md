# Diagnostic Engine

A production-ready **FastAPI** microservice for knowledge-based OBD-II
Diagnostic Trouble Code (DTC) lookups.

The service reads an enriched DTC dataset at startup, caches it in memory,
and exposes a JSON API for use by other backend services.

---

## Project Structure

```
diagnostic_engine/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py   # FastAPI dependency injection
│   │   └── routes.py         # Route handlers
│   ├── models/
│   │   ├── __init__.py
│   │   └── dtc.py            # Pydantic request/response models
│   ├── services/
│   │   ├── __init__.py
│   │   └── diagnostic_service.py  # Core business logic
│   ├── utils/
│   │   ├── __init__.py
│   │   └── logger.py         # Centralised logging
│   ├── __init__.py
│   ├── config.py             # Pydantic-Settings configuration
│   └── main.py               # FastAPI app + lifespan
├── data/
│   └── dtc_dataset.csv       # OBD-II DTC dataset (3742 codes)
├── .dockerignore
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── README.md
└── requirements.txt
```

---

## Quick Start

### Local (no Docker)

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) copy and edit the env file
cp .env.example .env

# 4. Start the service
uvicorn app.main:app --reload
```

The API is now available at <http://localhost:8000>.

### Docker Compose

```bash
docker compose up --build
```

The service starts on port **8000** (configurable via `PORT` in `.env`).

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Service identity |
| `GET` | `/health` | Health check |
| `GET` | `/diagnostics/{dtc_code}` | Full DTC record lookup |
| `GET` | `/search?keyword=` | Free-text search |
| `GET` | `/statistics` | Dataset statistics |

### Interactive docs

* Swagger UI — <http://localhost:8000/docs>
* ReDoc — <http://localhost:8000/redoc>

---

## Endpoint Reference

### `GET /diagnostics/{dtc_code}`

Returns the full diagnostic record for an OBD-II code.
Matching is case-insensitive (`p0301` == `P0301`).

**200 OK**
```json
{
  "dtc": "P0301",
  "description": "Cylinder 1 Misfire Detected",
  "subsystem": "Ignition",
  "category": "Engine",
  "severity": "High",
  "severity_score": 4,
  "safe_to_drive": "No",
  "immediate_repair": "Yes",
  "explanation": "Cylinder 1 is not firing correctly...",
  "driver_action": "Stop driving if severe misfire persists..."
}
```

**404 Not Found**
```json
{ "error": "DTC code not found" }
```

---

### `GET /search?keyword=misfire`

Searches `description`, `subsystem`, and `category` columns.

```json
{
  "keyword": "misfire",
  "total": 8,
  "results": [
    {
      "dtc": "P0300",
      "description": "Random/Multiple Cylinder Misfire Detected",
      ...
    }
  ]
}
```

---

### `GET /statistics`

```json
{
  "total_dtcs": 3742,
  "severity_distribution": {
    "Low": 890,
    "Medium": 1240,
    "High": 980,
    "Critical": 632
  },
  "category_distribution": { "Engine": 1500, "Body": 800, ... },
  "subsystem_distribution": { "Ignition": 420, "Fuel System": 380, ... }
}
```

---

## Configuration

All settings can be overridden via environment variables or a `.env` file.

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_NAME` | `Diagnostic Engine` | Name shown in docs |
| `SERVICE_VERSION` | `1.0.0` | API version |
| `DATASET_PATH` | `data/dtc_dataset.csv` | Path to the CSV |
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8000` | Bind port |
| `RELOAD` | `false` | Enable uvicorn hot-reload |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

---

## Dataset

The dataset is a CSV file with the following columns:

| Column | Type | Description |
|--------|------|-------------|
| `dtc_code` | str | OBD-II code (e.g. `P0301`) |
| `description` | str | Short fault description |
| `subsystem` | str | Vehicle subsystem |
| `category` | str | Top-level category |
| `severity` | str | Low / Medium / High / Critical |
| `severity_score` | int | Numeric score 1–5 |
| `safe_to_drive` | str | Yes / No / Depends |
| `immediate_repair` | str | Yes / No |
| `explanation` | str | Technical explanation |
| `driver_action` | str | Recommended driver action |

The dataset is mounted as a **read-only volume** in Docker so it can be
updated without rebuilding the image.

---

## Development — Hot Reload in Docker

Uncomment the `command` and additional `volumes` block in
`docker-compose.yml` to enable `--reload` inside the container:

```yaml
command: >
  uvicorn app.main:app
  --host 0.0.0.0
  --port 8000
  --reload
volumes:
  - ./data:/app/data:ro
  - ./app:/app/app
```
