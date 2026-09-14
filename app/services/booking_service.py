from sqlalchemy.orm import Session
import logging
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

logger = logging.getLogger(__name__)

def book_seat(
    db: Session,
    redis_client,
    user_id: int,
    event_id: int,
    seat_id: int,
) -> Booking:

    

    try:

        logger.info(
        "booking attempt started",
        extra={
            "user_id": user_id,
            "event_id": event_id,
            "seat_id": seat_id,
        },
        )

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

        if seat.status == SeatStatus.BOOKED:
            raise SeatNotAvailableError()

        if seat.status == SeatStatus.HELD:
            redis_key = f"seat_hold:{seat_id}"
            hold_user_id = redis_client.get(redis_key)

            if hold_user_id is None:
                raise SeatNotAvailableError()

            if int(hold_user_id) != user_id:
                raise SeatNotAvailableError()

    
        booking = Booking(
            user_id=user_id,
            event_id=event.id,
            total_amount=seat.price,
            status=BookingStatus.CONFIRMED,
        )

        db.add(booking)

        db.flush()

        original_status = seat.status

        seat.status = SeatStatus.BOOKED
        seat.booking_id = booking.id

        if original_status == SeatStatus.HELD:
            redis_client.delete(f"seat_hold:{seat_id}")

        db.commit()
        db.refresh(booking)

        logger.info(
            "booking created successfully",
            extra={
                "booking_id": booking.id,
                "user_id": user_id,
                "event_id": event_id,
                "seat_id": seat_id,
            },
        )

        return booking

    except Exception:
        db.rollback()

        logger.exception(
            "booking failed",
            extra={
                "user_id": user_id,
                "event_id": event_id,
                "seat_id": seat_id,
            },
        )

        raise