from fastapi import FastAPI

app = FastAPI(title="Trip Planner API", version="0.1.0")


DESTINATIONS = [
    {"id": 1, "name": "Lisbon", "country": "PT"},
    {"id": 2, "name": "Kyoto", "country": "JP"},
    {"id": 3, "name": "Cape Town", "country": "ZA"},
]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/destinations")
def list_destinations() -> list[dict]:
    return DESTINATIONS
