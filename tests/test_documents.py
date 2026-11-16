from pathlib import Path

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app import storage
from app.main import app

client = TestClient(app)

TRIP = {
    "title": "Spring in Lisbon",
    "destination_id": 1,
    "start_date": "2027-04-10",
    "end_date": "2027-04-15",
}
PDF = b"%PDF-1.7\n" + b"x" * 100


@pytest.fixture(autouse=True)
def upload_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Write uploads into a temporary folder that pytest deletes afterwards."""
    monkeypatch.setattr(storage, "UPLOAD_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def trip_id() -> int:
    return client.post("/trips", json=TRIP).json()["id"]


def upload(trip_id: int, content: bytes, name: str = "ticket.pdf", **data: str):
    return client.post(
        f"/trips/{trip_id}/documents",
        files={"file": (name, content, "application/pdf")},
        data=data,
    )


def test_create_trip_sets_location_header() -> None:
    response = client.post("/trips", json=TRIP)
    assert response.headers["location"] == f"/trips/{response.json()['id']}"


def test_upload_pdf_is_201_and_stored(trip_id: int, upload_dir: Path) -> None:
    response = upload(trip_id, PDF, note="outbound flight")
    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["content_type"] == "application/pdf"
    assert body["size_bytes"] == len(PDF)
    assert body["note"] == "outbound flight"
    assert response.headers["location"] == f"/trips/{trip_id}/documents/{body['id']}"
    assert (upload_dir / str(trip_id) / f"{body['id']}.pdf").read_bytes() == PDF


def test_fake_pdf_is_415(trip_id: int) -> None:
    response = upload(trip_id, b"MZ\x90\x00 really an exe")
    assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    assert response.json() == {"detail": "Only PDF, PNG or JPEG files"}


def test_too_large_is_413(trip_id: int, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(storage, "MAX_DOCUMENT_BYTES", 50)
    response = upload(trip_id, PDF)
    assert response.status_code == status.HTTP_413_CONTENT_TOO_LARGE
    assert response.json() == {"detail": "File too large (max 5 MB)"}


def test_upload_to_unknown_trip_is_404() -> None:
    response = upload(9999, PDF)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Trip not found"}


def test_client_filename_is_not_used_as_path(trip_id: int, upload_dir: Path) -> None:
    body = upload(trip_id, PDF, name="../../etc/passwd").json()
    assert body["filename"] == "../../etc/passwd"
    assert [p.name for p in (upload_dir / str(trip_id)).iterdir()] == [
        f"{body['id']}.pdf"
    ]


def test_list_and_download(trip_id: int) -> None:
    document_id = upload(trip_id, PDF, name="flight.pdf").json()["id"]
    listed = client.get(f"/trips/{trip_id}/documents").json()
    assert [d["id"] for d in listed] == [document_id]

    response = client.get(f"/trips/{trip_id}/documents/{document_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.content == PDF
    assert response.headers["content-type"] == "application/pdf"
    assert 'filename="flight.pdf"' in response.headers["content-disposition"]


def test_download_from_wrong_trip_is_404(trip_id: int) -> None:
    document_id = upload(trip_id, PDF).json()["id"]
    other_trip = client.post("/trips", json=TRIP).json()["id"]
    response = client.get(f"/trips/{other_trip}/documents/{document_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
