from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.redis_client import async_redis_client
from app.core.idempotency import (
    check_and_store_idempotency,
    store_idempotent_result,
)
from app.models.user import User
from app.models.seat import Seat
from app.models.enums import SeatStatus
from app.services.payment_service import create_checkout_session


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


@router.post("/checkout/{seat_id}")
async def create_checkout(
    seat_id: int,
    idempotency_key: str = Header(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # 1. Check idempotency
    is_duplicate, stored = await check_and_store_idempotency(
        async_redis_client,
        idempotency_key,
    )

    if is_duplicate:
        if stored is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Checkout request is already being processed.",
            )

        return stored

    # 2. Find the seat
    seat = (
        db.query(Seat)
        .filter(Seat.id == seat_id)
        .first()
    )

    if not seat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seat not found",
        )

    # 3. Seat must be held
    if seat.status != SeatStatus.HELD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seat must be held before checkout",
        )

    # 4. Create Stripe Checkout Session
    try:
        session = create_checkout_session(
            seat=seat,
            user=current_user,
            idempotency_key=idempotency_key,
        )

        result = {
            "checkout_url": session.url,
        }

        # 5. Store result for future retries
        await store_idempotent_result(
            async_redis_client,
            idempotency_key,
            result,
        )

        return result

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session",
        )