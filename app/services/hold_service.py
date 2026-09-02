from sqlalchemy.orm import Session

from app.core.exceptions import (
    EventNotFoundError,
    SeatNotAvailableError,
    SeatNotFoundError,
    SeatEventMismatchError,
)

from app.models.enums import SeatStatus
from app.models.event import Event
from app.models.seat import Seat


def hold_seat(
    db: Session,
    redis_client,
    user_id: int,
    event_id: int,
    seat_id: int,
):
    event = (
        db.query(Event)
        .filter(Event.id == event_id)
        .first()
    )

    if not event:
        raise EventNotFoundError()

    seat = (
        db.query(Seat)
        .filter(Seat.id == seat_id)
        .with_for_update()
        .first()
    )

    if not seat:
        raise SeatNotFoundError()

    if seat.event_id != event_id:
        raise SeatEventMismatchError()

    if seat.status != SeatStatus.AVAILABLE:
        raise SeatNotAvailableError()

    try:
        seat.status = SeatStatus.HELD

        db.commit()

        redis_key = f"seat_hold:{seat_id}"

        redis_client.setex(
            redis_key,
            300,
            str(user_id),
        )

        return {
            "seat_id": seat_id,
            "user_id": user_id,
            "status": SeatStatus.HELD,
            "expires_in": 300,
        }

    except Exception:
        db.rollback()
        raise