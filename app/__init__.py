"""
Formula 1 API - Main application module.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import ALLOWED_ORIGINS
from .routes import drivers, races, teams, standings

tags_metadata = [
    {
        "name": "General",
        "description": "Root and health check endpoints.",
    },
    {
        "name": "Standings",
        "description": "Driver and Constructor Championship standings by year or year range (e.g. 2020-2025).",
    },
    {
        "name": "Teams",
        "description": "Constructor (Team) performance per race, historical points, and season breakdowns.",
    },
    {
        "name": "Drivers",
        "description": "Driver search with nationality, team, name, and year filters, plus career race histories.",
    },
    {
        "name": "Races",
        "description": "Grand Prix season calendars, winners, country filters, and full classifications.",
    },
]

app = FastAPI(
    title="Formula 1 Historical & Live API",
    description="""
🏎️ **Formula 1 API** provides clean, unified endpoints for Formula 1 standings, team performance, drivers, and race results from 1950 to present.

### Key Capabilities
* 🔍 **Advanced Filtering**:
  * Filter races by `year`, `country`, and `winner` (e.g. `GET /races?year=2024&country=Italy`).
  * Filter drivers by `name`, `nationality`, `team`, and `year` (e.g. `GET /drivers?nationality=British&team=mercedes`).
* 🏁 **Team Year Performance**: Race-by-race points breakdown for constructors across single years or year ranges.
* 📅 **Flexible Year Queries**: Accepts single years (`2023`) or year ranges (`2020-2025`) across all endpoints.
* 🏆 **Standings**: Driver & Team championship standings.
* 🏎️ **Driver History**: Career race results with automatic driver name / slug resolution (e.g. `antonelli`, `verstappen`, `hamilton`).
* 📊 **Detailed Classifications**: Full race results including car numbers, finish times, retirements, and championship points.
    """,
    version="1.5.0",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS with restricted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# Register route routers
app.include_router(drivers.router)
app.include_router(races.router)
app.include_router(teams.router)
app.include_router(standings.router)


# General endpoints
@app.get("/", tags=["General"], summary="API Root")
def read_root():
    return {
        "message": "Welcome to the Formula 1 API!",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }


@app.get("/health", tags=["General"], summary="Health Check")
def health_check():
    return {"status": "healthy"}
