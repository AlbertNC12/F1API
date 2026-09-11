"""
Web scraping module for Formula 1 data.
Contains functions for fetching standings, races, and driver results.
"""
import datetime
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Union

import requests
from bs4 import BeautifulSoup
from fastapi import HTTPException

from .config import HTTP_SESSION, HTTP_TIMEOUT, COUNTRY_MAP
from .cache import CACHE_LOCK, RESPONSE_CACHE


def parse_year_param(year_input: Union[str, int]) -> List[int]:
    """Parse year parameter and return list of years."""
    val = str(year_input).strip()
    if "-" in val:
        parts = val.split("-")
        if len(parts) != 2:
            raise HTTPException(
                status_code=422,
                detail="Invalid year range format. Expected 'YYYY-YYYY' (e.g., 2020-2025)."
            )
        start_str, end_str = parts[0].strip(), parts[1].strip()
        if not start_str.isdigit() or not end_str.isdigit():
            raise HTTPException(
                status_code=422,
                detail="Year range must contain numeric years (e.g., 2020-2025)."
            )
        start, end = int(start_str), int(end_str)
        if start > end:
            start, end = end, start
        if start < 1950 or end > 2050:
            raise HTTPException(
                status_code=422,
                detail=f"Years must be within 1950 and 2050. Given: {start}-{end}"
            )
        return list(range(start, end + 1))
    else:
        if not val.isdigit():
            raise HTTPException(
                status_code=422,
                detail="Year must be a number (e.g. 2023) or a range (e.g. 2020-2025)."
            )
        y = int(val)
        if y < 1950 or y > 2050:
            raise HTTPException(
                status_code=422,
                detail=f"Year must be between 1950 and 2050. Given: {y}"
            )
        return [y]


def resolve_driver(identifier: str) -> Optional[dict]:
    """Resolve a driver identifier to driver info from registry."""
    from .cache import load_driver_directory
    
    if not identifier:
        return None

    registry = load_driver_directory()
    clean_raw = re.sub(r"[^a-zA-Z0-9\-_ ]", "", identifier).strip().lower()
    query = clean_raw.replace(" ", "-")

    if query in registry:
        return registry[query]

    for d in registry.values():
        if d["driver_id"].lower() == clean_raw.lower():
            return d

    spaced_query = query.replace("-", " ")
    for d in registry.values():
        if query in d["driver_slug"] or spaced_query in d["name"].lower():
            return d

    return None


def fetch_single_year_driver_standings(year: int):
    """Fetch driver championship standings for a single year."""
    cache_key = f"driver_standings:{year}"
    with CACHE_LOCK:
        if cache_key in RESPONSE_CACHE:
            return RESPONSE_CACHE[cache_key]

    url = f"https://www.formula1.com/en/results/{year}/drivers"
    try:
        response = HTTP_SESSION.get(url, timeout=HTTP_TIMEOUT)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch data from Formula 1 website: {str(e)}")

    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table")
    if not table:
        return None

    standings = []
    tbody = table.find("tbody") or table
    for tr in tbody.find_all("tr"):
        cols = tr.find_all("td")
        if len(cols) >= 5:
            pos_text = cols[0].get_text(strip=True)

            driver_link = cols[1].find("a")
            driver_id = None
            driver_slug = None
            if driver_link and "href" in driver_link.attrs:
                m = re.search(r"/drivers/([A-Z0-9]+)/([a-z0-9\-]+)", driver_link["href"])
                if m:
                    driver_id = m.group(1)
                    driver_slug = m.group(2)

            raw_spans = [s.get_text(strip=True) for s in cols[1].find_all("span") if not s.find_all("span") and s.get_text(strip=True)]
            driver_name = " ".join(raw_spans[:2]) if len(raw_spans) >= 2 else cols[1].get_text(strip=True)
            driver_code = raw_spans[2] if len(raw_spans) >= 3 else ""

            nationality = cols[2].get_text(strip=True)
            team = cols[3].get_text(strip=True)
            pts_text = cols[4].get_text(strip=True)

            try:
                points = float(pts_text) if "." in pts_text else int(pts_text)
            except ValueError:
                points = pts_text

            standings.append({
                "position": int(pos_text) if pos_text.isdigit() else pos_text,
                "driver": driver_name,
                "code": driver_code,
                "driver_id": driver_id,
                "driver_slug": driver_slug,
                "nationality": nationality,
                "team": team,
                "points": points
            })

    if not standings:
        return None

    result = {
        "year": year,
        "total_drivers": len(standings),
        "standings": standings
    }
    with CACHE_LOCK:
        RESPONSE_CACHE[cache_key] = result
    return result


def fetch_single_year_team_standings(year: int):
    """Fetch team/constructor standings for a single year."""
    cache_key = f"team_standings:{year}"
    with CACHE_LOCK:
        if cache_key in RESPONSE_CACHE:
            return RESPONSE_CACHE[cache_key]

    url = f"https://www.formula1.com/en/results/{year}/team"
    try:
        response = HTTP_SESSION.get(url, timeout=HTTP_TIMEOUT)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch data from Formula 1 website: {str(e)}")

    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table")
    if not table:
        return None

    standings = []
    tbody = table.find("tbody") or table
    for tr in tbody.find_all("tr"):
        cols = tr.find_all("td")
        if len(cols) >= 3:
            pos_text = cols[0].get_text(strip=True)
            team_link = cols[1].find("a")
            team_slug = None
            if team_link and "href" in team_link.attrs:
                m = re.search(r"/team/([^/]+)", team_link["href"])
                if m:
                    team_slug = m.group(1)

            team_name = cols[1].get_text(strip=True)
            pts_text = cols[2].get_text(strip=True)

            try:
                points = float(pts_text) if "." in pts_text else int(pts_text)
            except ValueError:
                points = pts_text

            standings.append({
                "position": int(pos_text) if pos_text.isdigit() else pos_text,
                "team": team_name,
                "team_slug": team_slug,
                "points": points
            })

    if not standings:
        return None

    result = {
        "year": year,
        "total_teams": len(standings),
        "standings": standings
    }
    with CACHE_LOCK:
        RESPONSE_CACHE[cache_key] = result
    return result


def parse_team_year_performance(year: int, team_slug: str):
    """Parse a team's race-by-race performance for a specific year."""
    cache_key = f"team_perf:{year}:{team_slug}"
    with CACHE_LOCK:
        if cache_key in RESPONSE_CACHE:
            return RESPONSE_CACHE[cache_key]

    url = f"https://www.formula1.com/en/results/{year}/team/{team_slug}"
    try:
        response = HTTP_SESSION.get(url, timeout=HTTP_TIMEOUT)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find("table")
        if not table:
            return None

        races = []
        tbody = table.find("tbody") or table
        for tr in tbody.find_all("tr"):
            cols = tr.find_all("td")
            if len(cols) >= 3:
                a_tag = cols[0].find("a")
                race_id, race_slug = None, None
                if a_tag and "href" in a_tag.attrs:
                    m = re.search(r"/races/(\d+)/([^/]+)/race-result", a_tag["href"])
                    if m:
                        race_id = m.group(1)
                        race_slug = m.group(2)

                for svg in cols[0].find_all("svg"):
                    svg.decompose()
                gp = cols[0].get_text(strip=True)
                date = cols[1].get_text(strip=True)
                pts = cols[2].get_text(strip=True)

                try:
                    points = float(pts) if "." in pts else int(pts)
                except ValueError:
                    points = pts

                races.append({
                    "grand_prix": gp,
                    "date": date,
                    "race_id": race_id,
                    "race_slug": race_slug,
                    "points": points
                })

        if races:
            tot_pts = sum(r["points"] for r in races if isinstance(r["points"], (int, float)))
            result = {
                "year": year,
                "team_slug": team_slug,
                "total_races": len(races),
                "total_points": tot_pts,
                "races": races
            }
            with CACHE_LOCK:
                RESPONSE_CACHE[cache_key] = result
            return result
    except Exception:
        pass
    return None


def resolve_team_slug_for_year(year: int, team_identifier: str) -> Optional[str]:
    """Resolve a team identifier to a team slug for a specific year."""
    clean_id = team_identifier.strip().lower().replace(" ", "-")
    standings_data = fetch_single_year_team_standings(year)
    if not standings_data:
        return None

    for t in standings_data["standings"]:
        ts = t.get("team_slug")
        if ts:
            if ts.lower() == clean_id or clean_id in ts.lower() or clean_id in t["team"].lower():
                return ts
    return None


def fetch_team_performance_multi_year(team_identifier: str, years: List[int]):
    """Fetch a team's performance across multiple years."""
    clean_id = team_identifier.strip().lower()

    def fetch_for_year(y: int):
        matched_slug = resolve_team_slug_for_year(y, clean_id)
        if matched_slug:
            return parse_team_year_performance(y, matched_slug)
        return parse_team_year_performance(y, team_identifier)

    with ThreadPoolExecutor(max_workers=25) as executor:
        results = [r for r in executor.map(fetch_for_year, years) if r is not None]

    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No performance data found for team '{team_identifier}' in requested year(s)."
        )

    results.sort(key=lambda x: x["year"])
    total_races = sum(s["total_races"] for s in results)
    total_points = sum(s["total_points"] for s in results)

    if len(years) == 1:
        return results[0]

    return {
        "team_identifier": team_identifier,
        "total_seasons": len(results),
        "total_races": total_races,
        "total_points": total_points,
        "seasons": results
    }


def parse_driver_year_races(year: int, driver_id: str, driver_slug: str):
    """Parse a driver's races for a specific year."""
    cache_key = f"driver_races:{year}:{driver_id}:{driver_slug}"
    with CACHE_LOCK:
        if cache_key in RESPONSE_CACHE:
            return RESPONSE_CACHE[cache_key]

    url = f"https://www.formula1.com/en/results/{year}/drivers/{driver_id}/{driver_slug}"
    try:
        response = HTTP_SESSION.get(url, timeout=HTTP_TIMEOUT)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            table = soup.find("table")
            if not table:
                return None

            tbody = table.find("tbody") or table
            races = []
            for tr in tbody.find_all("tr"):
                cols = tr.find_all("td")
                if len(cols) >= 5:
                    for svg in cols[0].find_all("svg"):
                        svg.decompose()
                    gp = cols[0].get_text(strip=True)
                    date = cols[1].get_text(strip=True)
                    team = cols[2].get_text(strip=True)
                    pos = cols[3].get_text(strip=True)
                    pts = cols[4].get_text(strip=True)

                    try:
                        points = float(pts) if "." in pts else int(pts)
                    except ValueError:
                        points = pts

                    races.append({
                        "grand_prix": gp,
                        "date": date,
                        "team": team,
                        "race_position": int(pos) if pos.isdigit() else pos,
                        "points": points
                    })

            if races:
                result = {
                    "year": year,
                    "total_races": len(races),
                    "races": races
                }
                with CACHE_LOCK:
                    RESPONSE_CACHE[cache_key] = result
                return result
    except Exception:
        pass
    return None


def fetch_all_driver_races(driver_id: str, driver_slug: str, years: Optional[List[int]] = None):
    """Fetch all races for a driver across multiple years."""
    if years is not None and len(years) == 1:
        y = years[0]
        result = parse_driver_year_races(y, driver_id, driver_slug)
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"No race results found for driver '{driver_id}/{driver_slug}' in year {y}"
            )
        return {
            "driver_id": driver_id,
            "driver_slug": driver_slug,
            "total_seasons": 1,
            "total_races": result["total_races"],
            "seasons": [result]
        }

    years_to_check = years if years is not None else range(1950, datetime.date.today().year + 2)

    with ThreadPoolExecutor(max_workers=25) as executor:
        futures = [
            executor.submit(parse_driver_year_races, y, driver_id, driver_slug)
            for y in years_to_check
        ]
        results = [f.result() for f in futures if f.result() is not None]

    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"Driver '{driver_id}/{driver_slug}' not found or has no race results."
        )

    results.sort(key=lambda x: x["year"])
    total_races = sum(s["total_races"] for s in results)

    return {
        "driver_id": driver_id,
        "driver_slug": driver_slug,
        "total_seasons": len(results),
        "total_races": total_races,
        "seasons": results
    }


def parse_year_races_with_winners(year: int):
    """Parse all races for a year with winner information."""
    cache_key = f"year_races:{year}"
    with CACHE_LOCK:
        if cache_key in RESPONSE_CACHE:
            return RESPONSE_CACHE[cache_key]

    url = f"https://www.formula1.com/en/results/{year}/races"
    try:
        response = HTTP_SESSION.get(url, timeout=HTTP_TIMEOUT)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find("table")
        if not table:
            return None

        tbody = table.find("tbody") or table
        races = []
        for tr in tbody.find_all("tr"):
            cols = tr.find_all("td")
            if len(cols) >= 6:
                a_tag = cols[0].find("a")
                race_id = None
                race_slug = None
                if a_tag and "href" in a_tag.attrs:
                    m = re.search(r"/races/(\d+)/([^/]+)/race-result", a_tag["href"])
                    if m:
                        race_id = m.group(1)
                        race_slug = m.group(2)

                for svg in cols[0].find_all("svg"):
                    svg.decompose()
                gp = cols[0].get_text(strip=True)
                date = cols[1].get_text(strip=True)

                winner_spans = [s.get_text(strip=True) for s in cols[2].find_all("span") if not s.find_all("span") and s.get_text(strip=True)]
                winner_name = " ".join(winner_spans[:2]) if len(winner_spans) >= 2 else cols[2].get_text(strip=True)
                winner_code = winner_spans[2] if len(winner_spans) >= 3 else ""

                team = cols[3].get_text(strip=True)
                laps_text = cols[4].get_text(strip=True)
                time_text = cols[5].get_text(strip=True)

                races.append({
                    "grand_prix": gp,
                    "date": date,
                    "race_id": race_id,
                    "race_slug": race_slug,
                    "winner": winner_name,
                    "winner_code": winner_code,
                    "team": team,
                    "laps": int(laps_text) if laps_text.isdigit() else laps_text,
                    "time": time_text
                })

        if races:
            result = {
                "year": year,
                "total_races": len(races),
                "races": races
            }
            with CACHE_LOCK:
                RESPONSE_CACHE[cache_key] = result
            return result
    except Exception:
        pass
    return None


def fetch_detailed_race_result(year: int, race_id: str, race_slug: str):
    """Fetch the detailed race classification for a specific race."""
    cache_key = f"race_detail:{year}:{race_id}:{race_slug}"
    with CACHE_LOCK:
        if cache_key in RESPONSE_CACHE:
            return RESPONSE_CACHE[cache_key]

    url = f"https://www.formula1.com/en/results/{year}/races/{race_id}/{race_slug}/race-result"
    try:
        response = HTTP_SESSION.get(url, timeout=HTTP_TIMEOUT)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch data from Formula 1 website: {str(e)}")

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Unable to retrieve race result for {race_slug} ({year})"
        )

    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table")
    if not table:
        raise HTTPException(
            status_code=404,
            detail=f"No race result table found for race '{race_id}/{race_slug}' in {year}"
        )

    classification = []
    tbody = table.find("tbody") or table
    for tr in tbody.find_all("tr"):
        cols = tr.find_all("td")
        if len(cols) >= 7:
            pos_text = cols[0].get_text(strip=True)
            car_no = cols[1].get_text(strip=True)

            driver_spans = [s.get_text(strip=True) for s in cols[2].find_all("span") if not s.find_all("span") and s.get_text(strip=True)]
            driver_name = " ".join(driver_spans[:2]) if len(driver_spans) >= 2 else cols[2].get_text(strip=True)
            driver_code = driver_spans[2] if len(driver_spans) >= 3 else ""

            team = cols[3].get_text(strip=True)
            laps = cols[4].get_text(strip=True)
            time_retired = cols[5].get_text(strip=True)
            pts = cols[6].get_text(strip=True)

            try:
                points = float(pts) if "." in pts else int(pts)
            except ValueError:
                points = pts

            classification.append({
                "position": int(pos_text) if pos_text.isdigit() else pos_text,
                "car_number": int(car_no) if car_no.isdigit() else car_no,
                "driver": driver_name,
                "driver_code": driver_code,
                "team": team,
                "laps": int(laps) if laps.isdigit() else laps,
                "time_or_retired": time_retired,
                "points": points
            })

    if not classification:
        raise HTTPException(status_code=404, detail="No classification rows found for race result.")

    result = {
        "year": year,
        "race_id": race_id,
        "race_slug": race_slug,
        "total_classified": len(classification),
        "results": classification
    }
    with CACHE_LOCK:
        RESPONSE_CACHE[cache_key] = result
    return result


def race_matches_country(race: dict, country_query: str) -> bool:
    """Check if a race matches the given country query."""
    q = country_query.strip().lower()
    gp = race.get("grand_prix", "").lower()
    slug = race.get("race_slug", "").lower()

    if q in gp or q in slug:
        return True

    patterns = COUNTRY_MAP.get(q, [q])
    for p in patterns:
        if p in gp or p in slug:
            return True
    return False
