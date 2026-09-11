"""Races-related endpoints."""
import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from fastapi import APIRouter, Path, Query, HTTPException

from ..scraper import (
    parse_year_param,
    parse_year_races_with_winners,
    fetch_detailed_race_result,
    race_matches_country
)

router = APIRouter(prefix="/races", tags=["Races"])


@router.get("", summary="Historical Race Winners (with Year, Country, Winner Filters)")
@router.get("/all", include_in_schema=False)
def get_all_races(
    year: Optional[str] = Query(None, description="Optional specific year (e.g. '2024') or range (e.g. '2020-2025')"),
    country: Optional[str] = Query(None, max_length=50, description="Optional country or Grand Prix location filter (e.g. 'Italy', 'Australia', 'Monaco')"),
    winner: Optional[str] = Query(None, max_length=50, description="Optional winner driver filter (e.g. 'Hamilton', 'Verstappen')")
):
    """
    Fetches Grand Prix races with optional filtering by year, country, and winner.
    Examples:
    - /races?year=2024
    - /races?country=Italy
    - /races?year=2024&country=Italy
    - /races?winner=hamilton
    """
    if year is not None:
        years_to_check = parse_year_param(year)
    else:
        start_year = 1950
        current_year = datetime.date.today().year + 1
        years_to_check = list(range(start_year, current_year + 1))

    with ThreadPoolExecutor(max_workers=25) as executor:
        results = [r for r in executor.map(parse_year_races_with_winners, years_to_check) if r is not None]

    if not results:
        raise HTTPException(
            status_code=404,
            detail="No race results found across the requested seasons."
        )

    # Apply filters per race
    if country or winner:
        w_clean = winner.strip().lower() if winner else None
        filtered_seasons = []
        for s in results:
            matching_races = []
            for r in s["races"]:
                if country and not race_matches_country(r, country):
                    continue
                if w_clean and w_clean not in r.get("winner", "").lower() and w_clean not in r.get("winner_code", "").lower():
                    continue
                matching_races.append(r)
            if matching_races:
                filtered_seasons.append({
                    "year": s["year"],
                    "total_races": len(matching_races),
                    "races": matching_races
                })
        results = filtered_seasons

    if not results:
        raise HTTPException(
            status_code=404,
            detail="No races matched the specified filter criteria."
        )

    results.sort(key=lambda x: x["year"])
    total_races = sum(s["total_races"] for s in results)

    # Return single-season format if single year requested without extra outer wrapping
    if year is not None and len(years_to_check) == 1 and not country and not winner:
        return results[0]

    return {
        "year_filter": year if year else "1950-present",
        "country_filter": country,
        "winner_filter": winner,
        "total_seasons": len(results),
        "total_races": total_races,
        "seasons": results
    }


@router.get("/{year}", summary="Season Races and Winners (Single Year or Range)")
def get_races_by_year(
    year: str = Path(..., description="Championship year (e.g. '2023') or range (e.g. '2020-2025')"),
    country: Optional[str] = Query(None, description="Optional country filter (e.g. 'Italy', 'Australia')")
):
    years = parse_year_param(year)
    with ThreadPoolExecutor(max_workers=25) as executor:
        results = [r for r in executor.map(parse_year_races_with_winners, years) if r is not None]

    if not results:
        raise HTTPException(status_code=404, detail=f"No race results found for year {year}")

    if country:
        filtered_seasons = []
        for s in results:
            matching_races = [r for r in s["races"] if race_matches_country(r, country)]
            if matching_races:
                filtered_seasons.append({
                    "year": s["year"],
                    "total_races": len(matching_races),
                    "races": matching_races
                })
        results = filtered_seasons

    if not results:
        raise HTTPException(status_code=404, detail=f"No races matched country '{country}' in {year}")

    if len(years) == 1 and not country:
        return results[0]

    results.sort(key=lambda x: x["year"])
    total_races = sum(s["total_races"] for s in results)

    return {
        "year_range": year,
        "country_filter": country,
        "total_seasons": len(results),
        "total_races": total_races,
        "seasons": results
    }


@router.get("/{year}/{race_identifier}", summary="Detailed Race Classification")
def get_race_classification(
    year: int = Path(..., ge=1950, le=2050, description="Championship year (e.g. 2026)"),
    race_identifier: str = Path(..., min_length=1, max_length=60, pattern=r"^[a-zA-Z0-9\-_ ]+$", description="Grand Prix slug or ID (e.g. 'australia', '1279')")
):
    year_races = parse_year_races_with_winners(year)
    if not year_races:
        raise HTTPException(status_code=404, detail=f"No races found for year {year}")

    target_race = None
    clean_ident = race_identifier.strip().lower()
    for race in year_races["races"]:
        if (race.get("race_slug") and clean_ident in race["race_slug"].lower()) or \
           (race.get("race_id") and race["race_id"] == clean_ident) or \
           (clean_ident in race["grand_prix"].lower()):
            target_race = race
            break

    if not target_race or not target_race.get("race_id") or not target_race.get("race_slug"):
        raise HTTPException(
            status_code=404,
            detail=f"Race '{race_identifier}' not found in {year} season."
        )

    return fetch_detailed_race_result(year, target_race["race_id"], target_race["race_slug"])


@router.get("/{year}/{race_id}/{race_slug}/race-result", include_in_schema=False)
@router.get("/{year}/{race_id}/{race_slug}", include_in_schema=False)
def get_detailed_race_result_explicit(
    year: int = Path(..., ge=1950, le=2050),
    race_id: str = Path(..., min_length=1, max_length=20, pattern=r"^[a-zA-Z0-9]+$"),
    race_slug: str = Path(..., min_length=1, max_length=60, pattern=r"^[a-zA-Z0-9\-]+$")
):
    return fetch_detailed_race_result(year, race_id, race_slug)
