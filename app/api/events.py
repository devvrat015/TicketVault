from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.models.seat import Seat
from app.models.enums import SeatStatus
from app.api.deps import get_db
from app.api.deps import require_role
from app.models.enums import UserRole
from app.models.event import Event
from app.models.user import User
from app.models.venue import Venue
from app.schemas.event import EventCreate, EventOut, EventUpdate
from app.core.cache import (
    get_cache,
    set_cache,
    delete_cache,
)

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
    delete_cache("events:list:all")

    return new_event


@router.get(
    "/",
    response_model=list[EventOut],
)
def get_all_events(
    db: Session = Depends(get_db),
):
    cache_key = "events:list:all"

    cached = get_cache(cache_key)

    if cached is not None:
        return cached

    events = (
        db.query(Event)
        .options(joinedload(Event.venue))
        .all()
    )

    result = [
        EventOut.model_validate(event).model_dump(mode="json")
        for event in events
    ]

    set_cache(
        cache_key,
        result,
        ttl=60,
    )

    return result    


@router.get(
    "/{event_id}",
    response_model=EventOut,
)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
):
    cache_key = f"event:{event_id}"

    cached = get_cache(cache_key)

    if cached is not None:
        return cached

    event = (
        db.query(Event)
        .options(joinedload(Event.venue))
        .filter(Event.id == event_id)
        .first()
    )

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    result = EventOut.model_validate(event).model_dump(mode="json")

    set_cache(
        cache_key,
        result,
        ttl=60,
    )

    return result


@router.put(
    "/{event_id}",
    response_model=EventOut,
)
def update_event(
    event_id: int,
    event_data: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.ORGANIZER, UserRole.ADMIN)
    ),
):
    event = (
        db.query(Event)
        .options(joinedload(Event.venue))
        .filter(Event.id == event_id)
        .first()
    )

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    # Ownership check
    if (
        current_user.role != UserRole.ADMIN
        and event.organizer_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own events",
        )

    venue = db.query(Venue).filter(
        Venue.id == event_data.venue_id
    ).first()

    if venue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venue not found",
        )

    result = (
    db.query(Event)
    .filter(
        Event.id == event_id,
        Event.version == event_data.version,
    )
    .update(
        {
            Event.title: event_data.title,
            Event.description: event_data.description,
            Event.event_date: event_data.event_date,
            Event.venue_id: event_data.venue_id,
            Event.version: Event.version + 1,
        },
        synchronize_session=False,
    )
)

    db.commit()

    if result == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Event was modified by someone else. Please refresh and try again.",
        )

    db.refresh(event)
    delete_cache(f"event:{event_id}")
    delete_cache("events:list:all")

    return event


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.ORGANIZER, UserRole.ADMIN)
    ),
):
    event = db.query(Event).filter(Event.id == event_id).first()

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    if (
        current_user.role != UserRole.ADMIN
        and event.organizer_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own events",
        )

    db.delete(event)
    db.commit()
    delete_cache(f"event:{event_id}")
    delete_cache("events:list:all")