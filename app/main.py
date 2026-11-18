from itertools import count
from typing import Annotated

from fastapi import FastAPI, File, Form, Path, Query, Response, UploadFile, status
from fastapi.responses import FileResponse

from app import storage
from app.errors import (
    DestinationNotFound,
    DocumentNotFound,
    FileTooLarge,
    TripNotFound,
    UnknownDestination,
    UnsupportedFileType,
    add_error_handlers,
    error_docs,
)
from app.schemas import DestinationOut, DocumentOut, TripCreate, TripOut

app = FastAPI(title="Trip Planner API", version="0.1.0")
add_error_handlers(app)

DESTINATIONS: list[DestinationOut] = [
    DestinationOut(id=1, name="Lisbon", country="PT", daily_cost_eur=90),
    DestinationOut(id=2, name="Kyoto", country="JP", daily_cost_eur=140),
    DestinationOut(id=3, name="Cape Town", country="ZA", daily_cost_eur=80),
    DestinationOut(id=4, name="Porto", country="PT", daily_cost_eur=75),
    DestinationOut(id=5, name="Osaka", country="JP", daily_cost_eur=120),
]
TRIPS: dict[int, TripOut] = {}
_trip_ids = count(start=1)  # 1, 2, 3, ... never repeats, even after a delete
DOCUMENTS: dict[int, DocumentOut] = {}
_document_ids = count(start=1)


# --- helpers: return a real object or raise -------------------------------------
def get_destination_or_raise(destination_id: int) -> DestinationOut:
    for destination in DESTINATIONS:
        if destination.id == destination_id:
            return destination
    raise DestinationNotFound()


def get_trip_or_raise(trip_id: int) -> TripOut:
    if trip_id not in TRIPS:
        raise TripNotFound()
    return TRIPS[trip_id]


# --- endpoints ----------------------------------------------------------------------
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/destinations", responses=error_docs(422))
def list_destinations(
    country: Annotated[str | None, Query(pattern="^[A-Z]{2}$")] = None,
    max_daily_cost: Annotated[int | None, Query(ge=1)] = None,
    q: Annotated[str | None, Query(min_length=2, max_length=50)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[DestinationOut]:
    results = DESTINATIONS
    if country is not None:
        results = [d for d in results if d.country == country]
    if max_daily_cost is not None:
        results = [d for d in results if d.daily_cost_eur <= max_daily_cost]
    if q is not None:
        results = [d for d in results if q.lower() in d.name.lower()]
    return results[offset : offset + limit]


@app.get("/destinations/{destination_id}", responses=error_docs(404, 422))
def get_destination(destination_id: Annotated[int, Path(ge=1)]) -> DestinationOut:
    return get_destination_or_raise(destination_id)


@app.post("/trips", status_code=status.HTTP_201_CREATED, responses=error_docs(422))
def create_trip(trip: TripCreate, response: Response) -> TripOut:
    if not any(d.id == trip.destination_id for d in DESTINATIONS):
        raise UnknownDestination(trip.destination_id)
    new_trip = TripOut(id=next(_trip_ids), **trip.model_dump())
    TRIPS[new_trip.id] = new_trip
    response.headers["Location"] = f"/trips/{new_trip.id}"
    return new_trip


@app.get("/trips")
def list_trips() -> list[TripOut]:
    return list(TRIPS.values())


@app.get("/trips/{trip_id}", responses=error_docs(404, 422))
def get_trip(trip_id: Annotated[int, Path(ge=1)]) -> TripOut:
    return get_trip_or_raise(trip_id)


@app.delete(
    "/trips/{trip_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=error_docs(404, 422),
)
def delete_trip(trip_id: Annotated[int, Path(ge=1)]) -> None:
    get_trip_or_raise(trip_id)
    del TRIPS[trip_id]


@app.post(
    "/trips/{trip_id}/documents",
    status_code=status.HTTP_201_CREATED,
    responses=error_docs(404, 413, 415, 422),
)
def upload_document(
    trip_id: Annotated[int, Path(ge=1)],
    file: Annotated[UploadFile, File(description="PDF, PNG or JPEG, max 5 MB")],
    response: Response,
    note: Annotated[str | None, Form(max_length=200)] = None,
) -> DocumentOut:
    get_trip_or_raise(trip_id)

    data = file.file.read(storage.MAX_DOCUMENT_BYTES + 1)
    if len(data) > storage.MAX_DOCUMENT_BYTES:
        raise FileTooLarge("File too large (max 5 MB)")

    detected = storage.detect_type(data)
    if detected is None:
        raise UnsupportedFileType()
    content_type, extension = detected

    document = DocumentOut(
        id=next(_document_ids),
        trip_id=trip_id,
        filename=file.filename or "unnamed",
        content_type=content_type,
        size_bytes=len(data),
        note=note,
    )
    storage.save_document(storage.document_path(trip_id, document.id, extension), data)
    DOCUMENTS[document.id] = document
    response.headers["Location"] = f"/trips/{trip_id}/documents/{document.id}"
    return document


@app.get("/trips/{trip_id}/documents", responses=error_docs(404, 422))
def list_documents(trip_id: Annotated[int, Path(ge=1)]) -> list[DocumentOut]:
    get_trip_or_raise(trip_id)
    return [d for d in DOCUMENTS.values() if d.trip_id == trip_id]


@app.get(
    "/trips/{trip_id}/documents/{document_id}",
    response_class=FileResponse,
    responses=error_docs(404, 422),
)
def download_document(
    trip_id: Annotated[int, Path(ge=1)], document_id: Annotated[int, Path(ge=1)]
) -> FileResponse:
    document = DOCUMENTS.get(document_id)
    if document is None or document.trip_id != trip_id:
        raise DocumentNotFound()
    extension = storage.EXTENSIONS[document.content_type]
    return FileResponse(
        storage.document_path(trip_id, document_id, extension),
        media_type=document.content_type,
        filename=document.filename,
    )
