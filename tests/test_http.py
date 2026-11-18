from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.errors import add_error_handlers
from app.main import app

client = TestClient(app)


def test_response_is_json() -> None:
    response = client.get("/destinations")
    assert response.headers["content-type"] == "application/json"


def test_405_says_which_methods_are_allowed() -> None:
    response = client.delete("/destinations")
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert response.headers["allow"] == "GET"
    assert response.json()["error"]["code"] == "method_not_allowed"


def test_unknown_path_uses_our_error_format() -> None:
    response = client.get("/hotels")  # no route has this path
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"error": {"code": "not_found", "message": "Not Found"}}


def test_422_uses_our_error_format() -> None:
    response = client.get("/destinations?limit=0")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json() == {
        "error": {
            "code": "validation_error",
            "message": "Invalid request",
            "details": [
                {
                    "loc": ["query", "limit"],
                    "msg": "Input should be greater than or equal to 1",
                    "type": "greater_than_equal",
                }
            ],
        }
    }


def test_a_bug_is_500_without_details() -> None:
    crashing = FastAPI()
    add_error_handlers(crashing)

    @crashing.get("/boom")
    def boom() -> dict:
        raise RuntimeError("database password is hunter2")

    response = TestClient(crashing, raise_server_exceptions=False).get("/boom")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {
        "error": {"code": "internal_error", "message": "Internal server error"}
    }
    assert "hunter2" not in response.text
