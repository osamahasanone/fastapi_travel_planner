from fastapi import status
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

VALID = {
    "title": "Spring in Lisbon",
    "destination_id": 1,
    "start_date": "2027-04-10",
    "end_date": "2027-04-15",
    "travelers": 2,
    "budget_eur": 1200,
}


def errors(response) -> list[tuple[list, str]]:
    return [(e["loc"], e["type"]) for e in response.json()["detail"]]


def test_create_trip_returns_it_with_an_id() -> None:
    response = client.post("/trips", json=VALID)
    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["id"] >= 1
    assert body["title"] == "Spring in Lisbon"
    assert body["start_date"] == "2027-04-10"


def test_defaults_are_filled_in() -> None:
    minimal = {
        k: VALID[k] for k in ("title", "destination_id", "start_date", "end_date")
    }
    body = client.post("/trips", json=minimal).json()
    assert body["travelers"] == 1
    assert body["budget_eur"] is None


def test_created_trip_can_be_read_back() -> None:
    trip_id = client.post("/trips", json=VALID).json()["id"]
    response = client.get(f"/trips/{trip_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == trip_id
    assert trip_id in [t["id"] for t in client.get("/trips").json()]


def test_unknown_trip_is_404() -> None:
    response = client.get("/trips/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Trip not found"}


def test_end_date_must_be_after_start_date() -> None:
    response = client.post("/trips", json={**VALID, "end_date": "2027-04-01"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert errors(response) == [(["body", "end_date"], "value_error")]


def test_unknown_fields_are_rejected() -> None:
    response = client.post("/trips", json={**VALID, "budjet_eur": 900})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert errors(response) == [(["body", "budjet_eur"], "extra_forbidden")]


def test_every_bad_field_is_reported() -> None:
    response = client.post("/trips", json={**VALID, "travelers": 0, "title": ""})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert sorted(errors(response)) == [
        (["body", "title"], "string_too_short"),
        (["body", "travelers"], "greater_than_equal"),
    ]


def test_unknown_destination_is_422() -> None:
    response = client.post("/trips", json={**VALID, "destination_id": 99})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert errors(response) == [(["body", "destination_id"], "destination_not_found")]


def test_missing_body_is_422() -> None:
    response = client.post("/trips")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert errors(response) == [(["body"], "missing")]


def test_response_includes_computed_nights() -> None:
    body = client.post("/trips", json=VALID).json()
    assert body["nights"] == 5  # noqa: PLR2004


def test_delete_trip_is_204_with_empty_body() -> None:
    trip_id = client.post("/trips", json=VALID).json()["id"]
    response = client.delete(f"/trips/{trip_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b""
    assert client.get(f"/trips/{trip_id}").status_code == status.HTTP_404_NOT_FOUND


def test_delete_unknown_trip_is_404() -> None:
    response = client.delete("/trips/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Trip not found"}


def test_ids_are_not_reused_after_delete() -> None:
    first = client.post("/trips", json=VALID).json()["id"]
    second = client.post("/trips", json=VALID).json()["id"]
    client.delete(f"/trips/{first}")
    third = client.post("/trips", json=VALID).json()["id"]
    assert third not in (first, second)
    assert client.get(f"/trips/{second}").status_code == status.HTTP_200_OK
