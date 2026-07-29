from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import BookingStatus


class BookingResponse(BaseModel):
    id: int
    user_id: int
    event_id: int
    total_amount: Decimal
    status: BookingStatus
    created_at: datetime

    model_config = {
        "from_attributes": True
    }