from pydantic import BaseModel


class VenueCreate(BaseModel):
    name: str
    city: str
    address: str


class VenueOut(BaseModel):
    id: int
    name: str
    city: str
    address: str
    model_config = {
        "from_attributes": True
    }