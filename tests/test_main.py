from fastapi import status
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}


def test_list_destinations() -> None:
    response = client.get("/destinations")
    assert response.status_code == status.HTTP_200_OK
    assert [d["name"] for d in response.json()] == ["Lisbon", "Kyoto", "Cape Town"]


def test_unknown_path_is_404() -> None:
    assert client.get("/hotels").status_code == status.HTTP_404_NOT_FOUND


def test_wrong_method_is_405() -> None:
    assert (
        client.post("/destinations").status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    )
