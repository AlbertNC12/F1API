"""Teams-related endpoints."""
import datetime
from typing import Optional

from fastapi import APIRouter, Path, Query

from ..scraper import parse_year_param, fetch_team_performance_multi_year

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("/{team_identifier}/performance", summary="Constructor Race-by-Race Performance")
@router.get("/{team_identifier}", include_in_schema=False)
def get_team_performance(
    team_identifier: str = Path(..., min_length=1, max_length=60, pattern=r"^[a-zA-Z0-9\-_ ]+$", description="Team name or slug (e.g. 'Mercedes', 'Red-Bull', 'Ferrari', 'McLaren')"),
    year: Optional[str] = Query(None, description="Optional year (e.g. '2023') or range (e.g. '2020-2025')")
):
    if year is not None:
        years = parse_year_param(year)
    else:
        current_year = datetime.date.today().year + 1
        years = list(range(current_year - 4, current_year + 1))

    return fetch_team_performance_multi_year(team_identifier, years)


@router.get("/{team_identifier}/performance/{year}", summary="Constructor Performance for Specific Year/Range")
def get_team_performance_by_year_path(
    team_identifier: str = Path(..., min_length=1, max_length=60, pattern=r"^[a-zA-Z0-9\-_ ]+$", description="Team name or slug (e.g. 'Mercedes', 'Ferrari', 'Red-Bull')"),
    year: str = Path(..., description="Championship year (e.g. '2023') or range (e.g. '2020-2025')")
):
    years = parse_year_param(year)
    return fetch_team_performance_multi_year(team_identifier, years)
