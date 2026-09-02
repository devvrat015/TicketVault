from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.exceptions import (
    EventNotFoundError,
    SeatNotAvailableError,
    SeatNotFoundError,
    SeatEventMismatchError,
)
from app.models.user import User
from app.schemas.booking import BookingResponse
from app.services.booking_service import book_seat
from app.core.redis_client import redis_client
from app.services import hold_service
from app.core.redis_client import redis_client, publish_event

router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"],
)


@router.post(
    "/{event_id}/book-seat/{seat_id}",
    response_model=BookingResponse,
)
async def book_seat_route(
    event_id: int,
    seat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        booking = book_seat(
        db=db,
        redis_client=redis_client,
        user_id=current_user.id,
        event_id=event_id,
        seat_id=seat_id,
        )

        await publish_event(
        f"event:{event_id}:updates",
        {
        "seat_id": seat_id,
        "status": "booked",
        },
        )

        return booking

    except EventNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    except SeatNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seat not found",
        )

    except SeatEventMismatchError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seat does not belong to this event",
        )

    except SeatNotAvailableError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seat not available",
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to book seat.",
        )


@router.post("/events/{event_id}/seats/{seat_id}/hold")
async def hold_seat_route(
    event_id: int,
    seat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        hold = hold_service.hold_seat(
            db=db,
            redis_client=redis_client,
            user_id=current_user.id,
            event_id=event_id,
            seat_id=seat_id,
        )

        await publish_event(
            f"event:{event_id}:updates",
            {
            "seat_id": seat_id,
            "status": "held",
            },
        )

        return hold

    except EventNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    except SeatNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Seat not found",
        )

    except SeatEventMismatchError:
        raise HTTPException(
            status_code=400,
            detail="Seat does not belong to this event",
        )

    except SeatNotAvailableError:
        raise HTTPException(
            status_code=400,
            detail="Seat not available",
        )