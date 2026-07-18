from datetime import datetime

from pydantic import BaseModel, field_validator

from app.schemas.venue import VenueOut


class EventCreate(BaseModel):
    title: str
    description: str
    event_date: datetime
    venue_id: int

    @field_validator("event_date")
    @classmethod
    def validate_event_date(cls, value: datetime):
        if value < datetime.now():
            raise ValueError("Event date cannot be in the past")
        return value


class EventOut(BaseModel):
    id: int
    title: str
    description: str
    event_date: datetime

    venue: VenueOut

    model_config = {
        "from_attributes": True
    }