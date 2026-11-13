from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
SPEC = client.get("/openapi.json").json()


def responses(path: str, method: str) -> dict:
    return SPEC["paths"][path][method]["responses"]


def test_create_trip_documents_201() -> None:
    assert "201" in responses("/trips", "post")


def test_404_is_documented_with_its_body() -> None:
    for path, method in [
        ("/trips/{trip_id}", "get"),
        ("/trips/{trip_id}", "delete"),
        ("/destinations/{destination_id}", "get"),
    ]:
        not_found = responses(path, method)["404"]
        schema = not_found["content"]["application/json"]["schema"]
        assert schema == {"$ref": "#/components/schemas/ErrorMessage"}


def test_delete_trip_documents_204_without_body() -> None:
    assert "content" not in responses("/trips/{trip_id}", "delete")["204"]


def test_trip_out_schema_includes_nights() -> None:
    trip_out = SPEC["components"]["schemas"]["TripOut"]
    assert "nights" in trip_out["properties"]
