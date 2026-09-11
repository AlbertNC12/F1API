from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to the Formula 1 API!",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_standings_driver_single_year():
    response = client.get("/standings/drivers/2023")
    assert response.status_code == 200
    data = response.json()
    assert data["year"] == 2023
    assert data["total_drivers"] > 0
    assert len(data["standings"]) > 0


def test_standings_driver_year_range():
    response = client.get("/standings/drivers/2023-2024")
    assert response.status_code == 200
    data = response.json()
    assert data["year_range"] == "2023-2024"
    assert data["total_seasons"] == 2
    assert len(data["seasons"]) == 2
    assert data["seasons"][0]["year"] == 2023
    assert data["seasons"][1]["year"] == 2024


def test_year_validation_boundaries():
    response_low = client.get("/standings/drivers/1900")
    assert response_low.status_code == 422

    response_high = client.get("/standings/drivers/2999")
    assert response_high.status_code == 422


def test_teams_standings_single_and_range():
    response_single = client.get("/standings/teams/2023")
    assert response_single.status_code == 200
    assert response_single.json()["year"] == 2023

    response_range = client.get("/standings/teams/2022-2023")
    assert response_range.status_code == 200
    data = response_range.json()
    assert data["total_seasons"] == 2


def test_team_performance_single_year():
    response = client.get("/teams/Mercedes/performance?year=2023")
    assert response.status_code == 200
    data = response.json()
    assert data["year"] == 2023
    assert "Mercedes" in data["team_slug"]
    assert data["total_races"] == 22
    assert data["total_points"] > 0
    assert len(data["races"]) == 22


def test_team_performance_year_range():
    response = client.get("/teams/Mercedes/performance?year=2022-2023")
    assert response.status_code == 200
    data = response.json()
    assert data["total_seasons"] == 2


def test_drivers_filter_nationality_british():
    response = client.get("/drivers?nationality=British")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    # Hamilton should be in British drivers
    hamilton_found = any("hamilton" in d["driver_slug"] for d in data["drivers"])
    assert hamilton_found


def test_drivers_filter_name_hamilton():
    response = client.get("/drivers?name=hamilton")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert "lewis-hamilton" in data["drivers"][0]["driver_slug"]


def test_drivers_filter_team_alfa_romeo():
    response = client.get("/drivers?teams=alfa romeo")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    # Check that returned drivers drove for Alfa Romeo
    for d in data["drivers"]:
        assert any("alfa romeo" in t.lower() for t in d.get("teams", []))


def test_drivers_filter_combined_name_and_year():
    response = client.get("/drivers?name=hamilton&year=2023")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert 2023 in data["drivers"][0]["years"]


def test_driver_short_endpoint_antonelli():
    response = client.get("/drivers/antonelli/races")
    assert response.status_code == 200
    data = response.json()
    assert data["driver_id"] == "ANDANT01"
    assert data["driver_slug"] == "kimi-antonelli"
    assert data["total_races"] > 0


def test_races_filter_year_2024():
    response = client.get("/races?year=2024")
    assert response.status_code == 200
    data = response.json()
    assert data["year"] == 2024
    assert data["total_races"] == 24


def test_races_filter_country_italy():
    response = client.get("/races?year=2023&country=Italy")
    assert response.status_code == 200
    data = response.json()
    assert data["total_races"] >= 1
    for s in data["seasons"]:
        for r in s["races"]:
            assert "italy" in r["grand_prix"].lower() or "monza" in r["grand_prix"].lower()


def test_detailed_race_result_explicit():
    response = client.get("/races/2026/1279/australia/race-result")
    assert response.status_code == 200
    data = response.json()
    assert data["year"] == 2026
    assert data["race_id"] == "1279"
    assert data["race_slug"] == "australia"
    assert data["total_classified"] > 0


def test_detailed_race_result_by_slug():
    response = client.get("/races/2026/australia")
    assert response.status_code == 200
    data = response.json()
    assert data["year"] == 2026
    assert data["race_slug"] == "australia"
    assert data["total_classified"] > 0
