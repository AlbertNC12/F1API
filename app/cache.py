"""
Cache and registry management module.
Handles driver registry loading and response caching.
"""
import datetime
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

from bs4 import BeautifulSoup

from .config import HTTP_SESSION, HTTP_TIMEOUT

# Thread-safe storage for driver registry
REGISTRY_LOCK = threading.Lock()
DRIVER_REGISTRY: Dict[str, dict] = {}

# Thread-safe response cache
CACHE_LOCK = threading.Lock()
RESPONSE_CACHE: Dict[str, dict] = {}


def load_driver_directory(force_reload: bool = False) -> Dict[str, dict]:
    """
    Load the driver registry from Formula 1 website for all years.
    Returns a dictionary mapping driver slugs to driver info.
    Uses thread pooling for concurrent year scraping.
    """
    global DRIVER_REGISTRY
    if DRIVER_REGISTRY and not force_reload:
        return DRIVER_REGISTRY

    with REGISTRY_LOCK:
        if DRIVER_REGISTRY and not force_reload:
            return DRIVER_REGISTRY

        current_year = datetime.date.today().year + 1
        years = range(1950, current_year + 1)

        def scrape_drivers_for_year(year: int) -> List[dict]:
            url = f"https://www.formula1.com/en/results/{year}/drivers"
            try:
                resp = HTTP_SESSION.get(url, timeout=HTTP_TIMEOUT)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.content, "html.parser")
                    table = soup.find("table")
                    if not table:
                        return []
                    tbody = table.find("tbody") or table
                    found = []
                    for tr in tbody.find_all("tr"):
                        cols = tr.find_all("td")
                        if len(cols) >= 5:
                            a = cols[1].find("a")
                            d_id, d_slug = None, None
                            if a and "href" in a.attrs:
                                m = re.search(r"/en/results/\d+/drivers/([A-Z0-9]+)/([a-z0-9\-]+)", a["href"])
                                if m:
                                    d_id, d_slug = m.group(1), m.group(2)

                            raw_spans = [s.get_text(strip=True) for s in cols[1].find_all("span") if not s.find_all("span") and s.get_text(strip=True)]
                            name = " ".join(raw_spans[:2]) if len(raw_spans) >= 2 else cols[1].get_text(strip=True)
                            code = raw_spans[2] if len(raw_spans) >= 3 else ""
                            nat = cols[2].get_text(strip=True)
                            team = cols[3].get_text(strip=True)

                            if d_slug and d_id:
                                found.append({
                                    "driver_id": d_id,
                                    "driver_slug": d_slug,
                                    "name": name,
                                    "code": code,
                                    "nationality": nat,
                                    "team": team,
                                    "year": year
                                })
                    return found
            except Exception:
                pass
            return []

        with ThreadPoolExecutor(max_workers=25) as executor:
            results = executor.map(scrape_drivers_for_year, years)
            registry = {}
            for driver_list in results:
                for d in driver_list:
                    slug = d["driver_slug"]
                    if slug not in registry:
                        registry[slug] = {
                            "driver_id": d["driver_id"],
                            "driver_slug": d["driver_slug"],
                            "name": d["name"],
                            "code": d["code"],
                            "nationality": d["nationality"],
                            "teams": [d["team"]] if d.get("team") else [],
                            "years": [d["year"]],
                            "team_years": {d["team"]: [d["year"]]} if d.get("team") else {}
                        }
                    else:
                        entry = registry[slug]
                        if d.get("team") and d["team"] not in entry["teams"]:
                            entry["teams"].append(d["team"])
                        if d["year"] not in entry["years"]:
                            entry["years"].append(d["year"])
                            entry["years"].sort()
                        # Track team-year pairs
                        if d.get("team"):
                            if d["team"] not in entry["team_years"]:
                                entry["team_years"][d["team"]] = []
                            if d["year"] not in entry["team_years"][d["team"]]:
                                entry["team_years"][d["team"]].append(d["year"])
                                entry["team_years"][d["team"]].sort()

        if registry:
            DRIVER_REGISTRY = registry

    return DRIVER_REGISTRY
