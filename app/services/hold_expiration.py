import asyncio

from app.core.redis_client import redis_client, publish_event
from app.core.redis_client import redis_client
from app.core.database import SessionLocal
from app.models.enums import SeatStatus
from app.models.seat import Seat


async def release_expired_seat(seat_id: int):
    db = SessionLocal()

    try:
        seat = (
            db.query(Seat)
            .filter(Seat.id == seat_id)
            .with_for_update()
            .first()
        )

        if not seat:
            return

        if seat.status != SeatStatus.HELD:
            return

        event_id = seat.event_id

        seat.status = SeatStatus.AVAILABLE

        db.commit()

        await publish_event(
            f"event:{event_id}:updates",
            {
                "seat_id": seat_id,
                "status": "available",
            },
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


async def listen_for_expired_holds():
    pubsub = redis_client.pubsub()

    pubsub.psubscribe("__keyevent@0__:expired")

    print("REDIS EXPIRATION LISTENER STARTED")

    try:
        while True:
            message = await asyncio.to_thread(
                pubsub.get_message,
                ignore_subscribe_messages=True,
                timeout=1.0,
            )

            if message:
                print("REDIS MESSAGE:", message)

                if message["type"] == "pmessage":
                    key = message["data"]

                    if key.startswith("seat_hold:"):
                        seat_id = int(key.split(":")[1])

                        print("HOLD EXPIRED:", seat_id)

                        await release_expired_seat(seat_id)

            await asyncio.sleep(0.1)

    finally:
        pubsub.close()