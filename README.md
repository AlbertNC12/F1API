# 🏎️ Formula 1 Historical & Live REST API

A high-performance, asynchronous REST API built with **FastAPI** and **BeautifulSoup4** that dynamically scrapes and formats official Formula 1 championship standings, constructor performance, driver career statistics, and Grand Prix race results from 1950 to present.

---

## 🚀 Key Features

- 🔍 **Advanced Filters**:
  - Filter races by `year`, `country`, and `winner` (e.g. `GET /races?country=Italy` or `GET /races?year=2024&country=Italy`).
  - Filter drivers by `name`, `nationality`, `team`, and `year` (e.g. `GET /drivers?nationality=British` or `GET /drivers?name=hamilton&year=2023`).
- 🏁 **Constructor (Team) Performance**: Race-by-race points breakdown for any team (e.g. `Mercedes`, `Red-Bull`, `Ferrari`, `McLaren`).
- 📅 **Flexible Year Ranges**: Query single years (e.g. `2023`) or multi-year ranges (e.g. `2020-2025`) across all endpoints.
- 🏆 **Championship Standings**: Complete Driver & Constructor (Team) standings from 1950 to present.
- 🏎️ **Automatic Driver Slug Resolution**: Query driver career race history using just a surname (`antonelli`, `verstappen`, `hamilton`), full slug (`kimi-antonelli`), or official ID (`ANDANT01`).
- 🏁 **Grand Prix Calendars & Winners**: Retrieve race calendars, winners, completed laps, and finish times for any season or range of seasons.
- 📊 **Detailed Race Results**: Drill down into complete race classifications (car numbers, finishing positions, gaps, retirements, points).
- 🛡️ **Hardened & Resilient**: Input validation, connection pooling with retry backoff, thread-safe memory caching, and CORS support.

---

## 🛠️ Quick Start

### 1. Local Python Setup

```bash
# Clone and enter the project directory
cd PythonProject

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the API server
python main.py
```

The server will start at `http://127.0.0.1:8000`.

---

### 2. Docker Setup

```bash
# Build the Docker image
docker build -t f1-api .

# Run the container
docker run -d -p 8000:8000 --name f1-api-container f1-api
```

---

## 📖 Interactive Documentation

FastAPI automatically generates interactive API documentation:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc UI**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📡 API Reference & Query Filters

### 1. Races & Grand Prix Filters

| Method | Endpoint | Query Parameters | Description |
|---|---|---|---|
| `GET` | `/races` | `?year=2024` | Get all races for a specific year or range (`?year=2020-2025`) |
| `GET` | `/races` | `?country=Italy` | Filter races by country (e.g. `Italy`, `Australia`, `Monaco`, `UK`, `USA`) |
| `GET` | `/races` | `?winner=hamilton` | Filter races by winner name |
| `GET` | `/races` | `?year=2024&country=Italy` | Combined filters |
| `GET` | `/races/{year}/{race_identifier}` | None | Detailed race classification (e.g. `/races/2026/australia`) |

---

### 2. Driver Search & Filters

| Method | Endpoint | Query Parameters | Description |
|---|---|---|---|
| `GET` | `/drivers` | `?nationality=British` | Filter drivers by nationality (e.g. `British`, `GBR`, `Italian`, `NED`, `German`) |
| `GET` | `/drivers` | `?name=hamilton` | Filter drivers by name or surname |
| `GET` | `/drivers` | `?teams="alfa romeo"` | Filter drivers by team constructor |
| `GET` | `/drivers` | `?year=2023` | Filter drivers active in a season or range (`?year=2020-2025`) |
| `GET` | `/drivers` | `?name=hamilton&year=2023` | Combined driver filters |
| `GET` | `/drivers/{driver_identifier}/races` | `?year=2025` | Driver career race history (e.g. `/drivers/antonelli/races`) |

---

### 3. Team Performance Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/teams/{team_identifier}/performance` | Race-by-race points breakdown for a team (optional `?year=2023` or `?year=2020-2025`) |
| `GET` | `/teams/{team_identifier}/performance/{year}` | Specific year or range performance (e.g. `/teams/Ferrari/performance/2023`) |

---

### 4. Standings Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/standings/drivers/{year}` | Driver Championship standings (single year `2023` or range `2020-2025`) |
| `GET` | `/standings/teams/{year}` | Constructor Championship standings (single year `2023` or range `2020-2025`) |

---

## 🧪 Running Tests

Execute the automated pytest suite:

```bash
pytest -v
```
