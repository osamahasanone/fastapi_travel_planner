from fastapi import status
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_response_is_json() -> None:
    response = client.get("/destinations")
    assert response.headers["content-type"] == "application/json"


def test_405_says_which_methods_are_allowed() -> None:
    response = client.delete("/destinations")
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert response.headers["allow"] == "GET"


def test_errors_use_detail() -> None:
    response = client.get("/hotels")  # not built yet (Step 4)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Not Found"}
