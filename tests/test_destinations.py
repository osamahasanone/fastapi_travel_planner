from fastapi import status
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def names(response) -> list[str]:
    return [d["name"] for d in response.json()]


def test_get_one_destination() -> None:
    response = client.get("/destinations/4")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Porto"


def test_unknown_destination_is_404() -> None:
    response = client.get("/destinations/99")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Destination not found"}


def test_destination_id_must_be_positive_int() -> None:
    for bad in ("abc", "0"):
        response = client.get(f"/destinations/{bad}")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        assert response.json()["detail"][0]["loc"] == ["path", "destination_id"]


def test_filter_by_country() -> None:
    assert names(client.get("/destinations?country=PT")) == ["Lisbon", "Porto"]


def test_filters_combine() -> None:
    response = client.get("/destinations?country=JP&max_daily_cost=130")
    assert names(response) == ["Osaka"]


def test_search_by_name() -> None:
    assert names(client.get("/destinations?q=to")) == ["Kyoto", "Cape Town", "Porto"]


def test_limit_and_offset() -> None:
    assert names(client.get("/destinations?limit=2&offset=1")) == ["Kyoto", "Cape Town"]


def test_invalid_query_values_are_422() -> None:
    for url, field in [
        ("/destinations?country=pt", "country"),
        ("/destinations?limit=0", "limit"),
        ("/destinations?limit=101", "limit"),
        ("/destinations?max_daily_cost=cheap", "max_daily_cost"),
    ]:
        response = client.get(url)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, url
        assert response.json()["detail"][0]["loc"] == ["query", field]
