from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.seat import Seat
from app.models.enums import SeatStatus
from app.api.deps import get_db
from app.api.deps import require_role
from app.models.enums import UserRole
from app.models.event import Event
from app.models.user import User
from app.models.venue import Venue
from app.schemas.event import EventCreate, EventOut

router = APIRouter(
    prefix="/events",
    tags=["Events"],
)


@router.post(
    "/",
    response_model=EventOut,
    status_code=status.HTTP_201_CREATED,
)
def create_event(
    event: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.ORGANIZER, UserRole.ADMIN)
    ),
):
    # Check if the venue exists
    venue = db.query(Venue).filter(Venue.id == event.venue_id).first()

    if venue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venue not found",
        )

    new_event = Event(
        title=event.title,
        description=event.description,
        event_date=event.event_date,
        venue_id=event.venue_id,
        organizer_id=current_user.id,
    )

    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    

    rows = ["A", "B", "C", "D", "E"]

    for row in rows:
        for seat_number in range(1, 11):
            seat = Seat(
                row_label=row,
                seat_number=seat_number,
                price=500,
                status=SeatStatus.AVAILABLE,
                event_id=new_event.id,
            )

            db.add(seat)

    db.commit()
    return new_event