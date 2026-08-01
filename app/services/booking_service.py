from sqlalchemy.orm import Session

from app.core.exceptions import (
    EventNotFoundError,
    SeatNotAvailableError,
    SeatNotFoundError,
    SeatEventMismatchError,
)
from app.models.booking import Booking
from app.models.enums import BookingStatus, SeatStatus
from app.models.event import Event
from app.models.seat import Seat


def book_seat(
    db: Session,
    user_id: int,
    event_id: int,
    seat_id: int,
) -> Booking:

    event = db.query(Event).filter(Event.id == event_id).first()

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
        booking = Booking(
            user_id=user_id,
            event_id=event.id,
            total_amount=seat.price,
            status=BookingStatus.CONFIRMED,
        )

        db.add(booking)

        db.flush()

        seat.status = SeatStatus.BOOKED
        seat.booking_id = booking.id

        db.commit()
        db.refresh(booking)

        return booking

    except Exception:
        db.rollback()
        raise