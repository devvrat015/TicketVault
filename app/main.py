from fastapi import FastAPI
from app.core.config import settings
import asyncio
import logging
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.auth import router as auth_router
from app.api.organizer import router as organizer_router
from app.api.venues import router as venues_router
from app.api.events import router as events_router
from app.api.bookings import router as bookings_router
from app.api.ws import router as ws_router
from app.services.hold_expiration import listen_for_expired_holds
from app.core.pubsub_listener import listen_for_events
from app.core.redis_client import async_redis_client
from app.api.payments import router as payments_router
from app.api.webhooks import router as webhooks_router
from app.core.logging_config import setup_logging

setup_logging()

logger = logging.getLogger(__name__)
class RequestLoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start = time.time()

        logger.info(
            "request started",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
            },
        )

        try:
            response = await call_next(request)

        except Exception:
            duration_ms = round((time.time() - start) * 1000, 2)

            logger.exception(
                "request failed",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                    "duration_ms": duration_ms,
                },
            )

            raise

        duration_ms = round((time.time() - start) * 1000, 2)

        logger.info(
            "request completed",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        response.headers["X-Request-ID"] = request_id

        return response

    
async def lifespan(app: FastAPI):

    await async_redis_client.config_set(
    "notify-keyspace-events",
    "Ex"
    )
    
    expired_holds_task = asyncio.create_task(
        listen_for_expired_holds()
    )

    pubsub_task = asyncio.create_task(
        listen_for_events()
    )

    yield

    expired_holds_task.cancel()
    pubsub_task.cancel()

    try:
        await expired_holds_task
    except asyncio.CancelledError:
        pass

    try:
        await pubsub_task
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan)

app.add_middleware(RequestLoggingMiddleware)

app.include_router(auth_router)
app.include_router(organizer_router)
app.include_router(venues_router)
app.include_router(events_router)
app.include_router(bookings_router)
app.include_router(ws_router)
app.include_router(payments_router)
app.include_router(webhooks_router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": settings.APP_NAME
    }

@app.get("/ready")
async def ready(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        await async_redis_client.ping()

        return {
            "status": "ready"
        }

    except Exception as e:
        logger.error(
            "readiness check failed",
            extra={
                "error": str(e),
            },
        )

        raise HTTPException(
            status_code=503,
            detail="Service not ready"
        )

    
@app.get("/checkout-success")
def checkout_success(session_id: str):
    return {
        "message": "Payment successful",
        "session_id": session_id,
    }

@app.get("/checkout-cancel")
def checkout_cancel():
    return {
        "message": "Payment cancelled"
    }
