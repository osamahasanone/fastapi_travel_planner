from typing import Annotated, TypedDict

from fastapi import FastAPI, HTTPException, Path, Query

app = FastAPI(title="Trip Planner API", version="0.1.0")


class Destination(TypedDict):
    id: int
    name: str
    country: str
    daily_cost_eur: int


DESTINATIONS: list[Destination] = [
    {"id": 1, "name": "Lisbon", "country": "PT", "daily_cost_eur": 90},
    {"id": 2, "name": "Kyoto", "country": "JP", "daily_cost_eur": 140},
    {"id": 3, "name": "Cape Town", "country": "ZA", "daily_cost_eur": 80},
    {"id": 4, "name": "Porto", "country": "PT", "daily_cost_eur": 75},
    {"id": 5, "name": "Osaka", "country": "JP", "daily_cost_eur": 120},
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
) -> list[Destination]:
    results = DESTINATIONS
    if country is not None:
        results = [d for d in results if d["country"] == country]
    if max_daily_cost is not None:
        results = [d for d in results if d["daily_cost_eur"] <= max_daily_cost]
    if q is not None:
        results = [d for d in results if q.lower() in d["name"].lower()]
    return results[offset : offset + limit]


@app.get("/destinations/{destination_id}")
def get_destination(destination_id: Annotated[int, Path(ge=1)]) -> Destination:
    for destination in DESTINATIONS:
        if destination["id"] == destination_id:
            return destination
    raise HTTPException(status_code=404, detail="Destination not found")
