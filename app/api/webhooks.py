import stripe

from fastapi import APIRouter, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.redis_client import async_redis_client, publish_event
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.redis_client import async_redis_client, publish_event
from app.core.idempotency import (
    check_and_store_idempotency,
    store_idempotent_result,
)
from app.models.booking import Booking
from app.models.seat import Seat
from app.models.enums import SeatStatus, BookingStatus


router = APIRouter()


async def finalize_booking(seat_id: int, user_id: int):
    db: Session = SessionLocal()

    try:
        seat = (
            db.query(Seat)
            .filter(Seat.id == seat_id)
            .with_for_update()
            .first()
        )

        if not seat:
            raise ValueError("Seat not found")

        if seat.status != SeatStatus.HELD:
            return None

        booking = Booking(
            user_id=user_id,
            event_id=seat.event_id,
            total_amount=seat.price,
            status=BookingStatus.CONFIRMED,
        )

        db.add(booking)
        db.flush()

        seat.status = SeatStatus.BOOKED
        seat.booking_id = booking.id

        # First make the database change permanent
        db.commit()

        # Now remove the temporary Redis hold
        await async_redis_client.delete(
            f"seat_hold:{seat_id}"
        )

        return {
            "booking_id": booking.id,
            "event_id": seat.event_id,
            "seat_id": seat.id,
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
):
    payload = await request.body()

    # 1. Verify that the webhook actually came from Stripe
    try:
        event = stripe.Webhook.construct_event(
            payload,
            stripe_signature,
            settings.STRIPE_WEBHOOK_SECRET,
        )

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid payload",
        )

    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=400,
            detail="Invalid webhook signature",
        )

    # 2. Prevent duplicate processing
    event_id = event["id"]

    is_duplicate, stored = await check_and_store_idempotency(
        async_redis_client,
        f"stripe_event:{event_id}",
    )

    if is_duplicate:
        return {"status": "already processed"}

    # 3. Handle successful checkout
    if event["type"] == "checkout.session.completed":

        session = event["data"]["object"]

        # Extra safety check
        if session.payment_status != "paid":
            return {"status": "payment not completed"}

        metadata = session.metadata or {}

        seat_id = int(metadata["seat_id"])
        user_id = int(metadata["user_id"])

        result = await finalize_booking(
            seat_id=seat_id,
            user_id=user_id,
        )

        # If booking was successfully created,
        # notify connected WebSocket clients.
        if result:
            await publish_event(
                f"event:{result['event_id']}:updates",
                {
                    "seat_id": result["seat_id"],
                    "status": "booked",
                },
            )

    # 4. Mark Stripe event as processed
    await store_idempotent_result(
        async_redis_client,
        f"stripe_event:{event_id}",
        {"processed": True},
    )

    return {"status": "success"}