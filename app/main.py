from itertools import count
from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Path, Query, status

from app.schemas import DestinationOut, ErrorMessage, TripCreate, TripOut

app = FastAPI(title="Trip Planner API", version="0.1.0")

NOT_FOUND: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorMessage, "description": "Not found"}
}

DESTINATIONS: list[DestinationOut] = [
    DestinationOut(id=1, name="Lisbon", country="PT", daily_cost_eur=90),
    DestinationOut(id=2, name="Kyoto", country="JP", daily_cost_eur=140),
    DestinationOut(id=3, name="Cape Town", country="ZA", daily_cost_eur=80),
    DestinationOut(id=4, name="Porto", country="PT", daily_cost_eur=75),
    DestinationOut(id=5, name="Osaka", country="JP", daily_cost_eur=120),
]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/destinations")
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


@app.get("/destinations/{destination_id}", responses=NOT_FOUND)
def get_destination(destination_id: Annotated[int, Path(ge=1)]) -> DestinationOut:
    for destination in DESTINATIONS:
        if destination.id == destination_id:
            return destination
    raise HTTPException(status_code=404, detail="Destination not found")


TRIPS: dict[int, TripOut] = {}
_trip_ids = count(start=1)  # 1, 2, 3, ... never repeats, even after a delete


@app.post("/trips", status_code=status.HTTP_201_CREATED)
def create_trip(trip: TripCreate) -> TripOut:
    if not any(d.id == trip.destination_id for d in DESTINATIONS):
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "type": "destination_not_found",
                    "loc": ["body", "destination_id"],
                    "msg": "Destination not found",
                    "input": trip.destination_id,
                }
            ],
        )
    new_trip = TripOut(id=next(_trip_ids), **trip.model_dump())
    TRIPS[new_trip.id] = new_trip
    return new_trip


@app.get("/trips")
def list_trips() -> list[TripOut]:
    return list(TRIPS.values())


@app.get("/trips/{trip_id}", responses=NOT_FOUND)
def get_trip(trip_id: Annotated[int, Path(ge=1)]) -> TripOut:
    if trip_id not in TRIPS:
        raise HTTPException(status_code=404, detail="Trip not found")
    return TRIPS[trip_id]


@app.delete(
    "/trips/{trip_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND,
)
def delete_trip(trip_id: Annotated[int, Path(ge=1)]) -> None:
    if trip_id not in TRIPS:
        raise HTTPException(status_code=404, detail="Trip not found")
    del TRIPS[trip_id]
