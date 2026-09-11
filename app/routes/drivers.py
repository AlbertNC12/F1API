"""Drivers-related endpoints."""
from typing import Optional

from fastapi import APIRouter, Path, Query, HTTPException

from ..cache import load_driver_directory
from ..config import NATIONALITY_TO_CODE
from ..scraper import resolve_driver, fetch_all_driver_races, parse_year_param

router = APIRouter(prefix="/drivers", tags=["Drivers"])


@router.get("", summary="List / Search Drivers with Filters")
def list_drivers(
    name: Optional[str] = Query(None, max_length=60, description="Filter by driver name or surname (e.g. 'hamilton', 'verstappen')"),
    nationality: Optional[str] = Query(None, max_length=40, description="Filter by nationality or country (e.g. 'British', 'GBR', 'Italian', 'NED')"),
    team: Optional[str] = Query(None, max_length=60, description="Filter by team/constructor (e.g. 'Alfa Romeo', 'Ferrari', 'Mercedes')"),
    teams: Optional[str] = Query(None, include_in_schema=False),
    year: Optional[str] = Query(None, description="Filter by active year or range (e.g. '2023', '2020-2025')")
):
    """
    Search and filter Formula 1 drivers by name, nationality, team, or active year.
    Examples:
    - /drivers?nationality=British
    - /drivers?name=hamilton
    - /drivers?teams=alfa romeo
    - /drivers?year=2023&team=ferrari
    """
    registry = load_driver_directory()
    drivers = list(registry.values())

    # 1. Filter by name
    if name:
        n = name.strip().lower()
        drivers = [
            d for d in drivers
            if n in d["name"].lower() or n in d["driver_slug"].lower() or n in d["driver_id"].lower()
        ]

    # 2. Filter by nationality
    if nationality:
        nat_raw = nationality.strip().lower()
        mapped_code = NATIONALITY_TO_CODE.get(nat_raw, nat_raw.upper())
        drivers = [
            d for d in drivers
            if d.get("nationality", "").upper() == mapped_code or nat_raw in d.get("nationality", "").lower()
        ]

    # 3. Filter by team (team or teams query param)
    team_query = team or teams
    if team_query:
        t_clean = team_query.strip().lower()
        if year:
            # Filter by team AND year - only show drivers at that team during those years
            target_years = set(parse_year_param(year))
            drivers = [
                d for d in drivers
                if any(
                    t_clean in team.lower() and any(y in target_years for y in d.get("team_years", {}).get(team, []))
                    for team in d.get("teams", [])
                )
            ]
        else:
            # Filter by team only - any year
            drivers = [
                d for d in drivers
                if any(t_clean in t.lower() for t in d.get("teams", []))
            ]

    # 4. Filter by active year(s)
    if year and not team_query:
        target_years = set(parse_year_param(year))
        drivers = [
            d for d in drivers
            if any(y in target_years for y in d.get("years", []))
        ]

    return {
        "total": len(drivers),
        "drivers": drivers
    }


@router.get("/{driver_identifier}/races", summary="Driver Career Race Results (with Year or Range Filter)")
@router.get("/{driver_identifier}", include_in_schema=False)
def get_driver_races(
    driver_identifier: str = Path(..., min_length=1, max_length=60, pattern=r"^[a-zA-Z0-9\-_ ]+$", description="Driver surname, slug, or ID (e.g. 'antonelli', 'kimi-antonelli', 'ANDANT01')"),
    year: Optional[str] = Query(None, description="Optional single year (e.g. '2025') or range (e.g. '2020-2025')")
):
    driver = resolve_driver(driver_identifier)
    if not driver:
        raise HTTPException(
            status_code=404,
            detail=f"Driver '{driver_identifier}' could not be resolved. Use /drivers to search available drivers."
        )

    parsed_years = parse_year_param(year) if year is not None else None
    return fetch_all_driver_races(driver["driver_id"], driver["driver_slug"], years=parsed_years)


@router.get("/{driver_id}/{driver_slug}/races", include_in_schema=False)
@router.get("/{driver_id}/{driver_slug}", include_in_schema=False)
def get_driver_races_explicit(
    driver_id: str = Path(..., min_length=1, max_length=20, pattern=r"^[a-zA-Z0-9]+$"),
    driver_slug: str = Path(..., min_length=1, max_length=60, pattern=r"^[a-zA-Z0-9\-]+$"),
    year: Optional[str] = Query(None, description="Optional single year (e.g. '2025') or range (e.g. '2020-2025')")
):
    parsed_years = parse_year_param(year) if year is not None else None
    return fetch_all_driver_races(driver_id, driver_slug, years=parsed_years)
