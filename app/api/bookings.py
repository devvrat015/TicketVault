from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.deps import get_current_active_user
from app.models.booking import Booking
from app.models.event import Event
from app.models.seat import Seat
from app.models.user import User
from app.models.enums import SeatStatus, BookingStatus
from app.schemas.booking import BookingResponse

router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"]
)

@router.post(
    "/{event_id}/book-seat/{seat_id}",
    response_model=BookingResponse
)
def book_seat(
    event_id: int,
    seat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:
     raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Event not found"
    )

    seat = db.query(Seat).filter(Seat.id == seat_id).first()

    if not seat:
     raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Seat not found"
    )

    if seat.event_id != event_id:
     raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Seat does not belong to this event"
    )

    if seat.status != SeatStatus.AVAILABLE:
     raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Seat not available"
    )

    try:
    # Create the booking
        booking = Booking(
            user_id=current_user.id,
            event_id=event.id,
            total_amount=seat.price,
            status=BookingStatus.CONFIRMED,
        )

        db.add(booking)

        # Flush to generate booking.id before commit
        db.flush()

        # Update the seat
        seat.status = SeatStatus.BOOKED
        seat.booking_id = booking.id

        # Commit the transaction
        db.commit()

        # Refresh the booking object
        db.refresh(booking)

        return booking

    except HTTPException:
        raise

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to book seat."
        )