"""Standings-related endpoints."""
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Path, HTTPException

from ..scraper import parse_year_param, fetch_single_year_driver_standings, fetch_single_year_team_standings

router = APIRouter(prefix="/standings", tags=["Standings"])


def get_driver_standings_impl(year: str):
    """Implementation for driver standings endpoints."""
    years = parse_year_param(year)
    if len(years) == 1:
        res = fetch_single_year_driver_standings(years[0])
        if not res:
            raise HTTPException(status_code=404, detail=f"No driver standings found for year {years[0]}")
        return res

    with ThreadPoolExecutor(max_workers=25) as executor:
        results = [r for r in executor.map(fetch_single_year_driver_standings, years) if r is not None]

    if not results:
        raise HTTPException(status_code=404, detail=f"No driver standings found for year range {year}")

    results.sort(key=lambda x: x["year"])
    return {
        "year_range": year,
        "total_seasons": len(results),
        "seasons": results
    }


@router.get("/drivers/{year}", summary="Driver Championship Standings (Single Year or Range)")
def get_driver_standings(
    year: str = Path(..., description="Championship year (e.g. '2023') or range (e.g. '2020-2025')")
):
    return get_driver_standings_impl(year)


def get_team_standings_impl(year: str):
    """Implementation for team standings endpoints."""
    years = parse_year_param(year)
    if len(years) == 1:
        res = fetch_single_year_team_standings(years[0])
        if not res:
            raise HTTPException(status_code=404, detail=f"No team standings found for year {years[0]}")
        return res

    with ThreadPoolExecutor(max_workers=25) as executor:
        results = [r for r in executor.map(fetch_single_year_team_standings, years) if r is not None]

    if not results:
        raise HTTPException(status_code=404, detail=f"No team standings found for year range {year}")

    results.sort(key=lambda x: x["year"])
    return {
        "year_range": year,
        "total_seasons": len(results),
        "seasons": results
    }


@router.get("/teams/{year}", summary="Constructor Standings (Single Year or Range)")
def get_team_standings(
    year: str = Path(..., description="Championship year (e.g. '2023') or range (e.g. '2020-2025')")
):
    return get_team_standings_impl(year)
