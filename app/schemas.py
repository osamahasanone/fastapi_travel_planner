from datetime import date

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class TripCreate(BaseModel):
    """What the client sends to create a trip (the request body)."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=80)
    destination_id: int = Field(ge=1)
    start_date: date
    end_date: date  # declared after start_date, so start_date is in info.data
    travelers: int = Field(default=1, ge=1, le=20)
    budget_eur: int | None = Field(default=None, ge=1)

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v: date, info: ValidationInfo) -> date:
        if "start_date" in info.data and v <= info.data["start_date"]:
            raise ValueError("must be after start_date")
        return v


class Trip(TripCreate):
    """A stored trip: everything the client sent, plus the id the server gave it."""

    id: int
