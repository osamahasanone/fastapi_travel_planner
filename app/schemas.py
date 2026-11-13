from datetime import date

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    computed_field,
    field_validator,
)


class DestinationOut(BaseModel):
    """A destination as the API returns it."""

    id: int
    name: str
    country: str
    daily_cost_eur: int


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


class TripOut(TripCreate):
    """A stored trip as the API returns it: the client's fields + id + nights."""

    id: int

    @computed_field
    @property
    def nights(self) -> int:
        return (self.end_date - self.start_date).days


class ErrorMessage(BaseModel):
    """The body of a 404: {"detail": "..."}. Used to document errors in OpenAPI."""

    detail: str
